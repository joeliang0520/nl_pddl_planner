#!/usr/bin/env python3
import os, re, json, argparse, csv, sys
from pathlib import Path
from collections import defaultdict
from typing import List, Tuple, Dict, Optional, Set

class PDDLFolderParser:
    ATOM_IN_PDDL = re.compile(r'\([^\(\)]+\)')
    VLOW_RE = re.compile(r'^v[0-9]+$', re.I)

    @staticmethod
    def _read_text(p: Path) -> str:
        return p.read_text(encoding="utf-8")

    @staticmethod
    def _strip_pddl_comments(s: str) -> str:
        return re.sub(r";[^\n]*", "", s)

    @classmethod
    def parse_pddl_init_atoms_from_text(cls, pddl_text: str) -> List[Tuple[str, List[str]]]:
        s = cls._strip_pddl_comments(pddl_text)
        m = re.search(r"\(:\s*init\b", s, flags=re.IGNORECASE)
        if not m:
            return []
        i = m.start()
        depth = 0
        start = None
        end = None
        for k in range(i, len(s)):
            ch = s[k]
            if ch == '(':
                depth += 1
                if start is None:
                    start = k
            elif ch == ')':
                depth -= 1
                if depth == 0:
                    end = k
                    break
        if start is None or end is None:
            return []
        body = s[m.end():end]
        atoms: List[Tuple[str, List[str]]] = []
        for t in cls.ATOM_IN_PDDL.findall(body):
            t2 = t.strip()[1:-1].strip()
            parts = t2.split()
            if not parts:
                continue
            head = parts[0].lower()
            args = [a.lower() for a in parts[1:]]
            atoms.append((head, args))
        return atoms

    @staticmethod
    def atoms_to_kb_strings(atoms: List[Tuple[str, List[str]]]) -> Set[str]:
        out = set()
        for pred, args in atoms:
            if args:
                out.add(f"{pred}({', '.join(args)})")
            else:
                out.add(f"{pred}()")
        return out

    @staticmethod
    def _strip_quotes(s: str) -> str:
        s = s.strip()
        return s[1:-1] if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"" else s

    @classmethod
    def _const_or_var_token(cls, a: str) -> str:
        return a if not cls.VLOW_RE.match(a) else a.upper()

    @classmethod
    def build_query_from_problem_init_atoms(cls, atoms: List[Tuple[str, List[str]]], constraints: Dict) -> str:
        parts: List[str] = []
        for pred, args in atoms:
            if args:
                a2 = [cls._const_or_var_token(x) for x in args]
                parts.append(f"{pred}({', '.join(a2)})")
            else:
                parts.append(f"{pred}()")
        if constraints:
            for v, c in constraints.get("eq", []):
                vtok = cls._const_or_var_token(str(v))
                parts.append(f"({vtok} == '{cls._strip_quotes(str(c))}')")
            for a, b in constraints.get("neq", []):
                atok = cls._const_or_var_token(str(a))
                btok = cls._const_or_var_token(str(b))
                if cls.VLOW_RE.match(str(b)):
                    parts.append(f"({atok} != {btok})")
                else:
                    parts.append(f"({atok} != '{cls._strip_quotes(str(b))}')")
        return " &\n    ".join(parts)

    def load_kb(self, folder: Path) -> Optional[Set[str]]:
        init_pddl = folder / "initial_state.pddl"
        if not init_pddl.exists():
            return None
        atoms = self.parse_pddl_init_atoms_from_text(self._read_text(init_pddl))
        return self.atoms_to_kb_strings(atoms)

    def load_manifest(self, folder: Path) -> Optional[List[Dict]]:
        manifest_json = folder / "manifest.json"
        if not manifest_json.exists():
            return None
        return json.loads(self._read_text(manifest_json))

    def build_problem_query(self, folder: Path, manifest_item: Dict) -> Optional[Tuple[str, List[Tuple[str, List[str]]]]]:
        problem_path = folder / manifest_item.get("problem", "")
        if not problem_path.exists():
            return None
        atoms = self.parse_pddl_init_atoms_from_text(self._read_text(problem_path))
        query = self.build_query_from_problem_init_atoms(atoms, manifest_item.get("constraints", {}))
        return query, atoms


class DatalogEquivalenceChecker:
    ATOM_RE = re.compile(r"([a-z][a-z0-9_]*)\s*\(([^()]*)\)|\b([a-z][a-z0-9_]*)\s*\(\s*\)", re.I)
    VAR_RE  = re.compile(r'^[A-Z]\w*$')

    @staticmethod
    def _strip_quotes(s: str) -> str:
        s = s.strip()
        return s[1:-1] if len(s) >= 2 and s[0] == s[-1] and s[0] in "'\"" else s

    @classmethod
    def parse_atom(cls, s: str) -> Tuple[str, List[str]]:
        m = re.match(r'\s*([a-z][a-z0-9_]*)\s*\(([^()]*)\)\s*$', s, re.I)
        if m:
            pred = m.group(1)
            args = [a.strip() for a in m.group(2).split(',')] if m.group(2).strip() else []
            return pred, [cls._strip_quotes(a) for a in args]
        s = s.strip()
        if s.endswith("()"):
            return s[:-2], []
        raise ValueError(f"bad atom: {s}")

    @classmethod
    def extract_atoms(cls, query: str) -> List[Tuple[str, List[str]]]:
        atoms = []
        for m in cls.ATOM_RE.finditer(query):
            if m.group(1):
                pred = m.group(1)
                args = [a.strip() for a in (m.group(2) or '').split(',')] if m.group(2) else []
                atoms.append((pred, args))
            else:
                atoms.append((m.group(3), []))
        return atoms

    @classmethod
    def extract_constraints(cls, query: str):
        eq_vc = []; eq_vv = []; ne_vc = []; ne_vv = []
        for v,c in re.findall(r"\(\s*([A-Z]\w*)\s*==\s*'([^']*)'\s*\)", query): eq_vc.append((v,cls._strip_quotes(c)))
        for c,v in re.findall(r"\(\s*'([^']*)'\s*==\s*([A-Z]\w*)\s*\)", query): eq_vc.append((v,cls._strip_quotes(c)))
        for v,c in re.findall(r"\(\s*([A-Z]\w*)\s*!=\s*'([^']*)'\s*\)", query): ne_vc.append((v,cls._strip_quotes(c)))
        for c,v in re.findall(r"\(\s*'([^']*)'\s*!=\s*([A-Z]\w*)\s*\)", query): ne_vc.append((v,cls._strip_quotes(c)))
        for a,b in re.findall(r"\(\s*([A-Z]\w*)\s*==\s*([A-Z]\w*)\s*\)", query): eq_vv.append((a,b))
        for a,b in re.findall(r"\(\s*([A-Z]\w*)\s*!=\s*([A-Z]\w*)\s*\)", query): ne_vv.append((a,b))
        return eq_vc, eq_vv, ne_vc, ne_vv

    @classmethod
    def vars_in_query(cls, query: str) -> List[str]:
        vs = set()
        for _, args in cls.extract_atoms(query):
            for a in args:
                if cls.VAR_RE.match(a): vs.add(a)
        for v in re.findall(r"\b([A-Z]\w*)\b", query):
            vs.add(v)
        return sorted(vs)

    @classmethod
    def parse_kb_facts(cls, kb_set: Set[str]):
        by_pred = defaultdict(list)
        consts = set()
        for s in kb_set:
            p, args = cls.parse_atom(s)
            by_pred[(p, len(args))].append(tuple(args))
            for a in args: consts.add(a)
        return by_pred, consts

    @classmethod
    def candidate_domain_for_var(cls, var, atoms, by_pred, forced_consts, universe_consts):
        domains = []
        for pred, args in atoms:
            if var in args:
                idxs = [k for k,a in enumerate(args) if a == var]
                pool = by_pred.get((pred, len(args)), [])
                filtered = []
                for fact in pool:
                    ok = True
                    for j, aj in enumerate(args):
                        if j in idxs: continue
                        if not cls.VAR_RE.match(aj):
                            if cls._strip_quotes(aj) != fact[j]: ok = False; break
                    if ok: filtered.append(fact)
                if not filtered: return set()
                if len(idxs) == 1:
                    domains.append({f[idxs[0]] for f in filtered})
                else:
                    cand = set()
                    for f in filtered:
                        vals = {f[j] for j in idxs}
                        if len(vals) == 1: cand.add(next(iter(vals)))
                    domains.append(cand)
        if not domains:
            return set(forced_consts) if forced_consts else set(universe_consts)
        dom = set.intersection(*map(set, domains))
        if forced_consts: dom &= set(forced_consts)
        return dom

    @classmethod
    def ground_atoms(cls, atoms, subst):
        out = set()
        for pred, args in atoms:
            g = []
            for a in args:
                g.append(subst[a] if cls.VAR_RE.match(a) else cls._strip_quotes(a))
            out.add(f"{pred}({', '.join(g)})" if g else f"{pred}()")
        return out

    @classmethod
    def check_constraints_partial(cls, subst, eq_vc, eq_vv, ne_vc, ne_vv):
        for v,c in eq_vc:
            if v in subst and subst[v] != c: return False
        for a,b in eq_vv:
            if a in subst and b in subst and subst[a] != subst[b]: return False
        for v,c in ne_vc:
            if v in subst and subst[v] == c: return False
        for a,b in ne_vv:
            if a in subst and b in subst and subst[a] == subst[b]: return False
        return True

    @classmethod
    def _prepare_domains(cls, query: str, KB: Set[str]):
        atoms = cls.extract_atoms(query)
        eq_vc, eq_vv, ne_vc, ne_vv = cls.extract_constraints(query)
        by_pred, all_consts = cls.parse_kb_facts(KB)
        forced = defaultdict(set)
        for v,c in eq_vc: forced[v].add(c)
        vnames = cls.vars_in_query(query)
        domains = {}
        for v in vnames:
            dom = cls.candidate_domain_for_var(v, atoms, by_pred, forced[v], all_consts)
            if not dom:
                return None
            domains[v] = sorted(dom)
        order = sorted(vnames, key=lambda x: len(domains[x]))
        return atoms, (eq_vc, eq_vv, ne_vc, ne_vv), vnames, domains, order

    @classmethod
    def first_substitution(cls, query: str, KB: Set[str]) -> Optional[Dict[str, str]]:
        prep = cls._prepare_domains(query, KB)
        if not prep:
            return None
        atoms, (eq_vc, eq_vv, ne_vc, ne_vv), vnames, domains, order = prep
        solution = None
        subst: Dict[str, str] = {}
        def dfs(k=0):
            nonlocal solution
            if solution is not None:
                return True
            if k == len(order):
                if not cls.check_constraints_partial(subst, eq_vc, eq_vv, ne_vc, ne_vv):
                    return False
                if cls.ground_atoms(atoms, subst) == KB:
                    solution = dict(subst)
                    return True
                return False
            v = order[k]
            for val in domains[v]:
                subst[v] = val
                if cls.check_constraints_partial(subst, eq_vc, eq_vv, ne_vc, ne_vv):
                    if dfs(k+1):
                        return True
            subst.pop(v, None)
            return False
        dfs(0)
        return solution


def process_folder(folder: Path, out_root: Path, parser: PDDLFolderParser, checker: DatalogEquivalenceChecker):
    results = []

    KB = parser.load_kb(folder)
    manifest = parser.load_manifest(folder)

    if KB is None:
        results.append({"folder": folder.name, "error": "initial_state.pddl missing"})
        return results
    if manifest is None:
        results.append({"folder": folder.name, "error": "manifest.json missing"})
        return results

    out_dir = out_root / folder.name
    out_dir.mkdir(parents=True, exist_ok=True)

    for item in manifest:
        entry = {
            "folder": folder.name,
            "problem": item.get("problem"),
            "subgoal_index": item.get("subgoal_index"),
            "disjunct_index": item.get("disjunct_index"),
        }
        built = parser.build_problem_query(folder, item)
        if built is None:
            entry.update({"equivalent": False, "num_solutions": 0, "error": "problem file missing"})
            results.append(entry)
            continue

        query, _atoms = built
        subst = checker.first_substitution(query, KB)

        entry.update({
            "equivalent": subst is not None,
            "num_solutions": 1 if subst is not None else 0,
            "witness": subst,
            "query": query,
        })
        results.append(entry)

    (out_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


def main():
    ap = argparse.ArgumentParser(description="Batch equivalence checker for PDDL folders")
    ap.add_argument("root", help="Path to the out_val-like root directory")
    ap.add_argument("--out", default=None, help="Output directory (default: <root>/equiv_results)")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    out_root = Path(args.out).resolve() if args.out else (root / "equiv_results")
    out_root.mkdir(parents=True, exist_ok=True)

    parser = PDDLFolderParser()
    checker = DatalogEquivalenceChecker()

    all_results = []
    for entry in sorted(root.iterdir()):
        if entry.is_dir():
            res = process_folder(entry, out_root, parser, checker)
            all_results.extend(res)

    csv_path = out_root / "summary.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["folder","problem","subgoal_index","disjunct_index","equivalent","num_solutions","error"])
        for r in all_results:
            w.writerow([
                r.get("folder"),
                r.get("problem"),
                r.get("subgoal_index"),
                r.get("disjunct_index"),
                "" if "equivalent" not in r else int(r["equivalent"]),
                "" if "num_solutions" not in r else r["num_solutions"],
                r.get("error",""),
            ])

    all_folders = {r.get("folder") for r in all_results if r.get("folder")}
    ok_folders = {r.get("folder") for r in all_results if r.get("equivalent")}
    missing_match = sorted(all_folders - ok_folders)

    if missing_match:
        print("Folders without a matching substitution:")
        for name in missing_match:
            print(name)
    else:
        print("All folders have at least one matching substitution.")

    print(f"Wrote per-folder results under: {out_root}")
    print(f"Summary CSV: {csv_path}")

if __name__ == "__main__":
    main()
