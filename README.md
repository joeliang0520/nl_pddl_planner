# NL-PDDL Planner

NL-PDDL Planner is a Python implementation of a regression-based planner that operates directly on natural language (NL) predicates. It integrates First-Order Logic (FOL) regression with successor state axioms (SSA) from Situation Calculus, and provides PDDL-style domain and problem representations for testing.

Features
- NL Parser – processes NL domain and problem descriptions into a logic formula
- Maintaining Core PDDL Structures – representations for domain and problem instances.
- Planning Algorithms – FOL regression planners for the Open World Planning Task.
- LLM Entailment – leverages large language models to detect predicate entailment between goal and domain entailments, even when predicate names differ.
- Logic Utilities – functions for formula manipulation, unification, and substitution.

Scripts are included to run the regression planner on a variety of domains.


## Table of Contents

- [Directory Structure](#directory-structure)
- [Getting Started](#getting-started)
- [Usage](#usage)

## Directory Structure

```
pddl_solver/
├── pddl_planner/                  # Core planning package
│   ├── logic/
│   │   ├── parser.py       	     # PDDL→logic parser
│   │   ├── nl_parser.py    	     # NL→logic parser
│   │   ├── formula.py             # Formula classes (Conjunctive, Disjunctive, Predicate, Equality), main file for logic
│   │   ├── nl_formula.py    	     # Formula classes (Predicate) with additional field for NL representation and functions to handle logic operation with NL
│   │   └── operation.py    	     # Unification & standardization operations
│   ├── pddl_core/
│   │   ├── domain.py       	     # PDDL Domain parser (types, predicates, actions)
│   │   ├── nl_domain.py    	     # NL Domain parser 
│   │   └── instance.py            # PDDL Problem parser (initial state, goal, objects)
│   │   └── nl_instance.py    	   # NL Problem parser (initial state, goal, objects)
│   └── planner/
│       └── planner.py             # PDDL RegressionPlanner & PDDL FOLRegressionPlanner
│       └── nl_planner.py    	     # NL FOLRegressionPlanner
│   └── llm/
│       └── llm.py    	           # Interface for entailment from both cache and LLM
│       └── llm_with_type.py       # Interface for entailment from both cache and LLM with Type Check
├── test/
│   ├── alfworld_text_with_misalignment.py    # Test script for ALFWorld Text with misalignment dataset
│   ├── alfworld_text.py    # Test script for ALFWorld Text dataset
│   ├── blockworld.py       # Test script for Blockworld Dataset
│   ├── misalignment_blockworld.py # Test script for Misalignment Blockworld Dataset
├── file/
│   ├── alfworld_text_with_misalignment
│   │   ├── alfworld_text_with_misalignment_model.json
│   │   ├── alfworld_text_with_misalignment_goal.json
│   ├──blockworld
│   │   ├── blockworld_model.json
│   │   ├── blockworld_goal.json
│   ├──misalignment_blockworld
│   │   ├── misalignment_blockworld_model.json
│   │   ├── blockworld_goal.json       
└── README.md               	   # This file
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


## Example of self-consistent LLM entailment:
### Example 1: goal: goal_obj is inside goal_recep |- action: ?o is in ?r

### Predicate Entailment Handling

If a predicate cannot be found in the **domain predicates**, the `llm.llm.entailment` function is invoked.  
This function attempts to determine whether the new predicate in the goal can be logically entailed by any domain predicate.  

The process works as follows:
1. Extract all domain predicates from the actions.
2. Apply substitutions on constant terms appearing in the goal.
3. Check possible entailments with each domain predicate.
4. Retrieve all predicates that are entailed.

---

#### Example (Verbose Log)

Below is the printed log from the `llm.llm.entailment('is inside')` function with `verbose=True` enabled:



```{text}
Failing to find "is inside" in domain predicates, attempting to entail it to a domain predicate

[Info] Checking entailment via cache/LLM for "goal_obj is inside goal_recep"

[Substitution] Existing substitution: {?o: goal_recep, ?r: goal_obj} between "is inside(goal_obj, goal_recep)" and "can contain(?r, ?o)"

[LLM Response] is goal_obj is inside goal_recep entailed by goal_obj can contain goal_recep ?: [False, Trure, False]

[Substitution] Existing substitution: {?r: goal_recep, ?o: goal_obj} between "is inside(goal_obj, goal_recep)" and "is in(?o, ?r)"

[LLM Response] is goal_obj is inside goal_recep entailed by goal_obj is in goal_recep ?: [True, True, True]

[Success] Predicate is inside(goal_obj, goal_recep) is entailed by is in from LLM
```

In this example, `goal_obj is inside goal_recep` only exists in the goal predicate, not the domain predicate. And it was successfully entailed by the `goal_obj is in goal_recep` predicates in Domains with three rounds of LLM entailments for self-consistency
