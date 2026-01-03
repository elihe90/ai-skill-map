from typing import Any, Dict, List, Optional

from .job_mapper import load_rules


DEFAULT_BY_LEVEL = {
    "A": ["3512100030", "3512100023", "4132300019", "2166100024", "2421200016", "1221100027"],
    "B": ["2511200021", "2511200020", "2511200005", "2511200003", "2421200016"],
    "C": ["2511200021", "2511200022", "2511200005", "2511200004", "2511200020"],
}


def recommend_courses(
    training_level: str,
    interview_scores: Dict[str, Any],
    profile: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """Return a simple list of recommended TVTO course codes for the given level."""
    rules = load_rules()
    catalog = rules.get("course_catalog", {})
    level = str(training_level).upper()

    base = DEFAULT_BY_LEVEL.get(level, DEFAULT_BY_LEVEL["A"])
    recommended = [code for code in base if code in catalog]

    if not recommended:
        allowed_rank = {"A": 1, "B": 2, "C": 3}.get(level, 1)
        sorted_codes = sorted(
            catalog.items(),
            key=lambda item: (
                {"A": 1, "B": 2, "C": 3}.get(item[1].get("level_hint", "C"), 3),
                item[0],
            ),
        )
        for code, meta in sorted_codes:
            rank = {"A": 1, "B": 2, "C": 3}.get(meta.get("level_hint", "C"), 3)
            if rank <= allowed_rank:
                recommended.append(code)
            if len(recommended) >= 5:
                break

    return _dedupe([str(code) for code in recommended])


def _dedupe(values: List[str]) -> List[str]:
    seen = set()
    output = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output
