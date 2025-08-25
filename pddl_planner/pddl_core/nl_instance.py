from pddl_planner.logic.nl_parser import NLParser
from pddl_planner.pddl_core.nl_domain import NLDomain
from pddl_planner.logic.formula import Predicate
from typing import List

class NLInstance():
    def __init__(self, pddl_problem: List[tuple], domain: NLDomain):
        self._domain = domain
        self._parser = NLParser()
        self._predicates = None
        self._goal = None
        self._objects = None
        self._parse_problem(pddl_problem)
        self._parse_predicates(pddl_problem)
        
    def _parse_problem(self, pddl_problem: List[tuple]):
        # self._init = self._parser.parse_init(list(pddl_problem.init))
        self._goal = self._parser.parse_goal(pddl_problem)
        #extract the terms and type from the goal
        type_tags = {}
        for block in pddl_problem:
            for term in block[1].keys():
                type_tags[term] = block[1][term]
        self._objects = [self._parser.parse_term(obj, type_tags=type_tags) for obj in type_tags.keys()]
    
    def _parse_predicates(self, pddl_problem: List[tuple]):
        """
        Parse and construct the list of predicates in the goal and store them in self._predicates.

        Args:
            pddl_problem (List[tuple]): The PDDL problem.
        """
        predicates: List[Predicate] = []
        for nl_predicate in pddl_problem:
            predicate = self._parser.parse_predicate(nl_predicate)
            predicates.append(predicate)
        self._predicates = predicates

    @property
    def domain(self):
        return self._domain
    
    @property
    def init(self):
        return self._init
    
    @property
    def goal(self):
        return self._goal
    
    @property
    def objects(self):
        return self._objects
    
    def __str__(self):
        return f"Instance: {self._domain.name}, Init: {self._init}, Goal: {self._goal}, Objects: {self._objects}"
    
    def __repr__(self):
        return f"Instance: {self._domain.name}, Init: {self._init}, Goal: {self._goal}, Objects: {self._objects}"
        