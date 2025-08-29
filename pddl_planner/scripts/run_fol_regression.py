import argparse
import json
import pddl
from pddl_planner.planner.planner import FOLRegressionPlanner, RegressionPlanner
from pddl_planner.planner.nl_planner import NLFOLRegressionPlanner

def run_test(domain_path, problem_path, planner_type, max_depth=3):
    dom = pddl.parse_domain(domain_path)
    prob = pddl.parse_problem(problem_path)

    if planner_type == "fol":
        planner_cls = FOLRegressionPlanner
    elif planner_type == "regression":
        planner_cls = RegressionPlanner
    elif planner_type == "nl_fol":
        planner_cls = NLFOLRegressionPlanner
    else:
        raise ValueError(f"Unknown planner: {planner_type}")

    planner = planner_cls(dom, prob, max_depth=max_depth)
    regressed_plans = planner.regress_plan()

    for subgoal, rev_plan, substitution in regressed_plans:
        print("Subgoal:", subgoal)
        rev_plan.reverse()
        print("Actions:", rev_plan)
        print("Substitution:", substitution)
        print("--------------------")

def main():
    parser = argparse.ArgumentParser(
        description="Run a regression planner over a PDDL domain & problem"
    )
    parser.add_argument(
        "--domain", "-d", required=True,
        help="Path to the PDDL domain file"
    )
    parser.add_argument(
        "--problem", "-p", required=True,
        help="Path to the PDDL problem file"
    )
    parser.add_argument(
        "--planner", choices=["fol", "regression", 'nl_fol'], default="fol",
        help="Which planner to use: fol (first‑order logic) or regression (ghallab's style)"
    )
    parser.add_argument(
        "--depth", "-m", type=int, default=3,
        help="Maximum regression depth"
    )
    args = parser.parse_args()
    if args.planner == "nl_fol":
        # check if the domain file is a json file
        if args.domain.endswith('.json'):
            with open(args.domain, 'r') as f:
                domain = json.load(f)
        else:
            raise ValueError("Domain file must be a json file")
        # check if the goal file is a json file
        if args.problem.endswith('.json'):
            with open(args.problem, 'r') as f:
                problem = json.load(f)
        else:
            raise ValueError("Problem file must be a json file")
        # run the test
        run_test(domain, problem, args.planner, args.depth)
    else:   
        run_test(args.domain, args.problem, args.planner, args.depth)

if __name__ == "__main__":
    main()