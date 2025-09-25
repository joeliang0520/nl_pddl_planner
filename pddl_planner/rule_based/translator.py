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

_COLOR_RE = r"red|blue|yellow|orange|green|purple|black|white"


def _split_sections(text: str) -> Tuple[str, str]:
    parts = text.split("[STATEMENT]")
    last = parts[-1]
    if "[PLAN]" in last:
        last = last.split("[PLAN]", 1)[0]

    pattern = re.compile(
        r"As initial conditions I have that[:,]?\s*(.+?)\s*My goal is to have that\s*(.+)",
        re.DOTALL,
    )
    match = pattern.search(last)
    if not match:
        return "", ""
    init_text = match.group(1).strip().strip(".")
    goal_text = match.group(2).strip().strip(".")
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
            r"As initial conditions I have that[:,]?\s*(.+?)\s*My goal is to have that\s*(.+)",
            re.DOTALL,
        )
        match = pattern.search(block)
        if not match:
            continue
        init_text = match.group(1).strip().strip(".")
        goal_text = match.group(2).strip().strip(".")
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


def _parse_state(text: str) -> List[Predicate]:
    text = text.replace(" and ", ", ")
    clauses = [c.strip() for c in text.split(",") if c.strip()]
    return [_parse_clause(c) for c in clauses]


def convert_text_to_nlpddl(text: str) -> Tuple[Domain, Problem]:
    init_text, goal_text = _split_sections(text)
    initial = _parse_state(init_text)
    goal = _parse_state(goal_text)
    problem = Problem(initial_state=initial, goal_state=goal)
    return BLOCKSWORLD_DOMAIN, problem


def convert_text_to_nlpddl_instances(text: str) -> Tuple[Domain, List[Problem]]:
    sections = _split_all_sections(text)
    problems: List[Problem] = []
    if sections:
        init_text, goal_text = sections[-1]
        initial = _parse_state(init_text)
        goal = _parse_state(goal_text)
        problems.append(Problem(initial_state=initial, goal_state=goal))
    return BLOCKSWORLD_DOMAIN, problems