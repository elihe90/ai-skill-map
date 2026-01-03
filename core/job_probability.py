from __future__ import annotations

from typing import Dict, List


def calculate_job_probability(
    job_id: str,
    solved_gaps: List[str],
    readiness_level: str,
    gaps_json: dict,
) -> Dict[str, str]:
    """Return a simple confidence label and Persian reason based on gaps + readiness."""
    solved_set = set(solved_gaps or [])
    jobs = gaps_json.get("jobs", []) if isinstance(gaps_json, dict) else []
    job = next((item for item in jobs if item.get("job_id") == job_id), None)

    base_map = {"A": "low", "B": "medium", "C": "medium"}
    base_confidence = base_map.get(str(readiness_level), "low")

    if not job:
        reason = (
            "اطلاعات کافی برای ارزیابی این شغل در دسترس نیست."
        )
        return {"confidence": base_confidence, "reason_fa": reason}

    required = job.get("required_gaps", []) if isinstance(job.get("required_gaps"), list) else []
    solved_required = [gap for gap in required if gap in solved_set]

    confidence = base_confidence
    if required and len(solved_required) == len(required):
        if confidence == "low":
            confidence = "medium"
        elif confidence == "medium":
            confidence = "high"

    if required:
        reason = (
            "بر اساس آمادگی عملی ("
            f"{readiness_level}) و حل شدن "
            f"{len(solved_required)}/{len(required)} گپ اصلی این شغل."
        )
    else:
        reason = (
            "بر اساس آمادگی عملی شما ارزیابی شد."
        )

    return {"confidence": confidence, "reason_fa": reason}
