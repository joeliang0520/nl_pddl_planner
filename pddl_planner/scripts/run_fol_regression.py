import argparse
import pddl
from pddl_planner.planner.planner import FOLRegressionPlanner, RegressionPlanner

def run_test(domain_path, problem_path, planner_type, max_depth=3):
    dom = pddl.parse_domain(domain_path)
    prob = pddl.parse_problem(problem_path)

    if planner_type == "fol":
        planner_cls = FOLRegressionPlanner
    elif planner_type == "regression":
        planner_cls = RegressionPlanner
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
        "--planner", choices=["fol", "regression"], default="fol",
        help="Which planner to use: fol (first‑order logic) or regression (ghallab's style)"
    )
    parser.add_argument(
        "--depth", "-m", type=int, default=3,
        help="Maximum regression depth"
    )
    args = parser.parse_args()
    run_test(args.domain, args.problem, args.planner, args.depth)

if __name__ == "__main__":
    main()