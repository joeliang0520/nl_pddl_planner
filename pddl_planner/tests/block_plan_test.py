import pddl
from pddl_planner.planner.planner import FOLRegressionPlanner


if __name__ == '__main__':
    # regression planner
    pddl_domain = pddl.parse_domain('files/blocks.pddl')
    pddl_problem = pddl.parse_problem('files/blocks_problem1.pddl')

    planner = FOLRegressionPlanner(pddl_domain, pddl_problem, max_depth=3)
    regressed_plans = planner.regress_plan()
    print("Regressed goals:")
    for plan in regressed_plans:
        print("Subgoal: ")
        print(plan[0])
        reversed_plan = plan[1]
        reversed_plan.reverse()
        print("Action: ", reversed_plan)
        print("Substitution: ", plan[2])
        print("--------------------")