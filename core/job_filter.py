import os
from typing import Any, Dict, Set


def allowed_domains_for_track(track: str) -> Set[str]:
    track = str(track or "").lower()
    if track == "content":
        return {"content", "marketing"}
    if track == "automation":
        return {"automation", "biz"}
    if track == "technical":
        return {"ai", "machine_learning", "data"}
    return set()


def filter_job_mapping_by_track(job_mapping: Dict[str, Any], track: str) -> Dict[str, Any]:
    """Filter job mapping by allowed domains for the track."""
    if not isinstance(job_mapping, dict):
        return {}

    allowed = allowed_domains_for_track(track)
    if not allowed:
        return job_mapping

    def _filter(items: Any) -> list:
        if not isinstance(items, list):
            return []
        filtered = []
        for item in items:
            if not isinstance(item, dict):
                continue
            domain = item.get("domain")
            if not domain:
                _debug_log_missing_domain(item.get("title_fa") or item.get("job_id"))
                filtered.append(item)
            elif str(domain) in allowed:
                filtered.append(item)
        return filtered

    return {
        **job_mapping,
        "reachable_jobs": _filter(job_mapping.get("reachable_jobs")),
        "next_level_jobs": _filter(job_mapping.get("next_level_jobs")),
    }


def _debug_log_missing_domain(job_label: Any) -> None:
    debug = os.getenv("DEBUG", "").lower() in {"1", "true", "yes", "on"}
    if debug:
        print(f"JOB_FILTER: missing domain for {job_label}")
