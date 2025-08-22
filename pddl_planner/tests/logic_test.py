import warnings
import unittest
from pddl_planner.logic.formula import Substitution, Predicate, ConjunctiveFormula, DisjunctiveFormula, Variable, Constant, FalseFormula, Equality, Formula
from pddl_planner.logic.operation import Operations

class TestOperations(unittest.TestCase):

    def setUp(self):
        self.operations = Operations()

    def test_unify_identical_constants(self):
        x = Constant("a")
        y = Constant("a")
        substitution = Substitution()
        result = self.operations.unify(x, y, substitution)
        self.assertEqual(result, substitution)

    def test_unify_variable_with_constant(self):
        x = Variable("X")
        y = Constant("a")
        substitution = Substitution()
        result = self.operations.unify(x, y, substitution)
        expected_substitution = Substitution({x: y})
        self.assertEqual(result, expected_substitution)

    def test_unify_different_constants(self):
        x = Constant("a")
        y = Constant("b")
        substitution = Substitution()
        result = self.operations.unify(x, y, substitution)
        self.assertIsNone(result)

    def test_unify_variable_with_variable(self):
        x = Variable("X")
        y = Variable("Y")
        substitution = Substitution()
        result = self.operations.unify(x, y, substitution)
        expected_substitution = Substitution({x: y})
        self.assertEqual(result, expected_substitution)

    def test_unify_variable_with_existing_substitution(self):
        x = Variable("X")
        y = Constant("a")
        substitution = Substitution({x: y})
        result = self.operations.unify(x, y, Substitution())
        self.assertEqual(result, substitution)

    def test_unify_identical_predicates(self):
        p1 = Predicate("P", False, Constant("a"))
        p2 = Predicate("P", False, Constant("a"))
        substitution = Substitution()
        result = self.operations.unify(p1, p2, Substitution())
        self.assertEqual(result, substitution)

    def test_unify_predicate_with_variable(self):
        p1 = Predicate("P", False, Variable("X"))
        p2 = Predicate("P", False, Constant("a"))
        substitution = Substitution()
        result = self.operations.unify(p1, p2, substitution)
        expected_substitution = Substitution({Variable("X"): Constant("a")})
        self.assertEqual(result, expected_substitution)

    def test_unify_different_predicates(self):
        p1 = Predicate("P", False, Constant("a"))
        p2 = Predicate("Q", False, Constant("a"))
        substitution = Substitution()
        result = self.operations.unify(p1, p2, substitution)
        self.assertIsNone(result)

    def test_unify_predicates_with_variables_and_constants(self):
        p1 = Predicate("P", False, Variable("X"), Constant("b"))
        p2 = Predicate("P", False, Constant("a"), Variable("Y"))
        substitution = Substitution()
        result = self.operations.unify(p1, p2, substitution)
        expected_substitution = Substitution({Variable("X"): Constant("a"), Variable("Y"): Constant("b")})
        self.assertEqual(result, expected_substitution)

    def test_unify_predicates_with_variables_and_constants_2(self):
        p1 = Predicate("P", False, Variable("X"), Variable("Z"))
        p2 = Predicate("P", False, Constant("a"), Variable("Y"))
        substitution = Substitution()
        result = self.operations.unify(p1, p2, substitution)
        expected_substitution = Substitution({Variable("X"): Constant("a"), Variable("Z"): Variable("Y")})
        self.assertEqual(result, expected_substitution)

    def test_predicate_eq_one_var(self):
        p1 = Predicate("P", False, Variable("X"))
        p2 = Predicate("P", False, Variable("Y"))
        result = p1 == p2
        self.assertEqual(result, False)

    def test_predicate_dup_one_var(self):
        p1 = Predicate("P", False, Variable("X"))
        p2 = Predicate("P", False, Variable("Y"))
        result = p1.is_duplicate(p2)
        self.assertEqual(result, True)

    def test_predicate_dup_three_var_true(self):
        p1 = Predicate("P", False, Variable("X"), Variable("Y"), Variable("X"))
        p2 = Predicate("P", False, Variable("Y"), Variable("X"), Variable("Y"))
        result = p1.is_duplicate(p2)
        self.assertEqual(result, True)

    def test_predicate_eq_three_var_false(self):
        p1 = Predicate("P", False, Variable("X"), Variable("Y"), Variable("X"))
        p2 = Predicate("P", False, Variable("Y"), Variable("X"), Variable("Z"))
        result = p1 == p2
        self.assertEqual(result, False)

class TestConjunctiveFormula(unittest.TestCase):

    def setUp(self):
        self.operations = Operations()

    def test_create_conjunctive_formula_with_literals(self):
        p1 = Predicate("P", False, Constant("a"))
        p2 = Predicate("Q", False, Variable("X"))
        conjunctive_formula = ConjunctiveFormula(p1, p2)
        conjunctive_formula_2 = ConjunctiveFormula(p2, p1)
        self.assertEqual(conjunctive_formula, conjunctive_formula_2)
        self.assertEqual(conjunctive_formula.clauses, [p1, p2])

    def test_add_clauses(self):
        p1 = Predicate("P", False, Constant("a"))
        p2 = Predicate("Q", False, Variable("X"))
        conjunctive_formula = ConjunctiveFormula(p1)
        conjunctive_formula.add_clause(p2)
        self.assertIn(p2, conjunctive_formula.clauses)

    def test_collect_terms(self):
        p1 = Predicate("P", False, Constant("a"))
        p2 = Predicate("Q", False, Variable("X"))
        conjunctive_formula = ConjunctiveFormula(p1, p2)
        terms = conjunctive_formula.collect_terms()
        self.assertEqual(terms, {Constant("a"), Variable("X")})

    def test_collect_vars(self):
        p1 = Predicate("P", False, Constant("a"))
        p2 = Predicate("Q", False, Variable("X"))
        conjunctive_formula = ConjunctiveFormula(p1, p2)
        vars = conjunctive_formula.collect_vars()
        self.assertEqual(vars, {Variable("X")})

    def test_collect_preds(self):
        p1 = Predicate("P", False, Constant("a"))
        p2 = Predicate("Q", False, Variable("X"))
        conjunctive_formula = ConjunctiveFormula(p1, p2)
        preds = conjunctive_formula.collect_preds()
        self.assertEqual(preds, {p1, p2})

    def test_substitute(self):
        p1 = Predicate("P", False, Variable("X"))
        p2 = Predicate("Q", False, Constant("b"))
        conjunctive_formula = ConjunctiveFormula(p1, p2)
        substitution = Substitution({Variable("X"): Constant("a")})
        substituted_formula = conjunctive_formula.substitute(substitution)
        expected_formula = ConjunctiveFormula(
            Predicate("P", False, Constant("a")), Predicate("Q", False, Constant("b"))
        )
        self.assertEqual(substituted_formula, expected_formula)

    def test_unify_identical_conjunctive_formulas(self):
        p1 = Predicate("P", False, Constant("a"))
        p2 = Predicate("Q", False, Variable("X"))
        cf1 = ConjunctiveFormula(p1, p2)
        cf2 = ConjunctiveFormula(p1, p2)
        substitution = Substitution()
        result = self.operations.unify(cf1, cf2, substitution)
        self.assertEqual(result, substitution)

    def test_unify_conjunctive_formula_with_variable(self):
        p1 = Predicate("P", False, Variable("X"))
        p2 = Predicate("Q", False, Constant("a"))
        cf1 = ConjunctiveFormula(p1, p2)
        cf2 = ConjunctiveFormula(p1, p2)
        substitution = Substitution()
        result = self.operations.unify(cf1, cf2, substitution)
        expected_substitution = Substitution()
        self.assertEqual(result, expected_substitution)

    def test_unify_different_conjunctive_formulas(self):
        p1 = Predicate("P", False, Constant("a"))
        p2 = Predicate("Q", False, Variable("X"))
        p3 = Predicate("R", False, Constant("b"))
        cf1 = ConjunctiveFormula(p1, p2)
        cf2 = ConjunctiveFormula(p1, p3)
        substitution = Substitution()
        result = self.operations.unify(cf1, cf2, substitution)
        self.assertIsNone(result)

    def test_unify_conjunctive_formulas_with_variables_and_constants(self):
        p1 = Predicate("P", False, Variable("X"), Constant("b"))
        p2 = Predicate("Q", False, Constant("a"), Variable("Y"))
        p3 = Predicate("P", False, Constant("c"), Variable("Z"))
        p4 = Predicate("Q", False, Constant("a"), Constant("d"))
        cf1 = ConjunctiveFormula(p1, p2)
        cf2 = ConjunctiveFormula(p4, p3)
        substitution = Substitution()
        result = self.operations.unify(cf1, cf2, substitution)
        expected_substitution = Substitution({Variable("X"): Constant("c"), Variable("Y"): Constant("d"), Variable("Z"): Constant("b")})
        self.assertEqual(result, expected_substitution)

    def test_unify_conjunctive_formulas_with_variables_and_constants_same_negative(self):
        p1 = Predicate("P", False, Variable("X"), Constant("b"))
        p2 = Predicate("Q", True, Constant("a"), Variable("Y"))
        p3 = Predicate("P", False, Constant("c"), Variable("Z"))
        p4 = Predicate("Q", True, Constant("a"), Constant("d"))
        cf1 = ConjunctiveFormula(p1, p2)
        cf2 = ConjunctiveFormula(p4, p3)
        substitution = Substitution()
        result = self.operations.unify(cf1, cf2, substitution)
        expected_substitution = Substitution({Variable("X"): Constant("c"), Variable("Y"): Constant("d"), Variable("Z"): Constant("b")})
        self.assertEqual(result, expected_substitution)

    def test_unify_conjunctive_formulas_with_variables_and_constants_different_negative(self):
        p1 = Predicate("P", False, Variable("X"), Constant("b"))
        p2 = Predicate("Q", False, Constant("a"), Variable("Y"))
        p3 = Predicate("P", True, Constant("c"), Variable("Z"))
        p4 = Predicate("Q", False, Constant("a"), Constant("d"))
        cf1 = ConjunctiveFormula(p1, p2)
        cf2 = ConjunctiveFormula(p4, p3)
        substitution = Substitution()
        result = self.operations.unify(cf1, cf2, substitution)
        self.assertIsNone(result)

    def test_unify_conjunctive_formulas_negated_pred(self):
        p1 = Predicate("P", False, Variable("A"), Variable("C"))
        # p2 = Predicate("Q", False, Variable("B"), Variable("C"))
        p3 = Predicate("P", True, Variable("B"), Variable("B"))
        # p4 = Predicate("Q", False, Variable("E"), Variable("G"))
        cf1 = ConjunctiveFormula(p1)
        cf2 = ConjunctiveFormula(p3)
        substitution = Substitution()
        result = self.operations.unify(cf1, cf2, substitution)
        self.assertIsNone(result)

    def test_unify_conjunctive_formulas_repeated_variables(self):
        p1 = Predicate("P", False, Variable("A"), Variable("A"))
        p3 = Predicate("P", False, Variable("B"), Variable("C"))
        cf1 = ConjunctiveFormula(p1)
        cf2 = ConjunctiveFormula(p3)
        substitution = Substitution()
        result1 = self.operations.unify(cf1, cf2, substitution)
        result2 = self.operations.unify(cf2, cf1, substitution)
        expected_substitution = Substitution({Variable("A"): Variable("C"), Variable("C"): Variable("B")})
        self.assertEqual(result1, expected_substitution)
        self.assertEqual(result1, result2)

    def test_unify_conjunctive_formulas_repeated_variables_2(self):
        p1 = Predicate("P", False, Variable("A"), Variable("C"))
        p3 = Predicate("P", False, Variable("B"), Variable("B"))
        cf1 = ConjunctiveFormula(p1)
        cf2 = ConjunctiveFormula(p3)
        substitution = Substitution()
        result1 = self.operations.unify(cf1, cf2, substitution)
        result2 = self.operations.unify(cf2, cf1, substitution)
        expected_substitution = Substitution({Variable("A"): Variable("B"), Variable("C"): Variable("B")})
        self.assertEqual(result1, result2)
        self.assertEqual(result1, expected_substitution)


    def test_unify_conjunctive_formulas_with_variables_and_different_constants(self):
        p1 = Predicate("P", False, Variable("X"), Constant("b"))
        p2 = Predicate("Q", False, Constant("a"), Variable("Y"))
        p3 = Predicate("P", False, Constant("c"), Constant("e"))
        p4 = Predicate("Q", False, Constant("a"), Constant("d"))
        p5 = Predicate("R", False, Constant("a"), Constant("d"))
        cf1 = ConjunctiveFormula(p1, p2)
        cf2 = ConjunctiveFormula(p4, p3, p5)
        substitution = Substitution()
        result = self.operations.unify(cf1, cf2, substitution)
        self.assertIsNone(result)

    def test_conjunctive_formula_eq_same_structure(self):
        p1 = Predicate("P", False, Variable("X"), Variable("Y"))
        p2 = Predicate("Q", False, Variable("Y"), Variable("Z"))
        cf1 = ConjunctiveFormula(p1, p2)
        p3 = Predicate("P", False, Variable("A"), Variable("B"))
        p4 = Predicate("Q", False, Variable("B"), Variable("C"))
        cf2 = ConjunctiveFormula(p3, p4)
        self.assertNotEqual(cf1, cf2)

    def test_conjunctive_formula_dup_same_structure(self):
        p1 = Predicate("P", False, Variable("X"), Variable("Y"))
        p2 = Predicate("Q", False, Variable("Y"), Variable("Z"))
        cf1 = ConjunctiveFormula(p1, p2)
        p3 = Predicate("P", False, Variable("A"), Variable("B"))
        p4 = Predicate("Q", False, Variable("B"), Variable("C"))
        cf2 = ConjunctiveFormula(p3, p4)
        self.assertTrue(cf1.is_duplicate(cf2))

    def test_conjunctive_formula_eq_different_structure(self):
        p1 = Predicate("P", False, Variable("X"), Variable("Y"))
        p2 = Predicate("Q", False, Variable("Y"), Variable("Z"))
        cf1 = ConjunctiveFormula(p1, p2)
        p3 = Predicate("P", False, Variable("A"), Variable("B"))
        p4 = Predicate("Q", False, Variable("C"), Variable("D"))
        cf2 = ConjunctiveFormula(p3, p4)
        self.assertNotEqual(cf1, cf2)

    def test_conjunctive_formula_eq_same_structure_with_constants(self):
        p1 = Predicate("P", False, Variable("X"), Constant("a"))
        p2 = Predicate("Q", False, Constant("a"), Variable("Y"))
        cf1 = ConjunctiveFormula(p1, p2)
        p3 = Predicate("P", False, Variable("A"), Constant("a"))
        p4 = Predicate("Q", False, Constant("a"), Variable("B"))
        cf2 = ConjunctiveFormula(p3, p4)
        self.assertNotEqual(cf1, cf2)

    def test_conjunctive_formula_dup_same_structure_with_constants(self):
        p1 = Predicate("P", False, Variable("X"), Constant("a"))
        p2 = Predicate("Q", False, Constant("a"), Variable("Y"))
        cf1 = ConjunctiveFormula(p1, p2)
        p3 = Predicate("P", False, Variable("A"), Constant("a"))
        p4 = Predicate("Q", False, Constant("a"), Variable("B"))
        cf2 = ConjunctiveFormula(p3, p4)
        self.assertTrue(cf1.is_duplicate(cf2))

    def test_conjunctive_formula_eq_different_structure_with_constants(self):
        p1 = Predicate("P", False, Variable("X"), Constant("a"))
        p2 = Predicate("Q", False, Constant("a"), Variable("Y"))
        cf1 = ConjunctiveFormula(p1, p2)
        p3 = Predicate("P", False, Variable("A"), Constant("b"))
        p4 = Predicate("Q", False, Constant("a"), Variable("B"))
        cf2 = ConjunctiveFormula(p3, p4)
        self.assertNotEqual(cf1, cf2)

class TestConjunctiveFormulaImplies(unittest.TestCase):
    def setUp(self):
        # Common predicates used for testing
        self.p1 = Predicate("P", False, Constant("a"))
        self.p2 = Predicate("Q", False, Variable("X"))
        self.p3 = Predicate("R", False, Constant("b"))

    def test_implies_identical_formulas(self):
        # Two identical formulas should imply each other.
        cf1 = ConjunctiveFormula(self.p1, self.p2)
        cf2 = ConjunctiveFormula(self.p1, self.p2)
        self.assertTrue(cf1.implies(cf2))
        self.assertTrue(cf2.implies(cf1))

    def test_implies_superset_formula(self):
        # A formula with extra clauses implies a formula with a subset of those clauses.
        cf_full = ConjunctiveFormula(self.p1, self.p2, self.p3)
        cf_subset = ConjunctiveFormula(self.p1, self.p2)
        self.assertTrue(cf_full.implies(cf_subset))
        # The reverse implication should fail.
        self.assertFalse(cf_subset.implies(cf_full))

    def test_implies_missing_clause(self):
        # If a clause in the other formula is not in the self formula then implication fails.
        cf1 = ConjunctiveFormula(self.p1)
        cf2 = ConjunctiveFormula(self.p1, self.p2)
        self.assertFalse(cf1.implies(cf2))

    def test_implies_non_conjunctive_input(self):
        # When 'other' is not a ConjunctiveFormula, the method should warn and return False.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            cf = ConjunctiveFormula(self.p1, self.p2)
            not_cf = self.p3  # p3 is a Predicate, not a ConjunctiveFormula.
            self.assertFalse(cf.implies(not_cf))

class TestDisjunctiveFormula(unittest.TestCase):

    def setUp(self):
        self.operations = Operations()

    def test_create_disjunctive_formula_with_literals(self):
        p1 = Predicate("P", False, Constant("a"))
        p2 = Predicate("Q", False, Variable("X"))
        disjunctive_formula = DisjunctiveFormula(p1, p2)
        disjunctive_formula_2 = DisjunctiveFormula(p2, p1)
        self.assertEqual(disjunctive_formula, disjunctive_formula_2)
        self.assertEqual(disjunctive_formula.clauses, [p1, p2])

    def test_add_clauses(self):
        p1 = Predicate("P", False, Constant("a"))
        p2 = Predicate("Q", False, Variable("X"))
        disjunctive_formula = DisjunctiveFormula(p1)
        disjunctive_formula.add_clause(p2)
        self.assertIn(p2, disjunctive_formula.clauses)

    def test_collect_terms(self):
        p1 = Predicate("P", False, Constant("a"))
        p2 = Predicate("Q", False, Variable("X"))
        disjunctive_formula = DisjunctiveFormula(p1, p2)
        terms = disjunctive_formula.collect_terms()
        self.assertEqual(terms, {Constant("a"), Variable("X")})

    def test_collect_vars(self):
        p1 = Predicate("P", False, Constant("a"))
        p2 = Predicate("Q", False, Variable("X"))
        disjunctive_formula = DisjunctiveFormula(p1, p2)
        vars = disjunctive_formula.collect_vars()
        self.assertEqual(vars, {Variable("X")})

    def test_collect_preds(self):
        p1 = Predicate("P", False, Constant("a"))
        p2 = Predicate("Q", False, Variable("X"))
        disjunctive_formula = DisjunctiveFormula(p1, p2)
        preds = disjunctive_formula.collect_preds()
        self.assertEqual(preds, {p1, p2})

    def test_substitute(self):
        p1 = Predicate("P", False, Variable("X"))
        p2 = Predicate("Q", False, Constant("b"))
        disjunctive_formula = DisjunctiveFormula(p1, p2)
        substitution = Substitution({Variable("X"): Constant("a")})
        substituted_formula = disjunctive_formula.substitute(substitution)
        expected_formula = DisjunctiveFormula(
            Predicate("P", False, Constant("a")), Predicate("Q", False, Constant("b"))
        )
        m = substituted_formula == expected_formula
        self.assertEqual(substituted_formula, expected_formula)

    def test_unify_identical_disjunctive_formulas(self):
        p1 = Predicate("P", False, Constant("a"))
        p2 = Predicate("Q", False, Variable("X"))
        df1 = DisjunctiveFormula(p1, p2)
        df2 = DisjunctiveFormula(p1, p2)
        substitution = Substitution()
        result = self.operations.unify(df1, df2, substitution)
        self.assertEqual(result, substitution)

    def test_unify_disjunctive_formula_with_variable(self):
        p1 = Predicate("P", False, Variable("X"))
        p2 = Predicate("Q", False, Constant("a"))
        df1 = DisjunctiveFormula(p1, p2)
        df2 = DisjunctiveFormula(p1, p2)
        substitution = Substitution()
        result = self.operations.unify(df1, df2, substitution)
        expected_substitution = Substitution()
        self.assertEqual(result, expected_substitution)

    def test_unify_different_disjunctive_formulas(self):
        p1 = Predicate("P", False, Constant("a"))
        p2 = Predicate("Q", False, Variable("X"))
        p3 = Predicate("R", False, Constant("b"))
        df1 = DisjunctiveFormula(p1, p2)
        df2 = DisjunctiveFormula(p1, p3)
        substitution = Substitution()
        result = self.operations.unify(df1, df2, substitution)
        self.assertIsNone(result)

    def test_unify_disjunctive_formulas_with_variables_and_constants(self):
        p1 = Predicate("P", False, Variable("X"), Constant("b"))
        p2 = Predicate("Q", False, Constant("a"), Variable("Y"))
        p3 = Predicate("P", False, Constant("c"), Variable("Z"))
        p4 = Predicate("Q", False, Constant("a"), Constant("d"))
        df1 = DisjunctiveFormula(p1, p2)
        df2 = DisjunctiveFormula(p4, p3)
        substitution = Substitution()
        result = self.operations.unify(df1, df2, substitution)
        expected_substitution = Substitution({Variable("X"): Constant("c"), Variable("Y"): Constant("d"), Variable("Z"): Constant("b")})
        self.assertEqual(result, expected_substitution)

    def test_unify_disjunctive_formulas_with_variables_and_constants_same_negative(self):
        p1 = Predicate("P", False, Variable("X"), Constant("b"))
        p2 = Predicate("Q", True, Constant("a"), Variable("Y"))
        p3 = Predicate("P", False, Constant("c"), Variable("Z"))
        p4 = Predicate("Q", True, Constant("a"), Constant("d"))
        df1 = DisjunctiveFormula(p1, p2)
        df2 = DisjunctiveFormula(p4, p3)
        substitution = Substitution()
        result = self.operations.unify(df1, df2, substitution)
        expected_substitution = Substitution({Variable("X"): Constant("c"), Variable("Y"): Constant("d"), Variable("Z"): Constant("b")})
        self.assertEqual(result, expected_substitution)

    def test_unify_disjunctive_formulas_with_variables_and_constants_different_negative(self):
        p1 = Predicate("P", False, Variable("X"), Constant("b"))
        p2 = Predicate("Q", False, Constant("a"), Variable("Y"))
        p3 = Predicate("P", True, Constant("c"), Variable("Z"))
        p4 = Predicate("Q", False, Constant("a"), Constant("d"))
        df1 = DisjunctiveFormula(p1, p2)
        df2 = DisjunctiveFormula(p4, p3)
        substitution = Substitution()
        result = self.operations.unify(df1, df2, substitution)
        self.assertIsNone(result)

    def test_unify_disjunctive_formulas_with_variables_and_different_constants(self):
        p1 = Predicate("P", False, Variable("X"), Constant("b"))
        p2 = Predicate("Q", False, Constant("a"), Variable("Y"))
        p3 = Predicate("P", False, Constant("c"), Constant("e"))
        p4 = Predicate("Q", False, Constant("a"), Constant("d"))
        p5 = Predicate("R", False, Constant("a"), Constant("d"))
        df1 = DisjunctiveFormula(p1, p2)
        df2 = DisjunctiveFormula(p4, p3, p5)
        substitution = Substitution()
        result = self.operations.unify(df1, df2, substitution)
        self.assertIsNone(result)

    def test_disjunctive_formula_eq_same_structure(self):
        p1 = Predicate("P", False, Variable("X"), Variable("Y"))
        p2 = Predicate("Q", False, Variable("Y"), Variable("Z"))
        df1 = DisjunctiveFormula(p1, p2)
        p3 = Predicate("P", False, Variable("A"), Variable("B"))
        p4 = Predicate("Q", False, Variable("B"), Variable("C"))
        df2 = DisjunctiveFormula(p3, p4)
        self.assertNotEqual(df1, df2)

    def test_disjunctive_formula_dup_same_structure(self):
        p1 = Predicate("P", False, Variable("X"), Variable("Y"))
        p2 = Predicate("Q", False, Variable("Y"), Variable("Z"))
        df1 = DisjunctiveFormula(p1, p2)
        p3 = Predicate("P", False, Variable("A"), Variable("B"))
        p4 = Predicate("Q", False, Variable("B"), Variable("C"))
        df2 = DisjunctiveFormula(p3, p4)
        self.assertTrue(df1.is_duplicate(df2))

    def test_disjunctive_formula_eq_different_structure(self):
        p1 = Predicate("P", False, Variable("X"), Variable("Y"))
        p2 = Predicate("Q", False, Variable("Y"), Variable("Z"))
        df1 = DisjunctiveFormula(p1, p2)
        p3 = Predicate("P", False, Variable("A"), Variable("B"))
        p4 = Predicate("Q", False, Variable("C"), Variable("D"))
        df2 = DisjunctiveFormula(p3, p4)
        self.assertNotEqual(df1, df2)

    def test_disjunctive_formula_dup_same_structure_with_constants(self):
        p1 = Predicate("P", False, Variable("X"), Constant("a"))
        p2 = Predicate("Q", False, Constant("a"), Variable("Y"))
        df1 = DisjunctiveFormula(p1, p2)
        p3 = Predicate("P", False, Variable("A"), Constant("a"))
        p4 = Predicate("Q", False, Constant("a"), Variable("B"))
        df2 = DisjunctiveFormula(p3, p4)
        self.assertTrue(df1.is_duplicate(df2))
    
    def test_disjunctive_formula_eq_same_structure_with_constants(self):
        p1 = Predicate("P", False, Variable("X"), Constant("a"))
        p2 = Predicate("Q", False, Constant("a"), Variable("Y"))
        df1 = DisjunctiveFormula(p1, p2)
        p3 = Predicate("P", False, Variable("A"), Constant("a"))
        p4 = Predicate("Q", False, Constant("a"), Variable("B"))
        df2 = DisjunctiveFormula(p3, p4)
        self.assertNotEqual(df1, df2)

    def test_disjunctive_formula_eq_different_structure_with_constants(self):
        p1 = Predicate("P", False, Variable("X"), Constant("a"))
        p2 = Predicate("Q", False, Constant("a"), Variable("Y"))
        df1 = DisjunctiveFormula(p1, p2)
        p3 = Predicate("P", False, Variable("A"), Constant("b"))
        p4 = Predicate("Q", False, Constant("a"), Variable("B"))
        df2 = DisjunctiveFormula(p3, p4)
        self.assertNotEqual(df1, df2)

class TestStandardize(unittest.TestCase):

    def setUp(self):
        self.operations = Operations()

    def test_standardize_predicate(self):
        p = Predicate("P", False,  Variable("X"), Variable("Y"))
        standardized_p = self.operations.standardize(p)[0]
        vars_in_standardized_p = standardized_p.collect_vars()
        self.assertEqual(len(vars_in_standardized_p), 2)
        self.assertNotEqual(vars_in_standardized_p, {Variable("X"), Variable("Y")})

    def test_standardize_conjunctive_formula(self):
        p1 = Predicate("P", False, Variable("X"), Constant("a"))
        p2 = Predicate("Q", False, Variable("Y"), Variable("X"))
        p3 = Predicate("P", False, Variable("Y"), Variable("X"))
        p4 = Predicate("Q", False, Variable("Y"), Variable("X"))
        conjunctive_formula = ConjunctiveFormula(p1, p2)
        conjunctive_formula_2 = ConjunctiveFormula(p3, p4)
        standardized_cf = self.operations.standardize(conjunctive_formula)[0]
        standardized_cf_2 = self.operations.standardize(conjunctive_formula_2)[0]
        vars_in_standardized_cf = standardized_cf.collect_vars()
        self.assertEqual(len(vars_in_standardized_cf), 2)
        self.assertNotEqual(vars_in_standardized_cf, {Variable("X"), Variable("Y")})
        self.assertNotEqual(standardized_cf, standardized_cf_2)

    

class TestAndOverOr(unittest.TestCase):

    def setUp(self):
        self.operations = Operations()

    def test_distribute_and_over_or_atomic(self):
        # Atomic formula: P(?X) should be wrapped as a single clause.
        p = Predicate("P", False, Variable("X"))
        # Atomic formulas have no _clauses so distribution wraps it.
        distributed = p.distribute_and_over_or()
        expected = DisjunctiveFormula(ConjunctiveFormula(p))
        self.assertEqual(distributed, expected)

    def test_distribute_and_over_or_nested_disjunction(self):
        # Formula: P(?X) ∨ (Q(?Y) ∨ R(?Z))
        p = Predicate("P", False, Variable("X"))
        q = Predicate("Q", False, Variable("Y"))
        r = Predicate("R", False, Variable("Z"))
        inner_disj = DisjunctiveFormula(q, r)
        formula = DisjunctiveFormula(p, inner_disj)
        distributed = formula.distribute_and_over_or()
        # Expected flattening: {P, Q, R} all wrapped in ConjunctiveFormula.
        expected = DisjunctiveFormula(
            ConjunctiveFormula(p),
            ConjunctiveFormula(q),
            ConjunctiveFormula(r)
        )
        self.assertEqual(distributed, expected)

    def test_distribute_and_over_or_mixed_conjunctions(self):
        # Formula: (P(?X) ∨ Q(?Y)) ∧ (R(?Z) ∨ S(?W))
        p = Predicate("P", False, Variable("X"))
        q = Predicate("Q", False, Variable("Y"))
        r = Predicate("R", False, Variable("Z"))
        s = Predicate("S", False, Variable("W"))
        left_disj = DisjunctiveFormula(p, q)
        right_disj = DisjunctiveFormula(r, s)
        formula = ConjunctiveFormula(left_disj, right_disj)
        distributed = formula.distribute_and_over_or()
        # Expected after distribution:
        # (P ∧ R) ∨ (P ∧ S) ∨ (Q ∧ R) ∨ (Q ∧ S)
        expected = DisjunctiveFormula(
            ConjunctiveFormula(p, r),
            ConjunctiveFormula(p, s),
            ConjunctiveFormula(q, r),
            ConjunctiveFormula(q, s)
        )
        self.assertEqual(distributed, expected)

    def test_distribute_and_over_or_nested_mixed(self):
        # Formula: (P(?X) ∧ Q(?Y)) ∨ (R(?Z) ∧ (S(?W) ∨ T(?V)))
        p = Predicate("P", False, Variable("X"))
        q = Predicate("Q", False, Variable("Y"))
        r = Predicate("R", False, Variable("Z"))
        s = Predicate("S", False, Variable("W"))
        t = Predicate("T", False, Variable("V"))
        part1 = ConjunctiveFormula(p, q)
        inner_disj = DisjunctiveFormula(s, t)
        part2 = ConjunctiveFormula(r, inner_disj)
        formula = DisjunctiveFormula(part1, part2)
        distributed = formula.distribute_and_over_or()
        # Expected: part1 remains and part2 distributes:
        # Expected: (P ∧ Q) ∨ (R ∧ S) ∨ (R ∧ T)
        expected = DisjunctiveFormula(
            ConjunctiveFormula(p, q),
            ConjunctiveFormula(r, s),
            ConjunctiveFormula(r, t)
        )
        self.assertEqual(distributed, expected)

    def test_distribute_and_over_or_complex(self):
        # Construct the formula: (((R(?Z) ∨ S(?W)) ∧ Q(?Y)) ∨ P(?X))
        r = Predicate("R", False, Variable("Z"))
        s = Predicate("S", False, Variable("W"))
        q = Predicate("Q", False, Variable("Y"))
        p = Predicate("P", False, Variable("X"))

        inner_disj = DisjunctiveFormula(r, s)
        inner_conj = ConjunctiveFormula(ConjunctiveFormula(inner_disj, q))
        formula = DisjunctiveFormula(inner_conj, p)
        
        distributed = formula.distribute_and_over_or()

        # Expected result is (R ∧ Q) ∨ (S ∧ Q) ∨ P, where P is wrapped in a ConjunctiveFormula.
        expected = DisjunctiveFormula(
            ConjunctiveFormula(r, q),
            ConjunctiveFormula(s, q),
            ConjunctiveFormula(p)
        )
        self.assertEqual(distributed, expected)

class TestSimplifyAndContradiction(unittest.TestCase):

    def test_simplify_conjunctive_formula_contradiction(self):
        """Test that a conjunctive formula containing a contradiction simplifies to FALSE."""
        # Create a predicate and its negation on the same variable.
        clear_x = Predicate("clear", False, Variable("x"))
        not_clear_x = Predicate("clear", True, Variable("x"))
        # Conjunctive formula: clear(?x) ∧ ¬clear(?x)
        cf = ConjunctiveFormula(clear_x, not_clear_x)
        simplified = cf.simplify()
        self.assertIsInstance(simplified, FalseFormula,
                              "Conjunction of a predicate with its negation should simplify to FALSE.")

    def test_simplify_disjunctive_formula_removes_false(self):
        """Test that a disjunctive formula removes disjuncts that simplify to FALSE."""
        # One disjunct is a contradiction; the other is noncontradictory.
        contradictory = ConjunctiveFormula(
            Predicate("clear", False, Variable("x")),
            Predicate("clear", True, Variable("x"))
        )
        non_contradictory = (Predicate("Q", False, Variable("x")))
        df = DisjunctiveFormula(contradictory, non_contradictory)
        simplified = df.simplify()
        # Expect the contradictory disjunct removed so that the simplified formula equals non_contradictory.
        self.assertEqual(simplified, DisjunctiveFormula(non_contradictory),
                         "The disjunct that simplifies to FALSE should be removed.")

    def test_has_contradiction_true(self):
        """Test that has_contradiction returns True when two formulas contradict each other."""
        formula1 = ConjunctiveFormula(Predicate("clear", False, Variable("x")))
        formula2 = ConjunctiveFormula(Predicate("clear", True, Variable("x")))
        self.assertTrue(formula1.has_contradiction(formula2),
                        "A formula and its negation should be detected as contradictory.")
        self.assertTrue(formula2.has_contradiction(formula1),
                        "Negation should be symmetric in contradiction detection.")

    def test_has_contradiction_false(self):
        """Test that has_contradiction returns False when formulas do not contradict each other."""
        formula1 = ConjunctiveFormula(Predicate("clear", False, Variable("x")))
        formula2 = ConjunctiveFormula(Predicate("handempty", False, Variable("y")))
        self.assertFalse(formula1.has_contradiction(formula2),
                         "Formulas with different predicates should not be contradictory.")
        
class TestEquality(unittest.TestCase):

    def test_get_negation(self):
        # Create an Equality in its positive form
        x = Variable("X")
        a = Constant("a")
        eq = Equality(x, a, is_neq=False)
        # Get its negation – this should toggle the is_neq flag.
        neg_eq = eq.get_negation()
        expected = Equality(x, a, is_neq=True)
        self.assertEqual(neg_eq, expected, "get_negation() should toggle the negation flag while preserving terms.")

    def test_distribute_and_over_or_equality(self):
        # Equality is atomic so distribution should wrap it in a ConjunctiveFormula inside a DisjunctiveFormula.
        x = Variable("X")
        a = Constant("a")
        eq = Equality(x, a, is_neq=False)
        distributed = eq.distribute_and_over_or()
        expected = DisjunctiveFormula(ConjunctiveFormula(eq))
        self.assertEqual(distributed, expected, "Atomic Equality should be wrapped as DisjunctiveFormula(ConjunctiveFormula(Equality)).")

class TestDisjunctiveFormulaSimplify(unittest.TestCase):
    def setUp(self):
        # Create atomic predicates representing literals.
        # For simplicity, we assume these predicates have no arguments.
        self.pC = Predicate("C", False)
        self.pD = Predicate("D", False)
        self.pE = Predicate("E", False)
        self.pF = Predicate("F", False)
    
    def test_subsumption_elimination(self):
        """
        Tests that:
            (C ∧ D ∧ E) ∨ (C ∧ D)
        simplifies to:
            (C ∧ D)
        """
        conj1 = ConjunctiveFormula(self.pC, self.pD, self.pE)
        conj2 = ConjunctiveFormula(self.pC, self.pD)
        disj = DisjunctiveFormula(conj1, conj2)
        simplified = disj.simplify()
        # Our simplify method returns a DisjunctiveFormula possibly with only one clause.
        # Extract that unique clause for comparison.
        if isinstance(simplified, DisjunctiveFormula):
            self.assertEqual(len(simplified.clauses), 1)
            result = simplified.clauses[0]
        else:
            result = simplified
        self.assertEqual(str(result), str(conj2))
    
    def test_no_subsumption_needed(self):
        """
        Tests that if no one disjunct subsumes another, no disjunct is removed.
        For example:
            (C ∧ D) ∨ (C ∧ E)
        should remain unchanged.
        """
        conj1 = ConjunctiveFormula(self.pC, self.pD)
        conj2 = ConjunctiveFormula(self.pC, self.pE)
        disj = DisjunctiveFormula(conj1, conj2)
        simplified = disj.simplify()
        # Expect two disjuncts
        self.assertEqual(len(simplified.clauses), 2)
        simplified_set = {str(cl) for cl in simplified.clauses}
        expected_set = {str(conj1), str(conj2)}
        self.assertEqual(simplified_set, expected_set)
    
    def test_all_false_simplify(self):
        """
        Tests that if all disjuncts simplify to false, a FalseFormula is returned.
        """
        false1 = FalseFormula()
        false2 = FalseFormula()
        disj = DisjunctiveFormula(false1, false2)
        simplified = disj.simplify()
        self.assertTrue(isinstance(simplified, FalseFormula))
    
    def test_duplicate_removal(self):
        """
        Tests that duplicate disjuncts are removed during simplification.
        """
        conj = ConjunctiveFormula(self.pC, self.pD)
        disj = DisjunctiveFormula(conj, conj)
        simplified = disj.simplify()
        # Expect one unique disjunct.
        if isinstance(simplified, DisjunctiveFormula):
            self.assertEqual(len(simplified.clauses), 1)
        else:
            self.assertEqual(str(simplified), str(conj))

class TestSimplifyEquality(unittest.TestCase):
    def test_simplify_equality_simple(self):
        """
        Test that in a conjunctive formula containing an equality X==Y (with both X and Y variables)
        and a predicate using Y, simplify_equality removes the equality clause and substitutes Y with X.
        """
        X = Variable("X")
        Y = Variable("Y")
        eq = Equality(X, Y, is_neq=False)
        p = Predicate("P", False, Y)  # Uses Y
        cf = ConjunctiveFormula(eq, p)
        simplified_formula, subst = cf.simplify_equality()
        expected_cf = ConjunctiveFormula(Predicate("P", False, X))
        # Check that the simplified formula equals the expected one and the substitution is as expected.
        self.assertEqual(str(simplified_formula), str(expected_cf),
                         "Predicate should now use the representative variable ?X.")
        self.assertEqual(str(subst), str(Substitution({Y: X})),
                         "Substitution should map ?Y to ?X.")

    def test_simplify_equality_clause_alone(self):
        """
        Test that when the conjunctive formula contains only an equality clause between two variables,
        the result is a FalseFormula (empty clause after removal) along with the proper substitution.
        """
        X = Variable("X")
        Y = Variable("Y")
        eq = Equality(X, Y, is_neq=False)
        cf = ConjunctiveFormula(eq)
        simplified_formula, subst = cf.simplify_equality()
        self.assertIsInstance(simplified_formula, FalseFormula,
                              "A formula containing only a variable equality should simplify to FALSE.")
        self.assertEqual(str(subst), str(Substitution({Y: X})),
                         "Substitution should map ?Y to ?X.")

    def test_simplify_equality_ignore_constant(self):
        """
        Test that an equality clause between a variable and a constant is not used for substitution,
        and the equality clause remains in the simplified formula.
        """
        X = Variable("X")
        const_a = Constant("a")
        eq = Equality(X, const_a, is_neq=False)
        p = Predicate("P", False, X)
        cf = ConjunctiveFormula(eq, p)
        simplified_formula, subst = cf.simplify_equality()
        # The equality clause (involving a constant) should remain.
        self.assertIn(str(eq), str(simplified_formula),
                      "Equality involving a constant should not be removed.")
        # And no substitution should be produced since the equality clause is not processed.
        self.assertEqual(str(subst), str(Substitution()),
                         "No substitution should be made when a constant is involved.")

    def test_simplify_equality_chain(self):
        """
        Test a chain of equalities: X==Y and Y==Z, with a predicate using Z.
        The function applies a one-pass substitution so that:
            - eq1 produces the mapping Y -> X,
            - eq2 produces the mapping Z -> Y.
        Then the predicate P(Z) becomes P(Y) after substitution.
        Both equality clauses are removed from the final formula.
        """
        X = Variable("X")
        Y = Variable("Y")
        Z = Variable("Z")
        eq1 = Equality(X, Y, is_neq=False)
        eq2 = Equality(Y, Z, is_neq=False)
        p = Predicate("P", False, Z)
        cf = ConjunctiveFormula(eq1, eq2, p)
        simplified_formula, subst = cf.simplify_equality()
        expected_cf = ConjunctiveFormula(Predicate("P", False, Y))
        expected_subst = Substitution({Y: X, Z: Y})
        self.assertEqual(str(simplified_formula), str(expected_cf),
                         "Chain substitution should yield predicate with ?Y replacing ?Z.")
        self.assertEqual(str(subst), str(expected_subst),
                         "Substitution should map ?Y to ?X and ?Z to ?Y.")
        
    def test_multiple_redundant_predicates(self):
        """
        Create a ConjunctiveFormula with two redundant equality clauses between variables ?X and ?Y,
        and two identical predicates using ?Y.
        After simplify_equality, the equalities (where both terms are variables) are removed,
        a substitution mapping { ?Y: ?X } is built, and all occurrences of ?Y are replaced.
        Duplicate predicates should be removed.
        """
        X = Variable("X")
        Y = Variable("Y")
        # Create two identical equality clauses; since both are between variables,
        # the one with the higher value (?Y) will be substituted.
        eq1 = Equality(X, Y, is_neq=False)
        eq2 = Equality(X, Y, is_neq=False)
        # Create two duplicate predicates that use ?Y.
        p1 = Predicate("P", False, Y)
        p2 = Predicate("P", False, X)
        # Build the conjunctive formula.
        cf = ConjunctiveFormula(eq1, eq2, p1, p2)
        simplified_formula, subst = cf.simplify_equality()
        
        # Expected: substitution mapping should be { ?Y: ?X } and the only remaining clause is P(?X).
        expected_formula = ConjunctiveFormula(Predicate("P", False, X))
        expected_subst = Substitution({Y: X})
        
        self.assertEqual(str(simplified_formula), str(expected_formula),
                         "After simplify_equality, duplicate predicate with ?Y should be substituted and deduplicated to use ?X.")
        self.assertEqual(str(subst), str(expected_subst),
                         "The substitution mapping must map ?Y to ?X.")
        
class TestFormulaTypeTermDict(unittest.TestCase):
    def setUp(self) -> None:
        # Create a shared variable to use in our formulas.
        self.v = Variable("v")
        # Define a simple type mapping for our tests.
        self.type_mapping = {self.v: {"block", "object"}}
    
    def test_conjunctive_type_dict_preservation(self) -> None:
        """
        Test that a ConjunctiveFormula built with a term_type_dict 
        preserves its type information after calling distribute_and_over_or().
        """
        # Create a predicate that uses variable v.
        pred = Predicate("P", False, self.v, term_type_dict=self.type_mapping)
        # Build a conjunctive formula with that predicate.
        conj_formula = ConjunctiveFormula(pred, term_type_dict=self.type_mapping)
        # Distribute (for a single conjunct, this should be equivalent to the original).
        distributed = conj_formula.distribute_and_over_or()
        
        # Check that the resulting formula is a DisjunctiveFormula 
        # whose disjunct(s) preserve the type mapping for variable v.
        # Expect a single disjunct equivalent to the original conjunct.
        self.assertTrue(hasattr(distributed, "term_type_dict"),
                        "The distributed formula should have a term_type_dict property.")
        # Depending on implementation, the type dict of the resulting formula should map self.v to {"block", "object"}
        self.assertIn(self.v, distributed.term_type_dict,
                      "The type dictionary should include the variable used in the formula.")
        self.assertEqual(distributed.term_type_dict[self.v], {"block", "object"},
                         "The type mapping for 'v' should be preserved after distribution.")
    
    def test_disjunctive_type_dict_preservation(self) -> None:
        """
        Test that a DisjunctiveFormula built from conflict‐free conjuncts preserves
        the individual type dictionaries after distribute_and_over_or().
        """
        # Create two different predicates (or use the same) with the same type mapping.
        pred1 = Predicate("P1", False, self.v, term_type_dict=self.type_mapping)
        pred2 = Predicate("P2", False, self.v, term_type_dict=self.type_mapping)
        # Construct two conjunctive formulas with these predicates.
        conj1 = ConjunctiveFormula(pred1, term_type_dict=self.type_mapping)
        conj2 = ConjunctiveFormula(pred2, term_type_dict=self.type_mapping)
        # Combine them into a disjunctive formula.
        disj_formula = DisjunctiveFormula(conj1, conj2, term_type_dict=self.type_mapping)
        # Distribute the disjunction (flattening, etc.)
        distributed = disj_formula.distribute_and_over_or()
        
        # Check that the resulting formula has the expected type mapping.
        # Depending on your implementation, the distributed formula might be a DisjunctiveFormula
        # with one or more disjuncts, each carrying the same type info.
        self.assertTrue(hasattr(distributed, "term_type_dict"),
                        "The distributed disjunctive formula should have a term_type_dict property.")
        self.assertIn(self.v, distributed.term_type_dict,
                      "The type dictionary of the distributed formula should include variable 'v'.")
        self.assertEqual(distributed.term_type_dict[self.v], {"block", "object"},
                         "The type mapping for 'v' should be preserved in the distributed disjunctive formula.")
        
        # Optionally, check each individual disjunct.
        for clause in distributed.clauses:
            self.assertTrue(hasattr(clause, "term_type_dict"),
                            "Each clause should have a term_type_dict property.")
            self.assertIn(self.v, clause.term_type_dict,
                          "Each clause's type dictionary should include variable 'v'.")
            self.assertEqual(clause.term_type_dict[self.v], {"block", "object"},
                             "Each clause should maintain the correct type mapping for 'v'.")
            
    def test_conjunctive_equality_type_dict_preservation(self) -> None:
        """
        Test that a ConjunctiveFormula containing an equality clause—with a fresh variable introduced—and
        a predicate (that uses that fresh variable) preserves its term_type_dict after distribute_and_over_or().
        """
        # Generate a fresh variable for the equality.
        new_var = Formula.get_new_var()  # e.g. returns a variable like ?V0
        # Define a type mapping that covers both self.v and new_var.
        type_map = {self.v: {"block", "object"}, new_var: {"block", "object"}}
        # Create an equality clause between self.v and the new variable.
        eq = Equality(self.v, new_var, is_neq=False, term_type_dict=type_map)
        # Create a predicate that uses the new variable.
        pred = Predicate("P", False, new_var, term_type_dict=type_map)
        # Build a conjunctive formula using the equality and the predicate.
        cf = ConjunctiveFormula(eq, pred, term_type_dict=type_map)
        # Distribute – for a pure conjunction the distribution should wrap the result in a DisjunctiveFormula.
        distributed = cf.distribute_and_over_or()
        
        # Check that the distributed formula (a DisjunctiveFormula) preserves the type mapping.
        self.assertTrue(hasattr(distributed, "term_type_dict"),
                        "The distributed formula should have a term_type_dict property.")
        # Both self.v and new_var should appear in the type mapping.
        self.assertIn(self.v, distributed.term_type_dict,
                      "The type dictionary should include the shared variable 'v'.")
        self.assertIn(new_var, distributed.term_type_dict,
                      "The type dictionary should include the fresh variable from the equality.")
        self.assertEqual(distributed.term_type_dict[self.v], {"block", "object"},
                         "The type mapping for 'v' should be preserved after distribution.")
        self.assertEqual(distributed.term_type_dict[new_var], {"block", "object"},
                         "The type mapping for the fresh variable should be preserved after distribution.")
    
    def test_disjunctive_equality_type_dict_preservation(self) -> None:
        """
        Test that a DisjunctiveFormula built from two conjunctive formulas,
        each containing an equality clause (with a new variable introduced) preserves
        the union of type mappings after distribute_and_over_or().
        """
        # First conjunct: equality between self.v and a fresh variable.
        fresh1 = Formula.get_new_var()
        type_map1 = {self.v: {"block", "object"}, fresh1: {"block", "object"}}
        eq1 = Equality(self.v, fresh1, is_neq=False, term_type_dict=type_map1)
        pred1 = Predicate("P1", False, fresh1, term_type_dict=type_map1)
        conj1 = ConjunctiveFormula(eq1, pred1, term_type_dict=type_map1)
        
        # Second conjunct: another equality between self.v and a different fresh variable.
        fresh2 = Formula.get_new_var()
        type_map2 = {self.v: {"block", "object"}, fresh2: {"block", "object"}}
        eq2 = Equality(self.v, fresh2, is_neq=False, term_type_dict=type_map2)
        pred2 = Predicate("P2", False, fresh2, term_type_dict=type_map2)
        conj2 = ConjunctiveFormula(eq2, pred2, term_type_dict=type_map2)
        
        # Combine the two conjuncts into a DisjunctiveFormula.
        # The overall type mapping is the union.
        union_map = {self.v: {"block", "object"}, fresh1: {"block", "object"}, fresh2: {"block", "object"}}
        disj_formula = DisjunctiveFormula(conj1, conj2, term_type_dict=union_map)
        distributed = disj_formula.distribute_and_over_or()
        
        # Check that the distributed formula and each of its disjuncts carry the full type mapping.
        self.assertTrue(hasattr(distributed, "term_type_dict"),
                        "The distributed disjunctive formula should have a term_type_dict property.")
        for term in (self.v, fresh1, fresh2):
            self.assertIn(term, distributed.term_type_dict,
                          f"The type dictionary should include variable {term}.")
            self.assertEqual(distributed.term_type_dict[term], {"block", "object"},
                             f"The type mapping for {term} should be preserved after distribution.")
        
        # Optionally, check each individual disjunct.
        for clause in distributed.clauses:
            self.assertTrue(hasattr(clause, "term_type_dict"),
                            "Each disjunct should have a term_type_dict property.")
            for term in (self.v, fresh1, fresh2):
                self.assertIn(term, clause.term_type_dict,
                              f"Each disjunct's type dictionary should include variable {term}.")
                self.assertEqual(clause.term_type_dict[term], {"block", "object"},
                                 f"Each disjunct should maintain the correct type mapping for {term}.")

class TestConjunctiveFormulaDuplicates(unittest.TestCase):

    def test_duplicate_not_equal(self):
        # Create variables and constants
        v84 = Variable("V84")
        v85 = Variable("V85")
        v86 = Variable("V86")
        v97 = Variable("V97")
        p0 = Constant("p0")
        l20 = Constant("l20")
        
        # Build equalities: ?V84 == p0 and ?V86 == l20
        eq1 = Equality(v84, p0, is_neq=False)
        eq2 = Equality(v86, l20, is_neq=False)
        
        # First formula: at(?V85, ?V97)
        f1 = ConjunctiveFormula(
            eq1,
            eq2,
            Predicate("at", False, v85, v97),
            Predicate("in", False, v84, v85)
        )
        
        # Second formula: at(?V85, ?V86)
        f2 = ConjunctiveFormula(
            eq1,
            eq2,
            Predicate("at", False, v85, v86),
            Predicate("in", False, v84, v85)
        )
        
        # They should not be duplicates since the second predicate differs.
        self.assertFalse(f1.is_duplicate(f2))
        self.assertNotEqual(f1, f2)

    def test_duplicate_equal(self):
        # Create variables and constants
        v84 = Variable("V84")
        v85 = Variable("V85")
        v86 = Variable("V86")
        v97 = Variable("V97")
        
        # First formula: at(?V85, ?V97)
        f1 = ConjunctiveFormula(
            Predicate("at", False, v85, v97),
            Predicate("in", False, v84, v85)
        )
        
        # Second formula: at(?V85, ?V86)
        f2 = ConjunctiveFormula(
            Predicate("at", False, v85, v86),
            Predicate("in", False, v84, v85)
        )
        
        # They should not be duplicates since the second predicate differs.
        self.assertTrue(f1.is_duplicate(f2))
        self.assertNotEqual(f1, f2)

if __name__ == '__main__':
    unittest.main()

