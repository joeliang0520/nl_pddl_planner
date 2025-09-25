#!/usr/bin/env python3
"""
summarize_results.py

Walks a results directory tree, computes token counts, plan depths,
and writes two CSVs:
- tokens.csv (per model summary with avg depths)
- depth_accuracy.csv (LLM correctness % by GT depth, per LLM)
"""

from __future__ import annotations
import argparse, csv, json, re, sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")
def _strip_trailing_commas(s: str) -> str:
    prev = None
    while prev != s:
        prev = s
        s = _TRAILING_COMMA_RE.sub(r"\1", s)
    return s
def load_json_tolerant(path: Path) -> Any:
    raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except Exception:
        pass
    try:
        return json.loads(_strip_trailing_commas(raw))
    except Exception:
        first, last = raw.find("{"), raw.rfind("}")
        if first != -1 and last != -1 and last > first:
            return json.loads(raw[first:last+1])
        raise

def iter_items(data: Any) -> Iterable[Dict[str, Any]]:
    if isinstance(data, dict):
        inst = data.get("instances")
        if isinstance(inst, list) and all(isinstance(x, dict) for x in inst):
            yield from inst
        else:
            yield data
    elif isinstance(data, list):
        for x in data:
            if isinstance(x, dict):
                yield x
    else:
        raise TypeError("Bad JSON top-level")

def _try_import_tiktoken():
    try:
        import tiktoken; return tiktoken
    except Exception:
        return None
def _try_import_hf():
    try:
        from transformers import AutoTokenizer; return AutoTokenizer
    except Exception:
        return None
def _try_import_sentencepiece():
    try:
        import sentencepiece as spm; return spm
    except Exception:
        return None

class Tokenizer:
    def count(self, text: str) -> int: raise NotImplementedError
class WhitespaceTokenizer(Tokenizer):
    _re = re.compile(r"\S+")
    def count(self, text): return len(self._re.findall(text)) if text else 0
class TiktokenTokenizer(Tokenizer):
    def __init__(self, enc="cl100k_base"):
        tk = _try_import_tiktoken()
        if not tk:
            self._enc = None
            self._fb = WhitespaceTokenizer()
            return
        try:
            self._enc = tk.get_encoding(enc)
        except Exception:
            self._enc = tk.get_encoding("cl100k_base")
        self._fb = None
    def count(self, text):
        if not text: return 0
        return len(self._enc.encode(text)) if self._enc else self._fb.count(text)
class HFTokenizer(Tokenizer):
    def __init__(self, mid: str):
        AT = _try_import_hf()
        if not AT:
            self._tok = None
            self._fb = WhitespaceTokenizer()
            return
        try:
            self._tok = AT.from_pretrained(mid, use_fast=True)
            self._fb = None
        except Exception:
            self._tok = None
            self._fb = WhitespaceTokenizer()
    def count(self, text):
        if not text: return 0
        return len(self._tok.encode(text)) if self._tok else self._fb.count(text)
class SentencePieceTokenizer(Tokenizer):
    def __init__(self, spm_path: Optional[Path]):
        spm = _try_import_sentencepiece()
        if not spm or not spm_path:
            self._sp = None
            self._fb = WhitespaceTokenizer()
            return
        try:
            self._sp = spm.SentencePieceProcessor(model_file=str(spm_path))
            self._fb = None
        except Exception:
            self._sp = None
            self._fb = WhitespaceTokenizer()
    def count(self, text):
        if not text: return 0
        return len(self._sp.encode(text)) if self._sp else self._fb.count(text)

@dataclass(frozen=True)
class ModelSpec:
    name: str
    detector: re.Pattern
    tokenizer: str
    note: str = ""
DEFAULT_SPECS = [
    ModelSpec("gpt-4o", re.compile(r"(^|/)openai/[^/]*gpt-?4o[^/]*/", re.I), "tiktoken:o200k_base"),
    ModelSpec("llama-3.1-405b", re.compile(r"(^|/)meta-llama/[^/]*llama[-_]?3\.1[-_]?405b[^/]*/", re.I),
              "hf:meta-llama/Llama-3.1-405b-instruct"),
    ModelSpec("gemini-2.0-flash-001", re.compile(r"(^|/)google/[^/]*gemini[-_]?2\.0[^/]*/", re.I),
              "whitespace"),
]
def make_tokenizer(spec: str, spm: Optional[Path], default: str) -> Tokenizer:
    if spec.startswith("tiktoken:"): return TiktokenTokenizer(spec.split(":",1)[1])
    if spec.startswith("hf:"): return HFTokenizer(spec.split(":",1)[1])
    if spec == "spm": return SentencePieceTokenizer(spm)
    if spec == "whitespace": return WhitespaceTokenizer()
    # default fallback
    return WhitespaceTokenizer()
def detect_model_spec(rel: str, specs):
    for s in specs:
        if s.detector.search(rel): return s
    return None

@dataclass
class Row:
    group: str
    provider_path: str
    model_name: str
    n: int
    avg_query: float
    avg_response: float
    avg_translation: float
    prompt_tokens: int
    avg_total: float
    sum_total: int
    avg_gt_depth: float
    avg_llm_depth: float

def walk_and_collect(root: Path, prompt_text: str, fields: Tuple[str,str,str],
                     specs, default_tok, spm, debug: bool=False, debug_max_items: int=3):
    rows: Dict[Tuple[str,str,str], Dict[str,Any]] = {}
    # depth_stats keyed BY MODEL (group, provider_path, model_name) and then gt_depth
    # depth_stats[(g,p,m)][gt_depth] -> {"n": int, "correct": int}
    depth_stats: Dict[Tuple[str,str,str], Dict[int, Dict[str,int]]] = {}

    prompt_cache: Dict[str,int] = {}
    def get_prompt(tok: Tokenizer):
        # cache by tokenizer class name (simple & sufficient for current specs)
        key = tok.__class__.__name__
        if key in prompt_cache: return prompt_cache[key]
        val = tok.count(prompt_text) if prompt_text else 0
        prompt_cache[key] = val
        return val

    for path in root.rglob("*.json"):
        rel = path.relative_to(root).as_posix()
        parts = rel.split("/")
        if len(parts) < 3: continue
        group, provider_path = parts[0], "/".join(parts[1:3])
        spec = detect_model_spec(rel, specs)
        tok = make_tokenizer(spec.tokenizer if spec else default_tok, spm, default_tok)
        prompt_tok = get_prompt(tok)

        try:
            data = load_json_tolerant(path)
        except Exception:
            continue

        for obj in iter_items(data):
            q = str(obj.get(fields[0], "") or "")
            r = str(obj.get(fields[1], "") or "")
            t = str(obj.get(fields[2], "") or "")
            qn, rn, tn = tok.count(q), tok.count(r), tok.count(t)
            total = qn + rn + tn + prompt_tok

            # --- robust depth calc ---
            _gt = obj.get("ground_truth_plan", "")
            if isinstance(_gt, dict):
                if "length" in _gt and isinstance(_gt["length"], int):
                    gt_depth = _gt["length"]
                else:
                    gp = _gt.get("plan", "")
                    gt_depth = gp.count("\n") if isinstance(gp, str) else 0
            elif isinstance(_gt, str):
                gt_depth = _gt.count("\n")
            else:
                gt_depth = 0

            _llm = obj.get("extracted_llm_plan", "")
            if isinstance(_llm, dict):
                lp = _llm.get("plan", "")
                llm_depth = lp.count("\n") if isinstance(lp, str) else 0
            elif isinstance(_llm, str):
                llm_depth = _llm.count("\n")
            else:
                llm_depth = 0

            llm_correct = bool(obj.get("llm_correct", False))

            # aggregate per-row (token & depth means)
            key = (group, provider_path, spec.name if spec else "unknown")
            agg = rows.setdefault(
                key,
                dict(n=0, sum_q=0, sum_r=0, sum_t=0, sum_total=0,
                     prompt_tokens=prompt_tok, sum_gt_depth=0, sum_llm_depth=0)
            )
            agg["n"] += 1
            agg["sum_q"] += qn
            agg["sum_r"] += rn
            agg["sum_t"] += tn
            agg["sum_total"] += total
            agg["sum_gt_depth"] += gt_depth
            agg["sum_llm_depth"] += llm_depth
            agg["prompt_tokens"] = prompt_tok  # stable

            # per-LLM depth stats (instead of a single global counter)
            per_model = depth_stats.setdefault(key, {})
            ds = per_model.setdefault(gt_depth, {"n": 0, "correct": 0})
            ds["n"] += 1
            if llm_correct:
                ds["correct"] += 1

    # build per-row summaries
    out: List[Row] = []
    for (g, p, m), a in sorted(rows.items()):
        n = max(1, a["n"])
        out.append(
            Row(
                g, p, m, a["n"],
                a["sum_q"] / n, a["sum_r"] / n, a["sum_t"] / n,
                a["prompt_tokens"], a["sum_total"] / n, a["sum_total"],
                a["sum_gt_depth"] / n, a["sum_llm_depth"] / n
            )
        )
    return out, depth_stats

def print_table(rows: List[Row]):
    if not rows:
        print("No rows")
        return
    headers = [
        "group","provider/model","model_name","n","avg_query","avg_response","avg_translation",
        "prompt_tokens","avg_total","sum_total","avg_gt_depth","avg_llm_depth"
    ]
    def fmt(v): return f"{v:.2f}" if isinstance(v, float) else str(v)
    matrix = [[r.group, r.provider_path, r.model_name, r.n, r.avg_query, r.avg_response,
               r.avg_translation, r.prompt_tokens, r.avg_total, r.sum_total,
               r.avg_gt_depth, r.avg_llm_depth] for r in rows]
    col_w = [max(len(h), max(len(fmt(row[i])) for row in matrix)) for i, h in enumerate(headers)]
    def join(cols): return " | ".join(fmt(c).ljust(col_w[i]) for i, c in enumerate(cols))
    print(join(headers))
    print("-+-".join("-"*w for w in col_w))
    for row in matrix:
        print(join(row))

def write_csv(rows: List[Row], out: Path):
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["group","provider_model","model_name","n","avg_query","avg_response",
                    "avg_translation","prompt_tokens","avg_total","sum_total",
                    "avg_gt_depth","avg_llm_depth"])
        for r in rows:
            w.writerow([r.group, r.provider_path, r.model_name, r.n,
                        f"{r.avg_query:.6f}", f"{r.avg_response:.6f}", f"{r.avg_translation:.6f}",
                        r.prompt_tokens, f"{r.avg_total:.6f}", r.sum_total,
                        f"{r.avg_gt_depth:.6f}", f"{r.avg_llm_depth:.6f}"])

def write_depth_accuracy(stats: Dict[Tuple[str,str,str], Dict[int, Dict[str,int]]], out: Path):
    """
    stats[(group, provider_path, model_name)][gt_depth] -> {"n": int, "correct": int}
    """
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["group","provider_model","model_name","gt_depth","n","n_correct","percent_correct"])
        # sort by key then by depth
        for (g, p, m) in sorted(stats.keys()):
            per_depth = stats[(g, p, m)]
            for d in sorted(per_depth.keys()):
                s = per_depth[d]
                n, c = s["n"], s["correct"]
                pct = (c / n * 100.0) if n else 0.0
                w.writerow([g, p, m, d, n, c, f"{pct:.2f}"])

def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", type=Path)
    ap.add_argument("--prompt-file", type=Path)
    ap.add_argument("--fields", nargs=3, default=("query","llm_raw_response","raw_translation"))
    ap.add_argument("--csv-out", type=Path)
    ap.add_argument("--default-tokenizer", default="whitespace")
    ap.add_argument("--llama-tokenizer", default="meta-llama/Llama-3.1-405b-instruct")
    ap.add_argument("--spm-model", type=Path)
    args = ap.parse_args(argv)

    prompt_text = args.prompt_file.read_text(encoding="utf-8") if args.prompt_file and args.prompt_file.exists() else ""

    specs = list(DEFAULT_SPECS)
    for i, s in enumerate(specs):
        if s.name.startswith("llama-3.1"):
            specs[i] = ModelSpec(s.name, s.detector, f"hf:{args.llama_tokenizer}", s.note)

    rows, depth_stats = walk_and_collect(
        args.root, prompt_text, tuple(args.fields), specs,
        args.default_tokenizer, args.spm_model
    )

    print_table(rows)

    if args.csv_out:
        write_csv(rows, args.csv_out)
        print(f"Wrote tokens summary to {args.csv_out}")
        depth_out = args.csv_out.with_name("depth_accuracy.csv")
        write_depth_accuracy(depth_stats, depth_out)
        print(f"Wrote depth accuracy to {depth_out}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
