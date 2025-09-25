from pddl_planner.rule_based.translator import (
    BLOCKSWORLD_DOMAIN,
    convert_text_to_nlpddl,
    convert_text_to_nlpddl_instances,
)


def test_convert_text_to_nlpddl():
    text = (
        "[STATEMENT]\nAs initial conditions I have that, "
        "the red block is clear, the hand is empty, the red block is on the table.\n"
        "My goal is to have that the red block is on top of the blue block."
    )
    domain, problem = convert_text_to_nlpddl(text)
    assert domain.actions[0].name == "pick_up"
    assert problem.initial_state[0].text == "red is clear"
    assert problem.goal_state[0].text == "red is on top of blue"


def test_convert_multiple_problems():
    text = (
        "[STATEMENT]\nAs initial conditions I have that, "
        "the red block is clear, the hand is empty.\n"
        "My goal is to have that the red block is on the table.\n"
        "[STATEMENT]\nAs initial conditions I have that, "
        "the blue block is clear, the hand is empty.\n"
        "My goal is to have that the blue block is on the table."
    )
    domain, problems = convert_text_to_nlpddl_instances(text)
    assert len(problems) == 2
    assert problems[0].initial_state[0].text == "red is clear"
    assert problems[1].goal_state[0].text == "blue is on the table"
