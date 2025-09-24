import argparse
import json
import pddl
import os
from pddl_planner.planner.nl_planner import NLFOLRegressionPlanner

def run_test(domain_path, problem_path, planner_type, max_depth=3, problem_index=0, cache_path=None, log_path=None, time_limit=None, verbose=True, llm_model=None, llm_cache_path=None):
    
    if not planner_type == "nl_fol":
        dom = pddl.parse_domain(domain_path)
        prob = pddl.parse_problem(problem_path)
    else:
        dom = domain_path
        prob = problem_path
        if isinstance(prob, list):
            prob = prob[problem_index] # take the first problem

    if planner_type == "fol" or planner_type == "nl_fol":
        planner_cls = NLFOLRegressionPlanner
    else:
        raise ValueError(f"Unknown planner: {planner_type}")

    if llm_cache_path is not None:
        #check if the cache json file exists
        if not os.path.exists(llm_cache_path):
            os.makedirs(os.path.dirname(llm_cache_path), exist_ok=True)
            with open(llm_cache_path, 'w') as f:
                json.dump({}, f)

    planner = planner_cls(dom, prob, max_depth=max_depth, cache_path=cache_path, 
    log_path=log_path, time_limit=time_limit, verbose=verbose, llm_model=llm_model, llm_cache_path=llm_cache_path)
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
        "--planner", choices=["fol", 'nl_fol'], default="fol",
        help="Which planner to use: fol (first‑order logic) or nl_fol (natural language first‑order logic)"
    )
    parser.add_argument(
        "--depth", "-m", type=int, default=3,
        help="Maximum regression depth"
    )
    parser.add_argument(
        "--problem_index", "-i", type=int, default=0,
        help="Problem index", required=False
    )
    parser.add_argument(
        "--cache_path", "-c", type=str, default=None,
        help="Cache path", required=False
    )
    parser.add_argument(
        "--log_path", "-l", type=str, default=None,
        help="Log path", required=False
    )
    parser.add_argument(
        "--time_limit", "-t", type=int, default=None,
        help="Time limit", required=False
    )
    parser.add_argument(
        "--verbose", "-v", type=bool, default=True,
        help="Verbose", required=False
    )
    parser.add_argument(
        "--llm_model", "-m", type=str, default="gpt-4o-mini",
        help="LLM model", required=False
    )
    parser.add_argument(
        "--llm_api_key", "-k", type=str, default=None,
        help="LLM API key", required=False
    )
    parser.add_argument(
        "--llm_cache_path", "-cc", type=str, default=None,
        help="LLM cache path", required=False
    )
    args = parser.parse_args()

    if args.problem_index is None:
        print("Problem index not provided, using the first problem")
        problem_index = 0
    else:
        problem_index = args.problem_index

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
        run_test(domain, problem, args.planner, args.depth, problem_index=problem_index, 
        cache_path=args.cache_path, log_path=args.log_path, time_limit=args.time_limit, 
        verbose=args.verbose, llm_model=args.llm_model, 
        llm_cache_path=args.llm_cache_path)

if __name__ == "__main__":
    main()