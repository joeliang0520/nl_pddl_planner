#!/usr/bin/env python3

import argparse
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
    args = parser.parse_args(argv)

    checker = BlockWorldInitialStateChecker(input_path=args.input)
    checker.load_json()
    checker.load_initial_facts()
    results = checker.evaluate_subgoals()

    # Print concise summary for quick visibility
    print("Initial State:")
    for s in checker.data.get("initial_state", []):
        print(f"  - {s}")
    print("\nPlans evaluation:")
    for plan_res in results["plans_evaluation"]:
        idx = plan_res["plan_index"]
        ok = plan_res["all_subgoals_satisfied"]
        if ok or not ok:
            print(f"Plan {idx}: all_subgoals_satisfied={ok}")
            # Print the corresponding raw disjoint (no substitution) if available
            try:
                raw_plan = (checker.data.get("plans", []) or [])[idx]
                raw_disj = {}
                if isinstance(raw_plan, dict):
                    raw_disj = raw_plan.get("subgoal_raw", {}) or {}
                clauses = []
                if isinstance(raw_disj, dict):
                    # Support both 'disjoint' (new) and 'disjoint_1' (legacy)
                    clauses = raw_disj.get("disjoint") or raw_disj.get("disjoint_1", []) or []
                if clauses:
                    print("   Disjoint (raw clauses):")
                    for c in clauses:
                        print(f"     - {c}")
            except Exception:
                pass
            actions = plan_res.get("action", [])
            if actions:
                print("   Actions:")
                for act in actions:
                    print(f"     - {act}")
            # Print the explicit conjunction formula of subgoals
            try:
                conj_preds = [sg.get("predicate", "") for sg in plan_res.get("subgoals", [])]
                if conj_preds:
                    print("   Conjunction:")
                    print("     " + " & ".join(conj_preds))
            except Exception:
                pass
            # Print conjunction status and bindings if available
            conj = plan_res.get("conjunction", {}) or {}
            if conj:
                print(f"   Conjunction satisfied: {conj.get('satisfied', False)}")
                vars_ = conj.get("variables") or []
                binds = conj.get("bindings")
                if vars_ and binds:
                    print(f"   Conjunction bindings (variables: {vars_}):")
                    for row in binds:
                        print(f"     - {row}")
            for sg in plan_res["subgoals"]:
                b = ""
                if sg["bindings"] is not None:
                    b = f" bindings={sg['bindings']}"
                print(f"   * {sg['predicate']}: {sg['satisfied']}{b}")

    if args.output:
        checker.save_results(args.output)


if __name__ == "__main__":
    main()
