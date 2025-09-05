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
    system_prompt = (
        "You are a translator that converts natural language planning descriptions into "
        "NL-PDDL JSON. Return an object with two fields: 'domain' and 'problem'. The "
        "domain has 'predicates' and 'actions'. Each predicate has 'text' and "
        "'arguments' (a mapping from variable names to types, default to 'object'). Each "
        "action has 'Action', 'Action name', 'Parameters', 'Preconditions', and 'Effects' "
        "with 'Positive' and 'Negative' predicates. The problem has 'initial_state' and "
        "'goal_state' lists of predicates. Use variable names prefixed with '?'. Only "
        "output JSON conforming to the provided schema."
    )

    schema = TranslationOutput.model_json_schema(by_alias=True)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": description},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "TranslationOutput", "schema": schema},
        },
        temperature=0,
    )

    response_dict = json.loads(completion.choices[0].message.content)
    return TranslationOutput.model_validate(response_dict)
