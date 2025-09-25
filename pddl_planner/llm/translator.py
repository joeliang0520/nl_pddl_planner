from __future__ import annotations

"""Utilities for translating natural language planning descriptions into NL-PDDL JSON.

The module defines Pydantic models mirroring the NL-PDDL data structures and a helper
function that uses the OpenAI Responses API to obtain structured output. The returned
objects can be serialized into the JSON layout expected by the planner's NL parsers.
"""

from typing import Dict, List, Optional

import json

from openai import OpenAI
from pydantic import (
    BaseModel,
    Field,
    ConfigDict,
    model_validator,
    field_validator,
)


class Predicate(BaseModel):
    """Natural language predicate schema."""

    text: str = Field(
        ..., description="Predicate description, e.g. 'the hand is empty'"
    )
    arguments: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping from variable names (e.g. '?x') to their types",
    )

    @model_validator(mode="before")
    @classmethod
    def _coerce_from_list(cls, data):
        """Allow `[text, args]` list format used in some LLM outputs."""
        if isinstance(data, list):
            text = data[0]
            args = data[1] if len(data) > 1 else {}
            return {"text": text, "arguments": args}
        return data

    @field_validator("arguments", mode="before")
    @classmethod
    def _args_from_list(cls, v):
        if isinstance(v, list):
            return {name: "object" for name in v}
        return v

    def to_list(self) -> List[object]:
        """Serialize to the `[text, {args}]` layout used in NL-PDDL files."""

        return [self.text, self.arguments]


class ActionName(BaseModel):
    """Natural language name for an action."""

    text: str = Field(
        ..., description="Action description with variables, e.g. 'pick up ?o'"
    )
    arguments: Dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def _from_primitive(cls, data):
        """Support either "action name" string or `[text, args]` list."""
        if isinstance(data, str):
            return {"text": data, "arguments": {}}
        if isinstance(data, list):
            text = data[0]
            args = data[1] if len(data) > 1 else {}
            return {"text": text, "arguments": args}
        return data

    @field_validator("arguments", mode="before")
    @classmethod
    def _args_from_list(cls, v):
        if isinstance(v, list):
            return {name: "object" for name in v}
        return v

    def to_list(self) -> List[object]:
        return [self.text, self.arguments]


class Effects(BaseModel):
    """Positive and negative effects of an action."""

    Positive: List[Predicate] = Field(default_factory=list)
    Negative: List[Predicate] = Field(default_factory=list)


class Action(BaseModel):
    """Action schema in NL-PDDL."""

    name: str = Field(..., alias="Action")
    action_name: ActionName = Field(..., alias="Action name")
    parameters: Dict[str, str] = Field(default_factory=dict, alias="Parameters")
    preconditions: List[Predicate] = Field(default_factory=list, alias="Preconditions")
    effects: Effects = Field(default_factory=Effects, alias="Effects")

    model_config = ConfigDict(populate_by_name=True)

    @field_validator("parameters", mode="before")
    @classmethod
    def _params_from_list(cls, v):
        if isinstance(v, list):
            return {name: "object" for name in v}
        return v

    def to_dict(self) -> Dict[str, object]:
        """Serialize to the NL-PDDL action dictionary format."""

        return {
            "Action": self.name,
            "Action name": self.action_name.to_list(),
            "Parameters": self.parameters,
            "Preconditions": [p.to_list() for p in self.preconditions],
            "Effects": {
                "Positive": [p.to_list() for p in self.effects.Positive],
                "Negative": [p.to_list() for p in self.effects.Negative],
            },
        }


class Domain(BaseModel):
    """NL-PDDL domain consisting of predicate and action schemas."""

    predicates: List[Predicate]
    actions: List[Action]


class Problem(BaseModel):
    """NL-PDDL problem consisting of initial and goal states."""

    initial_state: List[Predicate] = Field(alias="initial_state")
    goal_state: List[Predicate] = Field(alias="goal_state")

    model_config = ConfigDict(populate_by_name=True)


class TranslationOutput(BaseModel):
    """Combined domain and problem returned by the translator."""

    domain: Domain
    problem: Problem


def translate_to_nlpddl(
    description: str,
    model: str,
    api_key: Optional[str] = None,
) -> TranslationOutput:
    """Translate a natural language planning description to NL-PDDL structures.

    Parameters
    ----------
    description:
        The raw natural language description provided by the user.
    model:
        The OpenAI model name to use.
    api_key:
        Optional API key. If ``None`` the library relies on environment variables.

    Returns
    -------
    TranslationOutput
        Object containing the domain and problem models.
    """

    client = OpenAI(api_key=api_key)
    
    # Enhanced system prompt with clearer examples
    system_prompt = (
        "You are a translator that converts natural language planning descriptions "
        "into NL-PDDL JSON. Follow these critical rules:\n\n"
        "DOMAIN RULES:\n"
        "1. Domain predicates must use VARIABLES (e.g., ?b, ?x, ?b1, ?b2) not constants\n"
        "2. Action parameters must also use VARIABLES\n"
        "3. Preconditions and effects in actions must reference the action's parameters\n\n"
        "PROBLEM RULES:\n"
        "1. Problem predicates use CONSTANTS (e.g., 'red', 'blue', 'orange') not variables\n"
        "2. Initial state and goal state use specific object names from the problem\n"
        "3. Arguments dict maps constant names to 'object'\n\n"
        "CORRECT DOMAIN EXAMPLE:\n"
        '{"predicates": [\n'
        '  {"text": "the block is clear", "arguments": {"?b": "block"}},\n'
        '  {"text": "the hand is empty", "arguments": {}},\n'
        '  {"text": "?b1 is on top of ?b2", "arguments": {"?b1": "block", "?b2": "block"}}\n'
        '],\n'
        '"actions": [{\n'
        '  "Action": "pick_up",\n'
        '  "Action name": {"text": "pick up ?b", "arguments": {"?b": "block"}},\n'
        '  "Parameters": {"?b": "block"},\n'
        '  "Preconditions": [\n'
        '    {"text": "the hand is empty", "arguments": {}},\n'
        '    {"text": "?b is clear", "arguments": {"?b": "block"}}\n'
        '  ],\n'
        '  "Effects": {\n'
        '    "Positive": [{"text": "holding ?b", "arguments": {"?b": "block"}}],\n'
        '    "Negative": [{"text": "the hand is empty", "arguments": {}}]\n'
        '  }\n'
        '}]}\n\n'
        "CORRECT PROBLEM EXAMPLE:\n"
        '{"initial_state": [\n'
        '  {"text": "red is clear", "arguments": {"red": "object"}},\n'
        '  {"text": "blue is on top of orange", "arguments": {"blue": "object", "orange": "object"}}\n'
        '],\n'
        '"goal_state": [\n'
        '  {"text": "orange is on top of red", "arguments": {"orange": "object", "red": "object"}}\n'
        ']}\n\n'
        "Return JSON conforming to the provided schema."
    )

    # More explicit domain instruction
    domain_prompt = (
        "Extract the DOMAIN from this description. The domain defines:\n"
        "1. PREDICATES: General properties/relations using variables IN THE TEXT (e.g., '?b is clear', '?b1 is on top of ?b2')\n"
        "2. ACTIONS: Operations with parameters, preconditions, and effects\n\n"
        "IMPORTANT:\n"
        "- Use variables like ?b, ?b1, ?b2 IN THE PREDICATE TEXT ITSELF\n"
        "- All types should be 'object' (not 'block', 'robot', etc.)\n"
        "- Do NOT use specific colors (red, blue, etc.) in the domain - those belong in the problem\n\n"
        "Description:\n" + description
    )

    # ---- first call: domain ----
    domain_schema = Domain.model_json_schema(by_alias=True)
    domain_completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": domain_prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "Domain", "schema": domain_schema},
        },
        temperature=0,
    )
    domain_dict = json.loads(domain_completion.choices[0].message.content)
    domain = Domain.model_validate(domain_dict)

    # More explicit problem instruction
    problem_prompt = (
        "Using the domain below, extract the PROBLEM from the description.\n"
        "The problem specifies:\n"
        "1. INITIAL STATE: Current facts using specific object names (red, blue, etc.)\n"
        "2. GOAL STATE: Desired facts using specific object names\n\n"
        "Replace variables from domain predicates with actual object names.\n"
        "Example: domain predicate '?b is clear' becomes 'red is clear' in the problem.\n\n"
        "Domain:\n" + json.dumps(domain_dict, indent=2) +
        "\n\nOriginal description:\n" + description
    )

    # ---- second call: problem ----
    problem_schema = Problem.model_json_schema(by_alias=True)
    problem_completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": problem_prompt},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "Problem", "schema": problem_schema},
        },
        temperature=0,
    )
    problem_dict = json.loads(problem_completion.choices[0].message.content)
    problem = Problem.model_validate(problem_dict)

    # Post-process: ensure problem uses constants properly
    def _normalize_arguments(preds: List[Predicate]) -> None:
        for pred in preds:
            new_args: Dict[str, str] = {}
            for name, value in pred.arguments.items():
                # Remove any lingering variable markers
                clean_name = name.lstrip('?')
                new_args[clean_name] = "object"
            pred.arguments = new_args

    _normalize_arguments(problem.initial_state)
    _normalize_arguments(problem.goal_state)

    return TranslationOutput(domain=domain, problem=problem)


def goals_to_json(problems: Problem | List[Problem]) -> List[List[List[object]]]:
    """Serialize one or more problems into the goals-only JSON layout.

    Parameters
    ----------
    problems:
        A single :class:`Problem` instance or a list of problems.

    Returns
    -------
    list
        A JSON-ready list where each element corresponds to a goal set and is
        represented as a list of predicate instances in ``[text, {args}]``
        format.
    """

    if isinstance(problems, Problem):
        problems = [problems]

    goal_sets: List[List[List[object]]] = []
    for pr in problems:
        goal_sets.append([p.to_list() for p in pr.goal_state])
    return goal_sets
