import copy
import heapq
import json
import os
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Union
from pddl_planner.pddl_core.nl_domain import NLDomain
from pddl_planner.pddl_core.nl_instance import NLInstance
from pddl_planner.logic.operation import Operations
from pddl_planner.logic.nl_formula import NLPredicate
from pddl_planner.logic.formula import Substitution, Formula, Predicate, DisjunctiveFormula, ConjunctiveFormula, Term, Equality, FalseFormula
from pddl_planner.pddl_core.action import Action         
from pddl_planner.llm.llm import LLM
    
class NLPlanner():
    def __init__(self, nl_domain: str, nl_problem: str) -> None:
        """
        Initializes a Planner instance.

        Args:
            nl_domain (str): The domain PDDL file path.
            nl_problem (str): The problem PDDL file path.

        Returns:
            None
        """
        self._domain = NLDomain(nl_domain)
        self._instance = NLInstance(nl_problem, self._domain)
        self._operations = Operations()

    def plan(self):
        """
        Abstract method to generate a plan.

        Returns:
            None
        """
        pass

class NLFOLRegressionPlanner(NLPlanner):
    def __init__(self, nl_domain: str, nl_problem: str, max_depth: int = 16, 
    llm_model: str = "gpt-4o-mini", llm_api_key: str = os.getenv("OPENAI_API_KEY"), verbose: bool = True) -> None:
        """
        Initialize a FOL-RegressionPlanner based on First-Order Logic (FOL) and uses SSA from Situation Calculus.

        Args:
            nl_domain (str): The NL domain file path.
            nl_problem (str): The NL problem file path.
            max_depth (int, optional): The maximum depth of the plan tree. Defaults to 10.
            llm_model (str, optional): The model name of the LLM. Defaults to "gpt-4o-mini".
            llm_api_key (str, optional): The API key of the LLM. Defaults to os.getenv("OPENAI_API_KEY").
        """
        super().__init__(nl_domain, nl_problem)
        self._max_depth = max_depth
        self._ssa = self.create_SSA()
        self._verbose = verbose
        self._llm = LLM(model_name=llm_model, api_key=llm_api_key, verbose=verbose)
        
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
        def __init__(self, action: Action, sub_goal: Formula, parent: Optional["NLFOLRegressionPlanner.PlanNode"] = None, depth: int = 0, substitution: Substitution = Substitution()) -> None:
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
            self.children: List["NLFOLRegressionPlanner.PlanNode"] = []
            self.depth = depth
            self.substitution = substitution
        
        def add_child(self, child_node: "NLFOLRegressionPlanner.PlanNode") -> None:
            """
            Adds a child node.

            Args:
                child_node (PlanNode): The child node to add.

            Returns:
                None
            """
            self.children.append(child_node)

    def extract_plan(self, node: "NLFOLRegressionPlanner.PlanNode") -> List[Action]:
        """
        Extract the plan from the plan tree.

        Args:
            node (PlanNode): The node to extract the plan from.

        Returns:
            List[Action]: The list of actions in the plan.
        """
        plan: List[Action] = []
        while node.parent is not None:
            plan.append(node.action)
            node = node.parent
        plan.reverse()
        return plan


    def create_SSA(self, predicates: List[Predicate] = None) -> Dict[str, Dict[str, SSA_Node]]:
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

        all_ssa: Dict[str, Dict[str, NLFOLRegressionPlanner.SSA_Node]] = {}
        if predicates is None:
            predicates = self._domain.predicates
        for pred in predicates:
            print(f"Processing predicate: {pred.name}") 
            pred_ssa: Dict[str, NLFOLRegressionPlanner.SSA_Node] = {}
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
                    #print(f'returned_ssa: {str(negative_effect_axiom.get_negation())} for action "{action.name}" and predicate "{pred.name}"')
                else:
                    # No effect exists
                    ssa = DisjunctiveFormula(pred).distribute_and_over_or()

                pred_ssa[standardized_action.name] = NLFOLRegressionPlanner.SSA_Node(
                        pred.name,
                        pred.terms,
                        standardized_action.name,
                        standardized_action.parameters,
                        substitution,
                        ssa)
            all_ssa[pred.name] = pred_ssa
        return all_ssa

    def create_SSA_as_itself(self, predicate: Predicate) -> Dict[str, SSA_Node]:
        """
        Create SSA as itself.
        """
        pred_ssa: Dict[str, NLFOLRegressionPlanner.SSA_Node] = {}
        for action in self._domain.actions:
            standardized_action = action.standardize(self._operations)
            ssa = DisjunctiveFormula(predicate).distribute_and_over_or()
            pred_ssa[standardized_action.name] = NLFOLRegressionPlanner.SSA_Node(
                predicate.name,
                predicate.terms,
                standardized_action.name, 
                standardized_action.parameters, 
                Substitution(), ssa)
        return pred_ssa
                
    
    def regress_pred(self, predicate: NLPredicate, action: Action) -> DisjunctiveFormula:
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
        # check if the predicate is in domain predicates
        if predicate.name in self._ssa:
            ssa_node = self._ssa[predicate.name][action.name]
        else:
            # check if the predicate can be entailed as a domain predicate
            print(f'Failing to find "{predicate.name}" in domain predicates, attempting to entail it to a domain predicate') if self._verbose else None

            background_predicates = (copy.deepcopy(action), [clause for clause in self._instance.goal.clauses if isinstance(clause, NLPredicate)])
            entailed_pred = self._llm.entailment(predicate, self._domain.predicates, background_predicates=background_predicates)

            if entailed_pred is not None:
                if isinstance(entailed_pred.entailed, list):
                    ssa_node = []
                    for pred in entailed_pred.entailed:
                        if pred.name in self._ssa:
                            ssa_node.append(self._ssa[pred.name][action.name])
                    #ssa_node = DisjunctiveFormula(*ssa_node_lst).distribute_and_over_or() if not predicate.is_neg else ConjunctiveFormula(*ssa_node_lst).distribute_and_over_or()
                else:
                    ssa_node = self._ssa[entailed_pred.entailed.name][action.name]
                # update the predicate names and string representation as the entailed predicate
                #predicate = entailed_pred
            else:
                # create a new ssa node with postive and negative effects as none
                print(f'Failing to entail "{predicate.name}" in domain predicates, creating a new ssa node with postive and negative effects as none') if self._verbose else None
                self._ssa[predicate.name] = self.create_SSA_as_itself(predicate)
                ssa_node = self._ssa[predicate.name][action.name]

        # Build a substitution:
        # Map the stored predicate parameters to the input predicate's terms.
        if not isinstance(ssa_node, List):
            substitution = Substitution()
            # Honor recorded entailment permutation (if any) between predicate vars
            recorded = None
            try:
                recorded = predicate.get_entailed_substitution(ssa_node.predicate_name)
            except Exception:
                recorded = None
            inv_name_map = {}
            if recorded is not None:
                for k, v in recorded.items():
                    try:
                        inv_name_map[v.name] = k.name
                    except Exception:
                        pass
            target_name_to_term = {getattr(t, 'name', str(t)): t for t in predicate.terms}
            for idx, stored_pred_var in enumerate(ssa_node.predicate_params):
                mapped_target_name = inv_name_map.get(getattr(stored_pred_var, 'name', str(stored_pred_var)))
                if mapped_target_name is not None and mapped_target_name in target_name_to_term:
                    substitution[stored_pred_var] = target_name_to_term[mapped_target_name]
                else:
                    if idx < len(predicate.terms):
                        substitution[stored_pred_var] = predicate.terms[idx]
            # Map the stored action parameters to the input action's parameters.
            for stored_act_var, input_act_var in zip(ssa_node.action_params, action.parameters):
                substitution[stored_act_var] = input_act_var
        
            returned_ssa = copy.deepcopy(ssa_node.ssa)
            
            # if predicate.term_type_dict is not None and ssa_node.ssa.term_type_dict is not None:
            #     returned_ssa.term_type_dict.update(predicate.term_type_dict)
            # Substitute over the stored SSA formula
            # print(f'ssa_node: {ssa_node.predicate_params} action: {ssa_node.action_params} predicate: {predicate.terms}')
            # print(f'substitution: {substitution}')
            # print(f'returned_ssa: {ssa_node.ssa.clauses} for action "{action.name}" and predicate "{predicate.name}"')
            return returned_ssa.substitute(substitution)
        else:
            # ssa_node is a list of SSA_Nodes (entailed to multiple domain predicates)
            print('[Multiple Entailment] Found multiple domain predicates that entail "{predicate.name}"') if self._verbose else None
            substituted_ssas: List[Formula] = []
            for node in ssa_node:
                node_sub = Substitution()
                # Honor recorded entailment permutation per entailed predicate name
                recorded = None
                try:
                    recorded = predicate.get_entailed_substitution(node.predicate_name)
                except Exception:
                    recorded = None
                inv_name_map = {}
                if recorded is not None:
                    for k, v in recorded.items():
                        try:
                            inv_name_map[v.name] = k.name
                        except Exception:
                            pass
                target_name_to_term = {getattr(t, 'name', str(t)): t for t in predicate.terms}
                for idx, stored_pred_var in enumerate(node.predicate_params):
                    mapped_target_name = inv_name_map.get(getattr(stored_pred_var, 'name', str(stored_pred_var)))
                    if mapped_target_name is not None and mapped_target_name in target_name_to_term:
                        node_sub[stored_pred_var] = target_name_to_term[mapped_target_name]
                    else:
                        if idx < len(predicate.terms):
                            node_sub[stored_pred_var] = predicate.terms[idx]
                for stored_act_var, input_act_var in zip(node.action_params, action.parameters):
                    node_sub[stored_act_var] = input_act_var
                node_ssa = copy.deepcopy(node.ssa).substitute(node_sub)
                substituted_ssas.append(node_ssa)

            if not predicate.is_neg:
                combined = DisjunctiveFormula(*substituted_ssas).distribute_and_over_or()
            else:
                combined = ConjunctiveFormula(*substituted_ssas).distribute_and_over_or()
            return combined

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
                if isinstance(clause, NLPredicate):
                    # Regress the predicate clause using regress_pred
                    regressed_clause = self.regress_pred(clause, action)
                else:
                    regressed_clause = clause
                regressed_conjunct_list.append(regressed_clause)
            # Combine the regressed clauses and convert to DN
            regressed_disjunct_list.append(ConjunctiveFormula(*regressed_conjunct_list).distribute_and_over_or())
        # Return a flattened regressed goal  in DNF
        flattened_regressed_goal = DisjunctiveFormula(*regressed_disjunct_list).distribute_and_over_or()
        return flattened_regressed_goal
    
    def regress_plan(self, simplify_equality: bool = True, simplify_contradiction: bool = True, 
    simplify_typing: bool = True, simplify_dnf: bool = True, dup_detection: bool = True) -> List[Tuple[Formula, List[Action]]]:
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

        # Pre-compute goal predicate names for entailment gating
        goal_predicate_names = set()
        def _collect_goal_predicates(formula: Formula) -> None:
            if isinstance(formula, NLPredicate):
                goal_predicate_names.add(formula.name)
                return
            if hasattr(formula, 'clauses') and isinstance(getattr(formula, 'clauses'), list):
                for cl in formula.clauses:
                    _collect_goal_predicates(cl)
        _collect_goal_predicates(self._instance.goal)

        # A LLM-backed entailment checker for NLPredicate duplicate detection used in is_duplicate method
        def _entailment_checker(target: NLPredicate, pred: NLPredicate) -> bool:
            try:
                # Only attempt entailment if the candidate predicate name appears in the goal
                if pred.name not in goal_predicate_names:
                    return False
                # Check if a is entailed by b
                print(f'[Checking Entailment Back to the Goal] Checking if "{target.name}" entails the goal "{pred.name}"') if self._verbose else None
                entailed_predicate = self._llm.entailment(copy.deepcopy(pred), [copy.deepcopy(target)])
                if entailed_predicate is not None:
                    return True
            except Exception:
                return False

        NLPredicate.set_entailment_checker(_entailment_checker)

        plan = []
        goal = self._instance.goal.distribute_and_over_or()
        if not isinstance(goal, DisjunctiveFormula):
            raise ValueError(f"Goal must be a DisjunctiveFormula, but got {type(goal)}")
        frontier = [NLFOLRegressionPlanner.PlanNode(None, goal)]
        plan.append((frontier[0].sub_goal, [], Substitution()))

        visited_goal = []

        for clause in goal.clauses:
            if isinstance(clause, ConjunctiveFormula):
                visited_goal.append(clause)
        while frontier:
            current_node: NLFOLRegressionPlanner.PlanNode = frontier.pop(0)
            current_goal: Formula = current_node.sub_goal
            # Progress bar for current depth
            if self._verbose:
                bar_len = 20
                filled = int((current_node.depth / max(1, self._max_depth)) * bar_len)
                bar = "[" + "#" * filled + "-" * (bar_len - filled) + "]"
                print(f"[Depth] {current_node.depth}/{self._max_depth} {bar}")
            if current_node.depth >= self._max_depth:
                # exit if max depth is reached
                print(f'max depth reached: {current_node.depth}') if self._verbose else None
                continue
                
            for action in self._domain.actions:
                standardized_action = action.standardize(self._operations)
                regressed_goal = self.regress(current_goal, standardized_action)
                if simplify_contradiction:
                    regressed_goal = regressed_goal.simplify()
                simplified_goals = []
                substitution = Substitution()
                if isinstance(regressed_goal, Predicate):
                    continue

                if simplify_equality:
                    for clause in regressed_goal.clauses:
                        if isinstance(clause, ConjunctiveFormula):
                            # if clause is conjunction, simplify with equality further to get a substitution
                            clause, clause_substitution = clause.simplify_equality_variables_only(current_goal)
                            substitution.update(clause_substitution)
                        simplified_goals.append(clause)

                    regressed_goal = (
                        DisjunctiveFormula(*simplified_goals)
                        .substitute(substitution)
                        .simplify_plan()
                        .distribute_and_over_or()
                        if simplify_contradiction
                        else DisjunctiveFormula(*simplified_goals)
                        .substitute(substitution)
                        .distribute_and_over_or()
                    )
                    
                regressed_goal = self._operations.replace_domain_with_goal_fluents(regressed_goal, self._instance.goal)
                
                if (simplify_typing and self._domain.has_type_conflict(regressed_goal)) or isinstance(regressed_goal, FalseFormula):
                    # skip if there is a type conflict or the formula simplifes to false
                    continue
                # remove any conjuncts in the regressed goal that implies the seen subgoal
                regressed_goal_list = []
                if simplify_dnf or dup_detection:
                    for conjunct in regressed_goal.clauses:
                        if isinstance(conjunct, ConjunctiveFormula):
                            implies_found = any(conjunct.implies(formula) for formula in visited_goal) if simplify_dnf else False
                            duplicate_found = any(conjunct.is_duplicate(formula) for formula in visited_goal) if dup_detection else False
                            if not duplicate_found and not implies_found:
                                regressed_goal_list.append(conjunct)
                                visited_goal.append(conjunct)
                    regressed_goal = DisjunctiveFormula(*regressed_goal_list).simplify().distribute_and_over_or() if simplify_contradiction else DisjunctiveFormula(*regressed_goal_list).distribute_and_over_or()
                child_node = NLFOLRegressionPlanner.PlanNode(standardized_action, regressed_goal, current_node, current_node.depth + 1, {**current_node.substitution, **substitution})
                # add to the frontier and plan if the subgoal hasn't visited before
                if not isinstance(child_node.sub_goal, FalseFormula):
                    for conjunct in child_node.sub_goal.clauses:
                        if isinstance(conjunct, ConjunctiveFormula):
                            visited_goal.append(conjunct)
                        else:
                            print(f"Not a conjunctive formula: {conjunct}") if self._verbose else None
                    frontier.append(child_node)
                    plan.append((child_node.sub_goal, self.extract_plan(child_node), child_node.substitution))
    
        return plan
