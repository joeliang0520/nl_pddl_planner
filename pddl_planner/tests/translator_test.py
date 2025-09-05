from pddl_planner.llm.translator import (
    Action,
    ActionName,
    Effects,
    Predicate,
    Domain,
    Problem,
)


def test_serialization_helpers():
    empty = Predicate(text="the hand is empty")
    hold_pred = Predicate(text="holding ?o", arguments={"?o": "block"})
    action = Action(
        name="Pickup",
        action_name=ActionName(text="pick up ?o", arguments={"?o": "block"}),
        parameters={"?o": "block"},
        preconditions=[empty],
        effects=Effects(Positive=[hold_pred], Negative=[empty]),
    )

    domain = Domain(predicates=[empty, hold_pred], actions=[action])
    problem = Problem(initial_state=[empty], goal_state=[hold_pred])

    domain_json = [{"Predicate": [p.to_list() for p in domain.predicates]}]
    domain_json.extend([a.to_dict() for a in domain.actions])
    problem_json = [
        [p.to_list() for p in problem.initial_state],
        [p.to_list() for p in problem.goal_state],
    ]

    assert domain_json[0]["Predicate"][0][0] == "the hand is empty"
    assert domain_json[1]["Action"] == "Pickup"
    assert problem_json[1][0][0] == "holding ?o"


def test_predicate_and_actionname_coercion():
    pred = Predicate.model_validate(["block ?b is clear", ["?b"]])
    assert pred.arguments == {"?b": "object"}

    name = ActionName.model_validate("pickup ?b")
    assert name.text == "pickup ?b" and name.arguments == {}

    action = Action.model_validate(
        {
            "Action": "Pickup",
            "Action name": "pickup ?b",
            "Parameters": ["?b"],
            "Preconditions": [["the hand is empty", []]],
            "Effects": {"Positive": [["holding ?b", ["?b"]]], "Negative": []},
        }
    )
    assert action.parameters == {"?b": "object"}
