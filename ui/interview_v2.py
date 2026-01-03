from typing import Any, Callable, Dict, List

import streamlit as st

from core.interview_v2_question_generator import clear_question_cache, load_interview_questions


def load_interview_questions_v2(profile: Dict[str, Any], force_refresh: bool) -> Dict[str, Any]:
    """Load interview v2 questions, with LLM-generated core questions."""
    return load_interview_questions(profile=profile, force_refresh=force_refresh)


def render_interview_v2(
    on_finish: Callable[[Dict[str, Any], List[Dict[str, Any]]], None]
) -> None:
    """Render Interview v2 step-by-step UI and call on_finish when complete."""
    profile = st.session_state.get("profile") if isinstance(st.session_state.get("profile"), dict) else {}
    force_refresh = st.button("بازسازی سوالات با LLM", key="regen_questions")
    if force_refresh:
        clear_question_cache(profile)
        st.session_state.pop("interview_v2_answers", None)
        st.session_state["interview_v2_index"] = 0
    payload = load_interview_questions_v2(profile, force_refresh=False)
    st.session_state["interview_v2_payload"] = payload
    core_questions = payload.get("core", [])
    routing_questions = payload.get("routing", [])
    meta = payload.get("meta", {})
    ordered: List[Dict[str, Any]] = list(core_questions) + list(routing_questions)

    if not ordered:
        st.error("سوالات مصاحبه پیدا نشد.")
        return

    st.session_state.setdefault("interview_v2_index", 0)
    st.session_state.setdefault("interview_v2_answers", {})
    answers: Dict[str, Any] = st.session_state["interview_v2_answers"]

    index = st.session_state["interview_v2_index"]
    index = min(max(index, 0), len(ordered) - 1)
    question = ordered[index]
    qid = str(question.get("id"))

    st.subheader("مصاحبه هوش مصنوعی")
    if isinstance(meta, dict):
        core_source = str(meta.get("core_source", "fallback"))
        routing_source = str(meta.get("routing_source", "fallback"))
        if core_source.startswith("llm") and routing_source.startswith("llm"):
            st.caption("LLM فعال است (سوالات پویا)")
        else:
            st.caption("LLM غیرفعال است یا پاسخ نامعتبر بود؛ سوالات ثابت نمایش داده می‌شوند.")
        error = meta.get("llm_error")
        if error:
            st.caption(f"LLM خطا: {error}")
    st.caption(f"سوال {index + 1} از {len(ordered)}")
    st.markdown(question.get("text_fa", ""))

    answer_type = question.get("answer_type")
    hint = question.get("hint_fa")
    if hint:
        st.caption(hint)

    current = answers.get(qid, {})
    updated = _render_answer_widget(qid, answer_type, question, current)
    answers[qid] = updated
    st.session_state["interview_v2_answers"] = answers

    col_back, col_next, col_finish = st.columns(3)
    with col_back:
        go_back = st.button("قبلی", disabled=index == 0)
    with col_next:
        go_next = st.button("بعدی", disabled=index >= len(ordered) - 1)
    with col_finish:
        finish = st.button("پایان مصاحبه", disabled=index < len(ordered) - 1)

    if go_back:
        st.session_state["interview_v2_index"] = max(0, index - 1)
        return

    if go_next:
        ok, message = _validate_answer(question, updated)
        if not ok:
            st.error(message)
            return
        st.session_state["interview_v2_index"] = min(len(ordered) - 1, index + 1)
        return

    if finish:
        ok, message = _validate_all(ordered, answers)
        if not ok:
            st.error(message)
            return
        on_finish(answers, list(core_questions))


def _render_answer_widget(
    qid: str,
    answer_type: str,
    question: Dict[str, Any],
    current: Dict[str, Any],
) -> Dict[str, Any]:
    if answer_type == "text":
        value = current.get("text") if isinstance(current, dict) else ""
        text = st.text_area("پاسخ", value=value or "", height=160, key=f"{qid}_text")
        return {"text": text.strip()}

    if answer_type == "single_choice":
        options = question.get("options_fa", [])
        placeholder = "\u062a\u0648\u0636\u06cc\u062d \u06a9\u0648\u062a\u0627\u0647"
        radio_options = [placeholder] + list(options)
        choice = current.get("choice") if isinstance(current, dict) else ""
        index = radio_options.index(choice) if choice in radio_options else 0
        selected = st.radio("\u0627\u0646\u062a\u062e\u0627\u0628 \u06a9\u0646\u06cc\u062f", options=radio_options, index=index, key=f"{qid}_choice")
        return {"choice": "" if selected == placeholder else selected}

    if answer_type == "checkbox+text":
        options = question.get("options_fa", [])
        choices = current.get("choices") if isinstance(current, dict) else []
        if not isinstance(choices, list):
            choices = []
        selected = st.multiselect("انتخاب گزینه ها", options=options, default=choices, key=f"{qid}_choices")
        extra = current.get("text") if isinstance(current, dict) else ""
        text = st.text_input("توضیح کوتاه (اختیاری)", value=extra or "", key=f"{qid}_extra")
        return {"choices": selected, "text": text.strip()}

    return {}


def _validate_answer(question: Dict[str, Any], answer: Dict[str, Any]) -> tuple[bool, str]:
    qid = question.get("id")
    answer_type = question.get("answer_type")

    if answer_type == "text":
        text = str(answer.get("text", "")).strip()
        if not text:
            return False, "پاسخ را کامل کنید."
        if qid in ("CORE_Q2", "CORE_Q4") and len(text) < 40:
            return False, "پاسخ باید حداقل ۸۰ کاراکتر باشد."
        return True, ""

    if answer_type == "single_choice":
        choice = answer.get("choice")
        if not choice:
            return False, "\u0644\u0637\u0641\u0627 \u062d\u062f\u0627\u0642\u0644 \u06cc\u06a9 \u06af\u0632\u06cc\u0646\u0647 \u0627\u0646\u062a\u062e\u0627\u0628 \u06a9\u0646\u06cc\u062f."
        return True, ""

    if answer_type == "checkbox+text":
        choices = answer.get("choices")
        if not choices:
            return False, "حداقل یک گزینه را انتخاب کنید."
        return True, ""

    return True, ""


def _validate_all(questions: List[Dict[str, Any]], answers: Dict[str, Any]) -> tuple[bool, str]:
    for question in questions:
        qid = question.get("id")
        answer = answers.get(qid, {})
        ok, message = _validate_answer(question, answer)
        if not ok:
            return False, f"{question.get('text_fa', '')} - {message}"
    return True, ""
