import json
import random
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


Question = Dict[str, Any]


def load_question_bank(path: str = "data/interview_question_bank_fa.json") -> List[Question]:
    """Load the interview question bank from JSON."""
    data = Path(path).read_text(encoding="utf-8-sig")
    parsed = json.loads(data)
    if not isinstance(parsed, list):
        raise ValueError("question bank must be a list")
    return parsed


def select_questions(
    profile: Dict[str, Any],
    bank: List[Question],
    n: int = 5,
    seed: Optional[int] = 42,
) -> List[Question]:
    """Select a deterministic set of interview questions based on profile rules."""
    rng = random.Random(seed)
    if n <= 0:
        return []

    questions = _normalize_bank(bank)
    if not questions:
        return []

    if len(questions) <= n:
        picked = _pick_by_weight(questions, len(questions), rng)
        return [item["data"] for item in picked]

    constraints = _build_constraints(profile)
    counts = {name: 0 for name in constraints}
    selected: List[Dict[str, Any]] = []
    selected_ids = set()

    def add_choice(candidate: Dict[str, Any]) -> None:
        selected.append(candidate)
        selected_ids.add(candidate["id"])
        for name, spec in constraints.items():
            if counts[name] >= spec["need"]:
                continue
            if spec["predicate"](candidate):
                counts[name] += 1

    while len(selected) < n:
        best = None
        best_score = (-1, -1.0, 0.0)
        for candidate in questions:
            if candidate["id"] in selected_ids:
                continue
            cover = 0
            for name, spec in constraints.items():
                if counts[name] >= spec["need"]:
                    continue
                if spec["predicate"](candidate):
                    cover += 1
            if cover == 0:
                continue
            score = (cover, candidate["weight"], rng.random())
            if score > best_score:
                best_score = score
                best = candidate
        if best is None:
            break
        add_choice(best)

    if len(selected) < n:
        remaining = [item for item in questions if item["id"] not in selected_ids]
        for item in _pick_by_weight(remaining, n - len(selected), rng):
            selected.append(item)
            selected_ids.add(item["id"])

    result = [item["data"] for item in selected[:n]]
    if _normalize_digital_level(str(profile.get("digital_level", "")).strip()) == "ضعیف":
        return _apply_low_digital_overrides(result)
    return result


def _normalize_bank(bank: List[Question]) -> List[Dict[str, Any]]:
    unique: List[Dict[str, Any]] = []
    seen_ids = set()
    for item in bank:
        if not isinstance(item, dict):
            continue
        raw_id = str(item.get("id", "")).strip()
        if not raw_id or raw_id in seen_ids:
            continue
        seen_ids.add(raw_id)
        tags = item.get("tags")
        if not isinstance(tags, list):
            tags = []
        tag_set = {str(tag) for tag in tags if isinstance(tag, str)}
        difficulty = str(item.get("difficulty", "")).lower()
        weight = _safe_weight(item.get("weight", 1.0))
        unique.append(
            {
                "id": raw_id,
                "tags": tag_set,
                "difficulty": difficulty,
                "weight": weight,
                "data": item,
            }
        )
    return unique


def _safe_weight(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 1.0


def _pick_by_weight(
    candidates: List[Dict[str, Any]], count: int, rng: random.Random
) -> List[Dict[str, Any]]:
    shuffled = list(candidates)
    rng.shuffle(shuffled)
    return sorted(shuffled, key=lambda item: item["weight"], reverse=True)[:count]


def _build_constraints(profile: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    digital_raw = str(profile.get("digital_level", "")).strip()
    goal_raw = str(profile.get("goal") or profile.get("goal_type") or "").strip()
    preference_raw = str(profile.get("preference") or profile.get("interest") or "").strip()

    digital_level = _normalize_digital_level(digital_raw)
    goal = _normalize_goal(goal_raw)
    preference = _normalize_preference(preference_raw)

    required_digital = 2 if digital_level == "ضعیف" else 1
    required_execution = 2 if goal == "درآمد سریع" else 1
    required_easy = 2 if digital_level == "ضعیف" else 0
    required_learning = 1 if goal == "تغییر مسیر فنی" else 0
    required_problem_solving = 1 if goal == "تغییر مسیر فنی" else 0
    required_planning_or_quality = 1 if goal == "ارتقای شغلی" else 0
    required_problem_or_learning = 0 if (required_learning or required_problem_solving) else 1

    required_communication = 0
    required_preference_planning = 0
    required_preference_problem = 0
    if preference == "تولید محتوا و شبکه‌های اجتماعی":
        required_communication = 1
    elif preference == "اتوماسیون و بهبود کارهای اداری/گزارش":
        required_preference_planning = 1
    elif preference == "کار فنی و کدنویسی/حل مسئله":
        required_preference_problem = 1

    return _constraint_map(
        required_digital=required_digital,
        required_execution=required_execution,
        required_easy=required_easy,
        required_learning=required_learning,
        required_problem_solving=required_problem_solving,
        required_planning_or_quality=required_planning_or_quality,
        required_problem_or_learning=required_problem_or_learning,
        required_communication=required_communication,
        required_preference_planning=required_preference_planning,
        required_preference_problem=required_preference_problem,
    )


def _constraint_map(
    *,
    required_digital: int,
    required_execution: int,
    required_easy: int,
    required_learning: int,
    required_problem_solving: int,
    required_planning_or_quality: int,
    required_problem_or_learning: int,
    required_communication: int,
    required_preference_planning: int,
    required_preference_problem: int,
) -> Dict[str, Dict[str, Any]]:
    def has_tag(tag: str) -> Callable[[Dict[str, Any]], bool]:
        return lambda q: tag in q["tags"]

    def has_planning_or_quality(q: Dict[str, Any]) -> bool:
        return "planning" in q["tags"] or "quality" in q["tags"]

    def has_problem_or_learning(q: Dict[str, Any]) -> bool:
        return "problem_solving" in q["tags"] or "learning" in q["tags"]

    constraints: Dict[str, Dict[str, Any]] = {}
    if required_digital:
        constraints["digital"] = {"need": required_digital, "predicate": has_tag("digital")}
    if required_execution:
        constraints["execution"] = {
            "need": required_execution,
            "predicate": has_tag("execution"),
        }
    if required_easy:
        constraints["easy"] = {
            "need": required_easy,
            "predicate": lambda q: q["difficulty"] == "easy",
        }
    if required_learning:
        constraints["learning"] = {"need": required_learning, "predicate": has_tag("learning")}
    if required_problem_solving:
        constraints["problem_solving"] = {
            "need": required_problem_solving,
            "predicate": has_tag("problem_solving"),
        }
    if required_planning_or_quality:
        constraints["planning_or_quality"] = {
            "need": required_planning_or_quality,
            "predicate": has_planning_or_quality,
        }
    if required_problem_or_learning:
        constraints["problem_or_learning"] = {
            "need": required_problem_or_learning,
            "predicate": has_problem_or_learning,
        }
    if required_communication:
        constraints["communication"] = {
            "need": required_communication,
            "predicate": has_tag("communication"),
        }
    if required_preference_planning:
        constraints["preference_planning"] = {
            "need": required_preference_planning,
            "predicate": has_planning_or_quality,
        }
    if required_preference_problem:
        constraints["preference_problem"] = {
            "need": required_preference_problem,
            "predicate": has_problem_or_learning,
        }
    return constraints


def _normalize_goal(value: str) -> str:
    mapping = {
        "quick_income": "درآمد سریع",
        "career_upgrade": "ارتقای شغلی",
        "technical_switch": "تغییر مسیر فنی",
    }
    return mapping.get(value, value)


def _normalize_digital_level(value: str) -> str:
    mapping = {
        "weak": "ضعیف",
        "medium": "متوسط",
        "good": "خوب",
    }
    return mapping.get(value, value)


def _normalize_preference(value: str) -> str:
    mapping = {
        "content": "تولید محتوا و شبکه‌های اجتماعی",
        "automation": "اتوماسیون و بهبود کارهای اداری/گزارش",
        "technical": "کار فنی و کدنویسی/حل مسئله",
    }
    return mapping.get(value, value)


def _apply_low_digital_overrides(questions: List[Question]) -> List[Question]:
    updated = []
    for item in questions:
        if not isinstance(item, dict):
            updated.append(item)
            continue
        followups = item.get("followups_fa") if isinstance(item.get("followups_fa"), list) else []
        hint = " | ".join(str(x) for x in followups if x)
        payload = dict(item)
        if hint and "hint_fa" not in payload:
            payload["hint_fa"] = hint
        if "answer_type" not in payload:
            payload["answer_type"] = "checkbox+text"
        if "options_fa" not in payload and followups:
            payload["options_fa"] = followups
        updated.append(payload)
    return updated
