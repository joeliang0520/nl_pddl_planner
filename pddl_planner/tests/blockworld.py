import time
import pddl
import json
import os
from dotenv import load_dotenv

from pddl_planner.planner.nl_planner import NLFOLRegressionPlanner

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

    # load the goal blocks from the file    
    with open('files/blockworld_goal.json', 'r') as f:
        all_blocks = json.load(f)

    #save with indent 4
    # with open('files/NL_actions_new.json', 'w') as f:
    #     json.dump(domain, f, indent=4)
    # with open('files/NL_goals_new.json', 'w') as f:
    #     json.dump(all_blocks, f, indent=4)

    # create a directory to store the results
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # initialize the planner
    max_depth = 10
    save_path = os.path.join(current_dir, f'blockworld_results_depth{max_depth}')
    os.makedirs(save_path, exist_ok=True)
    for i, block in enumerate(all_blocks[13:14]):
        print(f'Problem {block} =========================================')
        planner = NLFOLRegressionPlanner(domain.copy(), block.copy(), max_depth=max_depth)
        #track time
        start_time = time.time()
        regressed_plans = planner.regress_plan()
        end_time = time.time()
        print(f'Time taken: {end_time - start_time} seconds')
        # create a empty text file to store the results
        save_file_path = os.path.join(save_path, f'blockworld_results_{i}.txt')
        with open(save_file_path, 'w') as f:
            # print the regressed plans
            #print("Regressed goals:")
            f.write("Regressed goals:\n")
            for plan in regressed_plans:
                #print("Subgoal: ")
                f.write("Subgoal: \n")
                
                #print(plan[0])
                f.write(str(plan[0]) + '\n')
                reversed_plan = plan[1]
                reversed_plan.reverse()
                actions = [p.substitute(plan[2]) for p in reversed_plan]
                #print("Action: ", actions)
                f.write(str(actions) + '\n')
                #print("Substitution: ", plan[2])
                f.write(str(plan[2]) + '\n')
                #print("--------------------")
                f.write("--------------------\n")
