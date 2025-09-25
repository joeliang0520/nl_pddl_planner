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
RBW_CLEAR      = "aqcjuuehivl8auwt"
RBW_ONTABLE    = "51nbwlachmfartjn"
RBW_HANDEMPTY  = "3covmuy4yrjthijd"
RBW_ON_REL     = "4dmf1cmtyxgsp94g"
RBW_HOLDING    = "gk5asm3f7u1fekpj"

RBW_PICK_UP    = "1jpkithdyjmlikck"
RBW_PUT_DOWN   = "9big8ruzarkkquyu"
RBW_STACK      = "2ijg9q8swj2shjel"
RBW_UNSTACK    = "xptxjrdkbi3pqsqr"

RANDOM_DOMAIN = Domain(
    predicates=[
        Predicate(text=RBW_HANDEMPTY),  # 0-ary
        Predicate(text=f"{RBW_CLEAR} ?o",     arguments={"?o": "object"}),
        Predicate(text=f"{RBW_ONTABLE} ?o",   arguments={"?o": "object"}),
        Predicate(text=f"?x {RBW_ON_REL} ?y", arguments={"?x": "object", "?y": "object"}),
        Predicate(text=f"{RBW_HOLDING} ?o",   arguments={"?o": "object"}),
    ],
    actions=[
        # pick-up
        Action(
            name="pick_up",
            action_name=ActionName(text=f"{RBW_PICK_UP} object ?o", arguments={"?o": "object"}),
            parameters={"?o": "object"},
            preconditions=[
                Predicate(text=RBW_HANDEMPTY),
                Predicate(text=f"{RBW_CLEAR} ?o",   arguments={"?o": "object"}),
                Predicate(text=f"{RBW_ONTABLE} ?o", arguments={"?o": "object"}),
            ],
            effects=Effects(
                Positive=[Predicate(text=f"{RBW_HOLDING} ?o", arguments={"?o": "object"})],
                Negative=[
                    Predicate(text=RBW_HANDEMPTY),
                    Predicate(text=f"{RBW_CLEAR} ?o",   arguments={"?o": "object"}),
                    Predicate(text=f"{RBW_ONTABLE} ?o", arguments={"?o": "object"}),
                ],
            ),
        ),
        # put-down
        Action(
            name="put_down",
            action_name=ActionName(text=f"{RBW_PUT_DOWN} object ?o", arguments={"?o": "object"}),
            parameters={"?o": "object"},
            preconditions=[Predicate(text=f"{RBW_HOLDING} ?o", arguments={"?o": "object"})],
            effects=Effects(
                Positive=[
                    Predicate(text=RBW_HANDEMPTY),
                    Predicate(text=f"{RBW_ONTABLE} ?o", arguments={"?o": "object"}),
                    Predicate(text=f"{RBW_CLEAR} ?o",   arguments={"?o": "object"}),
                ],
                Negative=[Predicate(text=f"{RBW_HOLDING} ?o", arguments={"?o": "object"})],
            ),
        ),
        # stack ?x on ?y   (…object ?x from object ?y)
        Action(
            name="stack",
            action_name=ActionName(
                text=f"{RBW_STACK} object ?x from object ?y",
                arguments={"?x": "object", "?y": "object"},
            ),
            parameters={"?x": "object", "?y": "object"},
            preconditions=[
                Predicate(text=f"{RBW_HOLDING} ?x", arguments={"?x": "object"}),
                Predicate(text=f"{RBW_CLEAR} ?y",   arguments={"?y": "object"}),
            ],
            effects=Effects(
                Positive=[
                    Predicate(text=f"?x {RBW_ON_REL} ?y", arguments={"?x": "object", "?y": "object"}),
                    Predicate(text=RBW_HANDEMPTY),
                    Predicate(text=f"{RBW_CLEAR} ?x", arguments={"?x": "object"}),
                ],
                Negative=[
                    Predicate(text=f"{RBW_HOLDING} ?x",   arguments={"?x": "object"}),
                    Predicate(text=f"{RBW_CLEAR} ?y",     arguments={"?y": "object"}),
                    # standard BW semantics: once stacked, ?x is no longer on the table
                    Predicate(text=f"{RBW_ONTABLE} ?x",   arguments={"?x": "object"}),
                ],
            ),
        ),
        # unstack ?x from ?y  (…object ?x from object ?y)
        Action(
            name="unstack",
            action_name=ActionName(
                text=f"{RBW_UNSTACK} object ?x from object ?y",
                arguments={"?x": "object", "?y": "object"},
            ),
            parameters={"?x": "object", "?y": "object"},
            preconditions=[
                Predicate(text=RBW_HANDEMPTY),
                Predicate(text=f"?x {RBW_ON_REL} ?y", arguments={"?x": "object", "?y": "object"}),
                Predicate(text=f"{RBW_CLEAR} ?x",      arguments={"?x": "object"}),
            ],
            effects=Effects(
                Positive=[
                    Predicate(text=f"{RBW_HOLDING} ?x", arguments={"?x": "object"}),
                    Predicate(text=f"{RBW_CLEAR} ?y",   arguments={"?y": "object"}),
                ],
                Negative=[
                    Predicate(text=RBW_HANDEMPTY),
                    Predicate(text=f"?x {RBW_ON_REL} ?y", arguments={"?x": "object", "?y": "object"}),
                ],
            ),
        ),
    ],
)   

_OBJ_RE = r"[a-z][a-z0-9_]*"
_GOAL_LEADIN_RE = r"(?:\s*(?:to have that|for the following to be true:))?"
_GOAL_STOP_RE   = r"(?=\s*(?:my plan is|return only the sequence of actions|\[plan\]|\[plan end\]|$))"


def _split_sections(text: str) -> Tuple[str, str]:
    parts = text.split("[STATEMENT]")
    last = parts[-1]
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


def _parse_clause_random(clause: str) -> Predicate:
    """Parse one clause of the randomized Blocksworld."""
    clause = clause.strip().strip(".")
    lower = clause.lower()

    if lower == RBW_HANDEMPTY:
        return Predicate(text=RBW_HANDEMPTY, arguments={})

    m = re.match(rf"{RBW_CLEAR}\s+object\s+(?P<o>{_OBJ_RE})$", lower, flags=re.IGNORECASE)
    if m:
        o = m.group("o")
        return Predicate(text=f"{RBW_CLEAR} {o}", arguments={o: "object"})

    m = re.match(rf"{RBW_ONTABLE}\s+object\s+(?P<o>{_OBJ_RE})$", lower, flags=re.IGNORECASE)
    if m:
        o = m.group("o")
        return Predicate(text=f"{RBW_ONTABLE} {o}", arguments={o: "object"})

    m = re.match(rf"{RBW_HOLDING}\s+object\s+(?P<o>{_OBJ_RE})$", lower, flags=re.IGNORECASE)
    if m:
        o = m.group("o")
        return Predicate(text=f"{RBW_HOLDING} {o}", arguments={o: "object"})

    m = re.match(rf"object\s+(?P<x>{_OBJ_RE})\s+{RBW_ON_REL}\s+object\s+(?P<y>{_OBJ_RE})$", lower, flags=re.IGNORECASE)
    if m:
        x, y = m.group("x"), m.group("y")
        return Predicate(text=f"{x} {RBW_ON_REL} {y}", arguments={x: "object", y: "object"})

    raise ValueError(f"Unrecognized clause: {clause}")

def _parse_state(text: str) -> List[Predicate]:
    text = re.split(r"(?is)\bmy plan is\b|\[plan(?: end)?\]", text)[0]
    text = re.sub(r"(?is)\breturn only the sequence of actions.*$", "", text)
    text = re.sub(r"^\s*(?:for the following to be true:|to have that)\s*", "", text, flags=re.IGNORECASE)
    text = text.replace(" and ", ", ")
    clauses = [c.strip() for c in text.split(",") if c.strip()]
    return [_parse_clause_random(c) for c in clauses]


def convert_text_to_nlpddl(text: str) -> Tuple[Domain, Problem]:
    init_text, goal_text = _split_sections(text)
    initial = _parse_state(init_text)
    goal = _parse_state(goal_text)
    problem = Problem(initial_state=initial, goal_state=goal)
    return RANDOM_DOMAIN, problem


def convert_text_to_nlpddl_instances(text: str) -> Tuple[Domain, List[Problem]]:
    sections = _split_all_sections(text)
    problems: List[Problem] = []
    if sections:
        init_text, goal_text = sections[-1]
        initial = _parse_state(init_text)
        goal = _parse_state(goal_text)
        problems.append(Problem(initial_state=initial, goal_state=goal))
    return RANDOM_DOMAIN, problems