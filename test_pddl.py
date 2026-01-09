import pddl
from pddl_planner.planner.planner import FOLRegressionPlanner
from pprint import pprint


if __name__ == '__main__':
    # regression planner
    pddl_domain = pddl.parse_domain('files/pddl/hh/hh_domain.pddl')
    pddl_problem = pddl.parse_problem('files/pddl/hh/hh_p1.pddl')

    planner = FOLRegressionPlanner(pddl_domain, pddl_problem, max_depth=4)
    regressed_plans = planner.regress_plan()
    print("Regressed goals:")
    subgoal_count = 0
    # for plan in regressed_plans:
    #     if len(plan[1]) > 2:
    #         goto_count = 0
    #         repeat_goto = False
    #         last_action_is_goto = False
    #         for p in plan[1]:
    #             if 'goto' in p.name:
    #                 goto_count += 1
    #                 if last_action_is_goto:
    #                     repeat_goto = True
    #                 last_action_is_goto = True
    #             else:
    #                 last_action_is_goto = False
                    
    #         if goto_count > 0 and not repeat_goto:
    #             if 'answer' in str(plan[0]):
    #                 print("Subgoal: ", subgoal_count)
    #                 pprint(plan[0])
    #                 reversed_plan = plan[1]
    #                 reversed_plan.reverse()
    #                 pprint(reversed_plan)
    #                 pprint(plan[2])
    #                 print("--------------------")
    #                 subgoal_count += 1
                
    for plan in regressed_plans:
        # if 'has-' in str(plan[0]):
        plan_names = [str(p.name) for p in plan[1]]
        # goto_count = len([str(p) for p in plan_names if 'goto' in plan_names])
        # ask_count = len([str(p) for p in plan_names if 'ask' in plan_names])
        # open_count = len([str(p) for p in plan_names if 'open' in plan_names])

        plan_list = ['goto-location', 'ask-priest-heaven', 'goto-location', 'open-door-heaven']
        plan_list.reverse()
        if plan_names == plan_list and 'answer' in str(plan[0]):
            print("Subgoal: ", subgoal_count)
            pprint(plan[0])
            reversed_plan = plan[1]
            reversed_plan.reverse()
            pprint(reversed_plan)
            print("--------------------")
            subgoal_count += 1