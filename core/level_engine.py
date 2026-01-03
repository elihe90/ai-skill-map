from typing import Any, Dict, Optional


def compute_learning_level(scores: Dict[str, Any]) -> float:
    """Average of learning, planning, ai_mindset (missing -> 0)."""
    values = [
        _score(scores, "learning"),
        _score(scores, "planning"),
        _score(scores, "ai_mindset"),
    ]
    return sum(values) / 3.0


def compute_execution_level(scores: Dict[str, Any]) -> float:
    """Average of execution, problem_solving (missing -> 0)."""
    values = [
        _score(scores, "execution"),
        _score(scores, "problem_solving"),
    ]
    return sum(values) / 2.0


def level_from_value(v: float) -> str:
    if v <= 2.0:
        return "A"
    if v < 4.0:
        return "B"
    return "C"


def determine_levels(scores: Dict[str, Any], track: Optional[str] = None) -> Dict[str, Any]:
    learning_value = compute_learning_level(scores)
    execution_value = compute_execution_level(scores)

    training_level = level_from_value(learning_value)
    readiness_level = level_from_value(execution_value)
    note_fa = _default_note(learning_value, execution_value, track)

    if learning_value >= 4.0 and execution_value <= 2.0:
        training_level = "B"
        readiness_level = "A"
        note_fa = "ذهنیت و یادگیری خوب است اما اجرای عملی نیاز به تقویت دارد."

    return {
        "learning_value": learning_value,
        "execution_value": execution_value,
        "training_level": training_level,
        "readiness_level": readiness_level,
        "note_fa": note_fa,
    }


def _score(scores: Dict[str, Any], key: str) -> float:
    try:
        return float(scores.get(key, 0))
    except (TypeError, ValueError):
        return 0.0


def _default_note(learning_value: float, execution_value: float, track: Optional[str]) -> str:
    if learning_value >= execution_value + 1.0:
        return "پتانسیل یادگیری بالاست اما تمرین عملی بیشتری لازم است."
    if execution_value >= learning_value + 1.0:
        return "اجرای عملی خوب است اما عمق یادگیری و برنامه‌ریزی نیاز به تقویت دارد."
    if track == "technical":
        return "تعادل خوبی دیده می‌شود؛ برای مسیر فنی، پروژه عملی کمک زیادی می‌کند."
    return "تعادل مناسبی بین یادگیری و اجرا دیده می‌شود."
