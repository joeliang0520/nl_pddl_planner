import pddl
import json
import os
from dotenv import load_dotenv

import pdb

from pddl_planner.planner.nl_planner import NLFOLRegressionPlanner

from plan_to_subgoals import PlanSubgoalConverter

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
    with open('./blockworld_domain.json', 'r') as f:
        domain = json.load(f)

    # load the goal blocks from the file    
    with open('./instance-10.json', 'r') as f:
        block_dict = json.load(f)

    test_goal = [block_dict["goal"]]
    test_init = block_dict["initial_state"]

    # pdb.set_trace()

    # create a directory to store the results
    current_dir = os.path.dirname(os.path.abspath(__file__))
    save_path = os.path.join(current_dir, f'alfworldtext_results')
    os.makedirs(save_path, exist_ok=True)

    converter = PlanSubgoalConverter()

    # initialize the planner
    for i, block in enumerate(test_goal):
        print(i, block )
        print(f'Problem {block} =========================================')
        print("Initial state:")
        print(test_init)
        planner = NLFOLRegressionPlanner(domain.copy(), test_goal[i].copy(), max_depth=5)
        regressed_plans = planner.regress_plan()

        converted = converter.convert_regressed_plans(regressed_plans)
        pddlized = converter.converted_items_to_pddl(converted)

        for item in converted:
            print(item)
        for item in pddlized:
            print(item)

        pass

        # create a empty text file to store the results
        save_file_path = os.path.join(save_path, f'alfworldtext_results_{i}.txt')
        with open(save_file_path, 'w') as f:
            # print the regressed plans
            print("Regressed goals:")
            f.write("Regressed goals:\n")
            for plan in regressed_plans:
                print("Subgoal: ")
                f.write("Subgoal: \n")
                print(plan[0])
                f.write(str(plan[0]) + '\n')
                reversed_plan = plan[1]
                reversed_plan.reverse()
                print("Action: ", reversed_plan)
                f.write(str(reversed_plan) + '\n')
                print("Substitution: ", plan[2])
                f.write(str(plan[2]) + '\n')
                print("--------------------")
                f.write("--------------------\n")
        # break
    #
