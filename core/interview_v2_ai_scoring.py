import hashlib
import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from core.env_loader import load_env


CACHE: Dict[str, Dict[str, Any]] = {}
DIMENSIONS = ("problem_solving", "execution", "learning", "planning", "ai_mindset")


def score_core_answers(
    core_answers: Dict[str, Any], core_questions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Score core interview answers using AvalAI or a local fallback."""
    combined_text = _build_combined_text(core_answers, core_questions)
    cache_key = hashlib.sha1(combined_text.encode("utf-8")).hexdigest()
    if cache_key in CACHE:
        return CACHE[cache_key]

    api_key, base_url, model = _get_api_settings()
    if api_key:
        try:
            response = _call_avalai(combined_text, api_key, base_url, model)
            parsed = _parse_response(response)
            if parsed:
                CACHE[cache_key] = parsed
                return parsed
        except Exception:
            pass

    fallback = _fallback_scores(combined_text)
    CACHE[cache_key] = fallback
    return fallback


def _build_combined_text(
    core_answers: Dict[str, Any], core_questions: List[Dict[str, Any]]
) -> str:
    parts = []
    for question in core_questions:
        qid = question.get("id")
        answer = core_answers.get(qid, {})
        answer_text = _format_answer(answer)
        parts.append(f"سوال: {question.get('text_fa', '')}\nپاسخ: {answer_text}\n")
    return "\n".join(parts).strip()


def _format_answer(answer: Any) -> str:
    if not isinstance(answer, dict):
        return str(answer or "")
    choices = answer.get("choices")
    text = answer.get("text")
    if choices:
        joined = "، ".join(str(item) for item in choices)
        if text:
            return f"انتخاب‌ها: {joined} | توضیح: {text}"
        return f"انتخاب‌ها: {joined}"
    if text:
        return str(text)
    return ""


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


def _call_avalai(combined_text: str, api_key: str, base_url: str, model: str) -> Dict[str, Any]:
    from urllib.parse import urlparse

    endpoint_path = "/chat/completions"
    final_url = base_url.rstrip("/") + endpoint_path
    debug = os.getenv("DEBUG", "").lower() in {"1", "true", "yes", "on"}
    if debug:
        print("AVALAI_BASE_URL=", base_url)
        print("AVALAI_ENDPOINT_PATH=", endpoint_path)
        print("AVALAI_FINAL_URL=", final_url)
        print("AVALAI_HOST=", urlparse(final_url).hostname)

    system_prompt = "You are a Persian interview analyst. Return STRICT JSON only, no markdown."
    user_prompt = f"""Analyze the following answers and return strict JSON in this schema:
{{
  "scores": {{"problem_solving":0..5,"execution":0..5,"learning":0..5,"planning":0..5,"ai_mindset":0..5}},
  "rationales_fa": {{"problem_solving":"...","execution":"...","learning":"...","planning":"...","ai_mindset":"..."}},
  "improvements_fa": ["...","...","..."],
  "summary_fa": "..."
}}

Rules:
- Use Persian in rationales, improvements, and summary_fa.
- summary_fa should be 2-4 short sentences.

Answers:
{combined_text}"""
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
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


def _parse_response(response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    choices = response.get("choices")
    if not choices:
        return None
    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str):
        return None
    json_text = _extract_json(content)
    if not json_text:
        return None

    parsed = json.loads(json_text)
    scores = parsed.get("scores", {})
    if not isinstance(scores, dict):
        return None

    cleaned_scores = {key: _clamp_score(scores.get(key)) for key in DIMENSIONS}
    parsed["scores"] = cleaned_scores

    rationales = parsed.get("rationales_fa")
    if not isinstance(rationales, dict):
        parsed["rationales_fa"] = {key: "" for key in DIMENSIONS}

    improvements = parsed.get("improvements_fa")
    if not isinstance(improvements, list):
        parsed["improvements_fa"] = []

    summary = parsed.get("summary_fa")
    if not isinstance(summary, str):
        parsed["summary_fa"] = ""

    return {
        "scores": parsed["scores"],
        "rationales_fa": parsed["rationales_fa"],
        "improvements_fa": parsed["improvements_fa"],
        "summary_fa": parsed["summary_fa"],
    }


def _fallback_scores(combined_text: str) -> Dict[str, Any]:
    lowered = combined_text.lower()
    total_words = len(lowered.split())
    length_points = min(2, total_words // 60)

    scores = {
        "problem_solving": _score_dimension(
            lowered,
            ("?????", "??????", "?????", "????", "??", "?????"),
            length_points,
        ),
        "execution": _score_dimension(
            lowered,
            ("????", "???", "?????", "?????", "????", "????"),
            length_points,
        ),
        "learning": _score_dimension(
            lowered,
            ("???????", "?????", "?????", "????", "??????", "??????"),
            length_points,
        ),
        "planning": _score_dimension(
            lowered,
            ("??????", "??????", "????", "?????", "???? ????", "?????"),
            length_points,
        ),
        "ai_mindset": _score_dimension(
            lowered,
            ("??? ??????", "ai", "???", "????", "??????", "???????"),
            length_points,
        ),
    }

    rationales = {key: "جمع‌بندی اولیه بر اساس متن پاسخ‌ها انجام شد." for key in DIMENSIONS}
    improvements = [
        "مثال‌های عملی‌تر و جزئیات بیشتری اضافه کن.",
        "معیارهای تصمیم‌گیریت را واضح‌تر بیان کن.",
        "گام‌های اجرا را منظم‌تر توضیح بده.",
    ]
    summary = "بر اساس پاسخ‌ها، سطح آمادگی فعلی مشخص شد و مسیرهای بهبود پیشنهاد می‌شود."

    return {
        "scores": scores,
        "rationales_fa": rationales,
        "improvements_fa": improvements,
        "summary_fa": summary,
    }


def _score_dimension(text: str, keywords: tuple[str, ...], length_points: int) -> int:
    hits = sum(1 for keyword in keywords if keyword in text)
    keyword_points = min(3, hits)
    return min(5, length_points + keyword_points)


def _clamp_score(value: Any) -> int:
    try:
        score = int(value)
    except (TypeError, ValueError):
        return 0
    return max(0, min(5, score))
