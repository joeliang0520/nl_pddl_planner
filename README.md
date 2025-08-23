# NL-PDDL Planner

A planner implemented in Python that thats Natural Languages (NL) predicates from the actions and goals as inputs and introduces a First‑Order Logic (FOL) Regression planner grounded in SSA from Situation Calculus, provides sample PDDL domains for testing, and includes scripts to run the FOL regression planner on different domains.

This repository includes:

- A **Parser** for NL domains and problems.
- **NL Planning algorithms**: FOL (First-Order Logic) Regression planners that can handles Natural Language entailments from NL predicates in problem to the domain predicates.
- **LLM Entailment** Using LLM to check if two predicates entails each others even if the name of the predicate is different.
- **Logic utilities**: NL Formula manipulation, unification, substitution.
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
│   │   ├── nl_formula.py      # Formula classes (Predicate) with additional field for NL representation
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


## Structure of NL Domain and Goal Files

We currently support a fixed JSON format for NL domain and goal files. See examples in `files/alfworldtext_domain.json` and `files/alfworldtext_goal.json`.

---

🗂 Domain File (*_domain.json)

The domain file is a JSON array:
	1.	First element: Predicates
	2.	Subsequent elements: Actions

Predicates block
```json
{
  "Predicate": [
    ["the agent's hand is empty", {}],
    ["the agent is holding ?o", {"?o": "object"}],
    ["?o is in ?r", {"?o": "object", "?r": "object"}]
  ]
}
```

Action block
```json
{
  "Action": "PutIn",
  "Action name": ["put ?o into ?r", {"?o": "object", "?r": "object"}],
  "Parameters": {"?o": "object", "?r": "object"},
  "Preconditions": [
    ["the agent is holding ?o", {"?o": "object"}]
  ],
  "Effects": {
    "Positive": [
      ["?o is in ?r", {"?o": "object", "?r": "object"}],
      ["the agent's hand is empty", {}]
    ],
    "Negative": [
      ["the agent is holding ?o", {"?o": "object"}]
    ]
  }
}
```

---

🎯 Goal File (*_goal.json)

The goal file is a JSON array of goal sets.
Each goal set is a list of predicate instances that must hold at the end.
```json
[
  [
    ["the agent's hand is empty", {}],
    ["goal_obj is a tomato", {"goal_obj": "object"}],
    ["goal_recep is a fridge", {"goal_recep": "object"}],
    ["goal_obj is inside goal_recep", {"goal_obj": "object", "goal_recep": "object"}]
  ]
]
```

---

✅ Conventions
	•	Variables start with ? (e.g., `?o`, `?r`).
	•	Types are strings (e.g., "`object").
	•	Exact string match is required across predicates, actions, and goals.
	•	Effects are split into "Positive" (add) and "Negative" (delete).

---


## Example of LLM entailment:
### Example 1: goal: goal_obj is inside goal_recep |- action: ?o is in ?r

fail to find the ssa node for the predicate, attempting to entail the "goal_obj is inside goal_recep" as a domain predicate

[Warning] fail to find the predicate "goal_obj is inside goal_recep" in the cache, checking via LLM

[Success] Existing substitution: {?o: goal_recep, ?r: goal_obj} between "goal_obj is inside goal_recep" and "?r can contain ?o"

[LLM Response] predicate "goal_obj is inside goal_recep" is entailed by "goal_obj can contain goal_recep" ?:  NO

[Success] Existing substitution: {?r: goal_recep, ?o: goal_obj} between "goal_obj is inside goal_recep" and "?o is in ?r"

[LLM Response] predicate "goal_obj is inside goal_recep" is entailed by "goal_obj is in goal_recep" ?:  YES

[Success] Predicate goal_obj is inside goal_recep is entailed by is in from LLM

---
### Example 2: goal_recep is a fridge |- action: ?r is a cooling device

fail to find the ssa node for the predicate, attempting to entail the "goal_recep is a fridge" as a domain predicate

[Warning] fail to find the predicate "goal_recep is a fridge" in the cache, checking via LLM

[Success] Existing substitution: {?o: goal_recep} between "goal_recep is a fridge" and "the agent is holding ?o"

[LLM Response] predicate "goal_recep is a fridge" is entailed by "the agent is holding goal_recep" ?:  NO

[Success] Existing substitution: {?r: goal_recep} between "goal_recep is a fridge" and "?r is a heating device"

[LLM Response] predicate "goal_recep is a fridge" is entailed by "goal_recep is a heating device" ?:  NO

[Success] Existing substitution: {?o: goal_recep} between "goal_recep is a fridge" and "?o is hot"

[LLM Response] predicate "goal_recep is a fridge" is entailed by "goal_recep is hot" ?:  NO

[Success] Existing substitution: {?r: goal_recep} between "goal_recep is a fridge" and "?r is a cleaning device"

[LLM Response] predicate "goal_recep is a fridge" is entailed by "goal_recep is a cleaning device" ?:  NO

[Success] Existing substitution: {?o: goal_recep} between "goal_recep is a fridge" and "?o is clean"

[LLM Response] predicate "goal_recep is a fridge" is entailed by "goal_recep is clean" ?:  NO

[Success] Existing substitution: {?r: goal_recep} between "goal_recep is a fridge" and "?r is a cooling device"

[LLM Response] predicate "goal_recep is a fridge" is entailed by "goal_recep is a cooling device" ?:  YES

[Success] Predicate goal_recep is a fridge is entailed by is a cooling device from LLM