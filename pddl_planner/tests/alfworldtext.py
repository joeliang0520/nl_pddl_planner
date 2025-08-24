import pddl
import ast
import json

from pddl_planner.planner.nl_planner import NLFOLRegressionPlanner

# load the goal blocks from the file
def load_goal_blocks(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Split by two or more newlines (separates blocks)
    blocks_text = [b.strip() for b in content.split("\n\n") if b.strip()]

    blocks = []
    for block in blocks_text:
        try:
            blocks.append(ast.literal_eval(block))
        except Exception as e:
            print("Skipping block due to parse error:", e)
    return blocks

# load the domain from the file
with open('files/alfworldtext_domain.json', 'r') as f:
    domain = json.load(f)

# load the goal blocks from the file    
all_blocks = load_goal_blocks("files/NL_goals.txt")

# initialize the planner
planner = NLFOLRegressionPlanner(domain.copy(), all_blocks[0].copy(), max_depth=10)
# #regress the goal blocks
print('before regress =========================================')
regressed_plans = planner.regress_plan()

# print the regressed plans
print("Regressed goals:")
for plan in regressed_plans:
    print("Subgoal: ")
    print(plan[0])
    reversed_plan = plan[1]
    reversed_plan.reverse()
    print("Action: ", reversed_plan)
    print("Substitution: ", plan[2])
    print("--------------------")