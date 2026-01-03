import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


LEVEL_ORDER = {"A": 1, "B": 2, "C": 3}
DIMENSIONS = ("execution", "problem_solving", "learning", "planning", "ai_mindset")


def load_rules(path: str = "data/job_course_rules_fa.json") -> Dict[str, Any]:
    """Load job-course rules from JSON."""
    data = Path(path).read_text(encoding="utf-8-sig")
    parsed = json.loads(data)
    if not isinstance(parsed, dict):
        raise ValueError("job rules must be a dict")
    parsed.setdefault("course_catalog", {})
    parsed.setdefault("job_rules", [])
    catalog_path = Path("data/course_catalog_fa.json")
    if catalog_path.exists():
        try:
            catalog = json.loads(catalog_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            catalog = {}
        if isinstance(catalog, dict) and catalog:
            parsed["course_catalog"] = catalog
    return parsed


def load_job_rules(path: str = "data/job_course_rules_fa.json") -> Dict[str, Any]:
    """Backward-compatible alias for load_rules."""
    return load_rules(path)


def level_rank(level: str) -> int:
    """Map a level to its rank (A=1, B=2, C=3)."""
    return LEVEL_ORDER.get(str(level).upper(), 0)


def compute_soft_fit(interview_scores: Dict[str, Any], soft_targets: Dict[str, Any]) -> int:
    """Compute soft-fit score (0..100) based on gaps from targets."""
    fits = []
    for dim in DIMENSIONS:
        user = _score(interview_scores.get(dim, 0))
        target = _score(soft_targets.get(dim, 0))
        gap = max(0, target - user)
        dim_fit = 1 - (gap / 5)
        fits.append(dim_fit)
    if not fits:
        return 0
    return int(round((sum(fits) / len(fits)) * 100))


def compute_course_fit(rule: Dict[str, Any], user_codes: set[str]) -> Dict[str, Any]:
    """Compute course coverage and missing requirements for a job rule."""
    required_all = _safe_list(rule.get("required_all"))
    required_any = _safe_list(rule.get("required_any"))
    nice_to_have = _safe_list(rule.get("nice_to_have"))

    satisfied_all = [code for code in required_all if code in user_codes]
    satisfied_any = [code for code in required_any if code in user_codes]
    satisfied_nice = [code for code in nice_to_have if code in user_codes]

    required_all_ok = len(required_all) == len(satisfied_all)
    required_any_ok = True if not required_any else bool(satisfied_any)

    all_part = 70 if not required_all else (len(satisfied_all) / len(required_all)) * 70
    any_part = 20 if (not required_any or required_any_ok) else 0
    nice_part = 10 if not nice_to_have else (len(satisfied_nice) / len(nice_to_have)) * 10
    coverage = int(round(all_part + any_part + nice_part))
    coverage = max(0, min(100, coverage))

    missing_codes = _missing_codes(required_all, required_any, satisfied_any, user_codes)
    next_codes = _prioritize_missing(required_all, missing_codes, rule.get("course_catalog", {}))

    return {
        "required_all_ok": required_all_ok,
        "required_any_ok": required_any_ok,
        "coverage": coverage,
        "missing_codes": missing_codes,
        "next_codes": next_codes,
        "satisfied_codes": _dedupe(satisfied_all + satisfied_any),
    }


def build_why_fa(
    rule: Dict[str, Any],
    course_fit: Dict[str, Any],
    soft_fit: int,
    interview_scores: Dict[str, Any],
    course_catalog: Dict[str, Any],
) -> List[str]:
    """Build short Persian bullets explaining course/soft fit."""
    reasons = []
    satisfied = course_fit.get("satisfied_codes", [])
    missing = course_fit.get("missing_codes", [])

    if satisfied:
        reasons.append(
            f"دوره های پوشش داده شده: {', '.join(_course_titles(satisfied, course_catalog))}"
        )
    else:
        reasons.append("هنوز دوره کلیدی از الزامات این نقش پوشش داده نشده است.")

    if missing:
        reasons.append(
            f"دوره های باقی مانده: {', '.join(_course_titles(missing, course_catalog))}"
        )

    gaps = _soft_gaps(interview_scores, rule.get("soft_targets", {}))
    if gaps:
        reasons.append(f"نیاز به تقویت: {'، '.join(gaps[:2])}.")
    else:
        reasons.append("مهارت های نرم در حد مطلوب است.")

    if soft_fit < 60:
        reasons.append("تقویت مهارت های نرم می تواند شانس موفقیت را بالا ببرد.")

    return reasons


def map_jobs_from_gap(gap: Dict[str, Any], top_k: int = 3) -> Dict[str, Any]:
    """Map GAP output to reachable and next-level jobs."""
    rules = load_rules()
    course_catalog = rules.get("course_catalog", {})
    job_rules = rules.get("job_rules", [])

    training_level = str(gap.get("training_level", "A"))
    user_codes = {str(code) for code in gap.get("recommended_courses", [])}
    blocked = {str(code) for code in gap.get("blocked_courses", [])}
    interview_scores = gap.get("interview_scores", {}) or {}

    reachable = []
    next_level = []
    current_rank = level_rank(training_level)

    for rule in job_rules:
        level = str(rule.get("level", "A"))
        rank = level_rank(level)
        rule_with_catalog = dict(rule)
        rule_with_catalog["course_catalog"] = course_catalog
        course_fit = compute_course_fit(rule_with_catalog, user_codes)
        soft_fit = compute_soft_fit(interview_scores, rule.get("soft_targets", {}))
        match_score = int(round(0.65 * course_fit["coverage"] + 0.35 * soft_fit))
        match_score = max(0, min(100, match_score))

        next_codes = [code for code in course_fit["next_codes"] if code not in blocked]
        why_fa = build_why_fa(rule, course_fit, soft_fit, interview_scores, course_catalog)

        payload = {
            "job_id": rule.get("job_id"),
            "title_fa": rule.get("title_fa"),
            "level": level,
            "domain": rule.get("domain"),
            "match_score": match_score,
            "why_fa": why_fa,
            "missing_courses": course_fit["missing_codes"],
            "next_courses_to_unlock": next_codes,
        }

        if rank <= current_rank:
            reachable.append(payload)
        elif rank == current_rank + 1:
            next_level.append(
                {
                    "job_id": rule.get("job_id"),
                    "title_fa": rule.get("title_fa"),
                    "level": level,
                    "match_score": match_score,
                    "why_fa": why_fa,
                    "unlock_with": next_codes,
                }
            )

    reachable.sort(key=lambda item: -item["match_score"])
    next_level.sort(key=lambda item: -item["match_score"])

    return {
        "reachable_jobs": reachable[: max(top_k, 0)],
        "next_level_jobs": next_level[: max(top_k, 0)],
    }


def map_jobs(
    training_level: str,
    recommended_course_codes: List[str],
    interview_scores: Dict[str, Any],
    top_k: int = 3,
) -> Dict[str, Any]:
    """Backward-compatible wrapper for gap-based mapping."""
    gap = {
        "training_level": training_level,
        "recommended_courses": recommended_course_codes,
        "interview_scores": interview_scores,
    }
    return map_jobs_from_gap(gap, top_k=top_k)


def _prioritize_missing(
    required_all: List[str],
    missing_codes: List[str],
    course_catalog: Dict[str, Any],
) -> List[str]:
    def _priority(code: str) -> tuple[int, int, str]:
        meta = course_catalog.get(code, {})
        level_hint = str(meta.get("level_hint", "C"))
        in_required_all = 0 if code in required_all else 1
        return (LEVEL_ORDER.get(level_hint, 3), in_required_all, code)

    return sorted(_dedupe(missing_codes), key=_priority)[:3]


def _course_titles(codes: Iterable[str], course_catalog: Dict[str, Any]) -> List[str]:
    titles = []
    for code in _dedupe(codes):
        meta = course_catalog.get(code, {})
        title = meta.get("title_fa") if isinstance(meta, dict) else None
        if isinstance(title, str):
            titles.append(f"{code} ({title})")
        else:
            titles.append(str(code))
    return titles


def _soft_gaps(interview_scores: Dict[str, Any], soft_targets: Dict[str, Any]) -> List[str]:
    labels = {
        "execution": "اجرا",
        "problem_solving": "حل مسئله",
        "learning": "یادگیری",
        "planning": "برنامه ریزی",
        "ai_mindset": "ذهنیت AI",
    }
    gaps = []
    for dim, label in labels.items():
        user = _score(interview_scores.get(dim, 0))
        target = _score(soft_targets.get(dim, 0))
        if user < target:
            gaps.append(label)
    return gaps


def _missing_codes(
    required_all: List[str],
    required_any: List[str],
    satisfied_any: List[str],
    user_codes: set[str],
) -> List[str]:
    missing = [code for code in required_all if code not in user_codes]
    if required_any and not satisfied_any:
        missing.extend(required_any)
    return _dedupe(missing)


def _safe_list(value: Any) -> List[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if isinstance(item, (str, int))]


def _score(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _dedupe(values: Iterable[str]) -> List[str]:
    seen = set()
    output = []
    for item in values:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output
