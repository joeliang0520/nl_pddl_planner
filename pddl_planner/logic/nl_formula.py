from typing import Set, Dict
from pddl_planner.logic.formula import Predicate, Term, Substitution, Variable
import copy
class NLPredicate(Predicate):
    def __init__(self, name: str, str_representation: str, is_neg: bool, *terms: "Term",
     term_type_dict: Dict["Term", Set[str]] = None, entailed_by: "NLPredicate" = None) -> None:
        super().__init__(name, is_neg, *terms, term_type_dict=term_type_dict)
        self._str_represntation = str_representation 
        self._entailed_by = entailed_by if entailed_by is not None else self

    def __str__(self) -> str:
        return f'{self._str_represntation}({", ".join(f"{str(term)}" for term in self.terms)})' if not self._is_neg else f'not {self._str_represntation}({", ".join(f"{str(term)}" for term in self.terms)})'

    def substitute(self, substitution: "Substitution") -> "NLPredicate":
        """Substitute the variables in the predicate using the provided substitution.

        Args:
            substitution (Substitution): A mapping of variables to terms.

        Returns:
            Predicate: A new Predicate with substitutions applied.
        """
        # combine the term_type_dict from the substitution with the term_type_dict of the predicate
        if self.term_type_dict is not None:
            for term1, term2 in substitution.items():
                if term1 in self.term_type_dict and term2 in self.term_type_dict:
                    self.term_type_dict[term2].update(self.term_type_dict[term1])
        # update the str_representation of the predicate

        for term in self.terms:
            self._str_represntation = self._str_represntation.replace(f' {str(term)}', f' {substitution.get(term, term)}').replace(f'{str(term)} ', f'{substitution.get(term, term)} ')
        self._str_represntation = self._str_represntation.strip()

        # return a new predicate with the updated str_representation
        return NLPredicate(self.name, self._str_represntation, self._is_neg, *[substitution.get(term, term) for term in self.terms], 
        term_type_dict={substitution.get(term, term): types for term, types in self.term_type_dict.items()} if self.term_type_dict is not None else None)

    def get_negation(self) -> "NLPredicate":
        """Get the negation of the predicate.

        Returns:
            Predicate: A new Predicate with the negation flag toggled.
        """
        return NLPredicate(self.name, self._str_represntation, not self._is_neg, *self.terms)

    @property
    def entailed(self) -> "NLPredicate":
        """Get the predicate that the predicate is entailed by.

        Returns:
            Predicate: The predicate that the predicate is entailed by.
        """
        return self._entailed_by
