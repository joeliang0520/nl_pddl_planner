import time
import pddl
import json
import os
from dotenv import load_dotenv

from pddl_planner.planner.nl_planner import NLFOLRegressionPlanner
from pddl_planner.logic.nl_parser import NLParser
from pddl_planner.logic.formula import DisjunctiveFormula

if __name__ == "__main__":
    env_flag = False
    try:
        load_dotenv()
        env_flag = True
    except Exception as e:
        print(f"Error loading .env file: {e}")
    if env_flag:
        print("Environment variables loaded successfully")
    else:
        print("Environment variables not loaded")
        
    # load the domain from the file
    with open('files/blockworld_domain.json', 'r') as f:
        domain = json.load(f)

    # load the problems (initial state and goal pairs) from the file
    with open('files/blockworld_problem.json', 'r') as f:
        all_blocks = json.load(f)

    #save with indent 4
    # with open('files/NL_actions_new.json', 'w') as f:
    #     json.dump(domain, f, indent=4)
    # with open('files/NL_goals_new.json', 'w') as f:
    #     json.dump(all_blocks, f, indent=4)

    # create a directory to store the results
    current_dir = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(current_dir, f'blockworld_results')
    os.makedirs(save_path, exist_ok=True)

    # initialize the planner
    for i, problem in enumerate(all_blocks[3:4]):
        # Expect each problem to be [initial_state, goal]; fall back to goal only
        if isinstance(problem, list) and len(problem) == 2 and isinstance(problem[0], list):
            init_state, goal = problem
        else:
            init_state = None
            goal = problem

        print(f'Problem {goal} =========================================')
        planner = NLFOLRegressionPlanner(domain.copy(), goal.copy(), max_depth=10)
        # track time
        start_time = time.time()
        regressed_plans = planner.regress_plan()
        end_time = time.time()
        print(f'Time taken: {end_time - start_time} seconds')

        # create a empty text file to store the results
        save_file_path = os.path.join(save_path, f'blockworld_results_{i}.txt')
        with open(save_file_path, 'w') as f:
            if init_state is not None:
                parser = NLParser()
                type_tags = {}
                for pred in init_state:
                    type_tags.update(pred[1])
                init_formula = parser.parse_formula(init_state, term_type_dict=type_tags)
                init_formula = DisjunctiveFormula(init_formula).distribute_and_over_or()
                print("Initial State:")
                print(init_formula)
                print("Actions:", [])
                print("Substitution:", {})
                print("--------------------")
                f.write("Initial State:\n")
                f.write(str(init_formula) + '\n')
                f.write(str([]) + '\n')
                f.write(str({}) + '\n')
                f.write("--------------------\n")
                f.write("Regressed goals:\n")
            else:
                f.write("Regressed goals:\n")

            for plan in regressed_plans:
                f.write("Subgoal: \n")
                f.write(str(plan[0]) + '\n')
                reversed_plan = plan[1]
                reversed_plan.reverse()
                actions = [p.substitute(plan[2]) for p in reversed_plan]
                f.write(str(actions) + '\n')
                f.write(str(plan[2]) + '\n')
                f.write("--------------------\n")
