#!/usr/bin/env python3
import argparse, json, re, sys
from pathlib import Path
from pyDatalog import pyDatalog

pyDatalog.create_terms('on, ontable, clear, holding, handempty, eq, neq, A, B, Z')
_var_re = re.compile(r'^v\d+$')

def parse_pddl_init(pddl_text: str):
    s = re.sub(r';[^\n]*', '', pddl_text)
    m = re.search(r'\(:init(.*?)\)\s*\)\s*$', s, flags=re.DOTALL | re.IGNORECASE)
    if not m:
        return []
    body = m.group(1)
    atoms = []
    for t in re.findall(r'\([^\(\)]+\)', body):
        t = t.strip()[1:-1].strip()
        parts = t.split()
        if not parts:
            continue
        head, args = parts[0].lower(), [a.lower() for a in parts[1:]]
        if head == 'handempty':
            atoms.append('handempty')
        else:
            atoms.append(f"{head} {' '.join(args)}")
    return atoms

def _reset_logic():
    pyDatalog.clear()
    eq(A, B)  <= (A == B)
    neq(A, B) <= ~(A == B)
    on(A, B)    <= eq(A, '__none__') & neq(A, '__none__')
    ontable(A)  <= eq(A, '__none__') & neq(A, '__none__')
    clear(A)    <= eq(A, '__none__') & neq(A, '__none__')
    holding(A)  <= eq(A, '__none__') & neq(A, '__none__')
    handempty() <= eq(Z, '__none__') & neq(Z, '__none__')

def _assert_world(init_atoms):
    for a in init_atoms:
        if a == 'handempty':
            +handempty(); continue
        head, *args = a.split()
        if head == 'on' and len(args) == 2:
            +on(args[0], args[1])
        elif head == 'ontable' and len(args) == 1:
            +ontable(args[0])
        elif head == 'clear' and len(args) == 1:
            +clear(args[0])
        elif head == 'holding' and len(args) == 1:
            +holding(args[0])

def _term(tok, var_env):
    if _var_re.match(tok):
        name = 'V' + tok[1:]
        if name not in var_env:
            var_env[name] = pyDatalog.Variable()
        return var_env[name]
    return tok

def _literal(a, var_env):
    if a == 'handempty':
        return handempty()
    head, *args = a.split()
    if head == 'on':
        return on(_term(args[0], var_env), _term(args[1], var_env))
    if head == 'ontable':
        return ontable(_term(args[0], var_env))
    if head == 'clear':
        return clear(_term(args[0], var_env))
    if head == 'holding':
        return holding(_term(args[0], var_env))
    raise ValueError(head)

def _constraint_literal(pred, t1, t2, var_env):
    return (eq if pred == 'eq' else neq)(_term(t1, var_env), _term(t2, var_env))

def disjunct_holds(init_atoms, disjunct_atoms, constraints=None):
    _reset_logic()
    _assert_world(init_atoms)
    var_env, conjunct = {}, None
    for a in disjunct_atoms:
        lit = _literal(a.lower(), var_env)
        conjunct = lit if conjunct is None else (conjunct & lit)
    if constraints:
        for t1, t2 in (constraints.get('eq') or []):
            lit = _constraint_literal('eq', t1, t2, var_env)
            conjunct = lit if conjunct is None else (conjunct & lit)
        for t1, t2 in (constraints.get('neq') or []):
            lit = _constraint_literal('neq', t1, t2, var_env)
            conjunct = lit if conjunct is None else (conjunct & lit)
    if conjunct is None:
        return False, None
    ans = conjunct.ask()
    if not ans:
        return False, None
    binding = {}
    sample = ans[0]
    for k, v in var_env.items():
        try:
            if v in sample:
                binding[k] = sample[v]
        except Exception:
            if k in sample:
                binding[k] = sample[k]
    return True, (binding or sample)

def process_one_case(case_dir: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((case_dir / 'manifest.json').read_text(encoding='utf-8'))
    init_atoms = parse_pddl_init((case_dir / 'initial_state.pddl').read_text(encoding='utf-8'))
    matched = None
    for item in manifest:
        disj_atoms = [x.lower() for x in item['init_atoms']]
        cons = item.get('constraints') or {"eq": [], "neq": []}
        ok, binding = disjunct_holds(init_atoms, disj_atoms, cons)
        if ok:
            matched = {**item, "status": "PASS", "bindings": binding,
                       "init_atoms_checked": disj_atoms, "constraints_checked": cons}
            break
    if matched:
        (out_dir / 'matched_case.json').write_text(json.dumps(matched, indent=2), encoding='utf-8')
        with open(out_dir / 'matched_case.txt', 'w', encoding='utf-8') as f:
            f.write(f"Matched subgoal s{matched['subgoal_index']} / disjunct d{matched['disjunct_index']}\n")
            f.write("Atoms: " + ", ".join(matched['init_atoms_checked']) + "\n")
            if matched.get("constraints_checked"):
                f.write("Constraints: " + json.dumps(matched["constraints_checked"]) + "\n")
            if matched.get("bindings"):
                f.write("One binding: " + json.dumps(matched["bindings"]) + "\n")
        print(f"[MATCH] {case_dir.name} :: s{matched['subgoal_index']}/d{matched['disjunct_index']}")
        if matched.get("bindings"):
            print(f"[BINDING] {matched['bindings']}")
        return {"case": case_dir.name, "status": "PASS",
                "subgoal": matched["subgoal_index"], "disjunct": matched["disjunct_index"]}
    else:
        print(f"[NO MATCH] {case_dir.name} :: tested {len(manifest)} disjunct(s)")
        return {"case": case_dir.name, "status": "NO_MATCH", "tested": len(manifest)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--indir',   required=True, help='Parent folder containing many subfolders (e.g., out_val/)')
    ap.add_argument('--outdir',  default='out_check', help='Parent folder for outputs per case')
    args = ap.parse_args()

    indir = Path(args.indir)
    out_parent = Path(args.outdir)
    out_parent.mkdir(parents=True, exist_ok=True)

    subdirs = [p for p in sorted(indir.iterdir()) if p.is_dir()]
    overall = []
    for d in subdirs:
        if not (d / 'manifest.json').exists() or not (d / 'initial_state.pddl').exists():
            continue
        res = process_one_case(d, out_parent / d.name)
        overall.append(res)

    (out_parent / 'overall.json').write_text(json.dumps(overall, indent=2), encoding='utf-8')
    with open(out_parent / 'overall.csv', 'w', encoding='utf-8') as f:
        f.write("case,status,subgoal,disjunct,tested\n")
        for r in overall:
            f.write(",".join([
                r.get("case",""),
                r.get("status",""),
                str(r.get("subgoal","")),
                str(r.get("disjunct","")),
                str(r.get("tested",""))
            ]) + "\n")

    ok = sum(1 for r in overall if r.get("status") == "PASS")
    nm = sum(1 for r in overall if r.get("status") == "NO_MATCH")
    print(f"[SUMMARY] {ok} PASS, {nm} NO_MATCH across {len(overall)} case(s)")
    return 0 if nm == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
