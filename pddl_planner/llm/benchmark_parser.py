from __future__ import annotations

"""Utilities for parsing NL benchmark JSON files into problem descriptions."""

from typing import List


def extract_problem_descriptions(query: str, num_examples: int) -> List[str]:
    """Extract natural language problems from a benchmark query string.

    The benchmark format interleaves a domain description with one or more
    ``[STATEMENT]`` sections, where the initial part is the domain description
    and the subsequent statements (after optional example statements) contain
    specific initial and goal conditions. Each problem statement may be
    followed by a ``[PLAN]`` section which is ignored.

    Parameters
    ----------
    query:
        Raw text from the benchmark's ``query`` field.
    num_examples:
        Number of leading ``[STATEMENT]`` sections that correspond to example
        problems. These are skipped in the output list.

    Returns
    -------
    List[str]
        A list where each entry is a natural language description composed of
        the domain description and one of the problem statements.
    """

    parts = query.split("[STATEMENT]")
    if len(parts) <= 1:
        return []

    domain = parts[0].strip()
    problem_sections = parts[1 + num_examples :]

    descriptions: List[str] = []
    for section in problem_sections:
        problem_text = section.split("[PLAN")[0].strip()
        if problem_text:
            descriptions.append(f"{domain}\n\n{problem_text}")
    return descriptions
