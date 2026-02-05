from typing import Any, Dict, List
import json
from pathlib import Path
import streamlit as st


def _load_question_bank() -> Dict[str, Any]:
    path = Path(__file__).resolve().parents[1] / "data" / "question_bank.v1.1.json"
    if not path.exists():
        return {"skills": [], "questions": [], "interviewPlans": {}}
    raw = path.read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    return data if isinstance(data, dict) else {"skills": [], "questions": [], "interviewPlans": {}}


def _build_question_index(questions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    index: Dict[str, Dict[str, Any]] = {}
    for q in questions:
        if isinstance(q, dict) and q.get("id"):
            index[str(q["id"])] = q
    return index


def _build_questions(level: str, bank: Dict[str, Any]) -> List[Dict[str, Any]]:
    plans = bank.get("interviewPlans", {}) if isinstance(bank.get("interviewPlans"), dict) else {}
    plan = plans.get(level, {}) if isinstance(plans.get(level), dict) else {}
    question_ids = plan.get("questionIds")
    if not isinstance(question_ids, list) or not question_ids:
        return []
    questions = list(bank.get("questions", [])) if isinstance(bank.get("questions"), list) else []
    index = _build_question_index(questions)
    selected: List[Dict[str, Any]] = []
    for qid in question_ids:
        q = index.get(str(qid))
        if q:
            selected.append(q)
    return selected


def _avg_scores(answers: Dict[str, Any]) -> Dict[str, int]:
    accum: Dict[str, List[int]] = {}
    for item in answers.values():
        if not isinstance(item, dict):
            continue
        skill = item.get("skillTarget")
        score = item.get("score")
        if skill is None or score is None:
            continue
        accum.setdefault(skill, []).append(int(score))
    output: Dict[str, int] = {}
    for k, vals in accum.items():
        output[k] = int(round(sum(vals) / max(1, len(vals))))
    return output


def render_interview_v2(on_finish) -> None:
    st.subheader("مصاحبه چندگزینه‌ای")
    level = st.radio(
        "سطح مصاحبه را انتخاب کنید",
        ["beginner", "intermediate", "advanced"],
        index=0,
        key="mcq_level",
    )
    goal_horizon = st.selectbox("هدف زمانی شما", ["درآمد سریع", "3 ماه", "6 ماه", "12 ماه"], index=1)
    time_per_week = st.number_input("زمان آزاد هفتگی (ساعت)", min_value=1, max_value=40, value=6, step=1)

    bank = _load_question_bank()
    if not bank.get("interviewPlans"):
        st.error("ساختار interviewPlans در فایل سوالات پیدا نشد.")
        return

    questions = _build_questions(level, bank)
    if st.session_state.get("mcq_questions_count") != len(questions):
        st.session_state["mcq_index"] = 0
        st.session_state["mcq_answers"] = {}
    st.session_state["mcq_questions"] = questions
    st.session_state["mcq_questions_count"] = len(questions)

    st.session_state.setdefault("mcq_index", 0)
    st.session_state.setdefault("mcq_answers", {})
    idx = int(st.session_state.get("mcq_index", 0))
    if questions:
        idx = min(max(idx, 0), len(questions) - 1)

    if not questions:
        st.error("برای این سطح سوالی تعریف نشده است.")
        return

    q = questions[idx]
    qid = q.get("id", str(idx))
    skill = q.get("skillTarget")
    v = q.get("versions", {}).get(level, {})
    qtext = v.get("questionFa", "")
    options = v.get("options", [])

    st.caption(f"سوال {idx + 1} از {len(questions)}")
    st.markdown(qtext)

    labels = [f"{opt.get('key')}) {opt.get('text')}" for opt in options]
    current = st.session_state["mcq_answers"].get(qid, {})
    current_key = current.get("key")
    default_index = 0
    if current_key:
        for i, opt in enumerate(options):
            if opt.get("key") == current_key:
                default_index = i
                break
    choice = st.radio("گزینه", labels, index=default_index, key=f"mcq_{qid}")
    sel_idx = labels.index(choice) if choice in labels else 0
    sel = options[sel_idx]
    st.session_state["mcq_answers"][qid] = {
        "skillTarget": skill,
        "key": sel.get("key"),
        "score": sel.get("score"),
        "text": sel.get("text"),
    }

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("قبلی", disabled=idx == 0):
            st.session_state["mcq_index"] = max(0, idx - 1)
            return
    with col2:
        if st.button("بعدی", disabled=idx >= len(questions) - 1):
            st.session_state["mcq_index"] = min(len(questions) - 1, idx + 1)
            return
    with col3:
        if st.button("پایان مصاحبه", disabled=idx < len(questions) - 1):
            scores = _avg_scores(st.session_state["mcq_answers"])
            on_finish({
                "level": level,
                "scores": scores,
                "goalHorizon": goal_horizon,
                "timePerWeek": int(time_per_week),
            })
            return
