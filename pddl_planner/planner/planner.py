import copy
import heapq
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Union
from pddl_planner.pddl_core.domain import Domain
from pddl_planner.pddl_core.instance import Instance
from pddl_planner.logic.operation import Operations
from pddl_planner.logic.formula import Substitution, Formula, Predicate, DisjunctiveFormula, ConjunctiveFormula, Term, Equality, FalseFormula
from pddl_planner.pddl_core.action import Action

class Planner():
    def __init__(self, pddl_domain: str, pddl_problem: str) -> None:
        """
        Initializes a Planner instance.

        Args:
            pddl_domain (str): The domain PDDL file path.
            pddl_problem (str): The problem PDDL file path.

        Returns:
            None
        """
        self._domain = Domain(pddl_domain)
        self._instance = Instance(pddl_problem, self._domain)
        self._operations = Operations()


    def plan(self):
        """
        Abstract method to generate a plan.

        Returns:
            None
        """
        pass

    
class FOLRegressionPlanner(Planner):
    def __init__(self, pddl_domain: str, pddl_problem: str, max_depth: int = 10) -> None:
        """
        Initialize a FOL-RegressionPlanner as proposed by us. This planner is based on First-Order Logic (FOL) and uses SSA from Situation Calculus.

        Args:
            pddl_domain (str): The domain PDDL file path.
            pddl_problem (str): The problem PDDL file path.
            max_depth (int, optional): The maximum depth of the plan tree. Defaults to 10.
            simplify_mode (tuple, optional): Simplification mode (DNF_subsumption, Equality_simplification, Typing_simplification). Defaults to (True, True, True).
        """
        super().__init__(pddl_domain, pddl_problem)
        self._max_depth = max_depth
        self._ssa = self.create_SSA()

    @dataclass
    class SSA_Node:
        """
        A node in representing the SSA.

        Attributes:
            predicate_name (str): The name of the predicate.
            predicate_params (List[Term]): The parameters of the predicate.
            action_name (str): The name of the action.
            action_params (List[Term]): The parameters of the action.
            ssa (Union[Predicate, DisjunctiveFormula]): The SSA formula.
        """
        predicate_name: str
        predicate_params: List[Term]
        action_name: str
        action_params: List[Term]
        substitutions: List[Substitution]
        ssa: Union[Predicate, DisjunctiveFormula]

    class PlanNode():
        def __init__(self, action: Action, sub_goal: Formula, parent: Optional["RegressionPlanner.PlanNode"] = None, depth: int = 0, substitution: Substitution = Substitution()) -> None:
            """
            Initializes a PlanNode. PlanNode is used to represent the planning tree.

            Args:
                planner (RegressionPlanner): The planner that this node belongs to.
                action (Action): The action leading to this node.
                sub_goal (Formula): The sub-goal for this node.
                parent (Optional[PlanNode], optional): The parent node. Defaults to None.
                depth (int, optional): The depth in the plan tree. Defaults to 0.

            Returns:
                None
            """
            self.action = action
            self.sub_goal = copy.deepcopy(sub_goal)
            self.parent = parent
            self.children: List["FOLRegressionPlanner.PlanNode"] = []
            self.depth = depth
            self.substitution = substitution
        
        def add_child(self, child_node: "FOLRegressionPlanner.PlanNode") -> None:
            """
            Adds a child node.

            Args:
                child_node (PlanNode): The child node to add.

            Returns:
                None
            """
            self.children.append(child_node)

    def extract_plan(self, node: "FOLRegressionPlanner.PlanNode") -> List[Action]:
        """
        Extract the plan from the plan tree.

        Args:
            node (PlanNode): The node to extract the plan from.

        Returns:
            List[Action]: The list of actions in the plan.
        """
        actions: List[Action] = []
        subgoals: List[Formula] = []
        while node.parent is not None:
            substitution = node.substitution
            action = node.action.substitute(substitution)
            actions.append(action)
            subgoals.append(node.sub_goal)
            node = node.parent
        plan = (actions, subgoals)
        return plan


    def create_SSA(self) -> Dict[str, Dict[str, SSA_Node]]:
        """
        Construct SSA from the domain's action schema for each predicate.
        
        This function returns a dictionary mapping each predicate (from domain.predicates)
        to a dictionary that maps an action name to a tuple. The tuple contains:
            1. The standardized action's parameters (List[Term]).
            2. The SSA value, which is either:
                - A DisjunctiveFormula computed from the positive or negative effect, or
                - The predicate itself when the effect does not include the predicate.
        
        Returns:
            Dict[Predicate, Dict[str, Tuple[List[Term], Union[Predicate, DisjunctiveFormula]]]]:
                The constructed SSA mapping.
        """

        def get_positive_effect_axiom(action: Action, predicate: Predicate) -> Tuple[Optional[DisjunctiveFormula], Substitution]:
            axioms = []
            substitution = Substitution()
            for clause in action.effects.clauses:
                if isinstance(clause, Predicate) and clause.name == predicate.name and not clause.is_neg:
                    sub = self._operations.unify(clause, predicate, Substitution())
                    if sub is not None:
                        for var, term in sub.items():
                            axioms.append(Equality(var, term, is_neq=False))
                        axioms.append(action.preconditions)
                        substitution.update(sub)
            if axioms:
                return (ConjunctiveFormula(*axioms, term_type_dict=action.preconditions.term_type_dict), substitution)
            return (None, Substitution())
        
        def get_negative_effect_axiom(action: Action, predicate: Predicate) -> Tuple[Optional[ConjunctiveFormula], Substitution]:
            axioms = []
            substitution = Substitution()
            for clause in action.effects.clauses:
                if isinstance(clause, Predicate) and clause.name == predicate.name and clause.is_neg:
                    sub = self._operations.unify(clause, predicate.get_negation(), Substitution())
                    if sub is not None:
                        for var, term in sub.items():
                            axioms.append(Equality(var, term, is_neq=False))
                        axioms.append(action.preconditions)
                        substitution.update(sub)
            if axioms:
                negative_effect_axiom = ConjunctiveFormula(*axioms)
                return (negative_effect_axiom, substitution)
            return (None, Substitution())

        all_ssa: Dict[str, Dict[str, FOLRegressionPlanner.SSA_Node]] = {}
        for pred in self._domain.predicates:
            pred_ssa: Dict[str, FOLRegressionPlanner.SSA_Node] = {}
            for action in self._domain.actions:
                standardized_action = action.standardize(self._operations)
                (positive_effect_axiom, substitution) = get_positive_effect_axiom(standardized_action, pred)
                (negative_effect_axiom, _) = get_negative_effect_axiom(standardized_action, pred)
                if positive_effect_axiom is not None and negative_effect_axiom is not None:
                    # Both positive and negative effects exist, ssa takes the form
                    # SSA = (positive_effect) ∨ (pred ∧ ¬negative_effect)
                    ssa = DisjunctiveFormula(positive_effect_axiom, ConjunctiveFormula(pred, negative_effect_axiom.get_negation())).simplify().distribute_and_over_or()

                elif positive_effect_axiom is not None:
                    # Only positive effect exists
                    # SSA = positive_effect ∨ pred
                    ssa = DisjunctiveFormula(positive_effect_axiom, pred).simplify().distribute_and_over_or()
                
                elif negative_effect_axiom is not None:
                    # Only negative effect exists
                    # SSA = pred ∧ ¬negative_effect
                    ssa = ConjunctiveFormula(negative_effect_axiom.get_negation(), pred).simplify().distribute_and_over_or()
                else:
                    # No effect exists
                    # SSA = pred
                    ssa = DisjunctiveFormula(pred).distribute_and_over_or()

                pred_ssa[standardized_action.name] = FOLRegressionPlanner.SSA_Node(
                        pred.name,
                        pred.terms,
                        standardized_action.name,
                        standardized_action.parameters,
                        substitution,
                        ssa)
            all_ssa[pred.name] = pred_ssa
        return all_ssa
    
    def regress_pred(self, predicate: Predicate, action: Action) -> DisjunctiveFormula:
        """
        Regress a predicate through an action via the stored SSA substitution.

        This function retrieves the corresponding SSA_Node for the given predicate and action.
        It then builds a substitution mapping that maps:
        - Each stored predicate parameter to the corresponding variable in the provided predicate.
        - Each stored action parameter to the corresponding variable in the provided action.
        Finally, it applies this substitution to the stored SSA formula and returns the resulting
        DisjunctiveFormula.

        Args:
            predicate (Predicate): The predicate whose variables are to be substituted.
            action (Action): The action used for regression whose parameters are mapped.

        Returns:
            DisjunctiveFormula: The regressed formula with variables substituted according to the SSA_Node.
        """
        ssa_node = self._ssa[predicate.name][action.name]
        # Build a substitution:
        # Map the stored predicate parameters to the input predicate's terms.
        substitution = Substitution()
        for stored_pred_var, input_pred_var in zip(ssa_node.predicate_params, predicate.terms):
            substitution[stored_pred_var] = input_pred_var
        # Map the stored action parameters to the input action's parameters.
        for stored_act_var, input_act_var in zip(ssa_node.action_params, action.parameters):
            substitution[stored_act_var] = input_act_var

        returned_ssa = copy.deepcopy(ssa_node.ssa)
        
        # if predicate.term_type_dict is not None and ssa_node.ssa.term_type_dict is not None:
        #     returned_ssa.term_type_dict.update(predicate.term_type_dict)
        # Substitute over the stored SSA formula

        return returned_ssa.substitute(substitution)
         

    def regress(self, goal: DisjunctiveFormula, action: Action) -> DisjunctiveFormula:
        """
        Regress the goal formula through the given action.

        This function takes a goal formula in Disjunctive Normal Form (DNF) and regresses each
        conjunctive component of the formula with respect to the given action. For each conjunct,
        it iterates over the clauses and uses 'regress_pred' on each predicate clause, retaining other
        clauses unchanged. After regressing all conjuncts, it recombines them into a new DNF formula
        and returns that as the regressed goal.

        Args:
            goal (DisjunctiveFormula): The goal formula in DNF to be regressed.
            action (Action): The action used for regression.

        Returns:
            DisjunctiveFormula: The regressed goal formula in Disjunctive Normal Form.
        """
        if not isinstance(goal, DisjunctiveFormula):
            raise ValueError(f"Goal must be a DisjunctiveFormula, but got {type(goal)}")
        regressed_disjunct_list = []
        for conjunct in goal.clauses:
            if not isinstance(conjunct, ConjunctiveFormula):
                raise ValueError(f"Each conjunct must be a ConjunctiveFormula, but got {type(conjunct)}")
            
            regressed_conjunct_list = []
            for clause in conjunct.clauses:
                if isinstance(clause, Predicate):
                    # Regress the predicate clause using regress_pred
                    regressed_clause = self.regress_pred(clause, action)
                else:
                    regressed_clause = clause
                regressed_conjunct_list.append(regressed_clause)
            # Combine the regressed clauses and convert to DNF
            regressed_disjunct_list.append(ConjunctiveFormula(*regressed_conjunct_list).distribute_and_over_or())
        
        # Return a flattened regressed goal  in DNF
        return DisjunctiveFormula(*regressed_disjunct_list).distribute_and_over_or()

    def regress_plan(self, simplify_equality: bool = True, simplify_contradiction: bool = True, simplify_typing: bool = True, simplify_dnf: bool = True, dup_detection: bool = True) -> List[Tuple[Formula, List[Action]]]:
        """
        Generate a regressed plan by iteratively regressing the goal through applicable actions.

        This method starts with the instance goal (converted to Disjunctive Normal Form if needed)
        and then iteratively regresses it using the available actions up to a maximum depth.
        At each regression step, it creates new plan tree nodes and tracks visited subgoals to avoid duplication.
        
        Returns:
            List[Tuple[Formula, List[Action]]]: A list of tuples where each tuple contains:
                - A subgoal (Formula) that represents a regressed goal state.
                - A list of actions (List[Action]) that form the plan to achieve that subgoal.
        """
        plan = []
        goal = self._instance.goal.distribute_and_over_or()


        if not isinstance(goal, DisjunctiveFormula):
            raise ValueError(f"Goal must be a DisjunctiveFormula, but got {type(goal)}")
        frontier = [FOLRegressionPlanner.PlanNode(None, goal)]
        plan.append((frontier[0].sub_goal, ([],[]), Substitution()))

        visited_goal = []

        for clause in goal.clauses:
            if isinstance(clause, ConjunctiveFormula):
                visited_goal.append(clause)

        while frontier:
            current_node: FOLRegressionPlanner.PlanNode = frontier.pop(0)
            current_goal: Formula = current_node.sub_goal
            if current_node.depth >= self._max_depth:
                # exit if max depth is reached
                continue
                
            for action in self._domain.actions:
                standardized_action = action.standardize(self._operations)
                regressed_goal = self.regress(current_goal, standardized_action).simplify() if simplify_contradiction else self.regress(current_goal, standardized_action)
                regressed_conjuncts = [c for c in regressed_goal.clauses if isinstance(c, ConjunctiveFormula)]

                for conjunct in regressed_conjuncts:
                    
                    clause_simplified, clause_sub = conjunct.simplify_equality(conjunct)

                    action = standardized_action.substitute(clause_sub)

                    # check for imply conflicts
                    if clause_simplified.check_implies(current_goal):
                        continue

                    # check for domain axioms conflicts
                    if self._operations.has_conflicting_domain_axioms(clause_simplified):
                        continue

                    # check for onehot conflicts
                    if self._operations.has_conflicting_onehot(clause_simplified):
                        continue

                    # simplify by domain axioms
                    subgoal_prev = current_node.sub_goal
                    subgoal_curr = clause_simplified
                    axiomed_caluse, axiom_sub = self._operations.simplify_by_domain_axiom(subgoal_curr, subgoal_prev)
                    clause_simplified = axiomed_caluse
                    if axiom_sub is not None:
                        action = action.substitute(axiom_sub)

                    # check for action conflicts
                    action_prev = current_node.action
                    action_curr = standardized_action
                    if self._operations.has_repeating_actions(action_prev, action_curr):
                        continue

                    new_subgoal = DisjunctiveFormula(clause_simplified)

                    child_node = FOLRegressionPlanner.PlanNode(action, new_subgoal, current_node, current_node.depth + 1, clause_sub)
                    if not isinstance(child_node.sub_goal, FalseFormula):
                        for conjunct in child_node.sub_goal.clauses:
                            if isinstance(conjunct, ConjunctiveFormula):
                                visited_goal.append(conjunct)
                        frontier.append(child_node)
                        plan.append((child_node.sub_goal, self.extract_plan(child_node), child_node.substitution))
        return plan

