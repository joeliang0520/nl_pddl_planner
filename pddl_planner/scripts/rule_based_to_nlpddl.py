#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from pddl_planner.rule_based.translator import convert_text_to_nlpddl_instances


def state_to_jsonable(state):
    return [a.to_list() if hasattr(a, "to_list") else a for a in state]


def domain_to_jsonable(domain):
    """Match the BW domain JSON format:
       [ { "Predicate": [ [text, {args}], ... ] }, {Action...}, {Action...}, ... ]
    """
    # Predicates block
    pred_block = {
        "Predicate": [
            (p.to_list() if hasattr(p, "to_list") else [getattr(p, "text", str(p)), getattr(p, "arguments", {})])
            for p in domain.predicates
        ]
    }
    items = [pred_block]

    # Actions (prefer .to_dict if available)
    for a in domain.actions:
        if hasattr(a, "to_dict"):
            items.append(a.to_dict())
            continue

        # Fallback manual mapping if .to_dict() is unavailable
        action_name_text = getattr(getattr(a, "action_name", None), "text", "")
        action_name_args = getattr(getattr(a, "action_name", None), "arguments", {})

        preconds = [
            (p.to_list() if hasattr(p, "to_list") else [getattr(p, "text", str(p)), getattr(p, "arguments", {})])
            for p in getattr(a, "preconditions", [])
        ]
        eff_pos = [
            (p.to_list() if hasattr(p, "to_list") else [getattr(p, "text", str(p)), getattr(p, "arguments", {})])
            for p in getattr(getattr(a, "effects", None), "Positive", [])
        ]
        eff_neg = [
            (p.to_list() if hasattr(p, "to_list") else [getattr(p, "text", str(p)), getattr(p, "arguments", {})])
            for p in getattr(getattr(a, "effects", None), "Negative", [])
        ]

        items.append(
            {
                "Action": getattr(a, "name", ""),
                "Action name": [action_name_text, action_name_args],
                "Parameters": getattr(a, "parameters", {}),
                "Preconditions": preconds,
                "Effects": {
                    "Positive": eff_pos,
                    "Negative": eff_neg,
                },
            }
        )

    return items


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Parse a benchmark JSON of NL descriptions and emit:\n"
            "- problem.json: [init, goal] per problem (aggregated)\n"
            "- goal.json: goal per problem (aggregated)\n"
            "- domain.json: domain (predicates + actions) used by the parser"
        )
    )
    parser.add_argument("--input", "-i", required=True, help="Path to the benchmark JSON file")
    parser.add_argument("--output-dir", "-o", required=True, help="Directory to write outputs")
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text())
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    all_problem_pairs = []  # each element: [ init_state_json, goal_state_json ]
    all_goals = []          # each element: goal_state_json
    captured_domain = None  # capture the first domain we see and write it once

    for inst in data.get("instances", []):
        description = inst.get("query", "")
        domain, problems = convert_text_to_nlpddl_instances(description)

        if captured_domain is None:
            captured_domain = domain

        for pr in problems:
            init_json = state_to_jsonable(pr.initial_state)
            goal_json = state_to_jsonable(pr.goal_state)
            all_problem_pairs.append([init_json, goal_json])
            all_goals.append(goal_json)

    # Write aggregated problems and goals
    (out_dir / "problem.json").write_text(json.dumps(all_problem_pairs, indent=2))
    (out_dir / "goal.json").write_text(json.dumps(all_goals, indent=2))

    # Write domain once (if we parsed any instance)
    if captured_domain is not None:
        domain_json = domain_to_jsonable(captured_domain)
        (out_dir / "domain.json").write_text(json.dumps(domain_json, indent=2))
        print(f"Wrote {out_dir / 'domain.json'}")

    print(f"Wrote {out_dir / 'problem.json'}")
    print(f"Wrote {out_dir / 'goal.json'}")


if __name__ == "__main__":
    main()
