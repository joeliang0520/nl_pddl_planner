import argparse
import json
from pathlib import Path

from pddl_planner.llm.benchmark_parser import extract_problem_descriptions
from pddl_planner.llm.translator import translate_to_nlpddl


def main() -> None:
    """Parse a benchmark JSON file and generate NL-PDDL problems."""

    parser = argparse.ArgumentParser(
        description=(
            "Parse a benchmark JSON containing natural language problem "
            "descriptions and emit NL-PDDL domain/problem files using an LLM "
            "translator."
        )
    )
    parser.add_argument(
        "--input", "-i", required=True, help="Path to the benchmark JSON file"
    )
    parser.add_argument(
        "--output-dir", "-o", required=True, help="Directory to write problems"
    )
    parser.add_argument(
        "--model", "-m", default="gpt-4.1", help="OpenAI model to use"
    )
    parser.add_argument(
        "--api-key", dest="api_key", default=None,
        help="OpenAI API key (defaults to environment variable)",
    )
    args = parser.parse_args()

    data = json.loads(Path(args.input).read_text())
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    for inst in data.get("instances", []):
        instance_id = inst.get("instance_id")
        num_examples = len(inst.get("example_instance_ids", []))
        problems = extract_problem_descriptions(inst.get("query", ""), num_examples)

        for idx, description in enumerate(problems):
            result = translate_to_nlpddl(
                description, model=args.model, api_key=args.api_key
            )
            domain_json = [{"Predicate": [p.to_list() for p in result.domain.predicates]}]
            domain_json.extend([a.to_dict() for a in result.domain.actions])
            problem_json = [
                [p.to_list() for p in result.problem.initial_state],
                [p.to_list() for p in result.problem.goal_state],
            ]

            prefix = f"instance_{instance_id}_problem_{idx}"
            (out_dir / f"{prefix}_domain.json").write_text(
                json.dumps(domain_json, indent=2)
            )
            (out_dir / f"{prefix}_problem.json").write_text(
                json.dumps(problem_json, indent=2)
            )

            print(f"Wrote {prefix}_domain.json and {prefix}_problem.json")


if __name__ == "__main__":
    main()
