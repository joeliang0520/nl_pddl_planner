from pddl_planner.planner.planner import RegressionPlanner
import pddl

if __name__ == '__main__':
    # test for ghallab's style regression planner
    pddl_domain = pddl.parse_domain('files/domain.pddl')

    pddl_problem = pddl.parse_problem('files/problem.pddl')

    planner = RegressionPlanner(pddl_domain, pddl_problem)
    plans = planner.plan_tree()
    for plan, actions in plans:
        print("sub_goal: ", plan)
        for action in actions:
            print(action)