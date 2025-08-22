# NL-PDDL Planner

A planner implemented in Python that thats Natural Languages (NL) predicates from the actions and goals as inputs and introduces a First‑Order Logic (FOL) Regression planner grounded in SSA from Situation Calculus, provides sample PDDL domains for testing, and includes scripts to run the FOL regression planner on different domains.

This repository includes:

- A **Parser** for NL domains and problems.
- **NL Planning algorithms**: FOL (First-Order Logic) Regression planners that can handles Natural Language entailments from NL predicates in problem to the domain predicates
- **Logic utilities**: Formula manipulation, unification, substitution.
- **Core PDDL structures**: Domain and problem instance representation.

## Table of Contents

- [Directory Structure](#directory-structure)
- [Getting Started](#getting-started)
- [Usage](#usage)

## Directory Structure

```
pddl_solver/
├── pddl_planner/           # Core planning package
│   ├── logic/
│   │   ├── parser.py       # PDDL→logic parser
│   │   ├── nl_parser.py       # NL→logic parser (*new*)
│   │   ├── formula.py      # Formula classes (Conjunctive, Disjunctive, Predicate, Equality), main file for logic
│   │   └── operation.py    # Unification & standardization operations
│   ├── pddl_core/
│   │   ├── domain.py       # PDDL Domain parser (types, predicates, actions)
│   │   ├── nl_domain.py       # NL Domain parser (*new*)
│   │   └── instance.py     # PDDL Problem parser (initial state, goal, objects)
│   │   └── nl_instance.py     # NL Problem parser (initial state, goal, objects)
│   └── planner/
│       └── planner.py      # PDDL RegressionPlanner & PDDL FOLRegressionPlanner
│       └── nl_planner.py      # NL FOLRegressionPlanner (*new*)
│   └── llm/
│       └── llm.py          #Interface for entailment from both cache and LLM  (*new*)
├── test/
│   ├── alfworldtext.py # Example of alfworldtext problem with NL actions and goals
├── file/
│   ├── NL_actions.json # Contains examples of domains used in alfworldtext problem
│   ├── NL_goals.json  # Contains examples of problem used in alfworldtext problem
└── README.md               # This file
```

## Getting Started

1. Clone the repository:
2. Install dependencies:
   ```bash
   pip install -e .
   ```

## Usage

- **Run a NL Example**
  ```bash
  python pddl_planner/tests/alfworldtext.py
  ```

