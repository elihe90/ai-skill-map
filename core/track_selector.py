from typing import Any, Dict


def select_track(goal: str, weekly_time: str, preference: str) -> Dict[str, Any]:
    """Select learning track from routing answers."""
    track = "automation"
    if preference == "تولید محتوا و شبکه‌های اجتماعی":
        track = "content"
    elif preference == "اتوماسیون و بهبود کارهای اداری/گزارش":
        track = "automation"
    elif preference == "کار فنی و کدنویسی/حل مسئله":
        track = "technical"

    needs_longer_plan = False
    if goal == "تغییر مسیر فنی" and _is_low_time(weekly_time):
        needs_longer_plan = True

    return {"track": track, "needs_longer_plan": needs_longer_plan}


def _is_low_time(weekly_time: str) -> bool:
    if not weekly_time:
        return False
    normalized = _normalize_digits(weekly_time)
    normalized = normalized.replace(" ", "").replace("?", "-").replace("?", "-")
    return "1-2" in normalized


def _normalize_digits(text: str) -> str:
    mapping = str.maketrans("????????????????????", "01234567890123456789")
    return text.translate(mapping)
