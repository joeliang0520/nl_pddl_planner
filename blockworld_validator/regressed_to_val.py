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

# ---------- Normalization ----------

def normalize_predicates(text: str) -> str:
    out = text
    for pat, repl in TEXT_PRED_MAP:
        out = re.sub(pat, repl, out, flags=re.IGNORECASE)
    # keep 'is' in constraints; only strip when followed by known predicate names
    out = re.sub(r"\bis\s+(?=(on|ontable|clear)\b)", "", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out

# ---------- Constraint parsing (== / !=) per disjunct ----------

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
    # convert ?V123 -> v123
    return re.sub(r"^\?[Vv](\d+)$", r"v\1", tok)

def parse_constraints(text: str) -> Tuple[Dict[str, str], List[Tuple[str, str]], str]:
    """
    Returns:
      subst: mapping from '?Vn' -> constant or another '?Vm' (temporarily), later normalized
      neq_pairs: list of ('lhs','rhs') tokens with !=
      cleaned_text: text with all constraint conjuncts removed
    """
    # collect all constraints across the disjunct
    equalities: List[Tuple[str, str]] = []
    inequalities: List[Tuple[str, str]] = []

    # We will remove any conjuncts that are *pure* constraints: (?V == X) or (?V != X)
    # Approach: in a conservative way, just strip occurrences of these patterns.
    def repl_constraint(m):
        return " "  # remove matched text; the outer spaces will be normalized

    for m in CONSTRAINT_RE.finditer(text):
        a, op, b = m.group(1), m.group(2), m.group(3)
        if op == "==":
            equalities.append((a, b))
        else:
            inequalities.append((a, b))

    cleaned = CONSTRAINT_RE.sub(repl_constraint, text)

    # Resolve equalities with union-find
    uf = UnionFind()
    # First union all var-var equalities
    for a, b in equalities:
        if is_var(a) and is_var(b):
            uf.union(a, b)

    # Build initial map of representative -> chosen constant if any
    rep_const: Dict[str, str] = {}
    # process var-const equalities
    for a, b in equalities:
        if is_var(a) and not is_var(b):
            ra = uf.find(a)
            rep_const[ra] = b
        elif not is_var(a) and is_var(b):
            rb = uf.find(b)
            rep_const[rb] = a
        elif not is_var(a) and not is_var(b):
            # const == const (rare in these traces) -> if unequal, this disjunct is contradictory
            pass

    # produce final substitution map: each var -> (that var group's constant if any) else -> group rep
    subst: Dict[str, str] = {}
    for node in list(uf.parent.keys()):
        rep = uf.find(node)
        if node.startswith("?"):
            if rep in rep_const:
                subst[node] = rep_const[rep]  # bind to constant
            else:
                subst[node] = rep            # bind to representative var (still with '?V..')

    # any variables that appeared only in var-const eqs (not touched by uf) should also be in subst
    for a, b in equalities:
        if is_var(a) and not is_var(b):
            subst.setdefault(a, b)
        if not is_var(a) and is_var(b):
            subst.setdefault(b, a)

    return subst, inequalities, normalize_predicates(cleaned)

def violates_neq(subst: Dict[str, str], neq_pairs: List[Tuple[str, str]]) -> bool:
    """
    After applying equalities, check whether any != becomes impossible
    (i.e., both sides reduce to the same concrete symbol).
    """
    def resolve(tok: str) -> str:
        # follow substitution chain; ultimately normalize var to its representative/const
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

# ---------- Atom & action substitution ----------

def extract_atoms_from_formula(formula: str) -> List[str]:
    atoms = []
    for m in ATOM_RE.finditer(formula):
        frag = m.group(0).strip()
        if frag.lower() == "handempty":
            atoms.append("handempty")
            continue
        if "(" not in frag:
            print(f"[DEBUG] Skipping malformed atom: {frag}")
            continue
        name, args = frag.split("(", 1)
        args = args[:-1]
        args = args.replace(",", " ")
        args = re.sub(r"\s+", " ", args).strip()
        atoms.append(f"{name.strip()} {args}")
    return atoms

def apply_subst_token(tok: str, subst: Dict[str, str]) -> str:
    # resolve chains inside subst
    seen = set()
    cur = tok
    while cur in subst and cur not in seen:
        seen.add(cur)
        cur = subst[cur]
    # normalize var spelling if still a var
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
    # args are already normalized (consts or 'v123'); keep the legacy normalization as a fallback
    args = [re.sub(r"^\?[Vv](\d+)$", r"v\1", a) for a in args]
    return f"({head} {' '.join(args)})"

def atoms_from_disjunct(disj_text: str) -> Tuple[List[str], Dict[str, str], List[Tuple[str, str]]]:
    """
    Parse one disjunct, extract constraints, apply them to atoms.
    Returns (atoms_applied, subst_map, neq_pairs)
    """
    t = disj_text.strip()
    if t.startswith("(") and t.endswith(")"):
        t = t[1:-1].strip()

    # 1) Extract constraints and clean them out of the textual formula
    subst, neq_pairs, cleaned = parse_constraints(t)

    # 2) Split by ∧ and extract atoms from the non-constraint pieces
    conjuncts = [c.strip() for c in CONJ_SPLIT_RE.split(cleaned)] if "∧" in cleaned else [cleaned]
    atoms = []
    for conj in conjuncts:
        # Ignore naked empty conjuncts that result from stripping constraints
        if not conj or conj in {"(", ")"}:
            continue
        atoms.extend(extract_atoms_from_formula(conj))

    # 3) Apply per-disjunct substitution to atoms
    atoms = [apply_subst_atom(a, subst) for a in atoms]

    # 4) Deduplicate while preserving order
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
            print(f"[WARN] Unrecognized action descriptor: {desc}")
            continue
        args = [a.strip() for a in args_str.split(",") if a.strip()]
        # apply equality substitutions per disjunct if provided
        if subst:
            args = [apply_subst_token(a, subst) for a in args]
        else:
            args = [re.sub(r"^\?[Vv](\d+)$", r"v\1", a) for a in args]
        actions.append((op, args))
    return actions

def is_stop_line(ln: str) -> bool:
    s = ln.strip()
    return s.startswith("[") or s.startswith("{") or s.startswith("-")

# ---------- Main parsing of the "Regressed goals" block ----------

def parse_blocks(text: str):
    parts = text.split("Subgoal:")
    if len(parts) <= 1:
        raise ValueError("No 'Subgoal:' found.")
    chunks = parts[1:]

    # We will now return per-disjunct actions (since equalities vary per disjunct)
    disjuncts_per_subgoal: List[List[List[str]]] = []
    actions_per_subgoal: List[List[List[Tuple[str, List[str]]]]] = []
    constants: Set[str] = set()

    def add_consts_from_atoms(atom_list):
        for a in atom_list:
            if a == "handempty":
                continue
            parts = a.split()
            args = parts[1:]
            for x in args:
                # atoms_from_disjunct has already applied subst -> args may be consts or 'v123'
                if re.match(r"^[A-Za-z]\w*$", x):  # constants only
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

        print(f"[DEBUG] Subgoal {ch_idx}: Formula = {formula_txt[:100]}...")

        disjunct_texts = [d.strip() for d in DISJ_SPLIT_RE.split(formula_txt)] if "∨" in formula_txt else [formula_txt]
        disjuncts_atoms: List[List[str]] = []
        disjuncts_actions: List[List[Tuple[str, List[str]]]] = []

        for dt in disjunct_texts:
            atoms, subst, neq_pairs = atoms_from_disjunct(dt)

            # Optional: prune disjuncts that violate != after equalities resolve.
            # If you prefer NOT to prune, comment out the next 3 lines.
            if violates_neq(subst, neq_pairs):
                print(f"[DEBUG]   Disjunct pruned due to violated '!=' constraints: {dt[:80]}...")
                continue

            add_consts_from_atoms(atoms)

            # Resolve actions with the SAME per-disjunct substitution
            acts = parse_action_list(action_line, subst) if action_line else []

            # Collect constants appearing only in actions
            for (_op, args) in acts:
                for a in args:
                    if re.match(r"^[A-Za-z]\w*$", a):
                        constants.add(a.lower())

            disjuncts_atoms.append(atoms)
            disjuncts_actions.append(acts)

            print(f"[DEBUG]   Disjunct atoms: {atoms}")
            print(f"[DEBUG]   Disjunct actions: {acts}")

        disjuncts_per_subgoal.append(disjuncts_atoms)
        actions_per_subgoal.append(disjuncts_actions)

    # Keep any v123 style names we may have, but they are NOT constants.
    # constants set should contain only letter-leading tokens -> already enforced above.

    print(f"[DEBUG] Total constants found: {sorted(constants)}")
    return disjuncts_per_subgoal, actions_per_subgoal, sorted(constants)

# ---------- PDDL emitters ----------

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

def derive_ssa_domain(original_domain_text: str) -> str:
    s = original_domain_text
    s = re.sub(r":precondition\s*\([^)]*\)", ":precondition (and)",
               s, flags=re.IGNORECASE | re.DOTALL)
    s = re.sub(r"(?is)\(define\s*\(\s*domain\s+[^\s\)]+\)",
               "(define (domain blocksworld-4ops-ssa)",
               s, count=1)
    return s

# ---------- Validator ----------

def run_validate(validate_bin: str, domain_path: Path, prob_path: Path, plan_path: Path, 
                 verbose: bool = False) -> Tuple[bool, str, dict]:
    cmd = [validate_bin, str(domain_path), str(prob_path), str(plan_path)]
    debug_info = {
        "command": " ".join(cmd),
        "domain_exists": domain_path.exists(),
        "problem_exists": prob_path.exists(),
        "plan_exists": plan_path.exists(),
    }
    if verbose:
        print(f"[DEBUG] Running: {debug_info['command']}")
        print(f"[DEBUG] Files exist - Domain: {debug_info['domain_exists']}, "
              f"Problem: {debug_info['problem_exists']}, Plan: {debug_info['plan_exists']}")

    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=10)
        debug_info["return_code"] = proc.returncode
        debug_info["stdout"] = proc.stdout or ""
        debug_info["stderr"] = proc.stderr or ""
    except FileNotFoundError as e:
        debug_info["error"] = str(e)
        return False, f"[ERROR] validator not found: {validate_bin} ({e})", debug_info
    except subprocess.TimeoutExpired:
        debug_info["error"] = "Timeout"
        return False, "[ERROR] Validator timed out after 10 seconds", debug_info
    
    out = debug_info["stdout"] + "\n" + debug_info["stderr"]

    success_patterns = [
        "Successful plans",
        "Plan valid",
        "Plan Validation details",
        "Goal satisfied"
    ]

    passed = any(pattern.lower() in out.lower() for pattern in success_patterns)
    if proc.returncode == 0 and not passed and "error" not in out.lower():
        passed = True

    if verbose:
        print(f"[DEBUG] Return code: {proc.returncode}")
        print(f"[DEBUG] Validation passed: {passed}")
        if not passed:
            print(f"[DEBUG] Output sample: {out[:500]}")

    return passed, out, debug_info

# ---------- CLI ----------

def main():
    ap = argparse.ArgumentParser(description="Convert 'Regressed goals' to PDDL problems/plans and validate with VAL.")
    ap.add_argument("--in", dest="infile", required=True, help="Path to 'Regressed goals' text file")
    ap.add_argument("--domain", dest="domain", required=False, help="Path to original domain PDDL")
    ap.add_argument("--mode", choices=["ssa", "strict"], default="ssa", 
                    help="ssa: emit SSA domain; strict: use original domain")
    ap.add_argument("--outdir", default="out_val", help="Output directory")
    ap.add_argument("--validator", default="validate", help="Path to VAL binary")
    ap.add_argument("--no-run", action="store_true", help="Only generate problems/plans")
    ap.add_argument("--verbose", "-v", action="store_true", help="Enable verbose debugging")
    ap.add_argument("--test-one", action="store_true", help="Test only first problem/plan pair")
    args = ap.parse_args()
    
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Reading input from: {args.infile}")
    raw = Path(args.infile).read_text(encoding="utf-8")

    try:
        disjuncts_per_subgoal, actions_per_subgoal, constants = parse_blocks(raw)
    except Exception as e:
        print(f"[ERROR] Failed to parse input: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    if not disjuncts_per_subgoal:
        print("[ERROR] No subgoals found in input")
        return 1
    
    goal_atoms = disjuncts_per_subgoal[0][0] if disjuncts_per_subgoal[0] else []
    if not goal_atoms:
        print("[WARN] First subgoal produced an empty goal. Check input formatting.")
    
    objects = constants
    print(f"[INFO] Found {len(objects)} objects: {objects}")
    print(f"[INFO] Goal atoms: {goal_atoms}")
    
    manifest = []
    for si in range(1, len(disjuncts_per_subgoal)):
        disjs = disjuncts_per_subgoal[si]
        acts_per_dj = actions_per_subgoal[si]
        for dj_idx, (atoms, acts) in enumerate(zip(disjs, acts_per_dj), start=1):
            prob_name = f"problem_s{si:02d}_d{dj_idx:02d}.pddl"
            plan_name = f"plan_s{si:02d}_d{dj_idx:02d}.soln"
            
            pddl = make_problem_pddl(
                objects, atoms, goal_atoms,
                domain_name=("blocksworld-4ops-ssa" if args.mode == "ssa" else "blocksworld-4ops")
            )
            
            (outdir / prob_name).write_text(pddl, encoding="utf-8")
            (outdir / plan_name).write_text(make_plan_file(acts), encoding="utf-8")
            
            manifest.append({
                "subgoal_index": si,
                "disjunct_index": dj_idx,
                "problem": prob_name,
                "plan": plan_name,
                "init_atoms": atoms,
                "actions": acts
            })
            
            if args.verbose:
                print(f"[DEBUG] Created {prob_name} with init: {atoms}")
                print(f"[DEBUG] Created {plan_name} with actions: {acts}")

    domain_path = None
    if args.mode == "ssa":
        if not args.domain or not Path(args.domain).exists():
            print("[ERROR] --domain is required in SSA mode (to derive SSA variant).")
            return 1
        dom_txt = Path(args.domain).read_text(encoding="utf-8")
        ssa_dom = derive_ssa_domain(dom_txt)
        domain_path = outdir / "domain-ssa.pddl"
        domain_path.write_text(ssa_dom, encoding="utf-8")
        print(f"[INFO] Generated SSA domain at: {domain_path}")
    else:
        if args.domain and Path(args.domain).exists():
            domain_path = Path(args.domain)
        else:
            domain_path = Path("blocksworld-4ops.pddl")
    
    (outdir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[INFO] Generated {len(manifest)} problem/plan pairs in: {outdir}")
    
    if args.no_run:
        print("[INFO] Skipping validation (--no-run).")
        return 0
    
    if not domain_path or not domain_path.exists():
        print(f"[ERROR] Domain file not found for validation: {domain_path}")
        return 1

    test_cmd = [args.validator, "--help"]
    try:
        subprocess.run(test_cmd, capture_output=True, check=False, timeout=2)
        print(f"[INFO] Validator found: {args.validator}")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print(f"[ERROR] Validator not found or not working: {args.validator}")
        print("[HINT] Install VAL from: https://github.com/KCL-Planning/VAL")
        return 1

    failures = []
    results = []
    
    items_to_test = manifest[:1] if args.test_one else manifest
    
    for idx, item in enumerate(items_to_test):
        prob = outdir / item["problem"]
        plan = outdir / item["plan"]
        
        print(f"[INFO] Validating {idx+1}/{len(items_to_test)}: s{item['subgoal_index']:02d}/d{item['disjunct_index']:02d}")
        
        ok, out, debug_info = run_validate(args.validator, domain_path, prob, plan, args.verbose)
        status = "PASS" if ok else "FAIL"
        
        results.append({**item, "status": status, "debug": debug_info})
        if not ok and (args.verbose or len(failures) < 5):
            print(f"[DEBUG] Validation failed for {prob.name}")
            print(f"[DEBUG] Full output:\n{out[:1000]}")

        if not ok:
            failures.append(item)

    (outdir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    with open(outdir / "results.csv", "w", encoding="utf-8") as f:
        f.write("subgoal,disjunct,problem,plan,status\n")
        for r in results:
            f.write(f"{r['subgoal_index']},{r['disjunct_index']},{r['problem']},{r['plan']},{r['status']}\n")

    if failures:
        print(f"\n[FAILURES] {len(failures)}/{len(items_to_test)} validations failed.")
        return 2
    else:
        print(f"\n[SUCCESS] All {len(items_to_test)} problem/plan pairs validated successfully.")
        return 0

if __name__ == "__main__":
    sys.exit(main())
