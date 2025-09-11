import os
import re
import json
import argparse
import subprocess
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Set
import sys

TEXT_PRED_MAP = [
    (r"\bi am holding\s*\(", "holding("),
    (r"\bthe hand is empty\s*\(\s*\)", "handempty"),
    (r"\bis on the table\s*\(", "ontable("),
    (r"\bis on top of\s*\(", "on("),
    (r"\bis clear\s*\(", "clear("),
]

ACTION_MAP = {
    "pick up ?b": "pick-up",
    "put down ?b": "put-down",
    "stack ?b1 on top of ?b2": "stack",
    "unstack ?b1 from ?b2": "unstack",
    "pick-up": "pick-up",
    "put-down": "put-down",
    "stack": "stack",
    "unstack": "unstack",
}

ATOM_RE = re.compile(r"[a-z][a-z0-9_-]*\s*\([^()]*\)|\bhandempty\b", re.IGNORECASE)
DISJ_SPLIT_RE = re.compile(r"\s+∨\s+")
CONJ_SPLIT_RE = re.compile(r"\s+∧\s+")
CONSTRAINT_RE = re.compile(r"(\?[Vv]\d+)\s*([=!]=)\s*([A-Za-z]\w+|\?[Vv]\d+)")

def normalize_predicates(text: str) -> str:
    out = text
    for pat, repl in TEXT_PRED_MAP:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    out = re.sub(r"\bis\s+(?=(on|ontable|clear)\b)", "", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out

class UnionFind:
    def __init__(self):
        self.parent: Dict[str, str] = {}

    def find(self, x: str) -> str:
        self.parent.setdefault(x, x)
        if self.parent[x] != x:
            self.parent[x] = self.find(self.parent[x])
        return self.parent[x]

    def union(self, a: str, b: str):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra

def is_var(tok: str) -> bool:
    return bool(re.fullmatch(r"\?[Vv]\d+", tok))

def var_to_plain(tok: str) -> str:
    return re.sub(r"^\?[Vv](\d+)$", r"v\1", tok)

def parse_constraints(text: str) -> Tuple[Dict[str, str], List[Tuple[str, str]], str]:
    equalities: List[Tuple[str, str]] = []
    inequalities: List[Tuple[str, str]] = []
    def repl_constraint(m):
        return " "
    for m in CONSTRAINT_RE.finditer(text):
        a, op, b = m.group(1), m.group(2), m.group(3)
        if op == "==":
            equalities.append((a, b))
        else:
            inequalities.append((a, b))
    cleaned = CONSTRAINT_RE.sub(repl_constraint, text)
    uf = UnionFind()
    for a, b in equalities:
        if is_var(a) and is_var(b):
            uf.union(a, b)
    rep_const: Dict[str, str] = {}
    for a, b in equalities:
        if is_var(a) and not is_var(b):
            ra = uf.find(a)
            rep_const[ra] = b
        elif not is_var(a) and is_var(b):
            rb = uf.find(b)
            rep_const[rb] = a
    subst: Dict[str, str] = {}
    for node in list(uf.parent.keys()):
        rep = uf.find(node)
        if node.startswith("?"):
            if rep in rep_const:
                subst[node] = rep_const[rep]
            else:
                subst[node] = rep
    for a, b in equalities:
        if is_var(a) and not is_var(b):
            subst.setdefault(a, b)
        if not is_var(a) and is_var(b):
            subst.setdefault(b, a)
    return subst, inequalities, normalize_predicates(cleaned)

def violates_neq(subst: Dict[str, str], neq_pairs: List[Tuple[str, str]]) -> bool:
    def resolve(tok: str) -> str:
        seen = set()
        while tok in subst and tok not in seen:
            seen.add(tok)
            tok = subst[tok]
        return tok
    for a, b in neq_pairs:
        ra, rb = resolve(a), resolve(b)
        if ra == rb:
            return True
    return False

def extract_atoms_from_formula(formula: str) -> List[str]:
    atoms = []
    for m in ATOM_RE.finditer(formula):
        frag = m.group(0).strip()
        if frag.lower() == "handempty":
            atoms.append("handempty")
            continue
        if "(" not in frag:
            continue
        name, args = frag.split("(", 1)
        args = args[:-1]
        args = args.replace(",", " ")
        args = re.sub(r"\s+", " ", args).strip()
        atoms.append(f"{name.strip()} {args}")
    return atoms

def apply_subst_token(tok: str, subst: Dict[str, str]) -> str:
    seen = set()
    cur = tok
    while cur in subst and cur not in seen:
        seen.add(cur)
        cur = subst[cur]
    if is_var(cur):
        return var_to_plain(cur)
    return cur

def apply_subst_atom(atom: str, subst: Dict[str, str]) -> str:
    if atom == "handempty":
        return "handempty"
    parts = atom.split()
    head, args = parts[0], parts[1:]
    new_args = [apply_subst_token(a, subst) for a in args]
    return f"{head} {' '.join(new_args)}"

def pddlize_atom(atom: str) -> str:
    if atom == "handempty":
        return "(handempty)"
    parts = atom.split()
    head, args = parts[0], parts[1:]
    args = [re.sub(r"^\?[Vv](\d+)$", r"v\1", a) for a in args]
    return f"({head} {' '.join(args)})"

def atoms_from_disjunct(disj_text: str) -> Tuple[List[str], Dict[str, str], List[Tuple[str, str]]]:
    t = disj_text.strip()
    if t.startswith("(") and t.endswith(")"):
        t = t[1:-1].strip()
    subst, neq_pairs, cleaned = parse_constraints(t)
    conjuncts = [c.strip() for c in CONJ_SPLIT_RE.split(cleaned)] if "∧" in cleaned else [cleaned]
    atoms = []
    for conj in conjuncts:
        if not conj or conj in {"(", ")"}:
            continue
        atoms.extend(extract_atoms_from_formula(conj))
    atoms = [apply_subst_atom(a, subst) for a in atoms]
    seen = set()
    uniq = []
    for a in atoms:
        if a not in seen:
            seen.add(a)
            uniq.append(a)
    return uniq, subst, neq_pairs

def parse_action_list(line: str, subst: Optional[Dict[str, str]] = None) -> List[Tuple[str, List[str]]]:
    actions = []
    for desc, args_str in re.findall(r"Action\('([^']+)'\(\[([^\]]*)\]\)\)", line):
        desc = desc.strip()
        op = ACTION_MAP.get(desc) or ACTION_MAP.get(re.sub(r"\s+", " ", desc).strip())
        if op is None:
            continue
        args = [a.strip() for a in args_str.split(",") if a.strip()]
        if subst:
            args = [apply_subst_token(a, subst) for a in args]
        else:
            args = [re.sub(r"^\?[Vv](\d+)$", r"v\1", a) for a in args]
        actions.append((op, args))
    return actions

def is_stop_line(ln: str) -> bool:
    s = ln.strip()
    return s.startswith("[") or s.startswith("{") or s.startswith("-")

def parse_initial_state(raw: str) -> Tuple[List[str], Set[str]]:
    if "Initial State:" not in raw:
        return [], set()
    seg = raw.split("Initial State:", 1)[1]
    lines = [ln for ln in (ln.strip() for ln in seg.replace("\r\n", "\n").splitlines()) if ln]
    formula_lines = []
    hit_stop = False
    for ln in lines:
        if not hit_stop and is_stop_line(ln):
            hit_stop = True
            continue
        if hit_stop:
            if ln.startswith("-"):
                break
            continue
        formula_lines.append(ln)
    formula_txt = normalize_predicates(" ".join(formula_lines))
    if formula_txt.startswith("((") and formula_txt.endswith("))"):
        formula_txt = formula_txt[1:-1].strip()
    disjuncts = [d.strip() for d in DISJ_SPLIT_RE.split(formula_txt)] if "∨" in formula_txt else [formula_txt]
    atoms_all: List[str] = []
    for dt in disjuncts:
        at, _, _ = atoms_from_disjunct(dt)
        atoms_all.extend(at)
    seen = set()
    init_atoms = []
    for a in atoms_all:
        if a not in seen:
            seen.add(a)
            init_atoms.append(a)
    constants: Set[str] = set()
    for a in init_atoms:
        if a == "handempty":
            continue
        parts = a.split()
        for x in parts[1:]:
            if re.match(r"^[A-Za-z]\w*$", x):
                constants.add(x.lower())
    return init_atoms, constants

def parse_blocks(text: str):
    parts = text.split("Subgoal:")
    if len(parts) <= 1:
        return [], [], [], []
    chunks = parts[1:]
    disjuncts_per_subgoal: List[List[List[str]]] = []
    actions_per_subgoal: List[List[List[Tuple[str, List[str]]]]] = []
    constraints_per_subgoal: List[List[Dict[str, List[List[str]]]]] = []
    constants: Set[str] = set()
    def add_consts_from_atoms(atom_list):
        for a in atom_list:
            if a == "handempty":
                continue
            parts = a.split()
            args = parts[1:]
            for x in args:
                if re.match(r"^[A-Za-z]\w*$", x):
                    constants.add(x.lower())
    for ch_idx, ch in enumerate(chunks):
        lines = [ln for ln in (ln.strip() for ln in ch.replace("\r\n", "\n").splitlines()) if ln]
        formula_lines = []
        rest_lines = []
        hit_stop = False
        for ln in lines:
            if not hit_stop and is_stop_line(ln):
                hit_stop = True
                rest_lines.append(ln)
                continue
            if not hit_stop:
                formula_lines.append(ln)
            else:
                rest_lines.append(ln)
        action_line = ""
        for ln in rest_lines:
            if ln.startswith("[Action"):
                action_line = ln
                break
        formula_txt = normalize_predicates(" ".join(formula_lines))
        if formula_txt.startswith("((") and formula_txt.endswith("))"):
            formula_txt = formula_txt[1:-1].strip()
        disjunct_texts = [d.strip() for d in DISJ_SPLIT_RE.split(formula_txt)] if "∨" in formula_txt else [formula_txt]
        disjuncts_atoms: List[List[str]] = []
        disjuncts_actions: List[List[Tuple[str, List[str]]]] = []
        disjuncts_constraints: List[Dict[str, List[List[str]]]] = []
        for dt in disjunct_texts:
            atoms, subst, neq_pairs = atoms_from_disjunct(dt)
            if violates_neq(subst, neq_pairs):
                continue
            add_consts_from_atoms(atoms)
            acts = parse_action_list(action_line, subst) if action_line else []
            for (_op, args) in acts:
                for a in args:
                    if re.match(r"^[A-Za-z]\w*$", a):
                        constants.add(a.lower())
            def _plain(tok: str) -> str:
                if is_var(tok):
                    return var_to_plain(tok)
                return tok.lower()
            eq_list = [[_plain(k), _plain(v)] for (k, v) in subst.items()]
            neq_list = [[_plain(a), _plain(b)] for (a, b) in neq_pairs]
            disjuncts_atoms.append(atoms)
            disjuncts_actions.append(acts)
            disjuncts_constraints.append({"eq": eq_list, "neq": neq_list})
        disjuncts_per_subgoal.append(disjuncts_atoms)
        actions_per_subgoal.append(disjuncts_actions)
        constraints_per_subgoal.append(disjuncts_constraints)
    return disjuncts_per_subgoal, actions_per_subgoal, sorted(constants), constraints_per_subgoal

def make_problem_pddl(objects, init_atoms, goal_atoms, domain_name="blocksworld-4ops"):
    obj_list = " ".join(objects)
    init_lines = "\n    ".join(pddlize_atom(a) for a in init_atoms) if init_atoms else ""
    goal_lines = "\n      ".join(pddlize_atom(a) for a in goal_atoms) if goal_atoms else ""
    return f"""(define (problem regcheck)
  (:domain {domain_name})
  (:objects {obj_list})
  (:init
    {init_lines}
  )
  (:goal (and
      {goal_lines}
  ))
)"""

def make_plan_file(actions):
    lines = []
    for op, args in actions:
        if args:
            lines.append(f"({op} {' '.join(args)})")
        else:
            lines.append(f"({op})")
    return "\n".join(lines) + "\n"

def run_validate(validate_bin: str, domain_path: Path, prob_path: Path, plan_path: Path) -> Tuple[bool, str]:
    cmd = [validate_bin, str(domain_path), str(prob_path), str(plan_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=10)
    out = (proc.stdout or "") + "\n" + (proc.stderr or "")
    success_patterns = ["Successful plans", "Plan valid", "Plan Validation details", "Goal satisfied"]
    passed = any(pattern.lower() in out.lower() for pattern in success_patterns)
    if proc.returncode == 0 and not passed and "error" not in out.lower():
        passed = True
    return passed, out

def get_domain_name(domain_path: Path) -> str:
    txt = domain_path.read_text(encoding="utf-8")
    m = re.search(r"\(define\s*\(\s*domain\s+([^\s\)]+)\s*\)", txt, flags=re.IGNORECASE)
    if m:
        return m.group(1)
    return "domain"

def process_single_file(infile: Path, outdir: Path, domain_path: Path, validator: str, no_run: bool, test_one: bool) -> Dict:
    outdir.mkdir(parents=True, exist_ok=True)
    raw = infile.read_text(encoding="utf-8")
    init_atoms, init_consts = parse_initial_state(raw)
    rg_part = raw.split("Regressed goals:", 1)[1] if "Regressed goals:" in raw else raw
    disjuncts_per_subgoal, actions_per_subgoal, constants, constraints_per_subgoal = parse_blocks(rg_part)
    goal_atoms = disjuncts_per_subgoal[0][0] if disjuncts_per_subgoal and disjuncts_per_subgoal[0] else []
    objects = sorted(set(constants) | set(init_consts))
    domain_name = get_domain_name(domain_path)
    manifest = []
    for si in range(1, len(disjuncts_per_subgoal)):
        disjs = disjuncts_per_subgoal[si]
        acts_per_dj = actions_per_subgoal[si]
        cons_per_dj = constraints_per_subgoal[si]
        for dj_idx, (atoms, acts, cons) in enumerate(zip(disjs, acts_per_dj, cons_per_dj), start=1):
            prob_name = f"problem_s{si:02d}_d{dj_idx:02d}.pddl"
            plan_name = f"plan_s{si:02d}_d{dj_idx:02d}.soln"
            pddl = make_problem_pddl(objects, atoms, goal_atoms, domain_name=domain_name)
            (outdir / prob_name).write_text(pddl, encoding="utf-8")
            (outdir / plan_name).write_text(make_plan_file(acts), encoding="utf-8")
            manifest.append({
                "subgoal_index": si,
                "disjunct_index": dj_idx,
                "problem": prob_name,
                "plan": plan_name,
                "init_atoms": atoms,
                "actions": acts,
                "constraints": cons
            })
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    if init_atoms:
        init_problem = make_problem_pddl(objects, init_atoms, goal_atoms, domain_name=domain_name)
        (outdir / "initial_state.pddl").write_text(init_problem, encoding="utf-8")
    if no_run:
        return {
            "input": str(infile),
            "results_file": str(outdir / "results.json"),
            "csv_file": str(outdir / "results.csv"),
            "tested": 0,
            "failures": 0,
            "status": "SKIPPED"
        }
    failures = []
    results = []
    items_to_test = manifest[:1] if test_one else manifest
    for item in items_to_test:
        prob = outdir / item["problem"]
        plan = outdir / item["plan"]
        ok, out = run_validate(validator, domain_path, prob, plan)
        status = "PASS" if ok else "FAIL"
        results.append({**item, "status": status})
        if not ok:
            failures.append({**item, "output": out})
    (outdir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    with open(outdir / "results.csv", "w", encoding="utf-8") as f:
        f.write("subgoal,disjunct,problem,plan,status\n")
        for r in results:
            f.write(f"{r['subgoal_index']},{r['disjunct_index']},{r['problem']},{r['plan']},{r['status']}\n")
    if failures:
        print(f"[FAILURES] {len(failures)}/{len(items_to_test)} :: {infile.name}")
        return {
            "input": str(infile),
            "results_file": str(outdir / "results.json"),
            "csv_file": str(outdir / "results.csv"),
            "tested": len(items_to_test),
            "failures": len(failures),
            "status": "FAIL"
        }
    else:
        print(f"[SUCCESS] All {len(items_to_test)} passed :: {infile.name}")
        return {
            "input": str(infile),
            "results_file": str(outdir / "results.json"),
            "csv_file": str(outdir / "results.csv"),
            "tested": len(items_to_test),
            "failures": 0,
            "status": "PASS"
        }

def main():
    ap = argparse.ArgumentParser(description="Convert parsed states/goals to PDDL and validate with VAL.")
    ap.add_argument("--in", dest="indir", required=True, help="Input folder of files.")
    ap.add_argument("--domain", dest="domain", required=True)
    ap.add_argument("--outdir", default="out_val")
    ap.add_argument("--validator", default="validate")
    ap.add_argument("--no-run", action="store_true")
    ap.add_argument("--test-one", action="store_true")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    domain_path = Path(args.domain)

    in_path = Path(args.indir)
    if not in_path.is_dir():
        print(f"[ERROR] Input path {in_path} is not a directory")
        return 1

    inputs: List[Path] = [p for p in sorted(in_path.iterdir()) if p.is_file() and not p.name.startswith(".")]

    overall_results = []
    total_tested = 0
    total_failures = 0

    for inp in inputs:
        subdir = outdir / inp.stem
        res = process_single_file(
            infile=inp,
            outdir=subdir,
            domain_path=domain_path,
            validator=args.validator,
            no_run=args.no_run,
            test_one=args.test_one,
        )
        overall_results.append(res)
        total_tested += res.get("tested", 0)
        total_failures += res.get("failures", 0)

    (outdir / "overall_results.json").write_text(json.dumps(overall_results, indent=2), encoding="utf-8")
    with open(outdir / "overall_results.csv", "w", encoding="utf-8") as f:
        f.write("input,results_file,csv_file,tested,failures,status\n")
        for r in overall_results:
            f.write(f"{r.get('input','')},{r.get('results_file','')},{r.get('csv_file','')},{r.get('tested',0)},{r.get('failures',0)},{r.get('status','')}\n")

    if args.no_run:
        print("[SUCCESS] Prepared outputs (validation skipped)")
        return 0

    if total_failures:
        print(f"[FAILURES] {total_failures}/{total_tested} across {len(inputs)} file(s)")
        return 2
    else:
        print(f"[SUCCESS] All {total_tested} plan(s) passed across {len(inputs)} file(s)")
        return 0

if __name__ == "__main__":
    sys.exit(main())
