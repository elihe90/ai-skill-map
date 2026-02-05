from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

from core.admin_store import upsert_user_record


BASE_DIR = Path(__file__).resolve().parents[1]

LEVEL_OPTIONS = {
    "beginner": "مبتدی",
    "intermediate": "متوسط",
    "advanced": "پیشرفته",
}

GOAL_OPTIONS = ["درآمد سریع", "3 ماه", "6 ماه", "12 ماه"]


def _load_question_bank() -> Dict[str, Any] | None:
    path = BASE_DIR / "data" / "question_bank.v1.1.json"
    if not path.exists():
        st.error("فایل question_bank.v1.1.json پیدا نشد. لطفاً آن را در data/ قرار دهید.")
        return None
    try:
        raw = path.read_text(encoding="utf-8-sig")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        st.error("خواندن فایل سوالات با خطا روبه‌رو شد. لطفاً فرمت JSON را بررسی کنید.")
        return None
    if not isinstance(data, dict):
        st.error("ساختار فایل سوالات نامعتبر است.")
        return None
    if "interviewPlans" not in data or "questions" not in data:
        st.error("فایل سوالات فاقد بخش interviewPlans یا questions است.")
        return None
    return data


def _build_question_index(questions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for q in questions:
        if isinstance(q, dict) and q.get("id"):
            index[str(q["id"])] = q
    return index


def _compute_scores(
    answer_scores: Dict[str, int],
    question_index: Dict[str, Dict[str, Any]],
    skills: List[str] | None = None,
) -> Dict[str, int]:
    skill_buckets: Dict[str, List[int]] = {}
    for qid, score in answer_scores.items():
        question = question_index.get(qid)
        if not question:
            continue
        skill = question.get("skillTarget")
        if not skill:
            continue
        skill_buckets.setdefault(skill, []).append(int(score))

    scores: Dict[str, int] = {}
    all_skills: List[str] = skills[:] if skills else []
    if not all_skills:
        for question in question_index.values():
            skill = question.get("skillTarget")
            if skill and skill not in all_skills:
                all_skills.append(skill)
    for skill in all_skills:
        values = skill_buckets.get(skill, [])
        scores[skill] = int(round(sum(values) / len(values))) if values else 0
    return scores


def render_interview_page() -> None:
    st.title("مصاحبه مهارتی (نسخه چندگزینه‌ای)")
    st.caption("لطفاً سطح مناسب خود را انتخاب کنید و به سوالات پاسخ دهید.")

    bank = _load_question_bank()
    if not bank:
        return

    interview_plans = bank.get("interviewPlans", {})
    if not isinstance(interview_plans, dict):
        st.error("بخش interviewPlans معتبر نیست.")
        return

    questions = bank.get("questions", [])
    if not isinstance(questions, list):
        st.error("لیست سوالات معتبر نیست.")
        return

    question_index = _build_question_index(questions)

    level = st.radio("سطح شما", list(LEVEL_OPTIONS.keys()), format_func=lambda v: LEVEL_OPTIONS[v])
    goal_horizon = st.selectbox("هدف زمانی شما", GOAL_OPTIONS, index=1)
    time_per_week = st.number_input("زمان آزاد هفتگی (ساعت)", min_value=1, max_value=40, value=6, step=1)

    plan = interview_plans.get(level, {})
    question_ids = plan.get("questionIds") if isinstance(plan, dict) else None
    if not isinstance(question_ids, list) or not question_ids:
        st.error("برای این سطح سوالی تعریف نشده است.")
        return

    st.markdown("---")
    st.subheader("سوالات")

    answers: Dict[str, int] = st.session_state.get("mcq_answers", {})
    for qid in question_ids:
        qid_str = str(qid)
        question = question_index.get(qid_str)
        if not question:
            st.warning(f"سوال با شناسه {qid_str} پیدا نشد.")
            continue
        versions = question.get("versions", {})
        version = versions.get(level, {})
        question_text = version.get("questionFa") or "متن سوال"
        options = version.get("options", [])
        if not isinstance(options, list) or not options:
            st.warning("گزینه‌های سوال ناقص است.")
            continue

        labels = [f"{opt.get('key', '')}) {opt.get('text', '')}" for opt in options]
        scores = [int(opt.get("score", 0)) for opt in options]

        default_index = 0
        stored = answers.get(qid_str)
        if stored in scores:
            default_index = scores.index(stored)

        choice = st.radio(question_text, labels, index=default_index, key=f"mcq_{qid_str}")
        selected_index = labels.index(choice)
        answers[qid_str] = scores[selected_index]

    st.session_state["mcq_answers"] = answers

    if st.button("ثبت و مشاهده نتایج"):
        if len(answers) < len(question_ids):
            st.warning("لطفاً به همه سوالات پاسخ دهید.")
            return
        skills_list = bank.get("skills")
        scores = _compute_scores(answers, question_index, skills_list if isinstance(skills_list, list) else None)
        st.session_state["interview_result"] = {
            "level": level,
            "scores": scores,
            "goalHorizon": goal_horizon,
            "timePerWeek": int(time_per_week),
        }
        st.session_state["interview_completed"] = True
        st.session_state.pop("recommended_jobs", None)
        user_id = st.session_state.get("user_id")
        if user_id:
            upsert_user_record(
                str(user_id),
                {
                    "current_step": "interview",
                    "profile": st.session_state.get("profile"),
                    "interview_answers": st.session_state.get("mcq_answers", {}),
                    "interview_result": st.session_state.get("interview_result"),
                    "interview_completed": True,
                },
            )
        if "current_step" in st.session_state:
            st.session_state["current_step"] = "results"
        st.success("مصاحبه ثبت شد. به صفحه نتایج بروید.")
        if hasattr(st, "rerun"):
            st.rerun()
        else:
            st.experimental_rerun()


render_interview_page()
