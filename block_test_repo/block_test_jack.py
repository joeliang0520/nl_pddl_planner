import pddl
import json
import os
import re
from dotenv import load_dotenv

import pdb

from pddl_planner.planner.nl_planner_sub import NLFOLRegressionPlanner

from plan_to_subgoals import PlanSubgoalConverter

from pddl_to_json import PDDLToJSON

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

    # Convert PDDL instance to JSON using conv and load it
    conv = PDDLToJSON()
    out_problem_json_path = conv.convert_problem_file(
        "block_world_test/planbench/instance-2.pddl", out_dir="out/"
    )
    with open(out_problem_json_path, 'r') as f:
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
        planner = NLFOLRegressionPlanner(domain.copy(), test_goal[i].copy(), max_depth=6, nl_init=None)
        regressed_plans = planner.regress_plan(simplify_equality=True, save_file_path='testout.txt')

        print("Regressed plans:")
        for plan in regressed_plans:
            print("Subgoal: ", plan[0])
            print("Actions: ", plan[1])
            print("Substitution: ", plan[2])
            print("----------------")

        # raise ValueError

        converted = converter.convert_regressed_plans(regressed_plans)
        pddlized = converter.converted_items_to_pddl(converted)

        # Prepare output JSON with initial state, overall goal predicates, and pddlized plans
        # Flatten initial state dict to a list of predicate strings
        init_predicates = []
        if isinstance(test_init, dict):
            for preds in test_init.values():
                if isinstance(preds, list):
                    init_predicates.extend(preds)
        else:
            # Fallback: if already a list
            init_predicates = list(test_init)

        # Convert overall NL goal to PDDL predicates via converter
        goal_predicates = converter.goal_entries_to_pddl(block)

        plans_out = []
        for item in pddlized:
            plans_out.append({
                'subgoal_raw': item.get('subgoal_raw', {}),  # disjuncts with original clause strings
                'action_raw': item.get('action_raw', []),
                'substitution': item.get('substitution', {}),
                'subgoal_predicates': item.get('subgoal_predicates', []),
                # Save actions as PDDL operator calls (e.g., unstack(b, c))
                'action': item.get('actions_pddl', []),


            })

        out_payload = {
            'initial_state': init_predicates,
            'goal_predicates': goal_predicates,
            'plans': plans_out,
        }

        out_path = os.path.join(current_dir, 'example_out_pddl_regression2.json')
        with open(out_path, 'w') as f:
            json.dump(out_payload, f, indent=2)
        print(f"Saved PDDL regression output -> {out_path}")

        # # create a empty text file to store the results
        # save_file_path = os.path.join(save_path, f'alfworldtext_results_{i}.txt')
        # with open(save_file_path, 'w') as f:
        #     # print the regressed plans
        #     print("Regressed goals:")
        #     f.write("Regressed goals:\n")
        #     for plan in regressed_plans:
        #         print("Subgoal: ")
        #         f.write("Subgoal: \n")
        #         print(plan[0])
        #         f.write(str(plan[0]) + '\n')
        #         reversed_plan = plan[1]
        #         reversed_plan.reverse()
        #         print("Action: ", reversed_plan)
        #         f.write(str(reversed_plan) + '\n')
        #         print("Substitution: ", plan[2])
        #         f.write(str(plan[2]) + '\n')
        #         print("--------------------")
        #         f.write("--------------------\n")
        # # break
    #
