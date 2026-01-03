from typing import Any, Dict, List


LABELS_FA = {
    "A": "آموزش‌های عمومی و ابزارمحور",
    "B": "آموزش‌های نیمه‌تخصصی",
    "C": "آموزش‌های تخصصی",
}


def determine_training_level(profile: Dict[str, Any], interview_scores: Dict[str, Any]) -> Dict[str, Any]:
    """Determine training level based on profile and interview scores."""
    execution = _score(interview_scores, "execution")
    problem_solving = _score(interview_scores, "problem_solving")
    learning = _score(interview_scores, "learning")
    planning = _score(interview_scores, "planning")
    ai_mindset = _score(interview_scores, "ai_mindset")

    goal = str(profile.get("goal", "")).strip()
    digital_level = str(profile.get("digital_level", "")).strip()

    if (
        execution <= 2
        or problem_solving <= 2
        or ai_mindset <= 2
        or digital_level == "ضعیف"
    ):
        level = "A"
        reasons = _reasons_for_a(execution, problem_solving, ai_mindset, digital_level)
    elif learning >= 4 and problem_solving >= 4 and planning >= 3 and goal == "تغییر مسیر فنی":
        level = "C"
        reasons = _reasons_for_c(learning, problem_solving, planning, goal)
    else:
        level = "B"
        reasons = _reasons_for_b(goal)

    return {
        "training_level": level,
        "label_fa": LABELS_FA[level],
        "reason_fa": _ensure_reason_count(reasons),
    }


def _score(scores: Dict[str, Any], key: str) -> int:
    try:
        return int(scores.get(key, 0))
    except (TypeError, ValueError):
        return 0


def _reasons_for_a(execution: int, problem_solving: int, ai_mindset: int, digital_level: str) -> List[str]:
    reasons: List[str] = []
    if execution <= 2:
        reasons.append("نیاز به تقویت مهارت اجرا دیده می‌شود.")
    if problem_solving <= 2:
        reasons.append("مهارت حل مسئله نیاز به تقویت دارد.")
    if ai_mindset <= 2:
        reasons.append("ذهنیت AI برای شروع مسیر تخصصی کافی نیست.")
    if digital_level == "ضعیف":
        reasons.append("سطح دیجیتال پایین است و باید تقویت شود.")
    return reasons


def _reasons_for_c(learning: int, problem_solving: int, planning: int, goal: str) -> List[str]:
    reasons = [
        "توان یادگیری بالا ارزیابی شده است.",
        "حل مسئله و برنامه‌ریزی در سطح مناسبی قرار دارد.",
    ]
    if goal == "تغییر مسیر فنی":
        reasons.append("هدف شما با مسیر تخصصی همسو است.")
    if learning >= 4 and problem_solving >= 4 and planning >= 3:
        reasons.append("آمادگی برای ورود به آموزش تخصصی دیده می‌شود.")
    return reasons


def _reasons_for_b(goal: str) -> List[str]:
    reasons = [
        "سطح فعلی برای مسیر نیمه‌تخصصی مناسب است.",
        "برای رسیدن به تخصص کامل به تقویت چند مهارت نیاز دارید.",
    ]
    if goal:
        reasons.append("هدف انتخابی شما با مسیر مرحله‌ای هماهنگ است.")
    return reasons


def _ensure_reason_count(reasons: List[str]) -> List[str]:
    if len(reasons) < 2:
        reasons.append("پایه‌های موردنیاز برای مسیر تخصصی کامل نیست.")
    if len(reasons) < 2:
        reasons.append("پیشنهاد می‌شود روی مهارت‌های پایه تمرکز کنید.")
    if len(reasons) > 4:
        return reasons[:4]
    return reasons
