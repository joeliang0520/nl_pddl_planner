import copy
from pddl_planner.logic.formula import Logic, Substitution, Formula, Predicate, ConjunctiveFormula, DisjunctiveFormula, Variable

class Operations(Logic):
    """Operations performed to formulas"""

    def occur_check(self, var, x):
        """Check if variable occurs in formula
        """
        return var in x.collect_vars()
    
    def unify(self, x: "Formula", y: "Formula", substitution: "Substitution") -> "Substitution":
        """ method to unify two formulas
         """
        if substitution is None:
            # failure
            return substitution

        elif x == y:
            return substitution
        
        elif isinstance(x, Variable):
            return self.unify_var(x, y, substitution)
        
        elif isinstance(y, Variable):
            return self.unify_var(y, x, substitution)

        elif isinstance(x, Predicate) and isinstance(y, Predicate):
            return self.unify(x.collect_terms(), y.collect_terms(), self.unify(x.collect_preds_name(), y.collect_preds_name(), substitution))
        
        elif (isinstance(x, ConjunctiveFormula) and isinstance(y, ConjunctiveFormula)) or (isinstance(x, DisjunctiveFormula) and isinstance(y, DisjunctiveFormula)):
            return self.unify(x.clauses, y.clauses, substitution)

        elif (isinstance(x, set) and isinstance(y, set)) or (isinstance(x, list) and isinstance(y, list)):
            x_copy = copy.deepcopy(x)
            y_copy = copy.deepcopy(y)
            x_first = x_copy.pop()
            y_first = y_copy.pop()
            return self.unify(x_copy, y_copy, self.unify(x_first, y_first, substitution))
        
        else:
            return None
        
    def unify_var(self, var, x, substitution):
        if var in substitution:
            return self.unify(substitution[var], x, substitution)
        elif x in substitution: 
            return self.unify(var, substitution[x], substitution)
        elif isinstance(x, Formula) and self.occur_check(var, x):
            return None
        else:
            substitution[var] = x
            return substitution

    def standardize(self, *formulas):
        """Standardize the variables in a formula"""
        all_vars = set()
        for formula in formulas:
            all_vars.update(formula.collect_vars())  # Collect vars from all formulas

        substitution = Substitution()
        for var in all_vars:
            if var not in substitution:
                substitution[var] = self.get_new_var()

        # Apply the substitution to each formula and return the standardized formulas
        standardized_formulas = [formula.substitute(substitution) for formula in formulas]
        return standardized_formulas

