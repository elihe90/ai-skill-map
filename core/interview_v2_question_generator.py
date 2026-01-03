import hashlib
import json
import os
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from core.env_loader import load_env


CACHE: Dict[str, Dict[str, Any]] = {}
CORE_IDS = ("CORE_Q1", "CORE_Q2", "CORE_Q3", "CORE_Q4")
ROUTE_IDS = ("ROUTE_Q5", "ROUTE_Q6", "ROUTE_Q7")


def load_interview_questions(
    profile: Optional[Dict[str, Any]] = None,
    path: str = "data/interview_questions_v2_fa.json",
    force_refresh: bool = False,
) -> Dict[str, Any]:
    """Load interview questions, preferring LLM-generated core and routing text."""
    static_payload = _load_static_questions(path)
    profile = profile or {}

    if force_refresh:
        clear_question_cache(profile)

    core, core_source = _generate_core_questions(profile, static_payload.get("core", []))
    routing, routing_source = _generate_routing_questions(profile, static_payload.get("routing", []))
    cache_key = _cache_key(profile)
    error = CACHE.get(cache_key, {}).get("llm_error")
    return {
        "version": "v2-llm",
        "core": core,
        "routing": routing,
        "meta": {
            "core_source": core_source,
            "routing_source": routing_source,
            "llm_error": error,
        },
    }


def _load_static_questions(path: str) -> Dict[str, Any]:
    data = Path(path).read_text(encoding="utf-8-sig")
    parsed = json.loads(data)
    if not isinstance(parsed, dict):
        raise ValueError("interview v2 questions must be a dict")
    return parsed


def clear_question_cache(profile: Optional[Dict[str, Any]] = None) -> None:
    """Clear cached questions for a specific profile or all profiles."""
    if profile:
        CACHE.pop(_cache_key(profile), None)
        return
    CACHE.clear()


def _generate_core_questions(
    profile: Dict[str, Any],
    fallback_core: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], str]:
    api_key, base_url, model = _get_api_settings()
    key = _cache_key(profile)
    if key in CACHE:
        cached = CACHE[key].get("core", [])
        source = CACHE[key].get("core_source", "fallback")
        if _normalize_core_questions(cached) and source.startswith("llm"):
            return cached, f"{source}_cached"
        if not api_key:
            return cached, f"{source}_cached"

    if not api_key:
        CACHE[key] = {**CACHE.get(key, {}), "llm_error": "missing_api_key"}
        CACHE[key] = {**CACHE.get(key, {}), "core": fallback_core, "core_source": "fallback"}
        return fallback_core, "fallback"
    if api_key:
        try:
            response = _call_avalai(_build_prompt(profile), api_key, base_url, model)
            parsed = _parse_response(response)
            normalized = _normalize_core_questions(parsed)
            if normalized:
                CACHE[key] = {**CACHE.get(key, {}), "core": normalized, "core_source": "llm"}
                CACHE[key].pop("llm_error", None)
                return normalized, "llm"
        except Exception as exc:
            CACHE[key] = {**CACHE.get(key, {}), "llm_error": f"core_error: {exc}"}

    CACHE[key] = {**CACHE.get(key, {}), "core": fallback_core, "core_source": "fallback"}
    return fallback_core, "fallback"


def _generate_routing_questions(
    profile: Dict[str, Any],
    fallback_routing: List[Dict[str, Any]],
) -> tuple[List[Dict[str, Any]], str]:
    if not fallback_routing:
        return [], "fallback"

    api_key, base_url, model = _get_api_settings()
    key = _cache_key(profile)
    if key in CACHE:
        cached = CACHE[key].get("routing", [])
        source = CACHE[key].get("routing_source", "fallback")
        if _valid_routing_questions(cached) and source.startswith("llm"):
            return cached, f"{source}_cached"
        if not api_key:
            return cached, f"{source}_cached"

    if not api_key:
        CACHE[key] = {**CACHE.get(key, {}), "llm_error": "missing_api_key"}
        CACHE[key] = {**CACHE.get(key, {}), "routing": fallback_routing, "routing_source": "fallback"}
        return fallback_routing, "fallback"
    if api_key:
        try:
            response = _call_avalai(_build_routing_prompt(profile, fallback_routing), api_key, base_url, model)
            parsed = _parse_response(response)
            merged = _merge_routing_texts(fallback_routing, parsed)
            if _valid_routing_questions(merged):
                CACHE[key] = {
                    **CACHE.get(key, {}),
                    "routing": merged,
                    "routing_source": "llm",
                }
                CACHE[key].pop("llm_error", None)
                return merged, "llm"
        except Exception as exc:
            CACHE[key] = {**CACHE.get(key, {}), "llm_error": f"routing_error: {exc}"}

    CACHE[key] = {**CACHE.get(key, {}), "routing": fallback_routing, "routing_source": "fallback"}
    return fallback_routing, "fallback"


def _cache_key(profile: Dict[str, Any]) -> str:
    summary = json.dumps(profile, ensure_ascii=True, sort_keys=True)
    return hashlib.sha1(summary.encode("utf-8")).hexdigest()


def _get_api_settings() -> tuple[Optional[str], str, str]:
    load_env()
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("AVALAI_API_KEY")
    base_url = os.getenv("AVALAI_BASE_URL", "https://api.avalai.ir/v1").strip()
    if "aval.ai" in base_url or "api.aval.ai" in base_url:
        raise ValueError("دامنه اشتباه است. AvalAI درست: https://api.avalai.ir/v1")
    if base_url.startswith("http://"):
        base_url = "https://" + base_url[len("http://") :]
    elif not base_url.startswith("https://"):
        base_url = "https://" + base_url.lstrip("/")
    model = os.getenv("OPENAI_MODEL") or os.getenv("AVALAI_MODEL") or "gpt-4o-mini"
    return api_key, base_url, model


def _build_prompt(profile: Dict[str, Any]) -> str:
    profile_hint = {
        "age": profile.get("age"),
        "employment_status": profile.get("employment_status"),
        "education_level": profile.get("education_level"),
        "digital_level": profile.get("digital_level"),
        "goal_type": profile.get("goal_type"),
        "weekly_time_budget_hours": profile.get("weekly_time_budget_hours"),
    }
    return (
        "Generate 4 Persian core interview questions for an AI usage interview. "
        "Return STRICT JSON only (no markdown), in this exact schema:\n"
        "[\n"
        "  {\n"
        "    \"id\": \"CORE_Q1\",\n"
        "    \"text_fa\": \"...\",\n"
        "    \"answer_type\": \"checkbox+text\",\n"
        "    \"options_fa\": [\"...\", \"...\"],\n"
        "    \"hint_fa\": \"...\"\n"
        "  },\n"
        "  {\"id\":\"CORE_Q2\",\"text_fa\":\"...\",\"answer_type\":\"text\",\"hint_fa\":\"...\"},\n"
        "  {\"id\":\"CORE_Q3\",\"text_fa\":\"...\",\"answer_type\":\"checkbox+text\",\"options_fa\":[\"...\"],\"hint_fa\":\"...\"},\n"
        "  {\"id\":\"CORE_Q4\",\"text_fa\":\"...\",\"answer_type\":\"text\",\"hint_fa\":\"...\"}\n"
        "]\n\n"
        "Rules:\n"
        "- Questions must be short, practical, non-technical, AI-usage themed.\n"
        "- CORE_Q1 and CORE_Q3 must include 4-6 options in options_fa.\n"
        "- Use Persian (Farsi) text for text_fa, options_fa, hint_fa.\n"
        "- Keep ids exactly CORE_Q1..CORE_Q4.\n\n"
        f"Profile context (may be empty): {json.dumps(profile_hint, ensure_ascii=True)}"
    )


def _build_routing_prompt(profile: Dict[str, Any], routing: List[Dict[str, Any]]) -> str:
    profile_hint = {
        "age": profile.get("age"),
        "employment_status": profile.get("employment_status"),
        "education_level": profile.get("education_level"),
        "digital_level": profile.get("digital_level"),
        "goal_type": profile.get("goal_type"),
        "weekly_time_budget_hours": profile.get("weekly_time_budget_hours"),
    }
    options = {
        item.get("id"): item.get("options_fa", [])
        for item in routing
        if isinstance(item, dict)
    }
    return (
        "Rewrite the routing question text and hint in Persian. "
        "Return STRICT JSON only (no markdown), in this schema:\n"
        "[\n"
        "  {\"id\":\"ROUTE_Q5\",\"text_fa\":\"...\",\"hint_fa\":\"...\"},\n"
        "  {\"id\":\"ROUTE_Q6\",\"text_fa\":\"...\",\"hint_fa\":\"...\"},\n"
        "  {\"id\":\"ROUTE_Q7\",\"text_fa\":\"...\",\"hint_fa\":\"...\"}\n"
        "]\n\n"
        "Rules:\n"
        "- Keep the intent of each question.\n"
        "- Do NOT change the options; they are fixed and provided below.\n"
        "- Keep texts short and clear.\n"
        "- Use Persian (Farsi) only.\n\n"
        f"Fixed options (do not change): {json.dumps(options, ensure_ascii=True)}\n"
        f"Profile context (may be empty): {json.dumps(profile_hint, ensure_ascii=True)}"
    )


def _call_avalai(prompt: str, api_key: str, base_url: str, model: str) -> Dict[str, Any]:
    from urllib.parse import urlparse

    endpoint_path = "/chat/completions"
    final_url = base_url.rstrip("/") + endpoint_path
    debug = os.getenv("DEBUG", "").lower() in {"1", "true", "yes", "on"}
    if debug:
        print("AVALAI_BASE_URL=", base_url)
        print("AVALAI_ENDPOINT_PATH=", endpoint_path)
        print("AVALAI_FINAL_URL=", final_url)
        print("AVALAI_HOST=", urlparse(final_url).hostname)
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a Persian interview designer. Output strict JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        final_url,
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
        return json.loads(body)


def _parse_response(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    choices = response.get("choices")
    if not choices:
        return []
    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str):
        return []
    json_text = _extract_json(content)
    if not json_text:
        return []
    parsed = json.loads(json_text)
    if not isinstance(parsed, list):
        return []
    return parsed


def _extract_json(content: str) -> Optional[str]:
    start = content.find("[")
    end = content.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return None
    return content[start : end + 1].strip()


def _normalize_core_questions(questions: Any) -> List[Dict[str, Any]]:
    if not isinstance(questions, list) or len(questions) < 4:
        return []
    by_id = {
        item.get("id"): item
        for item in questions
        if isinstance(item, dict) and item.get("id") in CORE_IDS
    }
    if set(by_id.keys()) != set(CORE_IDS):
        return []

    ordered: List[Dict[str, Any]] = []
    for qid in CORE_IDS:
        item = by_id[qid]
        if not _valid_core_item(item, qid):
            return []
        ordered.append(item)
    return ordered


def _valid_core_item(item: Dict[str, Any], qid: str) -> bool:
    required = {"id", "text_fa", "answer_type", "hint_fa"}
    if not required.issubset(item.keys()):
        return False
    if item.get("answer_type") not in {"text", "checkbox+text"}:
        return False
    if qid in ("CORE_Q1", "CORE_Q3") and item.get("answer_type") != "checkbox+text":
        return False
    if qid in ("CORE_Q2", "CORE_Q4") and item.get("answer_type") != "text":
        return False
    if item.get("answer_type") == "checkbox+text":
        options = item.get("options_fa")
        if not isinstance(options, list) or not (4 <= len(options) <= 6):
            return False
    return True


def _valid_routing_questions(questions: Any) -> bool:
    if not isinstance(questions, list) or len(questions) != 3:
        return False
    ids = [item.get("id") for item in questions if isinstance(item, dict)]
    if set(ids) != set(ROUTE_IDS):
        return False
    for item in questions:
        if not isinstance(item, dict):
            return False
        if not item.get("text_fa") or not item.get("hint_fa"):
            return False
        if item.get("answer_type") != "single_choice":
            return False
        options = item.get("options_fa")
        if not isinstance(options, list) or not options:
            return False
    return True


def _merge_routing_texts(
    fallback: List[Dict[str, Any]], parsed: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    if not parsed or not isinstance(parsed, list):
        return fallback
    by_id = {item.get("id"): item for item in parsed if isinstance(item, dict)}
    merged = []
    for item in fallback:
        if not isinstance(item, dict):
            continue
        override = by_id.get(item.get("id"), {})
        merged.append(
            {
                "id": item.get("id"),
                "text_fa": override.get("text_fa") or item.get("text_fa"),
                "answer_type": "single_choice",
                "options_fa": item.get("options_fa", []),
                "hint_fa": override.get("hint_fa") or item.get("hint_fa"),
            }
        )
    return merged
