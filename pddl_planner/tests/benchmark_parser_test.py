from pddl_planner.llm.benchmark_parser import extract_problem_descriptions


def test_extract_problem_descriptions():
    query = (
        "Intro text about domain\n"
        "[STATEMENT] As initial conditions I have A. My goal is B.\n"
        "[PLAN]\nact1\n[PLAN END]\n"
        "[STATEMENT] As initial conditions I have C. My goal is D.\n"
        "[PLAN]"
    )
    descs = extract_problem_descriptions(query, num_examples=1)
    assert len(descs) == 1
    assert "Intro text about domain" in descs[0]
    assert "initial conditions I have C" in descs[0]
    assert "My goal is D" in descs[0]
