#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from pddl_planner.rule_based.translator import convert_text_to_nlpddl_instances


def state_to_jsonable(state):
    return [a.to_list() if hasattr(a, "to_list") else a for a in state]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Parse a benchmark JSON of NL Blocksworld descriptions and emit "
            "problems.json ([init, goal] per problem) and goals.json (goal per problem) "
            "using the rule-based converter."
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

    for inst in data.get("instances", []):
        description = inst.get("query", "")
        _, problems = convert_text_to_nlpddl_instances(description)

        for pr in problems:
            init_json = state_to_jsonable(pr.initial_state)
            goal_json = state_to_jsonable(pr.goal_state)
            all_problem_pairs.append([init_json, goal_json])
            all_goals.append(goal_json)

    (out_dir / "problem.json").write_text(json.dumps(all_problem_pairs, indent=2))
    (out_dir / "goal.json").write_text(json.dumps(all_goals, indent=2))

    print(f"Wrote {out_dir / 'problem.json'}")
    print(f"Wrote {out_dir / 'goal.json'}")


if __name__ == "__main__":
    main()
