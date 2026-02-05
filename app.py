import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import streamlit as st

from core.interview_v2_ai_scoring import score_core_answers

from core.course_recommender_v2 import recommend_courses
from core.admin_store import upsert_user_record
from core.gap_engine import SkillGapEngine
from core.job_filter import filter_job_mapping_by_track
from core.job_mapper import load_rules, map_jobs_from_gap
from core.level_engine import determine_levels
from core.track_selector import select_track
from core.user_feedback_generator import AvalAIClient, generate_user_feedback
from core.loader import load_skills
from core.models import Skill
from core.service import filter_skills, list_categories
from core.training_level import determine_training_level
from ui.interview_v2 import render_interview_v2
from ui.auth_page import render_auth_page
from ui.landing_page import render_landing_page
from ui.profile_form import render_profile_form
from ui.results_page import render_results_page
from ui.skills import render_skill_list
from ui.theme import apply_global_theme, render_top_bar, safe_text

DATA_PATH = Path(__file__).parent / "data" / "skills.json"
GAPS_PATH = Path(__file__).parent / "data" / "gaps" / "content_ai_gaps.json"
STEPS = (
    ("landing", "\u0645\u0639\u0631\u0641\u06cc"),
    ("auth", "\u062b\u0628\u062a\u200c\u0646\u0627\u0645"),
    ("profile", "\u067e\u0631\u0648\u0641\u0627\u06cc\u0644"),
    ("interview", "\u0645\u0635\u0627\u062d\u0628\u0647"),
    ("skill_map", "\u0646\u0642\u0634\u0647 \u0645\u0647\u0627\u0631\u062a"),
    ("results", "\u0646\u062a\u0627\u06cc\u062c"),
)

DIGITAL_LABELS = {
    "weak": "\u0636\u0639\u06cc\u0641",
    "medium": "\u0645\u062a\u0648\u0633\u0637",
    "good": "\u062e\u0648\u0628",
}
GOAL_LABELS = {
    "quick_income": "\u062f\u0631\u0622\u0645\u062f \u0633\u0631\u06cc\u0639",
    "career_upgrade": "\u0627\u0631\u062a\u0642\u0627\u06cc \u0634\u063a\u0644\u06cc",
    "technical_switch": "\u062a\u063a\u06cc\u06cc\u0631 \u0645\u0633\u06cc\u0631 \u0641\u0646\u06cc",
}

DEBUG = False


@st.cache_data
def get_skills() -> list[Skill]:
    return load_skills(DATA_PATH)


@st.cache_data
def get_course_catalog() -> dict:
    catalog_path = Path(__file__).parent / "data" / "course_catalog_fa.json"
    if catalog_path.exists():
        try:
            return json.loads(catalog_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            pass
    rules = load_rules()
    return rules.get("course_catalog", {})


@st.cache_data
def get_gap_catalog() -> dict:
    if not GAPS_PATH.exists():
        return {}
    return json.loads(GAPS_PATH.read_text(encoding="utf-8"))


def _init_state() -> None:
    st.session_state.setdefault("current_step", STEPS[0][0])
    if "profile" in st.session_state and "profile_completed" not in st.session_state:
        st.session_state["profile_completed"] = True
    if "interview_result" in st.session_state and "interview_completed" not in st.session_state:
        st.session_state["interview_completed"] = True
    st.session_state.setdefault("auth_completed", False)
    st.session_state.setdefault("registered", isinstance(st.session_state.get("user"), dict))
    st.session_state.setdefault("logged_in", False)
    if st.session_state.get("logged_in", False):
        st.session_state["auth_completed"] = True
    st.session_state.setdefault("auth_mode", "register")
    st.session_state.setdefault("profile_completed", False)
    st.session_state.setdefault("interview_completed", False)
    st.session_state.setdefault("steps_collapsed", False)


def _persist_user_snapshot(step: str, extra: Optional[Dict[str, Any]] = None) -> None:
    user_id = st.session_state.get("user_id")
    if not user_id:
        return
    payload: Dict[str, Any] = {
        "current_step": step,
        "profile_completed": bool(st.session_state.get("profile_completed")),
        "interview_completed": bool(st.session_state.get("interview_completed")),
    }
    user = st.session_state.get("user")
    if isinstance(user, dict) and user.get("name"):
        payload["name"] = user.get("name")
    if extra:
        payload.update(extra)
    upsert_user_record(str(user_id), payload)


def _reset_flow() -> None:
    st.session_state["current_step"] = "landing"
    st.session_state["auth_completed"] = False
    st.session_state["registered"] = False
    st.session_state["logged_in"] = False
    st.session_state["auth_mode"] = "register"
    st.session_state["profile_completed"] = False
    st.session_state["interview_completed"] = False
    for key in (
        "profile",
        "interview_scores",
        "interview_answers",
        "interview_v2_answers",
        "mcq_answers",
        "mcq_index",
        "mcq_questions",
        "gap",
        "skill_gaps",
        "job_mapping",
        "job_mapping_filtered",
        "user_feedback",
    ):
        st.session_state.pop(key, None)


def _logout() -> None:
    st.session_state["logged_in"] = False
    st.session_state["auth_completed"] = False
    st.session_state["current_step"] = "auth"
    st.session_state["auth_mode"] = "login"
    st.session_state["profile_completed"] = False
    st.session_state["interview_completed"] = False
    for key in (
        "user",
        "user_id",
        "profile",
        "interview_scores",
        "interview_result",
        "interview_answers",
        "interview_v2_answers",
        "mcq_answers",
        "mcq_index",
        "mcq_questions",
        "gap",
        "skill_gaps",
        "job_mapping",
        "job_mapping_filtered",
        "user_feedback",
        "course_recommendation",
        "recommended_jobs",
    ):
        st.session_state.pop(key, None)


def _step_label(step_key: str) -> str:
    for key, label in STEPS:
        if key == step_key:
            return label
    return step_key


def _is_locked(step_key: str) -> bool:
    if step_key == "landing":
        return False
    if step_key != "auth" and not st.session_state.get("auth_completed", False):
        return True
    if step_key == "interview":
        return not st.session_state.get("profile_completed", False)
    if step_key in ("skill_map", "results"):
        return not st.session_state.get("interview_completed", False)
    return False


def _go_to_step(step: str) -> None:
    if step not in {key for key, _ in STEPS}:
        return
    if _is_locked(step):
        return
    st.session_state["current_step"] = step


def _enforce_step() -> None:
    current = st.session_state.get("current_step", STEPS[0][0])
    if not _is_locked(current):
        return
    if not st.session_state.get("auth_completed", False):
        st.session_state["current_step"] = "auth"
    elif not st.session_state.get("profile_completed", False):
        st.session_state["current_step"] = "profile"
    else:
        st.session_state["current_step"] = "interview"


def _ensure_interview_state(question_count: int) -> None:
    st.session_state.setdefault("interview_index", 0)
    if "interview_answers" not in st.session_state:
        st.session_state["interview_answers"] = [""] * question_count
        return

    answers = st.session_state["interview_answers"]
    if len(answers) < question_count:
        answers = answers + [""] * (question_count - len(answers))
    elif len(answers) > question_count:
        answers = answers[:question_count]
    st.session_state["interview_answers"] = answers


def _selector_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    digital_raw = str(profile.get("digital_level", "")).strip()
    goal_raw = str(profile.get("goal") or profile.get("goal_type") or "").strip()
    digital_label = DIGITAL_LABELS.get(digital_raw, digital_raw or "\u0646\u0627\u0645\u0634\u062e\u0635")
    goal_label = GOAL_LABELS.get(goal_raw, goal_raw or "\u0646\u0627\u0645\u0634\u062e\u0635")
    return {"digital_level": digital_label, "goal": goal_label}


def _training_inputs(profile: Dict[str, Any], scores: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any]]:
    training_profile = _selector_profile(profile)
    training_scores = {
        "execution": int(scores.get("execution", 0)),
        "problem_solving": int(scores.get("problem_solving", 0)),
        "learning": int(scores.get("learning", 0)),
        "planning": int(scores.get("planning", 0)),
        "ai_mindset": int(scores.get("ai_mindset", 0)),
    }
    return training_profile, training_scores


def _get_course_codes() -> List[str]:
    candidates = ["recommended_course_codes", "recommended_courses", "course_codes"]
    for key in candidates:
        payload = st.session_state.get(key)
        if isinstance(payload, list):
            if all(isinstance(item, (str, int)) for item in payload):
                return [str(item) for item in payload]
            codes = []
            for item in payload:
                if isinstance(item, dict):
                    code = item.get("code") or item.get("course_code") or item.get("id")
                    if code is not None:
                        codes.append(str(code))
            if codes:
                return codes
    return []


def _get_blocked_codes() -> List[str]:
    candidates = ["blocked_courses", "blocked_course_codes"]
    for key in candidates:
        payload = st.session_state.get(key)
        if isinstance(payload, list):
            if all(isinstance(item, (str, int)) for item in payload):
                return [str(item) for item in payload]
            codes = []
            for item in payload:
                if isinstance(item, dict):
                    code = item.get("code") or item.get("course_code") or item.get("id")
                    if code is not None:
                        codes.append(str(code))
            if codes:
                return codes
    return []



def _get_route_answers() -> Dict[str, str]:
    answers = st.session_state.get("interview_v2_answers")
    if not isinstance(answers, dict):
        answers = {}
    goal = answers.get("ROUTE_Q5", {}).get("choice") if isinstance(answers.get("ROUTE_Q5"), dict) else ""
    weekly_time = answers.get("ROUTE_Q6", {}).get("choice") if isinstance(answers.get("ROUTE_Q6"), dict) else ""
    preference = answers.get("ROUTE_Q7", {}).get("choice") if isinstance(answers.get("ROUTE_Q7"), dict) else ""
    if goal or weekly_time or preference:
        return {"goal": str(goal or ""), "weekly_time": str(weekly_time or ""), "preference": str(preference or "")}

    profile = st.session_state.get("profile") if isinstance(st.session_state.get("profile"), dict) else {}
    goal_type = str(profile.get("goal_type") or "")
    goal_map = {
        "quick_income": "درآمد سریع",
        "career_upgrade": "ارتقای شغلی",
        "technical_switch": "تغییر مسیر فنی",
    }
    goal = goal_map.get(goal_type, "")

    weekly_hours = profile.get("weekly_time_budget_hours")
    weekly_time = ""
    try:
        hours = int(weekly_hours)
        if hours <= 2:
            weekly_time = "۱–۲ ساعت"
        elif hours <= 5:
            weekly_time = "۳–۵ ساعت"
        elif hours <= 10:
            weekly_time = "۶–۱۰ ساعت"
        else:
            weekly_time = "بیشتر از ۱۰ ساعت"
    except (TypeError, ValueError):
        weekly_time = ""

    preference = str(profile.get("preference") or "")
    return {"goal": goal, "weekly_time": weekly_time, "preference": preference}


def _build_interview_result(profile: Dict[str, Any], scores: Dict[str, Any]) -> Dict[str, Any]:
    goal_map = {
        "quick_income": "درآمد سریع",
        "career_upgrade": "3 ماه",
        "technical_switch": "6 ماه",
    }
    goal_horizon = goal_map.get(str(profile.get("goal_type") or ""), "12 ماه")
    time_per_week = 0
    try:
        time_per_week = int(profile.get("weekly_time_budget_hours") or 0)
    except (TypeError, ValueError):
        time_per_week = 0

    def _scale(value: Any) -> int:
        try:
            return max(0, min(100, int(value) * 20))
        except (TypeError, ValueError):
            return 0

    interview_scores = {
        "ai_literacy": _scale(scores.get("ai_mindset")),
        "prompting": _scale(scores.get("execution")),
        "office_tools": _scale(scores.get("planning")),
        "data_basics": _scale(scores.get("problem_solving")),
        "bi_tools": 0,
        "sql": 0,
        "programming": _scale(scores.get("learning")),
        "english": 0,
        "soft_skills": _scale(scores.get("planning")),
        "content_marketing": 0,
        "automation_tools": _scale(scores.get("execution")),
        "api_basics": _scale(scores.get("learning")),
        "process_thinking": _scale(scores.get("problem_solving")),
        "sales_crm": 0,
        "analytics": _scale(scores.get("problem_solving")),
        "design_tools": 0,
        "math_stats": _scale(scores.get("learning")),
        "ml_basics": _scale(scores.get("learning")),
        "communication": _scale(scores.get("planning")),
        "portfolio": _scale(scores.get("execution")),
    }

    return {
        "timePerWeek": time_per_week,
        "goalHorizon": goal_horizon,
        "scores": interview_scores,
    }


def _flatten_interview_answers(answers: Dict[str, Any]) -> str:
    if not isinstance(answers, dict):
        return ""
    parts: List[str] = []
    for value in answers.values():
        if isinstance(value, dict):
            choice = value.get("choice")
            if choice:
                parts.append(str(choice))
            choices = value.get("choices")
            if isinstance(choices, list):
                parts.extend(str(item) for item in choices if item)
            text = value.get("text")
            if text:
                parts.append(str(text))
        else:
            parts.append(str(value))
    return "\n".join(part for part in parts if part)


def _ensure_gap(decision: Dict[str, Any], interview_scores: Dict[str, Any]) -> Dict[str, Any]:
    gap: Dict[str, Any] = {}
    scores_payload = {
        "execution": int(interview_scores.get("execution", 0)),
        "problem_solving": int(interview_scores.get("problem_solving", 0)),
        "learning": int(interview_scores.get("learning", 0)),
        "planning": int(interview_scores.get("planning", 0)),
        "ai_mindset": int(interview_scores.get("ai_mindset", 0)),
    }
    gap["interview_scores"] = scores_payload

    existing = st.session_state.get("gap")
    recommended: List[str] = []
    blocked: List[str] = []
    if isinstance(existing, dict):
        previous = existing.get("recommended_courses")
        if isinstance(previous, list):
            recommended = [str(code) for code in previous]
        previous_blocked = existing.get("blocked_courses")
        if isinstance(previous_blocked, list):
            blocked = [str(code) for code in previous_blocked]

    if not recommended:
        recommended = _get_course_codes()

    track = st.session_state.get("track")
    needs_longer_plan = False
    route = _get_route_answers()
    if not track:
        track_info = select_track(route.get("goal", ""), route.get("weekly_time", ""), route.get("preference", ""))
        track = track_info.get("track")
        needs_longer_plan = bool(track_info.get("needs_longer_plan"))
        if track:
            st.session_state["track"] = track
            st.session_state["track_meta"] = track_info
    else:
        meta = st.session_state.get("track_meta")
        if isinstance(meta, dict):
            needs_longer_plan = bool(meta.get("needs_longer_plan"))

    levels = determine_levels(scores_payload, str(track or ""))
    gap["training_level"] = levels["training_level"]
    gap["readiness_level"] = levels["readiness_level"]
    gap["levels_note_fa"] = levels["note_fa"]

    gap["weekly_time"] = route.get("weekly_time", "")
    gap["goal"] = route.get("goal", "")
    gap["preference"] = route.get("preference", "")
    profile = st.session_state.get("profile")
    if isinstance(profile, dict):
        gap["profile"] = profile

    if not recommended:
        course_payload = recommend_courses(
            gap["training_level"],
            str(track or "automation"),
            route.get("weekly_time"),
            route.get("goal"),
        )
        recommended = course_payload.get("recommended_courses", [])
        blocked = course_payload.get("blocked_courses", [])
        st.session_state["course_recommendation"] = course_payload

    if not blocked:
        blocked = _get_blocked_codes()

    gap["recommended_courses"] = _dedupe([str(code) for code in recommended])
    if blocked:
        gap["blocked_courses"] = _dedupe([str(code) for code in blocked])
    if track:
        gap["track"] = str(track)

    st.session_state["gap"] = gap
    return gap


def _dedupe(values: List[str]) -> List[str]:
    seen = set()
    output = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def _course_titles(codes: Iterable[str], course_catalog: Dict[str, Any]) -> List[str]:
    titles = []
    for code in codes:
        meta = course_catalog.get(code, {})
        title = meta.get("title_fa") if isinstance(meta, dict) else None
        if isinstance(title, str):
            titles.append(f"{code} ({title})")
        else:
            titles.append(str(code))
    return titles


def _render_job_mapping(decision: Dict[str, Any], interview_scores: Dict[str, Any], show_level: bool = True) -> None:
    st.subheader("نقشه مهارت")
    if show_level:
        st.caption(
            f"سطح فعلی شما: {decision['label_fa']} (سطح {decision['training_level']})"
        )

    gap = st.session_state.get("gap")
    if not isinstance(gap, dict) or not gap.get("recommended_courses"):
        gap = _ensure_gap(decision, interview_scores)

    if not gap.get("recommended_courses"):
        st.info(
            "هنوز دوره‌های پیشنهادی ثبت نشده است. برای ادامه، پروفایل و مصاحبه را کامل کنید."
        )

    results = map_jobs_from_gap(gap, top_k=3)
    st.session_state["job_mapping"] = results
    course_catalog = get_course_catalog()

    if DEBUG:
        st.markdown("### DEBUG")
        st.code(json.dumps(gap, ensure_ascii=False, indent=2), language="json")
        recommended = gap.get("recommended_courses", [])
        st.caption(f"recommended_courses: {len(recommended)}")
        types = {type(code).__name__ for code in recommended}
        st.caption(f"code types: {', '.join(sorted(types)) if types else 'empty'}")

    st.markdown("### شغل‌های قابل دسترس")
    reachable = results.get("reachable_jobs", [])
    if not reachable:
        st.info("هنوز شغل قابل دسترس نمایش داده نشده است.")
    else:
        for job in reachable:
            st.markdown(f"**{job['title_fa']}** ? امتیاز {job['match_score']}/100")
            for reason in job.get("why_fa", []):
                st.markdown(f"- {reason}")
            missing = job.get("missing_courses", [])
            if missing:
                st.caption(
                    f"دوره‌های لازم برای تکمیل: {', '.join(_course_titles(missing, course_catalog))}"
                )
            next_courses = job.get("next_courses_to_unlock", [])
            if next_courses:
                st.caption(
                    f"برای باز شدن سریع‌تر: {', '.join(_course_titles(next_courses, course_catalog))}"
                )
            st.divider()

    st.markdown("### شغل‌های سطح بعدی")
    next_level = results.get("next_level_jobs", [])
    if not next_level:
        st.info("فعلاً شغل سطح بعدی نمایش داده نشده است.")
    else:
        for job in next_level:
            st.markdown(f"**{job['title_fa']}**")
            for reason in job.get("why_fa", []):
                st.markdown(f"- {reason}")
            unlock = job.get("unlock_with", [])
            if unlock:
                st.caption(
                    f"برای باز شدن: {', '.join(_course_titles(unlock, course_catalog))}"
                )
            st.divider()


def _render_user_feedback(report: Dict[str, Any]) -> None:
    st.markdown("### گزارش تحلیلی")
    summary = report.get("summary_fa", "")
    if summary:
        st.write(summary)

    strengths = report.get("strengths_fa", [])
    if strengths:
        st.markdown("**نقاط قوت:**")
        for item in strengths:
            st.markdown(f"- {item}")

    gaps = report.get("gaps_fa", [])
    if gaps:
        st.markdown("**اولویت‌های یادگیری:**")
        for item in gaps:
            st.markdown(f"- {item}")

    next_actions = report.get("next_actions_fa", [])
    if next_actions:
        st.markdown("**گام‌های بعدی:**")
        for action in next_actions:
            title = action.get("title", "گام")
            timeframe = action.get("timeframe", "")
            with st.expander(safe_text(f"{title} ({timeframe})")):
                steps = action.get("steps", [])
                for step in steps:
                    st.markdown(f"- {step}")

    course_plan = report.get("course_plan_fa", [])
    if course_plan:
        st.markdown("**مسیر آموزشی:**")
        for phase in course_plan:
            phase_title = phase.get("phase", "")
            st.markdown(f"**{phase_title}**")
            for course in phase.get("courses", []):
                code = course.get("code", "")
                title = course.get("title", "")
                why = course.get("why", "")
                st.markdown(f"- {code} ({title}) - {why}")

    job_path = report.get("job_path_fa", {})
    if isinstance(job_path, dict):
        target = job_path.get("target_job", {})
        if target:
            st.markdown("**شغل هدف:**")
            st.markdown(f"- {target.get('title', '')}: {target.get('why_fit', '')}")

        reachable = job_path.get("reachable_now", [])
        if reachable:
            st.markdown("**شغل‌های قابل دسترس:**")
            for item in reachable:
                st.markdown(f"- {item.get('title', '')}: {item.get('why', '')}")

        next_level = job_path.get("next_level", [])
        if next_level:
            st.markdown("**شغل‌های سطح بعدی:**")
            for item in next_level:
                unlock = item.get("unlock_with", [])
                unlock_text = ", ".join(unlock) if unlock else ""
                st.markdown(f"- {item.get('title', '')}: {unlock_text}")

    warnings = report.get("warnings_fa", [])
    if warnings:
        st.markdown("**هشدارها:**")
        for warning in warnings:
            st.markdown(f"- {warning}")

    st.button("دانلود گزارش", disabled=True)
def _render_interview_results() -> None:
    if not st.session_state.get("interview_completed"):
        st.warning("ابتدا مصاحبه را تکمیل کنید تا نتایج نمایش داده شود.")
        if st.button("رفتن به مصاحبه"):
            st.session_state["current_step"] = "interview"
            st.rerun()
        return

    scores = st.session_state.get("interview_scores")
    if not isinstance(scores, dict) or not scores:
        st.info("هنوز امتیاز مصاحبه ثبت نشده است. لطفاً مصاحبه را کامل کنید.")
        return

    profile = st.session_state.get("profile") or {}
    training_profile, training_scores = _training_inputs(profile, scores)

    decision = st.session_state.get("training_level_decision")
    if not isinstance(decision, dict):
        decision = determine_training_level(training_profile, training_scores)
        st.session_state["training_level_decision"] = decision

    track = st.session_state.get("track")
    if not track:
        route = _get_route_answers()
        track_info = select_track(route.get("goal", ""), route.get("weekly_time", ""), route.get("preference", ""))
        track = track_info.get("track")
        st.session_state["track"] = track
        st.session_state["track_meta"] = track_info

    gap = _ensure_gap(decision, training_scores)
    job_mapping = st.session_state.get("job_mapping")
    if not isinstance(job_mapping, dict):
        job_mapping = map_jobs_from_gap(gap)
        st.session_state["job_mapping"] = job_mapping

    filtered_jm = filter_job_mapping_by_track(job_mapping, gap.get("track", ""))
    st.session_state["job_mapping_filtered"] = filtered_jm

    interview_payload = st.session_state.get("interview_v2_payload", {})
    interview_questions: List[Dict[str, Any]] = []
    if isinstance(interview_payload, dict):
        interview_questions = list(interview_payload.get("questions", []))
    interview_answers = st.session_state.get("interview_v2_answers", {})

    gap_catalog = st.session_state.get("gap_catalog")
    if not isinstance(gap_catalog, dict):
        gap_catalog = get_gap_catalog()
        if gap_catalog:
            st.session_state["gap_catalog"] = gap_catalog
    if isinstance(gap_catalog, dict) and gap_catalog and "skill_gaps" not in st.session_state:
        gap_engine = SkillGapEngine(gap_catalog)
        answers_text = _flatten_interview_answers(interview_answers if isinstance(interview_answers, dict) else {})
        st.session_state["skill_gaps"] = gap_engine.evaluate_gaps(
            answers_text,
            gap.get("interview_scores", {}),
            evidence=None,
        )

    course_catalog = get_course_catalog()
    report = generate_user_feedback(
        gap=gap,
        interview_questions=interview_questions,
        interview_answers=interview_answers if isinstance(interview_answers, dict) else {},
        job_mapping=filtered_jm,
        course_catalog=course_catalog,
        avalai_client=AvalAIClient(),
    )
    st.session_state["user_feedback"] = report
    _persist_user_snapshot(
        "results",
        {
            "results_generated": True,
            "gap": gap,
            "job_mapping": filtered_jm,
            "user_feedback": report,
            "skill_gaps": st.session_state.get("skill_gaps"),
            "interview_result": st.session_state.get("interview_result"),
        },
    )
    render_results_page(course_catalog=course_catalog, debug=False)


def _handle_interview_mcq_finish(payload: Dict[str, Any]) -> None:
    level = str(payload.get("level") or "beginner")
    scores = payload.get("scores", {}) if isinstance(payload.get("scores"), dict) else {}

    profile = st.session_state.get("profile") or {}
    goal_map = {
        "quick_income": "درآمد سریع",
        "career_upgrade": "3 ماه",
        "technical_switch": "6 ماه",
    }
    goal_horizon = str(payload.get("goalHorizon") or "").strip()
    if not goal_horizon:
        goal_horizon = goal_map.get(str(profile.get("goal_type") or ""), "12 ماه")
    try:
        time_per_week = int(payload.get("timePerWeek") or 0)
    except (TypeError, ValueError):
        time_per_week = 0
    if not time_per_week:
        try:
            time_per_week = int(profile.get("weekly_time_budget_hours") or 0)
        except (TypeError, ValueError):
            time_per_week = 0

    st.session_state["interview_result"] = {
        "level": level,
        "scores": scores,
        "timePerWeek": time_per_week,
        "goalHorizon": goal_horizon,
    }
    st.session_state["interview_completed"] = True

    # minimal interview_scores for existing pipelines
    st.session_state["interview_scores"] = {
        "execution": int(scores.get("prompting", 0) / 20),
        "problem_solving": int(scores.get("data_basics", 0) / 20),
        "learning": int(scores.get("ai_literacy", 0) / 20),
        "planning": int(scores.get("office_tools", 0) / 20),
        "ai_mindset": int(scores.get("ai_literacy", 0) / 20),
    }

    _persist_user_snapshot(
        "interview",
        {
            "profile": st.session_state.get("profile"),
            "interview_answers": st.session_state.get("mcq_answers", {}),
            "interview_scores": st.session_state.get("interview_scores"),
            "interview_result": st.session_state.get("interview_result"),
            "interview_completed": True,
        },
    )

def _handle_interview_v2_finish(answers: Dict[str, Any], core_questions: List[Dict[str, Any]]) -> None:
    with st.spinner("\u062f\u0631 \u062d\u0627\u0644 \u062a\u062d\u0644\u06cc\u0644 \u067e\u0627\u0633\u062e\u200c\u0647\u0627..."):
        scoring = score_core_answers(answers, core_questions)

    scores = scoring.get("scores", {})
    # If scoring failed or returned zeros, boost with answer length to reflect effort
    answers_text = _flatten_interview_answers(answers if isinstance(answers, dict) else {})
    total_words = len(str(answers_text).split())
    length_base = 0
    if total_words >= 80:
        length_base = 2
    if total_words >= 140:
        length_base = 3
    if total_words >= 220:
        length_base = 4
    if total_words >= 320:
        length_base = 5
    if scores and all(int(scores.get(k, 0)) == 0 for k in scores.keys()):
        for k in scores.keys():
            scores[k] = max(int(scores.get(k, 0)), length_base)
    st.session_state["interview_scores"] = scores
    st.session_state["interview_result"] = _build_interview_result(
        st.session_state.get("profile") or {},
        scores,
    )
    st.session_state["interview_feedback"] = {
        "rationales_fa": scoring.get("rationales_fa", {}),
        "improvements_fa": scoring.get("improvements_fa", []),
        "summary_fa": scoring.get("summary_fa", ""),
    }

    profile = st.session_state.get("profile") or {}
    training_profile, training_scores = _training_inputs(profile, scores)
    decision = determine_training_level(training_profile, training_scores)
    st.session_state["training_level_decision"] = decision

    goal = answers.get("ROUTE_Q5", {}).get("choice", "")
    weekly_time = answers.get("ROUTE_Q6", {}).get("choice", "")
    preference = answers.get("ROUTE_Q7", {}).get("choice", "")
    track_info = select_track(str(goal), str(weekly_time), str(preference))
    st.session_state["track"] = track_info.get("track")
    st.session_state["track_meta"] = track_info

    levels = determine_levels(scores, track_info.get("track"))
    course_payload = recommend_courses(
        levels["training_level"],
        str(track_info.get("track") or "automation"),
        weekly_time,
        goal,
    )
    st.session_state["course_recommendation"] = course_payload

    gap: Dict[str, Any] = {
        "training_level": levels["training_level"],
        "readiness_level": levels["readiness_level"],
        "levels_note_fa": levels["note_fa"],
        "weekly_time": str(weekly_time),
        "goal": str(goal),
        "preference": str(preference),
        "recommended_courses": [str(code) for code in course_payload.get("recommended_courses", [])],
        "interview_scores": {
            "execution": int(scores.get("execution", 0)),
            "problem_solving": int(scores.get("problem_solving", 0)),
            "learning": int(scores.get("learning", 0)),
            "planning": int(scores.get("planning", 0)),
            "ai_mindset": int(scores.get("ai_mindset", 0)),
        },
    }
    profile = st.session_state.get("profile")
    if isinstance(profile, dict):
        gap["profile"] = profile
    if track_info.get("track"):
        gap["track"] = str(track_info.get("track"))
    blocked = course_payload.get("blocked_courses", [])
    if blocked:
        gap["blocked_courses"] = [str(code) for code in blocked]

    st.session_state["gap"] = gap
    gap_catalog = get_gap_catalog()
    if gap_catalog:
        st.session_state["gap_catalog"] = gap_catalog
        gap_engine = SkillGapEngine(gap_catalog)
        answers_text = _flatten_interview_answers(answers)
        st.session_state["skill_gaps"] = gap_engine.evaluate_gaps(
            answers_text,
            gap.get("interview_scores", {}),
            evidence=None,
        )
    st.session_state["job_mapping"] = map_jobs_from_gap(gap)
    st.session_state["interview_completed"] = True
    _persist_user_snapshot(
        "interview",
        {
            "profile": profile,
            "interview_answers": answers,
            "interview_scores": gap.get("interview_scores", {}),
            "interview_result": st.session_state.get("interview_result"),
            "course_recommendation": st.session_state.get("course_recommendation"),
            "gap": gap,
            "skill_gaps": st.session_state.get("skill_gaps"),
            "job_mapping": st.session_state.get("job_mapping"),
            "interview_completed": True,
        },
    )
    st.success("\u0645\u0635\u0627\u062d\u0628\u0647 \u062a\u06a9\u0645\u06cc\u0644 \u0634\u062f.")


def _render_interview() -> None:
    render_interview_v2(on_finish=_handle_interview_mcq_finish)
    if st.session_state.get("interview_completed"):
        st.button("\u0631\u0641\u062a\u0646 \u0628\u0647 \u0646\u062a\u0627\u06cc\u062c", on_click=_go_to_step, args=("results",))


def _render_steps_panel(current_step: str) -> None:
    def _completed(step_key: str) -> bool:
        if step_key == "landing":
            return st.session_state.get("auth_completed", False)
        if step_key == "auth":
            return st.session_state.get("auth_completed", False)
        if step_key == "profile":
            return st.session_state.get("profile_completed", False)
        if step_key == "interview":
            return st.session_state.get("interview_completed", False)
        if step_key == "skill_map":
            return current_step == "results"
        return False

    with st.container():
        st.markdown("<div class='sm-nav-anchor'></div>", unsafe_allow_html=True)
        collapsed = bool(st.session_state.get("steps_collapsed", False))
        toggle_label = "\u00bb" if collapsed else "\u00ab"
        st.markdown("<div class='sm-nav-title'>\u0645\u0631\u0627\u062d\u0644</div>", unsafe_allow_html=True)
        if st.button(safe_text(toggle_label), key="toggle_steps"):
            st.session_state["steps_collapsed"] = not collapsed
            if hasattr(st, "rerun"):
                st.rerun()
            else:
                st.experimental_rerun()

        if collapsed:
            st.markdown("<div class='sm-small'>\u0646\u0645\u0627\u06cc\u0634 \u062e\u0644\u0627\u0635\u0647</div>", unsafe_allow_html=True)
            for step_key, label in STEPS:
                locked = _is_locked(step_key)
                done = _completed(step_key)
                current = step_key == current_step
                icon = "\u2713" if done else ("\u25cf" if current else "\u25cb")
                class_name = "current" if current else "locked" if locked else ""
                st.markdown(
                    f"<div class='sm-step {class_name}'><div class='sm-step-label'><span>{icon}</span></div></div>",
                    unsafe_allow_html=True,
                )
            return

        for step_key, label in STEPS:
            locked = _is_locked(step_key)
            done = _completed(step_key)
            current = step_key == current_step
            icon = "\u2713" if done else ("\u25cf" if current else "\u25cb")
            status = (
                "\u062a\u06a9\u0645\u06cc\u0644 \u0634\u062f"
                if done
                else "\u062f\u0631 \u062d\u0627\u0644 \u0627\u0646\u062c\u0627\u0645"
                if current
                else "\u062f\u0631 \u062d\u0627\u0644 \u0633\u0627\u062e\u062a"
                if locked
                else "\u0622\u0645\u0627\u062f\u0647"
            )
            label_safe = safe_text(label)
            status_safe = safe_text(status)
            class_name = "current" if current else "locked" if locked else ""
            st.markdown(
                f"<div class='sm-step {class_name}'><div class='sm-step-label'><span>{icon}</span>{label_safe}</div>"
                f"<div class='sm-step-status'>{status_safe}</div></div>",
                unsafe_allow_html=True,
            )
            if not locked and not current:
                st.button(
                    safe_text("\u0631\u0641\u062a\u0646"),
                    key=f"nav_{step_key}",
                    on_click=_go_to_step,
                    args=(step_key,),
                )

        if not st.session_state.get("auth_completed", False):
            st.info("\u0627\u0628\u062a\u062f\u0627 \u062b\u0628\u062a\u200c\u0646\u0627\u0645 \u0631\u0627 \u06a9\u0627\u0645\u0644 \u06a9\u0646\u06cc\u062f.")
        elif not st.session_state.get("profile_completed", False):
            st.info("\u0627\u0628\u062a\u062f\u0627 \u067e\u0631\u0648\u0641\u0627\u06cc\u0644 \u0631\u0627 \u06a9\u0627\u0645\u0644 \u06a9\u0646\u06cc\u062f.")
        elif not st.session_state.get("interview_completed", False):
            st.info("\u0627\u0628\u062a\u062f\u0627 \u0645\u0635\u0627\u062d\u0628\u0647 \u0631\u0627 \u06a9\u0627\u0645\u0644 \u06a9\u0646\u06cc\u062f.")


def main() -> None:
    apply_global_theme()
    _init_state()
    _enforce_step()

    current_step = st.session_state["current_step"]
    user_label = ""
    if st.session_state.get("logged_in", False):
        user = st.session_state.get("user", {})
        if isinstance(user, dict) and user.get("name"):
            user_label = str(user.get("name"))
    reset_clicked, logout_clicked = render_top_bar(
        _step_label(current_step),
        show_reset=current_step != "landing",
        user_label=user_label,
        show_logout=bool(st.session_state.get("logged_in", False)),
    )
    if reset_clicked:
        _reset_flow()
        if hasattr(st, "rerun"):
            st.rerun()
        else:
            st.experimental_rerun()
    if logout_clicked:
        _logout()
        if hasattr(st, "rerun"):
            st.rerun()
        else:
            st.experimental_rerun()

    if current_step == "landing":
        content_col = st.container()
        steps_col = None
    else:
        collapsed = bool(st.session_state.get("steps_collapsed", False))
        if collapsed:
            steps_col, content_col = st.columns([0.06, 0.94], gap="small")
        else:
            steps_col, content_col = st.columns([0.22, 0.78], gap="small")

    if steps_col is not None:
        with steps_col:
            _render_steps_panel(current_step)

    with content_col:
        if current_step == "landing":
            render_landing_page()
            return

        if current_step == "auth":
            submitted = render_auth_page()
            if submitted:
                _go_to_step("profile")
            return

        if current_step == "profile":
            ready = render_profile_form()
            if ready and "profile" in st.session_state:
                st.session_state["profile_completed"] = True
                _persist_user_snapshot("profile", {"profile": st.session_state.get("profile")})
            st.button("\u0627\u062f\u0627\u0645\u0647", on_click=_go_to_step, args=("interview",), disabled=not ready)
            return

        if current_step == "interview":
            _render_interview()
            return

        if current_step == "results":
            _render_interview_results()
            return

        if current_step == "skill_map":
            scores = st.session_state.get("interview_scores")
            if scores:
                profile = st.session_state.get("profile") or {}
                training_profile, training_scores = _training_inputs(profile, scores)
                decision = determine_training_level(training_profile, training_scores)
                _ensure_gap(decision, training_scores)
                _render_job_mapping(decision, training_scores, show_level=True)
            else:
                st.info(
                    "\u0628\u0631\u0627\u06cc \u0645\u0634\u0627\u0647\u062f\u0647 \u0646\u0642\u0634\u0647 \u0645\u0647\u0627\u0631\u062a\u200c\u0647\u0627\u060c "
                    "\u0627\u0628\u062a\u062f\u0627 \u0645\u0635\u0627\u062d\u0628\u0647 \u0631\u0627 \u06a9\u0627\u0645\u0644 \u06a9\u0646\u06cc\u062f."
                )

            skills = get_skills()
            categories = list_categories(skills)
            with st.expander("\u0641\u06cc\u0644\u062a\u0631 \u0645\u0647\u0627\u0631\u062a\u200c\u0647\u0627"):
                query = st.text_input("\u062c\u0633\u062a\u062c\u0648", key="skill_query")
                category = st.selectbox(
                    "\u062f\u0633\u062a\u0647\u200c\u0628\u0646\u062f\u06cc",
                    options=["\u0647\u0645\u0647"] + categories,
                    key="skill_category",
                )
                min_level = st.slider(
                    "\u062d\u062f\u0627\u0642\u0644 \u0633\u0637\u062d",
                    min_value=1,
                    max_value=5,
                    value=1,
                    key="skill_level",
                )

            filtered = filter_skills(
                skills,
                query=query,
                category=None if category == "\u0647\u0645\u0647" else category,
                min_level=min_level,
            )
            render_skill_list(filtered)
            return


if __name__ == "__main__":
    main()
