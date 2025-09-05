import argparse
import json
from pathlib import Path

from pddl_planner.llm.translator import goals_to_json
from pddl_planner.rule_based.translator import convert_text_to_nlpddl_instances


def main() -> None:
    """Convert a Blocksworld NL description to NL-PDDL using rule-based rules."""

    parser = argparse.ArgumentParser(
        description=(
            "Use a rule-based converter to translate a natural language "
            "Blocksworld description into NL-PDDL domain and problem JSON files."
        )
    )
    parser.add_argument(
        "--input", "-i", required=True,
        help="Path to a text file containing the natural language description",
    )
    parser.add_argument(
        "--domain-out", "-d", default="domain.json",
        help="Where to write the generated domain JSON",
    )
    parser.add_argument(
        "--problem-out", "-p", default="problem.json",
        help="Where to write the generated problem JSON",
    )
    parser.add_argument(
        "--goal-out", "-g", default="goal.json",
        help="Where to write the generated goals JSON",
    )
    args = parser.parse_args()

    description = Path(args.input).read_text()
    domain, problems = convert_text_to_nlpddl_instances(description)

    domain_json = [{"Predicate": [p.to_list() for p in domain.predicates]}]
    domain_json.extend([a.to_dict() for a in domain.actions])

    if len(problems) == 1:
        problem_json = [
            [p.to_list() for p in problems[0].initial_state],
            [p.to_list() for p in problems[0].goal_state],
        ]
        goal_json = goals_to_json(problems[0])
    else:
        problem_json = []
        for pr in problems:
            problem_json.append(
                [
                    [p.to_list() for p in pr.initial_state],
                    [p.to_list() for p in pr.goal_state],
                ]
            )
        goal_json = goals_to_json(problems)

    Path(args.domain_out).write_text(json.dumps(domain_json, indent=2))
    Path(args.problem_out).write_text(json.dumps(problem_json, indent=2))
    Path(args.goal_out).write_text(json.dumps(goal_json, indent=2))

    print(f"Domain written to {args.domain_out}")
    print(f"Problem written to {args.problem_out}")
    print(f"Goals written to {args.goal_out}")


if __name__ == "__main__":
    main()
