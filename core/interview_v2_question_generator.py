from __future__ import annotations

import hashlib
import json
import os
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from core.env_loader import load_env


TOTAL_QUESTIONS = 12
ALLOWED_INTENTS = {"probe", "clarify", "challenge"}
PHASE_BY_NUMBER = {
    1: 1,
    2: 1,
    3: 1,
    4: 2,
    5: 2,
    6: 2,
    7: 3,
    8: 3,
    9: 3,
    10: 4,
    11: 4,
    12: 4,
}
CACHE_FILE = Path(__file__).resolve().parent.parent / "data" / "interview_questions_cache.json"


def clear_question_cache(profile: Optional[Dict[str, Any]] = None) -> None:
    if not CACHE_FILE.exists():
        return
    if profile is None:
        CACHE_FILE.unlink(missing_ok=True)
        return
    cache = _load_cache()
    cache.pop(_cache_key(profile), None)
    _save_cache(cache)


def load_interview_questions(
    profile: Optional[Dict[str, Any]] = None,
    force_refresh: bool = False,
) -> Dict[str, Any]:
    profile = profile or {}
    if force_refresh:
        clear_question_cache(profile)
    questions, source, error = generate_all_questions(profile)
    return {
        "version": "v3-batch",
        "questions": questions,
        "meta": {"source": source, "llm_error": error},
    }


def generate_all_questions(profile: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], str, Optional[str]]:
    cache = _load_cache()
    key = _cache_key(profile)
    if key in cache:
        entry = cache[key]
        questions = entry.get("questions") if isinstance(entry, dict) else None
        if _validate_questions(questions):
            return questions, "cache", entry.get("llm_error")

    api_key, base_url, model = _get_api_settings()
    if not api_key:
        fallback = _fallback_questions()
        cache[key] = {"questions": fallback, "source": "fallback", "llm_error": "missing_api_key"}
        _save_cache(cache)
        return fallback, "fallback", "missing_api_key"

    prompt = _build_batch_prompt(profile)
    try:
        response = _call_avalai(prompt, api_key, base_url, model)
        parsed = _parse_question_list(response)
        normalized = _normalize_questions(parsed)
        if _validate_questions(normalized):
            cache[key] = {"questions": normalized, "source": "llm"}
            _save_cache(cache)
            return normalized, "llm", None
    except Exception as exc:
        cache[key] = {
            "questions": _fallback_questions(),
            "source": "fallback",
            "llm_error": str(exc),
        }
        _save_cache(cache)
        return _fallback_questions(), "fallback", str(exc)

    fallback = _fallback_questions()
    cache[key] = {"questions": fallback, "source": "fallback"}
    _save_cache(cache)
    return fallback, "fallback", None


def _fallback_questions() -> List[Dict[str, Any]]:
    return [
        {
            "questionNumber": 1,
            "phase": 1,
            "intent": "probe",
            "question": "هدف اصلی شما از ورود به حوزه هوش مصنوعی چیست؟",
            "signals": ["goal", "motivation"],
            "candidateRoles": [{"role": "AI Generalist", "confidence": 0.4}],
        },
        {
            "questionNumber": 2,
            "phase": 1,
            "intent": "clarify",
            "question": "به کدام حوزه‌های کاربردی AI علاقه بیشتری دارید؟",
            "signals": ["interest", "domain"],
            "candidateRoles": [{"role": "AI Generalist", "confidence": 0.4}],
        },
        {
            "questionNumber": 3,
            "phase": 1,
            "intent": "challenge",
            "question": "اگر بین یادگیری سریع و یادگیری عمیق یکی را انتخاب کنید، کدام را ترجیح می‌دهید؟",
            "signals": ["learning_style"],
            "candidateRoles": [{"role": "AI Generalist", "confidence": 0.4}],
        },
        {
            "questionNumber": 4,
            "phase": 2,
            "intent": "probe",
            "question": "درک شما از تفاوت هوش مصنوعی با برنامه‌نویسی سنتی چیست؟",
            "signals": ["conceptual_understanding"],
            "candidateRoles": [{"role": "AI Generalist", "confidence": 0.4}],
        },
        {
            "questionNumber": 5,
            "phase": 2,
            "intent": "clarify",
            "question": "با مفاهیمی مثل داده آموزشی، مدل، یا خطا آشنایی دارید؟ توضیح کوتاه بدهید.",
            "signals": ["ai_basics"],
            "candidateRoles": [{"role": "AI Generalist", "confidence": 0.4}],
        },
        {
            "questionNumber": 6,
            "phase": 2,
            "intent": "challenge",
            "question": "اگر یک مدل AI جواب اشتباه بدهد، چه عواملی می‌تواند علت باشد؟",
            "signals": ["reasoning", "ai_limits"],
            "candidateRoles": [{"role": "AI Generalist", "confidence": 0.4}],
        },
        {
            "questionNumber": 7,
            "phase": 3,
            "intent": "probe",
            "question": "چه ابزارهای AI را تاکنون استفاده کرده‌اید و برای چه کاری؟",
            "signals": ["tooling", "experience"],
            "candidateRoles": [{"role": "AI Generalist", "confidence": 0.5}],
        },
        {
            "questionNumber": 8,
            "phase": 3,
            "intent": "clarify",
            "question": "یک مثال بزنید که AI در کار شما زمان یا کیفیت را بهتر کرده باشد.",
            "signals": ["impact", "practicality"],
            "candidateRoles": [{"role": "AI Generalist", "confidence": 0.5}],
        },
        {
            "questionNumber": 9,
            "phase": 3,
            "intent": "challenge",
            "question": "در کار با ابزارهای AI، بزرگ‌ترین چالش شما چه بوده است؟",
            "signals": ["gap", "pain_points"],
            "candidateRoles": [{"role": "AI Generalist", "confidence": 0.5}],
        },
        {
            "questionNumber": 10,
            "phase": 4,
            "intent": "probe",
            "question": "به نظر شما برای ورود به بازار کار AI چه مهارتی ضروری‌تر است؟",
            "signals": ["market_readiness"],
            "candidateRoles": [{"role": "AI Generalist", "confidence": 0.5}],
        },
        {
            "questionNumber": 11,
            "phase": 4,
            "intent": "clarify",
            "question": "چه نوع نقش شغلی AI را برای خودتان مناسب‌تر می‌دانید و چرا؟",
            "signals": ["role_fit"],
            "candidateRoles": [{"role": "AI Generalist", "confidence": 0.5}],
        },
        {
            "questionNumber": 12,
            "phase": 4,
            "intent": "challenge",
            "question": "اگر امروز شروع کنید، اولین اقدام عملی شما برای ورود به مسیر AI چیست؟",
            "signals": ["actionability"],
            "candidateRoles": [{"role": "AI Generalist", "confidence": 0.5}],
        },
    ]


def _build_batch_prompt(profile: Dict[str, Any]) -> str:
    profile_hint = {
        "age": profile.get("age"),
        "employment_status": profile.get("employment_status"),
        "education_level": profile.get("education_level"),
        "digital_level": profile.get("digital_level"),
        "goal_type": profile.get("goal_type"),
        "weekly_time_budget_hours": profile.get("weekly_time_budget_hours"),
    }
    return (
        "تو یک مصاحبه‌گر هوشمند برای سنجش آمادگی افراد در حوزه «هوش مصنوعی» هستی.\n"
        "دامنه فقط: دوره‌های AI و مشاغل مرتبط با AI.\n\n"
        "هدف:\n"
        "- تشخیص مسیر مناسب فرد در AI (عمومی یا تخصصی)\n"
        "- سنجش گپ مهارتی\n"
        "- پیشنهاد دوره و نقش شغلی مناسب\n\n"
        "قواعد:\n"
        "- کل مصاحبه دقیقاً 12 سؤال باشد\n"
        "- هر پیام فقط یک سؤال کوتاه\n"
        "- لحن رسمی و محترمانه\n"
        "- سوال‌ها تطبیقی باشند (Adaptive)\n"
        "- اطلاعات حساس نپرس\n\n"
        "ساختار:\n"
        "فاز 1: جهت‌گیری و هدف AI (3 سؤال)\n"
        "فاز 2: سواد مفهومی AI (3 سؤال)\n"
        "فاز 3: ابزار و تجربه عملی (3 سؤال)\n"
        "فاز 4: آمادگی شغلی و بازار (3 سؤال)\n\n"
        "خروجی تو فقط JSON معتبر باشد (لیست 12 آیتمی):\n"
        "[\n"
        "  {\"questionNumber\": 1, \"phase\": 1, \"intent\": \"probe\", \"question\": \"...\", \"signals\": [\"...\"], \"candidateRoles\": [{\"role\":\"AI Generalist\",\"confidence\":0.0}] }\n"
        "]\n\n"
        "پس از سؤال 12، مصاحبه را متوقف کن.\n"
        "هیچ متن اضافه‌ای خارج از JSON ننویس.\n\n"
        f"پروفایل: {json.dumps(profile_hint, ensure_ascii=True)}\n"
    )


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


def _call_avalai(prompt: str, api_key: str, base_url: str, model: str) -> Dict[str, Any]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a Persian AI interview designer. Output strict JSON only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
    }
    data = json.dumps(payload).encode("utf-8")
    final_url = base_url.rstrip("/") + "/chat/completions"
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


def _parse_question_list(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    choices = response.get("choices")
    if not choices:
        return []
    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str):
        return []
    start = content.find("[")
    end = content.rfind("]")
    if start == -1 or end == -1 or end <= start:
        return []
    try:
        parsed = json.loads(content[start : end + 1])
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _normalize_questions(questions: Any) -> List[Dict[str, Any]]:
    if not isinstance(questions, list):
        return []
    normalized = []
    for item in questions:
        if not isinstance(item, dict):
            continue
        normalized.append(_normalize_question(item, int(item.get("questionNumber", len(normalized) + 1))))
    return normalized


def _normalize_question(item: Dict[str, Any], question_number: int) -> Dict[str, Any]:
    question_text = str(item.get("question", "")).strip()
    if not question_text:
        return {}
    intent = str(item.get("intent", "probe")).strip().lower()
    if intent not in ALLOWED_INTENTS:
        intent = "probe"
    signals = item.get("signals")
    if not isinstance(signals, list):
        signals = []
    cleaned_signals = [str(s) for s in signals if str(s).strip()][:5]
    roles = item.get("candidateRoles")
    cleaned_roles: List[Dict[str, Any]] = []
    if isinstance(roles, list):
        for role in roles:
            if not isinstance(role, dict):
                continue
            role_name = str(role.get("role", "AI Generalist")).strip() or "AI Generalist"
            try:
                confidence = float(role.get("confidence", 0.0))
            except (TypeError, ValueError):
                confidence = 0.0
            confidence = max(0.0, min(1.0, confidence))
            cleaned_roles.append({"role": role_name, "confidence": confidence})
    if not cleaned_roles:
        cleaned_roles = [{"role": "AI Generalist", "confidence": 0.0}]

    return {
        "questionNumber": question_number,
        "phase": PHASE_BY_NUMBER.get(question_number, 1),
        "intent": intent,
        "question": question_text,
        "signals": cleaned_signals,
        "candidateRoles": cleaned_roles,
    }


def _validate_questions(questions: Any) -> bool:
    if not isinstance(questions, list) or len(questions) != TOTAL_QUESTIONS:
        return False
    numbers = [q.get("questionNumber") for q in questions if isinstance(q, dict)]
    if set(numbers) != set(range(1, TOTAL_QUESTIONS + 1)):
        return False
    for item in questions:
        if not isinstance(item, dict):
            return False
        if not item.get("question"):
            return False
    return True


def _cache_key(profile: Dict[str, Any]) -> str:
    summary = json.dumps(profile, ensure_ascii=True, sort_keys=True)
    return hashlib.sha1(summary.encode("utf-8")).hexdigest()


def _load_cache() -> Dict[str, Any]:
    if not CACHE_FILE.exists():
        return {}
    try:
        raw = CACHE_FILE.read_text(encoding="utf-8-sig").strip()
        if not raw:
            return {}
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _save_cache(cache: Dict[str, Any]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, ensure_ascii=True, indent=2), encoding="utf-8")
