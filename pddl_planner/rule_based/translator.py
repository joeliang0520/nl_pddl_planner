from __future__ import annotations

"""Rule-based translation of Blocksworld text to NL-PDDL structures."""

import re
from typing import List, Tuple

from pddl_planner.llm.translator import (
    Action,
    ActionName,
    Domain,
    Effects,
    Predicate,
    Problem,
)

BLOCKSWORLD_DOMAIN = Domain(
    predicates=[
        Predicate(text="the hand is empty"),
        Predicate(text="?b is clear", arguments={"?b": "object"}),
        Predicate(text="?b is on the table", arguments={"?b": "object"}),
        Predicate(
            text="?b1 is on top of ?b2",
            arguments={"?b1": "object", "?b2": "object"},
        ),
        Predicate(text="I am holding ?b", arguments={"?b": "object"}),
    ],
    actions=[
        Action(
            name="pick_up",
            action_name=ActionName(text="pick up ?b", arguments={"?b": "object"}),
            parameters={"?b": "object"},
            preconditions=[
                Predicate(text="the hand is empty"),
                Predicate(text="?b is clear", arguments={"?b": "object"}),
                Predicate(text="?b is on the table", arguments={"?b": "object"}),
            ],
            effects=Effects(
                Positive=[Predicate(text="I am holding ?b", arguments={"?b": "object"})],
                Negative=[
                    Predicate(text="the hand is empty"),
                    Predicate(text="?b is clear", arguments={"?b": "object"}),
                    Predicate(text="?b is on the table", arguments={"?b": "object"}),
                ],
            ),
        ),
        Action(
            name="put_down",
            action_name=ActionName(text="put down ?b", arguments={"?b": "object"}),
            parameters={"?b": "object"},
            preconditions=[Predicate(text="I am holding ?b", arguments={"?b": "object"})],
            effects=Effects(
                Positive=[
                    Predicate(text="the hand is empty"),
                    Predicate(text="?b is on the table", arguments={"?b": "object"}),
                    Predicate(text="?b is clear", arguments={"?b": "object"}),
                ],
                Negative=[Predicate(text="I am holding ?b", arguments={"?b": "object"})],
            ),
        ),
        Action(
            name="stack",
            action_name=ActionName(
                text="stack ?b1 on top of ?b2",
                arguments={"?b1": "object", "?b2": "object"},
            ),
            parameters={"?b1": "object", "?b2": "object"},
            preconditions=[
                Predicate(text="I am holding ?b1", arguments={"?b1": "object"}),
                Predicate(text="?b2 is clear", arguments={"?b2": "object"}),
            ],
            effects=Effects(
                Positive=[
                    Predicate(
                        text="?b1 is on top of ?b2",
                        arguments={"?b1": "object", "?b2": "object"},
                    ),
                    Predicate(text="the hand is empty"),
                    Predicate(text="?b1 is clear", arguments={"?b1": "object"}),
                ],
                Negative=[
                    Predicate(text="I am holding ?b1", arguments={"?b1": "object"}),
                    Predicate(text="?b2 is clear", arguments={"?b2": "object"}),
                    Predicate(text="?b1 is on the table", arguments={"?b1": "object"}),
                ],
            ),
        ),
        Action(
            name="unstack",
            action_name=ActionName(
                text="unstack ?b1 from ?b2",
                arguments={"?b1": "object", "?b2": "object"},
            ),
            parameters={"?b1": "object", "?b2": "object"},
            preconditions=[
                Predicate(text="the hand is empty"),
                Predicate(
                    text="?b1 is on top of ?b2",
                    arguments={"?b1": "object", "?b2": "object"},
                ),
                Predicate(text="?b1 is clear", arguments={"?b1": "object"}),
            ],
            effects=Effects(
                Positive=[
                    Predicate(text="I am holding ?b1", arguments={"?b1": "object"}),
                    Predicate(text="?b2 is clear", arguments={"?b2": "object"}),
                ],
                Negative=[
                    Predicate(text="the hand is empty"),
                    Predicate(
                        text="?b1 is on top of ?b2",
                        arguments={"?b1": "object", "?b2": "object"},
                    ),
                ],
            ),
        ),
    ],
)
MYSTERY_DOMAIN = Domain(
    predicates=[
        # Facts used by the rules / states
        Predicate(text="Harmony"),
        Predicate(text="Province ?o", arguments={"?o": "object"}),
        Predicate(text="Planet ?o", arguments={"?o": "object"}),
        Predicate(text="Pain ?o", arguments={"?o": "object"}),
        Predicate(text="?x craves ?y", arguments={"?x": "object", "?y": "object"}),
    ],
    actions=[
        # Attack o
        Action(
            name="attack",
            action_name=ActionName(text="attack object ?o", arguments={"?o": "object"}),
            parameters={"?o": "object"},
            preconditions=[
                Predicate(text="Province ?o", arguments={"?o": "object"}),
                Predicate(text="Planet ?o", arguments={"?o": "object"}),
                Predicate(text="Harmony"),
            ],
            effects=Effects(
                Positive=[Predicate(text="Pain ?o", arguments={"?o": "object"})],
                Negative=[
                    Predicate(text="Province ?o", arguments={"?o": "object"}),
                    Predicate(text="Planet ?o", arguments={"?o": "object"}),
                    Predicate(text="Harmony"),
                ],
            ),
        ),
        # Succumb o
        Action(
            name="succumb",
            action_name=ActionName(text="succumb object ?o", arguments={"?o": "object"}),
            parameters={"?o": "object"},
            preconditions=[Predicate(text="Pain ?o", arguments={"?o": "object"})],
            effects=Effects(
                Positive=[
                    Predicate(text="Province ?o", arguments={"?o": "object"}),
                    Predicate(text="Planet ?o", arguments={"?o": "object"}),
                    Predicate(text="Harmony"),
                ],
                Negative=[Predicate(text="Pain ?o", arguments={"?o": "object"})],
            ),
        ),
        # Overcome x from y
        Action(
            name="overcome",
            action_name=ActionName(
                text="overcome object ?x from object ?y",
                arguments={"?x": "object", "?y": "object"},
            ),
            parameters={"?x": "object", "?y": "object"},
            preconditions=[
                # "Province other object" => Province ?y
                Predicate(text="Province ?y", arguments={"?y": "object"}),
                # "Pain object" => Pain ?x
                Predicate(text="Pain ?x", arguments={"?x": "object"}),
            ],
            effects=Effects(
                Positive=[
                    Predicate(text="Harmony"),
                    Predicate(text="Province ?x", arguments={"?x": "object"}),
                    # "Object Craves other object" => ?x craves ?y
                    Predicate(text="?x craves ?y", arguments={"?x": "object", "?y": "object"}),
                ],
                Negative=[
                    Predicate(text="Province ?y", arguments={"?y": "object"}),
                    Predicate(text="Pain ?x", arguments={"?x": "object"}),
                ],
            ),
        ),
        # Feast x from y
        Action(
            name="feast",
            action_name=ActionName(
                text="feast object ?x from object ?y",
                arguments={"?x": "object", "?y": "object"},
            ),
            parameters={"?x": "object", "?y": "object"},
            preconditions=[
                Predicate(text="?x craves ?y", arguments={"?x": "object", "?y": "object"}),
                Predicate(text="Province ?x", arguments={"?x": "object"}),
                Predicate(text="Harmony"),
            ],
            effects=Effects(
                Positive=[
                    Predicate(text="Pain ?x", arguments={"?x": "object"}),
                    # "Province other object" => Province ?y
                    Predicate(text="Province ?y", arguments={"?y": "object"}),
                ],
                Negative=[
                    Predicate(text="?x craves ?y", arguments={"?x": "object", "?y": "object"}),
                    Predicate(text="Province ?x", arguments={"?x": "object"}),
                    Predicate(text="Harmony"),
                ],
            ),
        ),
    ],
)
_COLOR_RE = r"red|blue|yellow|orange|green|purple|black|white"
_OBJ_RE = r"[a-z][a-z0-9_]*"
_GOAL_LEADIN_RE = r"(?:\s*(?:to have that|for the following to be true:))?"
_GOAL_STOP_RE   = r"(?=\s*(?:my plan is|return only the sequence of actions|\[plan\]|\[plan end\]|$))"


def _split_sections(text: str) -> Tuple[str, str]:
    parts = text.split("[STATEMENT]")
    last = parts[-1]
    # Trim at [PLAN] if present (helps when the boilerplate is present)
    if "[PLAN]" in last:
        last = last.split("[PLAN]", 1)[0]

    pattern = re.compile(
        rf"As initial conditions I have that[:,]?\s*(.+?)\s*"
        rf"My goal is{_GOAL_LEADIN_RE}\s*(.+?){_GOAL_STOP_RE}",
        re.DOTALL | re.IGNORECASE,
    )
    m = pattern.search(last)
    if not m:
        return "", ""
    init_text = m.group(1).strip().strip(".")
    goal_text = m.group(2).strip().strip(".")
    return init_text, goal_text


def _split_all_sections(text: str) -> List[Tuple[str, str]]:
    sections: List[Tuple[str, str]] = []
    for block in text.split("[STATEMENT]"):
        block = block.strip()
        if not block:
            continue
        if "[PLAN]" in block:
            block = block.split("[PLAN]", 1)[0]
        pattern = re.compile(
            rf"As initial conditions I have that[:,]?\s*(.+?)\s*"
            rf"My goal is{_GOAL_LEADIN_RE}\s*(.+?){_GOAL_STOP_RE}",
            re.DOTALL | re.IGNORECASE,
        )
        m = pattern.search(block)
        if not m:
            continue
        init_text = m.group(1).strip().strip(".")
        goal_text = m.group(2).strip().strip(".")
        sections.append((init_text, goal_text))
    return sections


def _parse_clause(clause: str) -> Predicate:
    """Convert a single natural language clause into a Predicate."""

    clause = clause.strip().strip(".")
    lower = clause.lower()

    if lower == "the hand is empty":
        return Predicate(text="the hand is empty", arguments={})

    m = re.match(rf"the (?P<color>{_COLOR_RE}) block is clear", lower)
    if m:
        color = m.group("color")
        return Predicate(text=f"{color} is clear", arguments={color: "object"})

    m = re.match(
        rf"the (?P<c1>{_COLOR_RE}) block is on top of the (?P<c2>{_COLOR_RE}) block",
        lower,
    )
    if m:
        c1, c2 = m.group("c1"), m.group("c2")
        return Predicate(
            text=f"{c1} is on top of {c2}",
            arguments={c1: "object", c2: "object"},
        )

    m = re.match(rf"the (?P<color>{_COLOR_RE}) block is on the table", lower)
    if m:
        color = m.group("color")
        return Predicate(text=f"{color} is on the table", arguments={color: "object"})

    m = re.match(rf"i am holding the (?P<color>{_COLOR_RE}) block", lower)
    if m:
        color = m.group("color")
        return Predicate(text=f"I am holding {color}", arguments={color: "object"})

    raise ValueError(f"Unrecognized clause: {clause}")

def _parse_clause_mystery(clause: str) -> Predicate:
    """Convert a single natural-language clause into a Predicate (mystery variant)."""
    clause = clause.strip().strip(".")
    lower = clause.lower()

    # 0-ary proposition
    if lower in {"harmony"}:
        return Predicate(text="Harmony", arguments={})

    # Unary predicates
    m = re.match(rf"planet object (?P<o>{_OBJ_RE})$", lower)
    if m:
        o = m.group("o")
        return Predicate(text=f"Planet {o}", arguments={o: "object"})

    m = re.match(rf"province object (?P<o>{_OBJ_RE})$", lower)
    if m:
        o = m.group("o")
        return Predicate(text=f"Province {o}", arguments={o: "object"})

    m = re.match(rf"pain object (?P<o>{_OBJ_RE})$", lower)
    if m:
        o = m.group("o")
        return Predicate(text=f"Pain {o}", arguments={o: "object"})

    # Binary predicate
    m = re.match(rf"object (?P<x>{_OBJ_RE}) craves object (?P<y>{_OBJ_RE})$", lower)
    if m:
        x, y = m.group("x"), m.group("y")
        return Predicate(text=f"{x} craves {y}", arguments={x: "object", y: "object"})

    raise ValueError(f"Unrecognized clause: {clause}")

def _parse_clause_randomized(clause: str) -> Predicate:
    """Convert a single natural language clause into a Predicate."""

    clause = clause.strip().strip(".")
    lower = clause.lower()

    if lower == "the hand is empty":
        return Predicate(text="the hand is empty", arguments={})

    m = re.match(rf"the (?P<color>{_COLOR_RE}) block is clear", lower)
    if m:
        color = m.group("color")
        return Predicate(text=f"{color} is clear", arguments={color: "object"})

    m = re.match(
        rf"the (?P<c1>{_COLOR_RE}) block is on top of the (?P<c2>{_COLOR_RE}) block",
        lower,
    )
    if m:
        c1, c2 = m.group("c1"), m.group("c2")
        return Predicate(
            text=f"{c1} is on top of {c2}",
            arguments={c1: "object", c2: "object"},
        )

    m = re.match(rf"the (?P<color>{_COLOR_RE}) block is on the table", lower)
    if m:
        color = m.group("color")
        return Predicate(text=f"{color} is on the table", arguments={color: "object"})

    m = re.match(rf"i am holding the (?P<color>{_COLOR_RE}) block", lower)
    if m:
        color = m.group("color")
        return Predicate(text=f"I am holding {color}", arguments={color: "object"})

    raise ValueError(f"Unrecognized clause: {clause}")

def _parse_state(text: str) -> List[Predicate]:
    # Remove any trailing plan boilerplate if it leaked in
    text = re.split(r"(?is)\bmy plan is\b|\[plan(?: end)?\]", text)[0]
    text = re.sub(r"(?is)\breturn only the sequence of actions.*$", "", text)

    # Remove common goal lead-ins
    text = re.sub(r"^\s*(?:for the following to be true:|to have that)\s*", "", text, flags=re.IGNORECASE)

    # Canonicalize separators and split
    text = text.replace(" and ", ", ")
    clauses = [c.strip() for c in text.split(",") if c.strip()]

    return [_parse_clause_mystery(c) for c in clauses]


def convert_text_to_nlpddl(text: str) -> Tuple[Domain, Problem]:
    init_text, goal_text = _split_sections(text)
    initial = _parse_state(init_text)
    goal = _parse_state(goal_text)
    problem = Problem(initial_state=initial, goal_state=goal)
    return MYSTERY_DOMAIN, problem


def convert_text_to_nlpddl_instances(text: str) -> Tuple[Domain, List[Problem]]:
    sections = _split_all_sections(text)
    problems: List[Problem] = []
    if sections:
        init_text, goal_text = sections[-1]
        initial = _parse_state(init_text)
        goal = _parse_state(goal_text)
        problems.append(Problem(initial_state=initial, goal_state=goal))
    return MYSTERY_DOMAIN, problems