import pddl
from pddl_planner.planner.planner import FOLRegressionPlanner
from pprint import pprint


if __name__ == '__main__':
    # regression planner
    pddl_domain = pddl.parse_domain('files/pddl/hh/hh_domain.pddl')
    pddl_problem = pddl.parse_problem('files/pddl/hh/hh_p1.pddl')

    planner = FOLRegressionPlanner(pddl_domain, pddl_problem, max_depth=8)
    regressed_plans = planner.regress_plan()
    print("Regressed goals:")
    subgoal_count = 0
                
    for plan in regressed_plans:
        plan_names = [str(p.name) for p in plan[1]]
        print("Subgoal: ", subgoal_count)
        pprint(plan[0])
        reversed_plan = plan[1]
        reversed_plan.reverse()
        subst = plan[2]
        reversed_plan = [p.substitute(subst) for p in reversed_plan]
        pprint(reversed_plan)
        pprint(plan[2])
        print("--------------------")
        subgoal_count += 1