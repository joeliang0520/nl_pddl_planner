#!/usr/bin/env python3

import argparse
import json
from typing import Optional, List

from initial_state_checker import (
    BlockWorldInitialStateChecker,
)


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(
        description="Check block-world initial state against subgoals using PyDatalog",
    )
    parser.add_argument(
        "--input",
        "-i",
        default="example_out_pddl_regression.json",
        help="Path to input JSON file (e.g., example_out_pddl_regression.json)",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="",
        help="Optional path to save JSON results",
    )
    parser.add_argument(
        "--print-mode",
        choices=["all", "subgoals_if_conj"],
        default="subgoals_if_conj",
        help=(
            "Control subgoal printing: 'all' prints all subgoals; "
            "'subgoals_if_conj' prints subgoals only when conjunction is satisfied"
        ),
    )
    args = parser.parse_args(argv)

    checker = BlockWorldInitialStateChecker(input_path=args.input)
    checker.load_json()
    checker.load_initial_facts()
    results = checker.evaluate_subgoals()

    # Print only requested sections per plan
    all_conj_satisfied = True
    found_any_conj = False
    for plan_res in results["plans_evaluation"]:
        idx = plan_res["plan_index"]
        ok = plan_res["all_subgoals_satisfied"]
        if ok:
            # Conjunction info first (also used below)
            conj = plan_res.get("conjunction", {}) or {}
            conj_sat = bool(conj.get('satisfied', False)) if conj else False
            # Subgoal predicates (from evaluated subgoals)
            try:
                conj_preds = [sg.get("predicate", "") for sg in plan_res.get("subgoals", [])]
                if conj_preds:
                    print("Subgoal Predicates:")
                    for p in conj_preds:
                        print(f"  - {p}")
            except Exception:
                pass
            # Disjoint (raw clauses) from original plan input
            try:
                raw_plan = (checker.data.get("plans", []) or [])[idx]
                raw_disj = {}
                if isinstance(raw_plan, dict):
                    raw_disj = raw_plan.get("subgoal_raw", {}) or {}
                clauses = []
                if isinstance(raw_disj, dict):
                    clauses = raw_disj.get("disjoint") or raw_disj.get("disjoint_1", []) or []
                if clauses:
                    print("Disjoint (raw clauses):")
                    for c in clauses:
                        print(f"  - {c}")
            except Exception:
                pass
            # Actions
            actions = plan_res.get("action", [])
            if actions:
                print("Actions:")
                for act in actions:
                    print(f"  - {act}")
            # Conjunction formula and details
            try:
                if plan_res.get("subgoals"):
                    print("Conjunction:")
                    print("  " + " & ".join([sg.get("predicate", "") for sg in plan_res["subgoals"]]))
            except Exception:
                pass
            if conj:
                print(f"Conjunction satisfied: {conj.get('satisfied', False)}")
                vars_ = conj.get("variables") or []
                binds = conj.get("bindings")
                if vars_ and binds:
                    print(f"Conjunction bindings (variables: {vars_}):")
                    for row in binds:
                        print(f"  - {row}")

            # Track overall conjunction satisfaction across all plans (regardless of print mode)
            if conj:
                found_any_conj = True
                if not conj_sat:
                    all_conj_satisfied = False

    # No overall summary when restricting output to requested sections

    if args.output:
        checker.save_results(args.output)


if __name__ == "__main__":
    main()
