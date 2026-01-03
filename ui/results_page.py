from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import streamlit as st

from core.job_probability import calculate_job_probability
from ui.results_v2 import render_results_page_v2
from ui.theme import card_container, safe_text


PRIORITY_ORDER = [
    "GAP_CONTENT_PUBLISHABLE_OUTPUT",
    "GAP_PROMPTING_FOR_CONTENT",
    "GAP_PORTFOLIO_WITH_AI",
    "GAP_CONTENT_PLANNING",
    "GAP_AUDIENCE_FIT_WITH_AI",
    "GAP_MULTIMODAL_CONTENT",
]

LEVEL_LABELS = {
    "A": "\u0622\u0645\u0648\u0632\u0634\u200c\u0647\u0627\u06cc \u0639\u0645\u0648\u0645\u06cc \u0648 \u0627\u0628\u0632\u0627\u0631\u0645\u062d\u0648\u0631",
    "B": "\u0622\u0645\u0648\u0632\u0634\u200c\u0647\u0627\u06cc \u0646\u06cc\u0645\u0647\u200c\u062a\u062e\u0635\u0635\u06cc",
    "C": "\u0622\u0645\u0648\u0632\u0634\u200c\u0647\u0627\u06cc \u062a\u062e\u0635\u0635\u06cc",
}
TRACK_LABELS = {
    "content": "\u062a\u0648\u0644\u06cc\u062f \u0645\u062d\u062a\u0648\u0627",
    "automation": "\u0627\u062a\u0648\u0645\u0627\u0633\u06cc\u0648\u0646",
    "technical": "\u0645\u0633\u06cc\u0631 \u0641\u0646\u06cc",
}
GOAL_LABELS = {
    "quick_income": "\u062f\u0631\u0622\u0645\u062f \u0633\u0631\u06cc\u0639",
    "career_upgrade": "\u0627\u0631\u062a\u0642\u0627\u06cc \u0634\u063a\u0644\u06cc",
    "technical_switch": "\u062a\u063a\u06cc\u06cc\u0631 \u0645\u0633\u06cc\u0631 \u0641\u0646\u06cc",
}
CONFIDENCE_LABELS = {
    "low": "\u06a9\u0645",
    "medium": "\u0645\u062a\u0648\u0633\u0637",
    "high": "\u0628\u0627\u0644\u0627",
}


def render_results_page(course_catalog: Optional[Dict[str, Any]] = None, debug: bool = False) -> None:
    profile = st.session_state.get("profile", {})
    scores = st.session_state.get("interview_scores", {})
    skill_gaps = st.session_state.get("skill_gaps", [])
    courses = st.session_state.get("course_recommendation") or st.session_state.get(
        "recommended_courses", {"quick": [], "upgrade": [], "avoid": []}
    )
    jobs = st.session_state.get("job_mapping", {"target": {}, "now": [], "related": [], "next": []})

    if not isinstance(courses, dict) or not courses:
        courses = {"quick": [], "upgrade": [], "avoid": []}
        gap = st.session_state.get("gap", {})
        if isinstance(gap, dict):
            courses["quick"] = [str(code) for code in gap.get("recommended_courses", [])]
            courses["avoid"] = [str(code) for code in gap.get("blocked_courses", [])]
    else:
        if "recommended_courses" in courses and "quick" not in courses:
            courses = {
                "quick": [str(code) for code in courses.get("recommended_courses", [])],
                "upgrade": [],
                "avoid": [str(code) for code in courses.get("blocked_courses", [])],
            }

    render_results_page_v2(
        profile=profile if isinstance(profile, dict) else {},
        scores=scores if isinstance(scores, dict) else {},
        skill_gaps=skill_gaps,
        courses=courses,
        jobs=jobs if isinstance(jobs, dict) else {},
        course_catalog=course_catalog if isinstance(course_catalog, dict) else None,
        debug=debug,
    )
    return
    job_mapping_payload = st.session_state.get("job_mapping_filtered")
    if not isinstance(job_mapping_payload, dict):
        job_mapping_payload = st.session_state.get("job_mapping")

    payload = normalize_session_payload(
        st.session_state.get("gap"),
        st.session_state.get("user_feedback"),
        job_mapping_payload,
    )
    gap = payload["gap"]
    feedback = payload["feedback"]
    job_mapping = payload["job_mapping"]
    course_catalog = course_catalog if isinstance(course_catalog, dict) else {}

    if debug:
        show_legacy = st.checkbox("\u0646\u0645\u0627\u06cc\u0634 \u0646\u0633\u062e\u0647 \u0642\u062f\u06cc\u0645\u06cc", value=False)
        if show_legacy:
            _render_results_page_legacy(gap, feedback, job_mapping, course_catalog, debug)
            return

    gap_catalog = st.session_state.get("gap_catalog")
    if not isinstance(gap_catalog, dict):
        gap_catalog = _load_gap_catalog()

    gap_lookup = _gap_lookup(gap_catalog)
    skill_gaps = st.session_state.get("skill_gaps")
    unsolved_map = _collect_unsolved(skill_gaps)

    with st.container():
        st.markdown("<div class='sm-sticky-anchor'></div>", unsafe_allow_html=True)
        col_badges, col_cta = st.columns([4, 1])
        with col_badges:
            _render_badges(gap)
        with col_cta:
            if st.button(
                "\u0634\u0631\u0648\u0639 \u0627\u0632 \u06af\u067e \u0634\u0645\u0627\u0631\u0647 \u06f1",
                type="primary",
                key="cta_top_gap",
            ):
                _toast("\u0645\u0633\u06cc\u0631 \u062a\u0645\u0631\u06cc\u0646 \u0622\u0645\u0627\u062f\u0647 \u0634\u062f. \u0627\u0632 \u06af\u067e \u0627\u0648\u0644 \u0634\u0631\u0648\u0639 \u06a9\u0646.")

    st.markdown("<h1 class='sm-h1'>\u0646\u062a\u0627\u06cc\u062c \u062a\u062d\u0644\u06cc\u0644 \u0645\u0633\u06cc\u0631 \u0634\u063a\u0644\u06cc</h1>", unsafe_allow_html=True)
    summary = feedback.get("summary_fa") if isinstance(feedback, dict) else None
    if summary:
        st.markdown(f"<p class='sm-subtitle'>{summary}</p>", unsafe_allow_html=True)
    else:
        st.markdown(
            "<p class='sm-subtitle'>\u0647\u0646\u0648\u0632 \u062f\u0627\u062f\u0647\u200c\u0627\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \U0001F331 \u0627\u0645\u0627 \u0627\u06cc\u0646 \u0635\u0641\u062d\u0647 \u0622\u0645\u0627\u062f\u0647 \u0627\u0633\u062a \u062a\u0627 \u0645\u0633\u06cc\u0631 \u0634\u0645\u0627 \u0631\u0627 \u0634\u0641\u0627\u0641 \u06a9\u0646\u062f.</p>",
            unsafe_allow_html=True,
        )

    st.markdown("<div class='sm-section'>", unsafe_allow_html=True)
    st.markdown("<div class='sm-section-title'>\u0646\u0642\u0627\u0637 \u0642\u0648\u062a \u0648 \u0627\u0648\u0644\u0648\u06cc\u062a \u06cc\u0627\u062f\u06af\u06cc\u0631\u06cc</div>", unsafe_allow_html=True)
    strengths = feedback.get("strengths_fa", []) if isinstance(feedback, dict) else []
    priorities = feedback.get("gaps_fa", []) if isinstance(feedback, dict) else []
    col_strengths, col_gaps = st.columns(2)
    with col_strengths:
        with card_container():
            st.markdown("<div class='sm-card-title'>\u0646\u0642\u0627\u0637 \u0642\u0648\u062a</div>", unsafe_allow_html=True)
            if strengths:
                for item in strengths:
                    st.markdown(f"- {item}")
            else:
                st.caption("\u0628\u0627 \u062a\u06a9\u0645\u06cc\u0644 \u0627\u0648\u0644\u06cc\u0646 \u062a\u0645\u0631\u06cc\u0646\u060c \u0646\u0642\u0627\u0637 \u0642\u0648\u062a \u0634\u0645\u0627 \u0645\u0634\u062e\u0635\u200c\u062a\u0631 \u0645\u06cc\u200c\u0634\u0648\u062f.")
    with col_gaps:
        with card_container():
            st.markdown("<div class='sm-card-title'>\u0627\u0648\u0644\u0648\u06cc\u062a \u06cc\u0627\u062f\u06af\u06cc\u0631\u06cc</div>", unsafe_allow_html=True)
            if priorities:
                for item in priorities:
                    st.markdown(f"- {item}")
            else:
                st.caption("\u0627\u0648\u0644\u0648\u06cc\u062a\u200c\u0647\u0627\u06cc \u06cc\u0627\u062f\u06af\u06cc\u0631\u06cc \u0628\u0639\u062f \u0627\u0632 \u062a\u06a9\u0645\u06cc\u0644 \u0627\u0648\u0644\u06cc\u0646 \u062a\u0645\u0631\u06cc\u0646 \u0631\u0648\u0634\u0646\u200c\u062a\u0631 \u0645\u06cc\u200c\u0634\u0648\u0646\u062f.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='sm-section'>", unsafe_allow_html=True)
    st.markdown("<div class='sm-section-title'>\u0642\u062f\u0645 \u0628\u0639\u062f\u06cc \u0634\u0645\u0627 (\u06f1\u06f0 \u062f\u0642\u06cc\u0642\u0647)</div>", unsafe_allow_html=True)
    hero_gap_id = select_top_unsolved(skill_gaps, n=1)
    hero_id = hero_gap_id[0] if hero_gap_id else None
    hero_meta = gap_lookup.get(hero_id, {}) if hero_id else {}
    hero_payload = unsolved_map.get(hero_id) if hero_id else None

    with card_container():
        if hero_meta:
            title = hero_meta.get("title_fa", hero_id or "")
            why = _truncate(hero_meta.get("why_important_fa", ""), 120)
            next_action = hero_payload.get("next_action") if isinstance(hero_payload, dict) else None
            micro_step = next_action.get("micro_step_fa", "") if isinstance(next_action, dict) else ""
            st.markdown(f"<div class='sm-card-title'>{title}</div>", unsafe_allow_html=True)
            if why:
                st.markdown(f"<div class='sm-body'>{why}</div>", unsafe_allow_html=True)
            if micro_step:
                st.markdown(f"<div class='sm-body'><strong>\u0647\u0645\u06cc\u0646 \u0627\u0645\u0631\u0648\u0632 \u0627\u0646\u062c\u0627\u0645 \u0628\u062f\u0647:</strong> {micro_step}</div>")
            col_primary, col_secondary = st.columns([1, 1])
            with col_primary:
                if st.button("\u0634\u0631\u0648\u0639 \u062a\u0645\u0631\u06cc\u0646 \u06f1\u06f0 \u062f\u0642\u06cc\u0642\u0647\u200c\u0627\u06cc", type="secondary", key="cta_hero"):
                    _toast("\u0639\u0627\u0644\u06cc\u0647! \u0627\u06cc\u0646 \u062a\u0645\u0631\u06cc\u0646 \u06a9\u0648\u062a\u0627\u0647 \u0631\u0627 \u0634\u0631\u0648\u0639 \u06a9\u0646.")
            with col_secondary:
                with st.expander("\u0646\u0645\u0627\u06cc\u0634 \u06af\u0627\u0645\u200c\u0647\u0627"):
                    _render_gap_blocks(hero_meta)
        else:
            st.info("\u0647\u0646\u0648\u0632 \u062f\u0627\u062f\u0647\u200c\u0627\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \U0001F331 \u06cc\u06a9 \u0645\u0635\u0627\u062d\u0628\u0647 \u06a9\u0648\u062a\u0627\u0647 \u0645\u06cc\u200c\u062a\u0648\u0627\u0646\u062f \u06af\u067e\u200c\u0647\u0627\u06cc \u0627\u0635\u0644\u06cc \u0631\u0627 \u0645\u0634\u062e\u0635 \u06a9\u0646\u062f.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='sm-section'>", unsafe_allow_html=True)
    st.markdown("<div class='sm-section-title'>\u0646\u0645\u0627\u06cc \u06a9\u0644\u06cc \u0645\u0633\u06cc\u0631</div>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns(3)

    solved_core, total_core = _core_gap_progress(skill_gaps)
    with col_a:
        _snapshot_card("\u06af\u067e\u200c\u0647\u0627\u06cc \u0627\u0635\u0644\u06cc \u062d\u0644 \u0634\u062f\u0647", f"{solved_core} \u0627\u0632 {total_core}")

    start_fast, total_courses = _start_course_progress(gap, feedback)
    with col_b:
        _snapshot_card("\u062f\u0648\u0631\u0647\u200c\u0647\u0627\u06cc \u0634\u0631\u0648\u0639 \u0633\u0631\u06cc\u0639", f"{start_fast} \u0627\u0632 {total_courses}")

    confidence_label = _target_job_confidence(skill_gaps, gap, gap_catalog, job_mapping)
    with col_c:
        _snapshot_card("\u0627\u062d\u062a\u0645\u0627\u0644 \u0634\u063a\u0644 \u0647\u062f\u0641", confidence_label or "\u062f\u0631 \u062d\u0627\u0644 \u0645\u062d\u0627\u0633\u0628\u0647")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='sm-section'>", unsafe_allow_html=True)
    st.markdown("<div class='sm-section-title'>\u06f3 \u06af\u067e \u0627\u0648\u0644\u0648\u06cc\u062a\u200c\u062f\u0627\u0631 \u0634\u0645\u0627</div>", unsafe_allow_html=True)
    top_gaps = select_top_unsolved(skill_gaps, n=3)
    if not top_gaps:
        st.info("\u0647\u0646\u0648\u0632 \u062f\u0627\u062f\u0647\u200c\u0627\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \U0001F331 \u0628\u0627 \u062a\u06a9\u0645\u06cc\u0644 \u0645\u0635\u0627\u062d\u0628\u0647\u060c \u06af\u067e\u200c\u0647\u0627\u06cc \u0627\u0648\u0644\u0648\u06cc\u062a\u200c\u062f\u0627\u0631 \u0646\u0645\u0627\u06cc\u0634 \u062f\u0627\u062f\u0647 \u0645\u06cc\u200c\u0634\u0648\u0646\u062f.")
    else:
        for gap_id in top_gaps:
            meta = gap_lookup.get(gap_id, {})
            payload = unsolved_map.get(gap_id, {})
            with card_container():
                st.markdown(f"<div class='sm-card-title'>{meta.get('title_fa', gap_id)}</div>", unsafe_allow_html=True)
                why_text = _truncate(meta.get("why_important_fa", ""), 120)
                if why_text:
                    st.markdown(f"<div class='sm-body'>{why_text}</div>", unsafe_allow_html=True)
                next_action = payload.get("next_action") if isinstance(payload, dict) else None
                if isinstance(next_action, dict):
                    st.markdown(
                        f"<div class='sm-body'><strong>{next_action.get('title_fa', '')}</strong></div>",
                        unsafe_allow_html=True,
                    )
                    if next_action.get("micro_step_fa"):
                        st.caption(next_action.get("micro_step_fa"))
                with st.expander("\u0646\u0645\u0627\u06cc\u0634 \u0647\u0645\u0647 \u06af\u0627\u0645\u200c\u0647\u0627"):
                    _render_gap_blocks(meta)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='sm-section'>", unsafe_allow_html=True)
    st.markdown("<div class='sm-section-title'>\u062f\u0648\u0631\u0647\u200c\u0647\u0627 (\u0627\u0628\u0632\u0627\u0631 \u062d\u0644 \u06af\u067e\u200c\u0647\u0627)</div>", unsafe_allow_html=True)
    start_courses, upgrade_courses = _extract_course_groups(gap, feedback)

    col_start, col_upgrade = st.columns([2, 1])
    with col_start:
        st.markdown("<div class='sm-card-title'>\u0634\u0631\u0648\u0639 \u0633\u0631\u06cc\u0639</div>", unsafe_allow_html=True)
        if start_courses:
            for code in start_courses[:3]:
                _course_card(code, course_catalog, gap_lookup)
        else:
            st.info("\u0647\u0646\u0648\u0632 \u062f\u0627\u062f\u0647\u200c\u0627\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \U0001F331 \u062f\u0648\u0631\u0647\u200c\u0647\u0627\u06cc \u0634\u0631\u0648\u0639 \u0633\u0631\u06cc\u0639 \u0628\u0639\u062f \u0627\u0632 \u062a\u06a9\u0645\u06cc\u0644 \u0645\u0635\u0627\u062d\u0628\u0647 \u0645\u06cc\u200c\u0622\u06cc\u0646\u062f.")

    with col_upgrade:
        with st.expander("\u0627\u0631\u062a\u0642\u0627"):
            if upgrade_courses:
                for code in upgrade_courses[:2]:
                    _course_card(code, course_catalog, gap_lookup)
            else:
                st.caption("\u0641\u0639\u0644\u0627 \u062f\u0648\u0631\u0647 \u0627\u0631\u062a\u0642\u0627 \u0645\u0634\u062e\u0635 \u0646\u06cc\u0633\u062a.")

    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='sm-section'>", unsafe_allow_html=True)
    st.markdown("<div class='sm-section-title'>\u0634\u063a\u0644\u200c\u0647\u0627 (\u0628\u0631\u0627\u06cc \u062a\u0631\u063a\u06cc\u0628 \u0648 \u0645\u0633\u06cc\u0631 \u0628\u0639\u062f\u06cc)</div>", unsafe_allow_html=True)
    track = str(gap.get("track", ""))
    if track and track != "content":
        st.info("\u0646\u0645\u0627\u06cc\u0634 \u0634\u063a\u0644\u200c\u0647\u0627 \u0628\u0631\u0627\u06cc \u0627\u06cc\u0646 \u0645\u0633\u06cc\u0631 \u062f\u0631 \u0646\u0633\u062e\u0647 \u0641\u0639\u0644\u06cc \u0641\u0639\u0627\u0644 \u0646\u06cc\u0633\u062a.")
    else:
        _render_job_cards(skill_gaps, gap, gap_catalog, feedback, job_mapping)
    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("\u062c\u0632\u0626\u06cc\u0627\u062a \u0628\u06cc\u0634\u062a\u0631"):
        scores = gap.get("interview_scores", {})
        if scores:
            st.json(scores)
        else:
            st.caption("\u0647\u0646\u0648\u0632 \u062f\u0627\u062f\u0647\u200c\u0627\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \U0001F331")
        if debug:
            st.json({"gap": gap, "user_feedback": feedback, "job_mapping": job_mapping})


def normalize_session_payload(
    gap: Optional[Dict[str, Any]],
    feedback: Optional[Dict[str, Any]],
    job_mapping: Optional[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    return {
        "gap": gap if isinstance(gap, dict) else {},
        "feedback": feedback if isinstance(feedback, dict) else {},
        "job_mapping": job_mapping if isinstance(job_mapping, dict) else {},
    }


@st.cache_data
def _load_gap_catalog() -> Dict[str, Any]:
    base_dir = Path(__file__).resolve().parents[1]
    path = base_dir / "data" / "gaps" / "content_ai_gaps.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _gap_lookup(gap_catalog: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    gaps = gap_catalog.get("gaps", []) if isinstance(gap_catalog, dict) else []
    lookup: Dict[str, Dict[str, Any]] = {}
    for item in gaps:
        if isinstance(item, dict) and item.get("gap_id"):
            lookup[str(item.get("gap_id"))] = item
    return lookup


def select_top_unsolved(skill_gaps: Optional[Dict[str, Any]], n: int = 3) -> List[str]:
    if not isinstance(skill_gaps, dict):
        return []
    unsolved = {
        gap_id
        for gap_id, payload in skill_gaps.items()
        if isinstance(payload, dict) and payload.get("status") == "unsolved"
    }
    ordered = [gap_id for gap_id in PRIORITY_ORDER if gap_id in unsolved]
    for gap_id in unsolved:
        if gap_id not in ordered:
            ordered.append(gap_id)
    return ordered[:n]


def _collect_unsolved(skill_gaps: Optional[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    if not isinstance(skill_gaps, dict):
        return {}
    output: Dict[str, Dict[str, Any]] = {}
    for gap_id, payload in skill_gaps.items():
        if isinstance(payload, dict) and payload.get("status") == "unsolved":
            output[str(gap_id)] = payload
    return output


def _render_badges(gap: Dict[str, Any]) -> None:
    level = str(gap.get("training_level", ""))
    level_label = LEVEL_LABELS.get(level, level) if level else "\u0646\u0627\u0645\u0634\u062e\u0635"
    _badge(f"\u0639\u06cc\u0627\u0631 \u0645\u0647\u0627\u0631\u062a\u06cc: {level_label}", "primary")

    track = str(gap.get("track", ""))
    track_label = TRACK_LABELS.get(track, track) if track else "\u0646\u0627\u0645\u0634\u062e\u0635"
    _badge(f"\u0645\u0633\u06cc\u0631: {track_label}", "success")

    weekly_time = str(gap.get("weekly_time", ""))
    if weekly_time:
        _badge(f"\u0632\u0645\u0627\u0646 \u0622\u0632\u0627\u062f: {weekly_time}", "warning")

    goal = str(gap.get("goal", "")).strip()
    if not goal:
        profile = gap.get("profile", {}) if isinstance(gap.get("profile"), dict) else {}
        goal_type = str(profile.get("goal_type", "")).strip()
        goal = GOAL_LABELS.get(goal_type, goal_type)
    if goal:
        _badge(f"\u0647\u062f\u0641: {goal}", "primary")


def _render_gap_blocks(gap_meta: Dict[str, Any]) -> None:
    blocks = gap_meta.get("blocks", []) if isinstance(gap_meta, dict) else []
    for block in blocks:
        title = block.get("title_fa", "")
        if title:
            st.markdown(f"**{title}**")
        steps = block.get("micro_steps_fa", []) if isinstance(block, dict) else []
        for step in steps:
            st.markdown(f"- {step}")


def _course_card(code: str, course_catalog: Dict[str, Any], gap_lookup: Dict[str, Dict[str, Any]]) -> None:
    with card_container():
        st.markdown(f"<div class='sm-card-title'>{code_title(code, course_catalog)}</div>", unsafe_allow_html=True)
        reason = _course_reason(code, gap_lookup)
        if reason:
            st.caption(reason)


def _course_reason(code: str, gap_lookup: Dict[str, Dict[str, Any]]) -> str:
    titles = []
    for gap in gap_lookup.values():
        courses = gap.get("recommended_courses", []) if isinstance(gap.get("recommended_courses"), list) else []
        for item in courses:
            if str(item.get("code")) == str(code) and gap.get("title_fa"):
                titles.append(gap.get("title_fa"))
    if titles:
        return f"\u06a9\u0645\u06a9 \u0628\u0647 \u062d\u0644: {', '.join(titles[:2])}"
    return "\u0628\u0631\u0627\u06cc \u062a\u0642\u0648\u06cc\u062a \u067e\u0627\u06cc\u0647\u200c\u0647\u0627\u06cc \u0627\u06cc\u0646 \u0645\u0633\u06cc\u0631"


def _start_course_progress(gap: Dict[str, Any], feedback: Dict[str, Any]) -> tuple[int, int]:
    start_courses, upgrade_courses = _extract_course_groups(gap, feedback)
    if start_courses:
        total = len(start_courses)
        return min(3, len(start_courses)), total
    recommended = _dedupe_codes(gap.get("recommended_courses", []))
    return min(3, len(recommended)), len(recommended)


def _extract_course_groups(gap: Dict[str, Any], feedback: Dict[str, Any]) -> tuple[List[str], List[str]]:
    course_plan = feedback.get("course_plan_fa", []) if isinstance(feedback, dict) else []
    start_courses: List[str] = []
    upgrade_courses: List[str] = []
    for phase in course_plan:
        if not isinstance(phase, dict):
            continue
        phase_name = str(phase.get("phase", ""))
        course_items = phase.get("courses", []) if isinstance(phase.get("courses"), list) else []
        codes = [str(item.get("code")) for item in course_items if isinstance(item, dict) and item.get("code")]
        if "\u0634\u0631\u0648\u0639" in phase_name:
            start_courses.extend(codes)
        else:
            upgrade_courses.extend(codes)
    if not start_courses:
        start_courses = _dedupe_codes(gap.get("recommended_courses", []))
    return _dedupe_codes(start_courses), _dedupe_codes(upgrade_courses)


def _core_gap_progress(skill_gaps: Optional[Dict[str, Any]]) -> tuple[int, int]:
    total = 3
    if not isinstance(skill_gaps, dict):
        return 0, total
    solved = 0
    for gap_id in PRIORITY_ORDER[:3]:
        payload = skill_gaps.get(gap_id, {})
        if isinstance(payload, dict) and payload.get("status") == "solved":
            solved += 1
    return solved, total


def _target_job_confidence(
    skill_gaps: Optional[Dict[str, Any]],
    gap: Dict[str, Any],
    gap_catalog: Dict[str, Any],
    job_mapping: Dict[str, Any],
) -> str:
    if not isinstance(skill_gaps, dict) or not isinstance(gap_catalog, dict):
        return ""
    solved = [
        gap_id
        for gap_id, payload in skill_gaps.items()
        if isinstance(payload, dict) and payload.get("status") == "solved"
    ]
    readiness = str(gap.get("readiness_level", ""))
    reachable = job_mapping.get("reachable_jobs", []) if isinstance(job_mapping, dict) else []
    for job in reachable:
        job_id = job.get("job_id")
        if job_id:
            result = calculate_job_probability(job_id, solved, readiness, gap_catalog)
            return CONFIDENCE_LABELS.get(result.get("confidence", ""), "")
    return ""


def _render_job_cards(
    skill_gaps: Optional[Dict[str, Any]],
    gap: Dict[str, Any],
    gap_catalog: Dict[str, Any],
    feedback: Dict[str, Any],
    job_mapping: Dict[str, Any],
) -> None:
    target_title = None
    target_reason = ""
    target_job_id = None
    job_path = feedback.get("job_path_fa", {}) if isinstance(feedback, dict) else {}
    if isinstance(job_path, dict):
        target_job = job_path.get("target_job", {})
        if isinstance(target_job, dict):
            target_title = target_job.get("title")
            target_reason = target_job.get("why_fit", "")

    reachable = job_mapping.get("reachable_jobs", []) if isinstance(job_mapping, dict) else []
    if not target_title and reachable:
        target_title = reachable[0].get("title_fa")
        target_reason = " ".join(reachable[0].get("why_fa", [])[:1])
        target_job_id = reachable[0].get("job_id")
    elif reachable:
        target_job_id = reachable[0].get("job_id")

    confidence_label = ""
    confidence_reason = ""
    if target_job_id and isinstance(skill_gaps, dict):
        solved = [
            gap_id
            for gap_id, payload in skill_gaps.items()
            if isinstance(payload, dict) and payload.get("status") == "solved"
        ]
        readiness = str(gap.get("readiness_level", ""))
        result = calculate_job_probability(target_job_id, solved, readiness, gap_catalog)
        confidence_label = CONFIDENCE_LABELS.get(result.get("confidence", ""), "")
        confidence_reason = result.get("reason_fa", "")

    with card_container():
        st.markdown("<div class='sm-card-title'>\u0634\u063a\u0644 \u0647\u062f\u0641 \u0634\u0645\u0627</div>", unsafe_allow_html=True)
        if target_title:
            label = f" ({confidence_label})" if confidence_label else ""
            st.markdown(f"<div class='sm-body'><strong>{target_title}</strong>{label}</div>", unsafe_allow_html=True)
            if target_reason:
                st.caption(target_reason)
            if confidence_reason:
                st.caption(confidence_reason)
        else:
            st.info("\u0647\u0646\u0648\u0632 \u062f\u0627\u062f\u0647\u200c\u0627\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \U0001F331 \u0634\u063a\u0644 \u0647\u062f\u0641 \u0628\u0639\u062f \u0627\u0632 \u062a\u06a9\u0645\u06cc\u0644 \u0645\u0635\u0627\u062d\u0628\u0647 \u0645\u0634\u062e\u0635 \u0645\u06cc\u200c\u0634\u0648\u062f.")

    if reachable:
        st.markdown("<div class='sm-card-title'>\u0634\u063a\u0644\u200c\u0647\u0627\u06cc \u0646\u0632\u062f\u06cc\u06a9</div>", unsafe_allow_html=True)
        for job in reachable[:3]:
            with card_container():
                st.markdown(f"<div class='sm-body'><strong>{job.get('title_fa', '')}</strong></div>", unsafe_allow_html=True)
                reasons = job.get("why_fa", []) if isinstance(job.get("why_fa"), list) else []
                if reasons:
                    st.caption(" ".join(reasons[:1]))


def _render_results_page_legacy(
    gap: Dict[str, Any],
    feedback: Dict[str, Any],
    job_mapping: Dict[str, Any],
    course_catalog: Dict[str, Any],
    debug: bool,
) -> None:
    st.markdown("## \u0646\u062a\u0627\u06cc\u062c \u062a\u062d\u0644\u06cc\u0644 \u0645\u0633\u06cc\u0631 \u0634\u063a\u0644\u06cc")
    summary = feedback.get("summary_fa", "") if isinstance(feedback, dict) else ""
    if summary:
        st.write(summary)
    else:
        st.info("\u0647\u0646\u0648\u0632 \u062f\u0627\u062f\u0647\u200c\u0627\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \U0001F331")

    st.markdown("### \u0646\u0642\u0627\u0637 \u0642\u0648\u062a \u0648 \u0627\u0648\u0644\u0648\u06cc\u062a \u06cc\u0627\u062f\u06af\u06cc\u0631\u06cc")
    strengths = feedback.get("strengths_fa", []) if isinstance(feedback, dict) else []
    gaps = feedback.get("gaps_fa", []) if isinstance(feedback, dict) else []
    col_strengths, col_gaps = st.columns(2)
    with col_strengths:
        st.markdown("**\u0646\u0642\u0627\u0637 \u0642\u0648\u062a**")
        if strengths:
            for item in strengths:
                st.markdown(f"- {item}")
        else:
            st.caption("\u0628\u0627 \u062a\u06a9\u0645\u06cc\u0644 \u0627\u0648\u0644\u06cc\u0646 \u062a\u0645\u0631\u06cc\u0646\u060c \u0646\u0642\u0627\u0637 \u0642\u0648\u062a \u0634\u0645\u0627 \u0645\u0634\u062e\u0635\u200c\u062a\u0631 \u0645\u06cc\u200c\u0634\u0648\u062f.")
    with col_gaps:
        st.markdown("**\u0627\u0648\u0644\u0648\u06cc\u062a \u06cc\u0627\u062f\u06af\u06cc\u0631\u06cc**")
        if gaps:
            for item in gaps:
                st.markdown(f"- {item}")
        else:
            st.caption("\u0627\u0648\u0644\u0648\u06cc\u062a\u200c\u0647\u0627\u06cc \u06cc\u0627\u062f\u06af\u06cc\u0631\u06cc \u0628\u0639\u062f \u0627\u0632 \u062a\u06a9\u0645\u06cc\u0644 \u0627\u0648\u0644\u06cc\u0646 \u062a\u0645\u0631\u06cc\u0646 \u0631\u0648\u0634\u0646\u200c\u062a\u0631 \u0645\u06cc\u200c\u0634\u0648\u0646\u062f.")

    st.markdown("### \u0627\u0644\u0627\u0646 \u062f\u0642\u06cc\u0642\u0627\u064b \u0686\u0647 \u06a9\u0627\u0631 \u06a9\u0646\u0645\u061f")
    actions = feedback.get("next_actions_fa", []) if isinstance(feedback, dict) else []
    if actions:
        for index, action in enumerate(actions):
            title = action.get("title", "\u06af\u0627\u0645 \u067e\u06cc\u0634\u0646\u0647\u0627\u062f\u06cc")
            timeframe = action.get("timeframe", "")
            label = f"{title} ({timeframe})" if timeframe else title
            with st.expander(safe_text(label), expanded=index == 0):
                for step in action.get("steps", []):
                    st.markdown(f"- {step}")
    else:
        st.info("\u0647\u0646\u0648\u0632 \u062f\u0627\u062f\u0647\u200c\u0627\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \U0001F331")

    st.markdown("### \u0645\u0633\u06cc\u0631 \u0622\u0645\u0648\u0632\u0634\u06cc \u067e\u06cc\u0634\u0646\u0647\u0627\u062f\u06cc")
    course_plan = feedback.get("course_plan_fa", []) if isinstance(feedback, dict) else []
    if course_plan:
        for index, phase in enumerate(course_plan):
            phase_title = phase.get("phase", "\u0645\u0631\u062d\u0644\u0647")
            with st.expander(safe_text(phase_title), expanded=index == 0):
                for course in phase.get("courses", []):
                    code = str(course.get("code", ""))
                    title = course.get("title", "")
                    why = course.get("why", "")
                    st.markdown(f"- {code_title(code, course_catalog, title)}: {why}")
    else:
        recommended = _dedupe_codes(gap.get("recommended_courses", []))
        if recommended:
            render_courses_list(recommended, course_catalog, "\u062f\u0648\u0631\u0647\u200c\u0647\u0627\u06cc \u067e\u06cc\u0634\u0646\u0647\u0627\u062f\u06cc")
        else:
            st.info("\u0647\u0646\u0648\u0632 \u062f\u0627\u062f\u0647\u200c\u0627\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \U0001F331")

    st.markdown("### \u0645\u0633\u06cc\u0631 \u0634\u063a\u0644\u06cc \u0634\u0645\u0627")
    job_path = feedback.get("job_path_fa", {}) if isinstance(feedback, dict) else {}
    target = job_path.get("target_job", {}) if isinstance(job_path, dict) else {}
    if target:
        st.markdown("**\u0634\u063a\u0644 \u0647\u062f\u0641**")
        st.markdown(f"- {target.get('title', '')}: {target.get('why_fit', '')}")

    st.markdown("**\u0641\u0631\u0635\u062a\u200c\u0647\u0627\u06cc \u0642\u0627\u0628\u0644 \u062f\u0633\u062a\u0631\u0633**")
    reachable = job_path.get("reachable_now", []) if isinstance(job_path, dict) else []
    if reachable:
        for job in reachable:
            st.markdown(f"- {job.get('title', '')}: {job.get('why', '')}")
    else:
        _render_job_mapping_fallback(job_mapping.get("reachable_jobs", []), max_items=3)

    st.markdown("**\u06af\u0627\u0645 \u0628\u0639\u062f\u06cc**")
    next_level = job_path.get("next_level", []) if isinstance(job_path, dict) else []
    if next_level:
        for job in next_level:
            unlock = ", ".join(job.get("unlock_with", []))
            suffix = f" (\u0628\u0631\u0627\u06cc \u0628\u0627\u0632 \u0634\u062f\u0646: {unlock})" if unlock else ""
            st.markdown(f"- {job.get('title', '')}{suffix}")
    else:
        _render_next_level_fallback(job_mapping.get("next_level_jobs", []), max_items=3)

    warnings = feedback.get("warnings_fa", []) if isinstance(feedback, dict) else []
    if warnings:
        st.markdown("**\u0647\u0634\u062f\u0627\u0631\u0647\u0627:**")
        for warning in warnings:
            st.markdown(f"- {warning}")

    with st.expander("\u062c\u0632\u0626\u06cc\u0627\u062a \u0628\u06cc\u0634\u062a\u0631"):
        scores = gap.get("interview_scores", {})
        if scores:
            st.json(scores)
        else:
            st.caption("\u0647\u0646\u0648\u0632 \u062f\u0627\u062f\u0647\u200c\u0627\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \U0001F331")
        if debug:
            st.json({"gap": gap, "user_feedback": feedback, "job_mapping": job_mapping})


def _badge(text: str, kind: str) -> None:
    st.markdown(
        f"<span class='sm-badge sm-badge-{kind}'>{text}</span>",
        unsafe_allow_html=True,
    )


def _snapshot_card(title: str, value: str) -> None:
    with card_container():
        st.markdown(f"<div class='sm-card-title'>{title}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='sm-body'><strong>{value}</strong></div>", unsafe_allow_html=True)


def _toast(message: str) -> None:
    if hasattr(st, "toast"):
        st.toast(message)
    else:
        st.success(message)


def _truncate(text: str, max_len: int) -> str:
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[: max_len - 3].rstrip() + "..."


def code_title(code: str, course_catalog: Dict[str, Any], title_override: str = "") -> str:
    code = str(code)
    if title_override:
        return f"{code} ({title_override})"
    meta = course_catalog.get(code, {}) if isinstance(course_catalog, dict) else {}
    title = meta.get("title_fa") if isinstance(meta, dict) else ""
    return f"{code} ({title})" if title else code


def render_courses_list(
    codes: Iterable[str],
    course_catalog: Dict[str, Any],
    header: Optional[str],
) -> None:
    if header:
        st.markdown(f"**{header}**")
    for code in _dedupe_codes(codes):
        st.markdown(f"- {code_title(code, course_catalog)}")


def _render_job_mapping_fallback(reachable_jobs: List[Dict[str, Any]], max_items: int) -> None:
    if not reachable_jobs:
        st.caption("\u0647\u0646\u0648\u0632 \u0634\u063a\u0644 \u0642\u0627\u0628\u0644 \u062f\u0633\u062a\u0631\u0633 \u0646\u0645\u0627\u06cc\u0634 \u062f\u0627\u062f\u0647 \u0646\u0634\u062f\u0647 \u0627\u0633\u062a.")
        return
    for job in reachable_jobs[:max_items]:
        title = job.get("title_fa", "")
        score = job.get("match_score")
        st.markdown(f"- {title} (\u0627\u0645\u062a\u06cc\u0627\u0632 {score}/100)")
        for reason in (job.get("why_fa", []) or [])[:2]:
            st.markdown(f"  - {reason}")


def _render_next_level_fallback(next_jobs: List[Dict[str, Any]], max_items: int) -> None:
    if not next_jobs:
        st.caption("\u0641\u0639\u0644\u0627 \u0634\u063a\u0644 \u0633\u0637\u062d \u0628\u0639\u062f\u06cc \u0646\u0645\u0627\u06cc\u0634 \u062f\u0627\u062f\u0647 \u0646\u0634\u062f\u0647 \u0627\u0633\u062a.")
        return
    for job in next_jobs[:max_items]:
        title = job.get("title_fa", "")
        unlock = job.get("unlock_with", [])
        unlock_text = ", ".join(unlock) if unlock else ""
        suffix = f" (\u0628\u0631\u0627\u06cc \u0628\u0627\u0632 \u0634\u062f\u0646: {unlock_text})" if unlock_text else ""
        st.markdown(f"- {title}{suffix}")


def _dedupe_codes(codes: Iterable[Any]) -> List[str]:
    seen = set()
    output = []
    for code in codes:
        value = str(code)
        if not value or value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output
