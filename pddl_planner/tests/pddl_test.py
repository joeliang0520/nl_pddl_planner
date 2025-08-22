import unittest
import pddl
# Import PDDL classes used by the Parser
from pddl.logic.base import And, Or, Not
from pddl.logic.terms import Variable as PDDLVariable, Constant as PDDLConstant
from pddl.logic.predicates import Predicate as PDDLPredicate
from types import SimpleNamespace

from pddl_planner.logic.parser import Parser
from pddl_planner.logic.formula import ConjunctiveFormula, DisjunctiveFormula, Predicate, Variable, Constant
from pddl_planner.pddl_core.domain import Domain

class TestParser(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = Parser()

    def test_parse_term_variable(self):
        # Test converting a PDDL variable to a logic Variable.
        pddl_var = PDDLVariable("x")
        term = self.parser.parse_term(pddl_var)
        self.assertIsInstance(term, Variable)
        # Instead of accessing .name, check the string representation.
        self.assertEqual(str(term), "?x")

    def test_parse_term_constant(self):
        # Test converting a PDDL constant to a logic Constant.
        pddl_const = PDDLConstant("a")
        term = self.parser.parse_term(pddl_const)
        self.assertIsInstance(term, Constant)
        # Use the string representation for constants.
        self.assertEqual(str(term), "a")

    def test_parse_predicate_positive_and_negative(self):
        # Construct a positive PDDL predicate using a blocks domain predicate (e.g., clear).
        pddl_pred = PDDLPredicate("clear", PDDLConstant("b1"))
        parsed_pred = self.parser.parse_predicate(pddl_pred)
        self.assertIsInstance(parsed_pred, Predicate)
        self.assertFalse(parsed_pred.is_neg)
        self.assertEqual(parsed_pred.name, "clear")

        # Construct a negated predicate using Not.
        negated = Not(pddl_pred)
        parsed_neg = self.parser.parse_predicate(negated)
        self.assertIsInstance(parsed_neg, Predicate)
        self.assertTrue(parsed_neg.is_neg)
        self.assertEqual(parsed_neg.name, "clear")

    def test_parse_formula_and_predicate(self):
        # Use predicates from the blocks domain.
        pddl_pred1 = PDDLPredicate("on", PDDLVariable("x"), PDDLVariable("y"))
        pddl_pred2 = PDDLPredicate("clear", PDDLVariable("b"))
        
        # Build a compound formula using And.
        pddl_and = And(pddl_pred1, pddl_pred2)
        logic_formula = self.parser.parse_formula(pddl_and)
        # Expect a ConjunctiveFormula since And is mapped to ConjunctiveFormula.
        self.assertIsInstance(logic_formula, ConjunctiveFormula)
        # Check that it contains the proper clauses.
        self.assertEqual(len(logic_formula.clauses), 2)
        for clause in logic_formula.clauses:
            self.assertIsInstance(clause, Predicate)

        # Test disjunction: build an Or formula.
        pddl_or = Or(pddl_pred1, pddl_pred2)
        logic_formula_or = self.parser.parse_formula(pddl_or)
        self.assertIsInstance(logic_formula_or, DisjunctiveFormula)
        self.assertEqual(len(logic_formula_or.clauses), 2)

    def test_parse_goal(self):
        # Create a goal using And of two predicates from blocks domain.
        # For example, require that a block is clear and that it is on another block.
        pddl_pred1 = PDDLPredicate("clear", PDDLConstant("b1"))
        pddl_pred2 = PDDLPredicate("on", PDDLConstant("b1"), PDDLConstant("b2"))
        pddl_goal = And(pddl_pred1, pddl_pred2)
        logic_goal = self.parser.parse_goal(pddl_goal)
        self.assertIsInstance(logic_goal, ConjunctiveFormula)
        self.assertGreater(len(logic_goal.clauses), 0)

    def test_parse_init(self):
        # Create an init block as a list of predicates from blocks domain.
        # For example, a robot is handempty and a block is ontable.
        pddl_pred1 = PDDLPredicate("handempty", PDDLConstant("r1"))
        pddl_pred2 = PDDLPredicate("ontable", PDDLConstant("b1"))
        pddl_init = [pddl_pred1, pddl_pred2]
        logic_init = self.parser.parse_init(pddl_init)
        self.assertIsInstance(logic_init, ConjunctiveFormula)
        self.assertEqual(len(logic_init.clauses), 2)

    def test_parse_blocks_domain(self):
        """
        Test parsing of the blocks.pddl domain file.
        This verifies that the domain is parsed, actions are present,
        and that the parser converts each action's precondition and effect into the proper logic formula.
        """
        blocks_domain = pddl.parse_domain('files/blocks.pddl')
        domain = Domain(blocks_domain)
        self.assertTrue(len(domain.actions) > 0, "No actions found in the blocks domain.")
        for action in domain.actions:
            self.assertIsInstance(action.preconditions, (ConjunctiveFormula, DisjunctiveFormula, Predicate))
            self.assertIsInstance(action.effects, (ConjunctiveFormula, DisjunctiveFormula, Predicate))
            


class TestDomain(unittest.TestCase):
    def setUp(self) -> None:
        """
        Setup by parsing the blocks.pddl domain and creating a Domain instance.
        """
        self.ppdl_domain = pddl.parse_domain('files/blocks.pddl')
        # print("Types: ", type(self.ppdl_domain.types))
        self.domain = Domain(self.ppdl_domain)

    def test_domain_actions(self) -> None:
        """
        Test that the domain parses actions correctly.
        
        Verifies that:
          - There is at least one action in the domain.
          - Each action has a name, parameters, precondition, and effect.
          - Precondition and effect formulas are parsed into known types.
        """
        self.assertTrue(len(self.domain.actions) > 0, "No actions found in the blocks domain.")
        for action in self.domain.actions:
            # Check that the action has a name.
            self.assertIsInstance(action.name, str)
            # Check that parameters are parsed as terms (Variables or Constants)
            for param in action.parameters:
                self.assertTrue(isinstance(param, (Variable, Constant)))
            # Check that precondition and effect formulas are of expected types.
            self.assertIsInstance(action.preconditions, (ConjunctiveFormula, DisjunctiveFormula, Predicate))
            print("Precondition Term type dict: ", action.preconditions.term_type_dict)
            self.assertIsNotNone(action.preconditions.term_type_dict, "PreconditionTerm type dictionary is empty.")
            self.assertIsInstance(action.effects, (ConjunctiveFormula, DisjunctiveFormula, Predicate))
            print("Effect Term type dict: ", action.effects.term_type_dict)
            self.assertIsNotNone(action.effects.term_type_dict, "Effect Term type dictionary is empty.")


    def test_domain_name(self) -> None:
        """
        Test that the domain name is correct.
        
        The blocks.pddl defines the domain name as 'blocks'.
        """
        self.assertEqual(self.domain.name.lower(), "blocks")

    def test_parse_predicates(self) -> None:
        """Test that the domain's predicates property is valid.
        
        Verifies that the predicates stored in Domain (domain.predicates) are non-empty
        and that each predicate is an instance of Predicate.
        """
        self.assertTrue(len(self.domain.predicates) > 0,
                        "No predicates found in the domain predicates list.")
        for pred in self.domain.predicates:
            self.assertIsInstance(pred, Predicate)

    def test_actions_parameters_contents(self) -> None:
        """
        Test that action parameters are correctly parsed and are of proper term types.
        
        For the 'pick-up' action (if it exists) check that its parameters correspond
        to a block and a robot.
        """
        # Look for an action with the name 'pick-up' (or similar, case-insensitive)
        pick_up_action = None
        for action in self.domain.actions:
            if action.name.lower() == "pick-up":
                pick_up_action = action
                break
        self.assertIsNotNone(pick_up_action, "No 'pick-up' action found in the blocks domain.")
        # Check expected number of parameters
        # According to the blocks.pddl, pick-up should have two parameters: a block and a robot.
        self.assertEqual(len(pick_up_action.parameters), 2)
        for param in pick_up_action.parameters:
            self.assertTrue(isinstance(param, (Variable, Constant)))

    def test_parse_types(self) -> None:
        """
        Test that the types are parsed correctly from blocks.pddl.
        
        For blocks.pddl the types clause is:
            (:types
                blockA blocks - block
                robots - robot
                block - object
            )
        So the Domain.types dictionary should have four keys "blockA", "blocks", "robots", and "block".
        """
        types_def = self.domain.types
        self.assertIsInstance(types_def, dict, "Expected types to be stored in a dictionary.")
        # Check that both 'block' and 'robot' are present.
        self.assertEqual(len(types_def), 4, "There should be exactly four types defined.")
        self.assertIn("blocks", types_def, "Expected 'block' type to be present.")
        self.assertIn("robots", types_def, "Expected 'robot' type to be present.")

    def test_same_type(self) -> None:
        """
        Test that a type is considered a subtype of itself.
        """
        self.assertTrue(self.domain.is_subtype_of("block", "block"))
    
    def test_direct_subtype(self) -> None:
        """
        Test that direct subtyping is recognized.
        For example: "blocks" is a subtype of "block", and "robots" is a subtype of "robot".
        """
        self.assertTrue(self.domain.is_subtype_of("blocks", "block"))
        self.assertTrue(self.domain.is_subtype_of("robots", "robot"))
    
    def test_indirect_subtype(self) -> None:
        """
        Test that indirect (recursive) subtyping is recognized.
        For example: "blocks" is a subtype of "object" because blocks -> block -> object.
        """
        self.assertTrue(self.domain.is_subtype_of("blocks", "object"))

    def test_no_subtype(self) -> None:
        """
        Test that types that are not existing in the domain return False.
        For example: "tree" is not a type inside the domain and should return false.
        """
        self.assertFalse(self.domain.is_subtype_of("tree", "robot"))
    
    def test_not_subtype(self) -> None:
        """
        Test that non-related types return False.
        For example: "blocks" is not a subtype of "robot" and "robots" is not a subtype of "block".
        """
        self.assertFalse(self.domain.is_subtype_of("blocks", "robot"))
        self.assertFalse(self.domain.is_subtype_of("robots", "block"))

class TestDomainTypeConflict(unittest.TestCase):
    def setUp(self) -> None:
        """
        Create a dummy PPDDL domain with a simple types mapping.
        
        In this mapping:
          - "block" and "robot" are subtypes of "object"
          - "object" has no supertype (None)
        """
        dummy_ppdl_domain = SimpleNamespace(
            name="test_domain",
            actions=[],
            predicates=[],
            types={"block": "object", "robot": "object", "object": None}
        )
        self.domain = Domain(dummy_ppdl_domain)
        # Create a sample variable for testing.
        self.v = Variable("v")
        self.w = Variable("w")
        self.P1 = Predicate("P1", False, self.v)
        self.P2 = Predicate("P2", False, self.v)
    
    def test_no_type_info(self) -> None:
        """
        If a formula has an empty term_type_dict then no conflict is detected.
        """
        # Create a ConjunctiveFormula with no type information.
        formula = ConjunctiveFormula(term_type_dict={})
        self.assertFalse(self.domain.has_type_conflict(formula),
                         "Expected no conflict when no type information is provided.")
    
    def test_conjunctive_no_conflict(self) -> None:
        """
        A conjunctive formula with a single term having compatible types (e.g. ["block", "object"])
        should not have a type conflict.
        """
        # "block" is a subtype of "object" in our domain.
        formula = ConjunctiveFormula(term_type_dict={self.v: ["block", "object"]})
        self.assertFalse(self.domain.has_type_conflict(formula),
                         "Expected no type conflict when types are compatible.")
    
    def test_conjunctive_conflict(self) -> None:
        """
        A conjunctive formula where a term has incompatible types (e.g. ["block", "robot"])
        should have a type conflict.
        """
        formula = ConjunctiveFormula(term_type_dict={self.v: ["block", "robot"]})
        self.assertTrue(self.domain.has_type_conflict(formula),
                        "Expected a type conflict when a term has incompatible types.")
    
    def test_disjunctive_no_conflict(self) -> None:
        """
        A disjunctive formula constructed from two conflict–free conjuncts should have no conflict.
        """
        # First conjunct: term v with types ["block", "object"] is conflict-free.
        conj1 = ConjunctiveFormula(term_type_dict={self.v: ["block", "object"]})
        # Second conjunct: term v with a single type.
        conj2 = ConjunctiveFormula(term_type_dict={self.v: ["block"]})
        disj_formula = DisjunctiveFormula(conj1, conj2)
        self.assertFalse(self.domain.has_type_conflict(disj_formula),
                         "Expected no type conflict for a disjunction of conflict-free formulas.")
    
    def test_disjunctive_conflict(self) -> None:
        """
        A disjunctive formula with at least one conjunct having a type conflict should be reported
        as conflicted.
        """
        # First conjunct: conflict-free.
        conj1 = ConjunctiveFormula(self.P1, term_type_dict={self.v: {"block", "object"}})
        # Second conjunct: conflict present.
        conj2 = ConjunctiveFormula(self.P2, term_type_dict={self.v: {"block", "robot"}})
        disj_formula = DisjunctiveFormula(conj1, conj2)
        self.assertTrue(self.domain.has_type_conflict(disj_formula),
                        "Expected a type conflict when one disjunct has incompatible type information.")

if __name__ == '__main__':
    unittest.main()