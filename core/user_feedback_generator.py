import hashlib
import json
import os
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from core.env_loader import load_env

try:
    import streamlit as st
except Exception:  # pragma: no cover - fallback for test/runtime isolation
    st = None


PROMPT_PATH = Path(__file__).parent / "prompts" / "user_feedback_fa.txt"
_FALLBACK_CACHE: Dict[str, Dict[str, Any]] = {}


class AvalAIClient:
    """Minimal AvalAI client for chat/completions."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ) -> None:
        load_env()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY") or os.getenv("AVALAI_API_KEY")
        self.base_url = base_url or os.getenv("AVALAI_BASE_URL", "https://api.avalai.ir/v1").strip()
        if self.base_url.startswith("http://"):
            self.base_url = "https://" + self.base_url[len("http://") :]
        elif not self.base_url.startswith("https://"):
            self.base_url = "https://" + self.base_url.lstrip("/")
        self.model = model or os.getenv("OPENAI_MODEL") or os.getenv("AVALAI_MODEL") or "gpt-4o-mini"

    def chat_completions(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("Missing AvalAI API key.")
        url = self.base_url.rstrip("/") + "/chat/completions"
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body)


def generate_user_feedback(
    gap: Dict[str, Any],
    interview_questions: List[Dict[str, Any]],
    interview_answers: Dict[str, Any],
    job_mapping: Dict[str, Any],
    course_catalog: Dict[str, Any],
    avalai_client: Any,
) -> Dict[str, Any]:
    """Generate user-facing feedback report from GAP + answers."""
    cache = _get_cache()
    cache_key = _build_cache_key(gap, interview_questions, interview_answers, job_mapping)
    if cache_key in cache:
        return cache[cache_key]

    prompt = _build_prompt(
        gap=gap,
        interview_questions=interview_questions,
        interview_answers=interview_answers,
        job_mapping=job_mapping,
        course_catalog=course_catalog,
    )

    report: Optional[Dict[str, Any]] = None
    if avalai_client is not None:
        try:
            report = _call_avalai(avalai_client, prompt)
            report = _validate_report(report, gap)
        except Exception:
            report = None

    if not report:
        report = _fallback_report(gap, job_mapping, course_catalog)

    cache[cache_key] = report
    return report


def _call_avalai(avalai_client: Any, prompt: str) -> Dict[str, Any]:
    payload = {
        "model": getattr(avalai_client, "model", "gpt-4o-mini"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
    }
    if hasattr(avalai_client, "chat_completions"):
        response = avalai_client.chat_completions(payload)
    elif callable(avalai_client):
        response = avalai_client(payload)
    else:
        raise ValueError("Invalid AvalAI client.")

    content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
    if not isinstance(content, str):
        raise ValueError("Invalid AvalAI response content.")
    json_text = _extract_json(content)
    if not json_text:
        raise ValueError("AvalAI response JSON not found.")
    return json.loads(json_text)


def _build_prompt(
    gap: Dict[str, Any],
    interview_questions: List[Dict[str, Any]],
    interview_answers: Dict[str, Any],
    job_mapping: Dict[str, Any],
    course_catalog: Dict[str, Any],
) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8-sig")
    training_level = gap.get("training_level", "")
    track = gap.get("track", "")
    scores = gap.get("interview_scores", {})

    recommended_codes = [str(code) for code in gap.get("recommended_courses", [])]
    recommended_courses_with_titles = _courses_with_titles(recommended_codes, course_catalog)

    reachable_jobs = job_mapping.get("reachable_jobs", [])[:3]
    next_level_jobs = job_mapping.get("next_level_jobs", [])[:3]

    answers_payload = _build_answers_payload(interview_questions, interview_answers)

    mapping = {
        "{{training_level}}": str(training_level),
        "{{track}}": str(track),
        "{{profile}}": json.dumps(gap.get("profile", {}), ensure_ascii=False),
        "{{interview_scores}}": json.dumps(scores, ensure_ascii=False),
        "{{interview_answers}}": json.dumps(answers_payload, ensure_ascii=False),
        "{{recommended_courses_with_titles}}": json.dumps(
            recommended_courses_with_titles, ensure_ascii=False
        ),
        "{{reachable_jobs}}": json.dumps(reachable_jobs, ensure_ascii=False),
        "{{next_level_jobs}}": json.dumps(next_level_jobs, ensure_ascii=False),
    }
    for key, value in mapping.items():
        template = template.replace(key, value)
    return template


def _build_answers_payload(
    interview_questions: List[Dict[str, Any]],
    interview_answers: Dict[str, Any],
) -> List[Dict[str, Any]]:
    if not interview_questions or not interview_answers:
        return []
    use_core = any(str(item.get("id", "")).startswith("CORE_") for item in interview_questions)
    items = []
    for question in interview_questions:
        qid = str(question.get("id", ""))
        if use_core and not qid.startswith("CORE_"):
            continue
        answer = interview_answers.get(qid)
        items.append(
            {
                "id": qid,
                "question": question.get("text_fa", ""),
                "answer": _answer_to_text(answer),
            }
        )
    return items


def _answer_to_text(answer: Any) -> str:
    if not isinstance(answer, dict):
        return str(answer or "")
    choices = answer.get("choices")
    text = answer.get("text")
    if choices:
        joined = "، ".join(str(item) for item in choices)
        if text:
            return f"{joined} | {text}"
        return joined
    if text:
        return str(text)
    if "choice" in answer:
        return str(answer.get("choice") or "")
    return ""


def _validate_report(report: Any, gap: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not isinstance(report, dict):
        return None

    required_keys = [
        "summary_fa",
        "strengths_fa",
        "gaps_fa",
        "next_actions_fa",
        "course_plan_fa",
        "job_path_fa",
    ]
    if any(key not in report for key in required_keys):
        return None

    if not isinstance(report.get("summary_fa"), str):
        return None
    if not isinstance(report.get("strengths_fa"), list):
        return None
    if not isinstance(report.get("gaps_fa"), list):
        return None
    if not isinstance(report.get("next_actions_fa"), list):
        return None
    if not isinstance(report.get("course_plan_fa"), list):
        return None
    if not isinstance(report.get("job_path_fa"), dict):
        return None

    report.setdefault("warnings_fa", [])
    if not isinstance(report.get("warnings_fa"), list):
        report["warnings_fa"] = []

    allowed_codes = {str(code) for code in gap.get("recommended_courses", [])}
    report["course_plan_fa"] = _filter_course_plan(report.get("course_plan_fa", []), allowed_codes)
    return report


def _filter_course_plan(plan: List[Dict[str, Any]], allowed: set[str]) -> List[Dict[str, Any]]:
    cleaned = []
    for phase in plan:
        if not isinstance(phase, dict):
            continue
        courses = []
        for course in phase.get("courses", []) if isinstance(phase.get("courses"), list) else []:
            if not isinstance(course, dict):
                continue
            code = str(course.get("code", "")).strip()
            if code and code in allowed:
                courses.append(course)
        cleaned.append(
            {
                "phase": phase.get("phase", ""),
                "courses": courses,
            }
        )
    return cleaned


def _fallback_report(
    gap: Dict[str, Any],
    job_mapping: Dict[str, Any],
    course_catalog: Dict[str, Any],
) -> Dict[str, Any]:
    level = str(gap.get("training_level", "A"))
    track = str(gap.get("track", ""))
    scores = gap.get("interview_scores", {})
    recommended = [str(code) for code in gap.get("recommended_courses", [])]

    summary = _summary_for_level(level, track)
    gaps = _gaps_from_scores(scores, count=3)
    course_plan = _basic_course_plan(recommended, course_catalog)
    job_path = _basic_job_path(job_mapping)

    return {
        "summary_fa": summary,
        "strengths_fa": [],
        "gaps_fa": gaps,
        "next_actions_fa": [
            {
                "title": "کارهای این هفته",
                "timeframe": "۷ روز",
                "steps": [
                    "روزانه ۲۰ دقیقه تمرین با ابزارهای ساده هوش مصنوعی",
                    "یک نمونه خروجی کوتاه (متن/تصویر) بساز و بازبینی کن",
                ],
            },
            {
                "title": "کارهای دو هفته آینده",
                "timeframe": "۱۴ روز",
                "steps": [
                    "یک مثال واقعی از کار یا علاقه خودت را با AI انجام بده",
                    "برای شروع دوره‌های پیشنهادی برنامه‌ریزی کن",
                ],
            },
        ],
        "course_plan_fa": course_plan,
        "job_path_fa": job_path,
        "warnings_fa": [],
    }


def _summary_for_level(level: str, track: str) -> str:
    if level == "A":
        return "الان در سطح شروع هستی. تمرکز روی پایه‌ها و استفاده درست از ابزارها مهم‌تر از تخصصی‌شدن سریع است."
    if level == "B":
        return "در سطح میانی هستی و با یک مسیر مشخص می‌توانی به خروجی واقعی برسی."
    return "سطح تو برای مسیر تخصصی مناسب است؛ حالا باید روی پروژه و عمق یادگیری کار کنی."


def _gaps_from_scores(scores: Dict[str, Any], count: int = 2) -> List[str]:
    labels = {
        "execution": "مهارت اجرا",
        "problem_solving": "حل مسئله",
        "learning": "یادگیری",
        "planning": "برنامه‌ریزی",
        "ai_mindset": "ذهنیت AI",
    }
    items = []
    for key, label in labels.items():
        value = _safe_int(scores.get(key, 0))
        items.append((value, label))
    items.sort(key=lambda item: item[0])
    return [label for _, label in items[:count]]


def _basic_course_plan(recommended: List[str], course_catalog: Dict[str, Any]) -> List[Dict[str, Any]]:
    fast = recommended[:2]
    upgrade = recommended[2:]
    return [
        {
            "phase": "شروع سریع",
            "courses": _courses_with_titles(fast, course_catalog, include_why=True),
        },
        {
            "phase": "مرحله ارتقا",
            "courses": _courses_with_titles(upgrade, course_catalog, include_why=True),
        },
    ]


def _basic_job_path(job_mapping: Dict[str, Any]) -> Dict[str, Any]:
    reachable = job_mapping.get("reachable_jobs", []) if isinstance(job_mapping, dict) else []
    next_level = job_mapping.get("next_level_jobs", []) if isinstance(job_mapping, dict) else []
    target = reachable[0] if reachable else {}
    return {
        "target_job": {
            "title": target.get("title_fa", ""),
            "why_fit": "با مسیر فعلی و دوره‌های شروع سریع هم‌خوانی دارد.",
        },
        "reachable_now": [
            {"title": job.get("title_fa", ""), "why": "با تکمیل دوره‌های شروع سریع قابل دسترس است."}
            for job in reachable[:3]
        ],
        "next_level": [
            {
                "title": job.get("title_fa", ""),
                "unlock_with": job.get("unlock_with", []),
            }
            for job in next_level[:3]
        ],
    }


def _courses_with_titles(
    codes: Iterable[str],
    course_catalog: Dict[str, Any],
    include_why: bool = False,
) -> List[Dict[str, Any]]:
    items = []
    for code in codes:
        meta = course_catalog.get(str(code), {}) if isinstance(course_catalog, dict) else {}
        title = meta.get("title_fa") if isinstance(meta, dict) else ""
        payload = {"code": str(code), "title": str(title or "")}
        if include_why:
            payload["why"] = "برای تقویت مهارت‌های پایه ضروری است."
        items.append(payload)
    return items


def _build_cache_key(
    gap: Dict[str, Any],
    interview_questions: List[Dict[str, Any]],
    interview_answers: Dict[str, Any],
    job_mapping: Dict[str, Any],
) -> str:
    reachable = job_mapping.get("reachable_jobs", []) if isinstance(job_mapping, dict) else []
    next_level = job_mapping.get("next_level_jobs", []) if isinstance(job_mapping, dict) else []
    answers_payload = _build_answers_payload(interview_questions, interview_answers)
    payload = {
        "scores": gap.get("interview_scores", {}),
        "recommended_courses": gap.get("recommended_courses", []),
        "reachable_jobs": [item.get("title_fa") for item in reachable[:3]],
        "next_level_jobs": [item.get("title_fa") for item in next_level[:3]],
        "answers": answers_payload,
    }
    serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True)
    return hashlib.sha1(serialized.encode("utf-8")).hexdigest()


def _extract_json(content: str) -> Optional[str]:
    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return content[start : end + 1].strip()


def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _get_cache() -> Dict[str, Dict[str, Any]]:
    if st is None:
        return _FALLBACK_CACHE
    if "user_feedback_cache" not in st.session_state:
        st.session_state["user_feedback_cache"] = {}
    return st.session_state["user_feedback_cache"]
