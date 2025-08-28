import pddl
import json
import os

from pddl_planner.planner.nl_planner import NLFOLRegressionPlanner

# load the domain from the file
with open('files/alfworldtext_domain.json', 'r') as f:
    domain = json.load(f)

# load the goal blocks from the file    
with open('files/alfworldtext_goal.json', 'r') as f:
    all_blocks = json.load(f)

current_dir = os.path.dirname(os.path.abspath(__file__))
save_path = os.path.join(current_dir, f'results')
os.makedirs(save_path, exist_ok=True)

# create a empty text file to store the results
# initialize the planner
for i, block in enumerate([all_blocks[2]]):
    print(f'Problem {block} =========================================')
    planner = NLFOLRegressionPlanner(domain.copy(), block.copy(), max_depth=10)
    regressed_plans = planner.regress_plan()
    # create a empty text file to store the results
    # get current directory
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
    #
