import argparse
import json
from pathlib import Path

from pddl_planner.llm.translator import translate_to_nlpddl


def main() -> None:
    """Translate a natural language planning description into NL-PDDL JSON files."""

    parser = argparse.ArgumentParser(
        description=(
            "Use an LLM to translate a natural language description of a planning "
            "domain and problem into NL-PDDL JSON files."
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
        "--model", "-m", default="gpt-4.1",
        help="OpenAI model to use for translation",
    )
    parser.add_argument(
        "--api-key", dest="api_key", default=None,
        help="OpenAI API key (defaults to environment variable)",
    )
    args = parser.parse_args()

    description = Path(args.input).read_text()

    result = translate_to_nlpddl(description, model=args.model, api_key=args.api_key)

    domain_json = [{"Predicate": [p.to_list() for p in result.domain.predicates]}]
    domain_json.extend([a.to_dict() for a in result.domain.actions])

    problem_json = [
        [p.to_list() for p in result.problem.initial_state],
        [p.to_list() for p in result.problem.goal_state],
    ]

    Path(args.domain_out).write_text(json.dumps(domain_json, indent=2))
    Path(args.problem_out).write_text(json.dumps(problem_json, indent=2))

    print(f"Domain written to {args.domain_out}")
    print(f"Problem written to {args.problem_out}")


if __name__ == "__main__":
    main()
