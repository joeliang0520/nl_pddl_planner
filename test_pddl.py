import pddl
from pddl_planner.planner.planner import FOLRegressionPlanner
from pprint import pprint


def check_subgoal_hh(subgoal):
    subgoal_satisfied = True
    subgoal_names = [str(p.name) for p in subgoal.collect_preds()]
    subgoal_count = subgoal_names.count('k-at-location')
    if subgoal_count > 1:
        subgoal_satisfied = False
    return subgoal_satisfied

def check_actions_hh(actions):
    actions_satisfied = True

    if actions!= [] and actions[0].name != 'goto-location':
        actions_satisfied = False
    
    for i in range(len(actions)-1):
        current_action = actions[i]
        next_action = actions[i+1]

        current_location = None
        next_location = None

        if current_action.name == 'goto-location':
            current_location = current_action.parameters[0]
            next_location = next_action.parameters[0]
        else:
            current_location = next_location
            action_location = current_action.parameters[-1]
            if action_location != current_location:
                actions_satisfied = False
            
    return actions_satisfied

if __name__ == '__main__':
    # regression planner
    pddl_domain = pddl.parse_domain('files/pddl/hh/hh_domain.pddl')
    pddl_problem = pddl.parse_problem('files/pddl/hh/hh_p1.pddl')

    planner = FOLRegressionPlanner(pddl_domain, pddl_problem, max_depth=6)
    regressed_plans = planner.regress_plan()
    print("Regressed goals:")
    num_subgoals = 0 
                

    for plan in regressed_plans:
        actions = plan[1][0]
        subgoals = plan[1][1]
        current_substitutions = plan[2]
        current_subgoal = plan[0]
        # plan_names = [str(p.name) for p in actions]
        # subgoal_names = [str(p.name) for p in current_subgoal.collect_preds()]
        # subgoal_count = subgoal_names.count('k-at-location')
        if check_subgoal_hh(current_subgoal):
            print("Subgoal: ", num_subgoals)
            print("Current subgoal: ", str(current_subgoal))
            for i in range(len(actions)):
                print(subgoals[i])
                print('\t', actions[i])

                # print(subgoals[i])
                
            pprint(current_substitutions)
            print("--------------------")
            num_subgoals += 1