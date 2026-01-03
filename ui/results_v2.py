from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import streamlit as st

from ui.theme import card_container, safe_text


PRIORITY_ORDER = [
    "GAP_CONTENT_PUBLISHABLE_OUTPUT",
    "GAP_PROMPTING_FOR_CONTENT",
    "GAP_PORTFOLIO_WITH_AI",
    "GAP_CONTENT_PLANNING",
    "GAP_AUDIENCE_FIT_WITH_AI",
    "GAP_MULTIMODAL_CONTENT",
]

PROBABILITY_LABELS = {
    "low": "\u06a9\u0645",
    "medium": "\u0645\u062a\u0648\u0633\u0637",
    "high": "\u0628\u0627\u0644\u0627",
}

RESULTS_V2_CSS = """
<style>
.rv2-title {
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 4px;
}
.rv2-subtitle {
    color: #6B7280;
    font-size: 14px;
    margin-bottom: 16px;
}
.rv2-badge-anchor {
    display: none;
}
div[data-testid="stVerticalBlock"]:has(> .rv2-badge-anchor) {
    display: inline-block;
    background: #DBEAFE;
    color: #1D4ED8;
    border: 1px solid #BFDBFE;
    border-radius: 999px;
    padding: 4px 10px;
    margin: 0 6px 6px 0;
}
</style>
"""


def _badge(text: str) -> None:
    with st.container():
        st.markdown("<div class='rv2-badge-anchor'></div>", unsafe_allow_html=True)
        st.write(safe_text(text))


def _load_gap_catalog() -> Dict[str, Any]:
    path = Path(__file__).resolve().parent.parent / "data" / "gaps" / "content_ai_gaps.json"
    if not path.exists():
        return {}
    try:
        raw = path.read_text(encoding="utf-8-sig")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def _load_course_catalog() -> Dict[str, Any]:
    catalog_path = Path(__file__).resolve().parent.parent / "data" / "course_catalog_fa.json"
    if catalog_path.exists():
        try:
            raw = catalog_path.read_text(encoding="utf-8-sig")
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            data = {}
        if isinstance(data, dict):
            return data

    rules_path = Path(__file__).resolve().parent.parent / "data" / "job_course_rules_fa.json"
    if not rules_path.exists():
        return {}
    try:
        raw = rules_path.read_text(encoding="utf-8-sig")
        data = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    catalog = data.get("course_catalog", {})
    return catalog if isinstance(catalog, dict) else {}


def _gap_lookup(gap_catalog: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    gaps = gap_catalog.get("gaps", []) if isinstance(gap_catalog, dict) else []
    lookup: Dict[str, Dict[str, Any]] = {}
    for gap in gaps:
        if isinstance(gap, dict) and gap.get("gap_id"):
            lookup[str(gap.get("gap_id"))] = gap
    return lookup


def _normalize_skill_gaps(skill_gaps: Any, gap_lookup: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    if isinstance(skill_gaps, dict):
        for gap_id, payload in skill_gaps.items():
            gap_id = str(gap_id)
            meta = gap_lookup.get(gap_id, {})
            record = {
                "gap_id": gap_id,
                "status": payload.get("status") if isinstance(payload, dict) else "",
                "next_action": payload.get("next_action") if isinstance(payload, dict) else None,
                "title_fa": meta.get("title_fa", gap_id),
                "why_important_fa": meta.get("why_important_fa", ""),
                "blocks": meta.get("blocks", []) if isinstance(meta, dict) else [],
            }
            output.append(record)
        return output
    if isinstance(skill_gaps, list):
        for item in skill_gaps:
            if not isinstance(item, dict):
                continue
            gap_id = str(item.get("gap_id", ""))
            meta = gap_lookup.get(gap_id, {})
            record = {
                "gap_id": gap_id,
                "status": item.get("status", ""),
                "next_action": item.get("next_action"),
                "title_fa": item.get("title_fa") or meta.get("title_fa", gap_id),
                "why_important_fa": item.get("why_important_fa") or meta.get("why_important_fa", ""),
                "blocks": item.get("blocks") or meta.get("blocks", []),
            }
            output.append(record)
    return output


def _sort_by_priority(gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    order = {gap_id: idx for idx, gap_id in enumerate(PRIORITY_ORDER)}

    def _key(item: Dict[str, Any]) -> int:
        return order.get(str(item.get("gap_id")), 999)

    return sorted(gaps, key=_key)


def _dedupe(items: Iterable[Any]) -> List[str]:
    seen = set()
    output = []
    for item in items:
        value = str(item)
        if not value or value in seen:
            continue
        seen.add(value)
        output.append(value)
    return output


def _normalize_courses(courses: Any) -> Dict[str, List[str]]:
    if not isinstance(courses, dict):
        return {"quick": [], "upgrade": [], "avoid": []}
    return {
        "quick": _dedupe(courses.get("quick", [])),
        "upgrade": _dedupe(courses.get("upgrade", [])),
        "avoid": _dedupe(courses.get("avoid", [])),
    }


def _course_meta(code: str, course_catalog: Dict[str, Any]) -> Tuple[str, str]:
    meta = course_catalog.get(str(code), {}) if isinstance(course_catalog, dict) else {}
    title = ""
    url = ""
    if isinstance(meta, dict):
        title = str(meta.get("title_fa", "")).strip()
        url = str(meta.get("register_url", "")).strip()
    return title, url


def _render_course_card(code: str, course_catalog: Dict[str, Any]) -> None:
    title, url = _course_meta(code, course_catalog)
    display_title = title or str(code)
    with card_container():
        st.write(safe_text(display_title))
        if url:
            st.markdown(f"[ثبت‌نام]({url})")


def _normalize_jobs(jobs: Any) -> Dict[str, Any]:
    if not isinstance(jobs, dict):
        return {"target": {}, "now": [], "related": [], "next": []}
    if {"target", "now", "related", "next"}.issubset(jobs.keys()):
        return jobs
    reachable = jobs.get("reachable_jobs", []) if isinstance(jobs.get("reachable_jobs"), list) else []
    next_level = jobs.get("next_level_jobs", []) if isinstance(jobs.get("next_level_jobs"), list) else []
    target = reachable[0] if reachable else {}
    now = reachable[:3]
    related = reachable[3:6]
    return {"target": target, "now": now, "related": related, "next": next_level}


def _job_title(job: Dict[str, Any]) -> str:
    if not isinstance(job, dict):
        return ""
    return str(job.get("title") or job.get("title_fa") or "").strip()


def _probability_label(job: Dict[str, Any]) -> str:
    if not isinstance(job, dict):
        return "\u062f\u0631 \u062d\u0627\u0644 \u0645\u062d\u0627\u0633\u0628\u0647"
    label = job.get("probability_label") or job.get("confidence")
    if isinstance(label, str) and label in PROBABILITY_LABELS:
        return PROBABILITY_LABELS[label]
    score = job.get("match_score")
    if isinstance(score, (int, float)):
        if score >= 70:
            return "\u0628\u0627\u0644\u0627"
        if score >= 40:
            return "\u0645\u062a\u0648\u0633\u0637"
        return "\u06a9\u0645"
    return "\u062f\u0631 \u062d\u0627\u0644 \u0645\u062d\u0627\u0633\u0628\u0647"


def _render_gap_blocks(blocks: List[Dict[str, Any]]) -> None:
    for block in blocks:
        if not isinstance(block, dict):
            continue
        title = str(block.get("title_fa", "")).strip()
        if title:
            st.write(title)
        steps = block.get("micro_steps_fa", []) if isinstance(block.get("micro_steps_fa"), list) else []
        for step in steps:
            st.caption(str(step))


def render_results_page_v2(
    profile: Dict[str, Any],
    scores: Dict[str, Any],
    skill_gaps: Any,
    courses: Dict[str, Any],
    jobs: Dict[str, Any],
    course_catalog: Optional[Dict[str, Any]] = None,
    debug: bool = False,
) -> None:
    st.markdown(RESULTS_V2_CSS, unsafe_allow_html=True)

    gap_catalog = st.session_state.get("gap_catalog")
    if not isinstance(gap_catalog, dict):
        gap_catalog = _load_gap_catalog()
    gap_lookup = _gap_lookup(gap_catalog)
    gaps = _normalize_skill_gaps(skill_gaps, gap_lookup)
    unsolved = [gap for gap in gaps if gap.get("status") != "solved"]
    unsolved = _sort_by_priority(unsolved)
    top_gap = unsolved[0] if unsolved else None

    course_groups = _normalize_courses(courses)
    if not isinstance(course_catalog, dict) or not course_catalog:
        course_catalog = _load_course_catalog()
    job_groups = _normalize_jobs(jobs)
    target_job = job_groups.get("target", {}) if isinstance(job_groups, dict) else {}
    probability_label = _probability_label(target_job)

    st.markdown("<div class='rv2-title'>\u0646\u062a\u0627\u06cc\u062c \u062a\u062d\u0644\u06cc\u0644 \u0645\u0633\u06cc\u0631 \u0634\u063a\u0644\u06cc</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='rv2-subtitle'>\u062e\u0644\u0627\u0635\u0647\u200c\u0627\u06cc \u06a9\u0648\u062a\u0627\u0647 \u0648 \u0642\u0627\u0628\u0644 \u0627\u0642\u062f\u0627\u0645 \u0628\u0631\u0627\u06cc \u0645\u0633\u06cc\u0631 \u0634\u0645\u0627</div>",
        unsafe_allow_html=True,
    )

    badge_items: List[str] = []
    if isinstance(profile, dict):
        track = profile.get("preference") or profile.get("track") or ""
        goal = profile.get("goal") or profile.get("goal_type") or ""
        weekly_time = profile.get("weekly_time") or profile.get("weekly_time_budget_hours") or ""
        if track:
            badge_items.append(f"\u0645\u0633\u06cc\u0631: {track}")
        if goal:
            badge_items.append(f"\u0647\u062f\u0641: {goal}")
        if weekly_time:
            badge_items.append(f"\u0632\u0645\u0627\u0646 \u0622\u0632\u0627\u062f: {weekly_time}")

    gap = st.session_state.get("gap", {})
    if isinstance(gap, dict):
        level = gap.get("training_level")
        if level:
            badge_items.append(f"\u0633\u0637\u062d: {level}")

    if badge_items:
        for item in badge_items:
            _badge(item)

    with card_container():
        st.subheader("\u062e\u0644\u0627\u0635\u0647")
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            st.metric(safe_text("\u0627\u062d\u062a\u0645\u0627\u0644 \u0634\u063a\u0644 \u0647\u062f\u0641"), probability_label)
        with col_b:
            st.metric(safe_text("\u06af\u067e\u200c\u0647\u0627\u06cc \u0628\u0627\u0632"), len(unsolved))
        with col_c:
            st.metric(safe_text("\u062f\u0648\u0631\u0647\u200c\u0647\u0627\u06cc \u0634\u0631\u0648\u0639 \u0633\u0631\u06cc\u0639"), len(course_groups.get("quick", [])))

    tabs = st.tabs(
        [
            safe_text("\u062e\u0644\u0627\u0635\u0647"),
            safe_text("\u06af\u067e\u200c\u0647\u0627"),
            safe_text("\u062f\u0648\u0631\u0647\u200c\u0647\u0627"),
            safe_text("\u0634\u063a\u0644\u200c\u0647\u0627"),
            safe_text("\u062c\u0632\u0626\u06cc\u0627\u062a"),
        ]
    )

    with tabs[0]:
        with card_container():
            st.subheader(safe_text("\u0642\u062f\u0645 \u0628\u0639\u062f\u06cc \u0634\u0645\u0627 (\u06f1\u06f0 \u062f\u0642\u06cc\u0642\u0647)"))
            if top_gap:
                st.write(top_gap.get("title_fa", top_gap.get("gap_id", "")))
                why = top_gap.get("why_important_fa", "")
                if why:
                    st.caption(str(why))
                next_action = top_gap.get("next_action") or {}
                if isinstance(next_action, dict) and next_action.get("micro_step_fa"):
                    st.write(next_action.get("micro_step_fa"))
                st.button(safe_text("\u0634\u0631\u0648\u0639 \u062a\u0645\u0631\u06cc\u0646 \u06f1\u06f0 \u062f\u0642\u06cc\u0642\u0647\u200c\u0627\u06cc"))
                with st.expander(safe_text("\u0646\u0645\u0627\u06cc\u0634 \u06af\u0627\u0645\u200c\u0647\u0627")):
                    _render_gap_blocks(top_gap.get("blocks", []))
            else:
                st.info("\u0647\u0646\u0648\u0632 \u06af\u067e\u200c\u0647\u0627\u06cc \u0628\u0627\u0632 \u0645\u0634\u062e\u0635 \u0646\u0634\u062f\u0647 \u0627\u0633\u062a.")

    with tabs[1]:
        if unsolved:
            for gap in unsolved[:3]:
                with card_container():
                    st.write(gap.get("title_fa", gap.get("gap_id", "")))
                    why = gap.get("why_important_fa", "")
                    if why:
                        st.caption(str(why))
                    next_action = gap.get("next_action") or {}
                    if isinstance(next_action, dict) and next_action.get("micro_step_fa"):
                        st.write(next_action.get("micro_step_fa"))
                    with st.expander(safe_text("\u0646\u0645\u0627\u06cc\u0634 \u06af\u0627\u0645\u200c\u0647\u0627")):
                        _render_gap_blocks(gap.get("blocks", []))
            with st.expander(safe_text("\u0646\u0645\u0627\u06cc\u0634 \u0647\u0645\u0647 \u06af\u067e\u200c\u0647\u0627")):
                for gap in unsolved:
                    st.write(gap.get("title_fa", gap.get("gap_id", "")))
        else:
            st.info("\u0647\u0646\u0648\u0632 \u06af\u067e\u200c\u0647\u0627\u06cc \u0628\u0627\u0632 \u0645\u0634\u062e\u0635 \u0646\u06cc\u0633\u062a.")

    with tabs[2]:
        quick = course_groups.get("quick", [])
        if quick:
            for code in quick[:3]:
                _render_course_card(code, course_catalog)
        else:
            st.info("\u062f\u0648\u0631\u0647\u200c\u0647\u0627\u06cc \u0634\u0631\u0648\u0639 \u0633\u0631\u06cc\u0639 \u0647\u0646\u0648\u0632 \u0645\u0634\u062e\u0635 \u0646\u06cc\u0633\u062a.")
        with st.expander(safe_text("\u0645\u0631\u062d\u0644\u0647 \u0627\u0631\u062a\u0642\u0627")):
            upgrade = course_groups.get("upgrade", [])
            if upgrade:
                for code in upgrade:
                    _render_course_card(code, course_catalog)
            else:
                st.caption("\u0641\u0639\u0644\u0627 \u062f\u0648\u0631\u0647 \u0627\u0631\u062a\u0642\u0627 \u0645\u0634\u062e\u0635 \u0646\u06cc\u0633\u062a.")
        with st.expander(safe_text("\U0001F6AB \u062f\u0648\u0631\u0647\u200c\u0647\u0627\u06cc\u06cc \u06a9\u0647 \u0641\u0639\u0644\u0627 \u062a\u0648\u0635\u06cc\u0647 \u0646\u0645\u06cc\u200c\u0634\u0648\u062f")):
            avoid = course_groups.get("avoid", [])
            if avoid:
                for code in avoid:
                    _render_course_card(code, course_catalog)
            else:
                st.caption("\u0645\u0648\u0631\u062f\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \u0627\u0633\u062a.")

    with tabs[3]:
        with card_container():
            target_title = _job_title(target_job)
            if target_title:
                st.write(f"\u0634\u063a\u0644 \u0647\u062f\u0641: {target_title}")
                st.caption(f"\u0627\u062d\u062a\u0645\u0627\u0644: {probability_label}")
            else:
                st.info("\u0634\u063a\u0644 \u0647\u062f\u0641 \u0647\u0646\u0648\u0632 \u0645\u0634\u062e\u0635 \u0646\u06cc\u0633\u062a.")

        now_jobs = job_groups.get("now", [])
        if now_jobs:
            st.write("\u0642\u0627\u0628\u0644\u200c\u062f\u0633\u062a\u0631\u0633 \u0627\u0644\u0627\u0646:")
            for job in now_jobs[:3]:
                st.caption(_job_title(job))

        with st.expander(safe_text("\u0634\u063a\u0644\u200c\u0647\u0627\u06cc \u0645\u0631\u062a\u0628\u0637")):
            related = job_groups.get("related", [])
            if related:
                for job in related:
                    st.write(_job_title(job))
            else:
                st.caption("\u0645\u0648\u0631\u062f\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \u0627\u0633\u062a.")

        with st.expander(safe_text("\u0645\u0634\u0627\u063a\u0644 \u0633\u0637\u062d \u0628\u0639\u062f\u06cc")):
            next_jobs = job_groups.get("next", [])
            if next_jobs:
                for job in next_jobs:
                    st.write(_job_title(job))
            else:
                st.caption("\u0645\u0648\u0631\u062f\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \u0627\u0633\u062a.")

    with tabs[4]:
        if debug:
            st.json(scores if isinstance(scores, dict) else {})
        else:
            st.caption("\u062c\u0632\u0626\u06cc\u0627\u062a \u0641\u0646\u06cc \u0641\u0642\u0637 \u062f\u0631 \u062d\u0627\u0644\u062a \u062f\u06cc\u0628\u0627\u06af \u0646\u0645\u0627\u06cc\u0634 \u062f\u0627\u062f\u0647 \u0645\u06cc\u200c\u0634\u0648\u062f.")
