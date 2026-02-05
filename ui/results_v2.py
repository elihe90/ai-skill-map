from __future__ import annotations

import json
from pathlib import Path
import os
from typing import Any, Dict, Iterable, List, Optional, Tuple

import streamlit as st

BASE_DIR = Path(__file__).resolve().parents[1]

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

SKILL_MAP_FA = {
    "bi_tools": {"title": "Power BI / داشبورد", "desc": "ساخت داشبورد و KPI"},
    "sql": {"title": "SQL مقدماتی", "desc": "گزارش‌گیری از دیتابیس"},
    "english": {"title": "انگلیسی کاربردی", "desc": "کار با ابزار و مستندات"},
    "content_marketing": {"title": "تولید محتوا با AI", "desc": "کپشن، سناریو، پیام تبلیغاتی"},
    "sales_crm": {"title": "فروش و CRM با AI", "desc": "پیگیری مشتری و پیام‌سازی فروش"},
    "design_tools": {"title": "ابزارهای طراحی (Canva)", "desc": "کاور، پوستر، اسلاید"},
    "ai_literacy": {"title": "سواد هوش مصنوعی", "desc": "درک کاربرد AI در کسب‌وکار"},
    "prompting": {"title": "پرامپت‌نویسی", "desc": "گرفتن خروجی دقیق و قابل استفاده"},
    "office_tools": {"title": "ابزارهای Office", "desc": "Excel/PowerPoint برای کار"},
    "data_basics": {"title": "مفاهیم پایه داده", "desc": "تمیزسازی و تحلیل اولیه"},
    "automation_tools": {"title": "اتوماسیون فرایند", "desc": "خودکارسازی کارها"},
    "api_basics": {"title": "API و اتصال", "desc": "اتصال سرویس‌ها"},
    "programming": {"title": "برنامه‌نویسی", "desc": "Python/JS برای پیاده‌سازی"},
    "portfolio": {"title": "نمونه‌کار", "desc": "خروجی واقعی و قابل ارائه"},
    "communication": {"title": "ارتباط و ارائه", "desc": "ارائه و تعامل تیمی"},
    "analytics": {"title": "تحلیل KPI", "desc": "تحلیل عملکرد کمپین/فروش"},
    "math_stats": {"title": "ریاضی و آمار", "desc": "پایه تحلیل و مدل‌سازی"},
    "ml_basics": {"title": "مبانی یادگیری ماشین", "desc": "آشنایی با مدل‌ها"},
}

SCORE_ALIASES = {
    "ai_literacy_score": "ai_literacy",
    "prompt_score": "prompting",
    "office": "office_tools",
    "data": "data_basics",
    "bi": "bi_tools",
    "english_level": "english",
    "softskills": "soft_skills",
    "content": "content_marketing",
    "automation": "automation_tools",
    "api": "api_basics",
    "process": "process_thinking",
    "sales": "sales_crm",
    "design": "design_tools",
    "math": "math_stats",
    "ml": "ml_basics",
    "comm": "communication",
}

JOB_TIME_FA = {
    "2-6_weeks": "? ?? ? ????",
    "2-8_weeks": "? ?? ? ????",
    "1-3_months": "? ?? ? ???",
    "2-4_months": "? ?? ? ???",
    "3-6_months": "? ?? ? ???",
    "6-12_months": "? ?? ?? ???",
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

JOB_LABELS = {
    "general": "عمومی",
    "semi_specialized": "نیمه‌تخصصی",
    "specialized": "تخصصی",
}

LEVEL_LABELS = {
    "A": "آماده ورود به مشاغل عمومی AI",
    "B": "آماده ورود به نقش‌های نیمه‌تخصصی AI",
    "C": "آماده ورود به نقش‌های تخصصی AI",
}

CHANCE_LABELS = {
    (0, 39): "کم",
    (40, 59): "متوسط",
    (60, 79): "خوب",
    (80, 100): "بسیار خوب",
}


def _badge(text: str) -> None:
    with st.container():
        st.markdown("<div class='rv2-badge-anchor'></div>", unsafe_allow_html=True)
        st.write(safe_text(text))


def _skill_meta(key: str) -> Dict[str, str]:
    return SKILL_MAP_FA.get(str(key), {"title": str(key).replace("_", " "), "desc": "مهارت مرتبط"})


def _normalize_scores(scores: Dict[str, Any]) -> Dict[str, int]:
    normalized: Dict[str, int] = {}
    for key, value in scores.items():
        canonical = SCORE_ALIASES.get(key, key)
        try:
            normalized[canonical] = int(value)
        except (TypeError, ValueError):
            normalized[canonical] = 0
    return normalized


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


def _load_jobs_catalog() -> List[Dict[str, Any]]:
    candidates = [
        BASE_DIR / "data" / "jobs.ir.ai.v1.json",
        BASE_DIR / "jobs.ir.ai.v1.json",
        Path("data/jobs.ir.ai.v1.json"),
        Path("jobs.ir.ai.v1.json"),
    ]
    for path in candidates:
        if not path.exists():
            continue
        try:
            raw = path.read_text(encoding="utf-8-sig")
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            items = data.get("jobs") or data.get("items") or []
            return [item for item in items if isinstance(item, dict)]
    return []


def _chance_label(score: int) -> str:
    for (low, high), label in CHANCE_LABELS.items():
        if low <= score <= high:
            return label
    return "کم"


def _score_job(job: Dict[str, Any], scores: Dict[str, Any]) -> int:
    weights = job.get("skillWeights", {}) if isinstance(job.get("skillWeights"), dict) else {}
    total = 0.0
    for key, weight in weights.items():
        try:
            w = float(weight)
        except (TypeError, ValueError):
            w = 0.0
        try:
            s = float(scores.get(key, 0))
        except (TypeError, ValueError):
            s = 0.0
        total += s * w
    return max(0, min(100, int(round(total))))



def _compute_why_fit(job: Dict[str, Any], scores: Dict[str, Any]) -> List[str]:
    weights = job.get("skillWeights", {}) if isinstance(job.get("skillWeights"), dict) else {}
    matches: List[Tuple[str, float]] = []
    for key, weight in weights.items():
        try:
            w = float(weight)
        except (TypeError, ValueError):
            w = 0.0
        try:
            s = float(scores.get(key, 0))
        except (TypeError, ValueError):
            s = 0.0
        matches.append((key, w * s))
    matches.sort(key=lambda item: item[1], reverse=True)
    reasons: List[str] = []
    for key, _ in matches[:2]:
        meta = _skill_meta(key)
        reasons.append(f"??? ??? ??? ?? ?{meta['title']}? ?? ???? ??? ??? ???? ???.")
    return reasons

def _compute_main_gaps(job: Dict[str, Any], scores: Dict[str, Any], top_n: int = 3) -> List[str]:
    weights = job.get("skillWeights", {}) if isinstance(job.get("skillWeights"), dict) else {}
    items = []
    for key, weight in weights.items():
        try:
            w = float(weight)
        except (TypeError, ValueError):
            w = 0.0
        try:
            s = float(scores.get(key, 0))
        except (TypeError, ValueError):
            s = 0.0
        items.append((key, w, s))
    items.sort(key=lambda item: (-item[1], item[2]))
    return [item[0] for item in items[:top_n]]


def _overall_gaps(scores: Dict[str, Any], top_n: int = 6) -> List[str]:
    items = []
    for key, value in scores.items():
        try:
            score = float(value)
        except (TypeError, ValueError):
            score = 0.0
        items.append((key, score))
    items.sort(key=lambda item: item[1])
    return [item[0] for item in items[:top_n]]


def _select_top_jobs(jobs: List[Dict[str, Any]], scores: Dict[str, Any]) -> List[Dict[str, Any]]:
    scored = []
    for job in jobs:
        score = _score_job(job, scores)
        scored.append({**job, "chanceScore": score, "chanceLabel": _chance_label(score)})
    scored.sort(key=lambda item: item.get("chanceScore", 0), reverse=True)

    general = [j for j in scored if j.get("category") == "general"]
    specialized = [j for j in scored if j.get("category") == "specialized"]
    other = [j for j in scored if j.get("category") not in {"general", "specialized"}]

    selected: List[Dict[str, Any]] = []
    selected.extend(general[:2])
    specialized_pool = specialized[:2]
    remaining = [j for j in scored if j not in selected and j not in specialized_pool]
    for job in specialized_pool:
        if len(selected) >= 5:
            break
        selected.append(job)
    for job in remaining:
        if len(selected) >= 5:
            break
        selected.append(job)
    if not selected:
        return scored[:5]
    return selected


def _fallback_jobs() -> List[Dict[str, Any]]:
    return [
        {
            "jobKey": "ai_generalist_business_operator",
            "titleFa": "اپراتور ابزارهای هوش مصنوعی در کسب‌وکار",
            "category": "general",
            "timeToEmployability": "2-6_weeks",
            "descriptionFa": "کار با ابزارهای AI برای امور روزمره کسب‌وکار.",
            "coreTasksFa": ["تولید متن", "خلاصه‌سازی", "گزارش ساده"],
            "skillWeights": {"ai_literacy": 0.2, "prompting": 0.35, "office_tools": 0.25, "english": 0.1},
            "portfolioIdeasFa": ["۳ گزارش کوتاه با AI"],
        },
        {
            "jobKey": "ai_content_creator",
            "titleFa": "تولیدکننده محتوا با هوش مصنوعی",
            "category": "general",
            "timeToEmployability": "2-8_weeks",
            "descriptionFa": "تولید کپشن، سناریو و محتوای کوتاه با ابزارهای AI.",
            "coreTasksFa": ["ایده‌پردازی محتوا", "بهبود لحن و ساختار"],
            "skillWeights": {"prompting": 0.35, "content_marketing": 0.25, "ai_literacy": 0.2},
            "portfolioIdeasFa": ["۳ پست برای یک برند"],
        },
        {
            "jobKey": "ai_marketing_assistant",
            "titleFa": "دستیار دیجیتال مارکتینگ مبتنی بر AI",
            "category": "semi_specialized",
            "timeToEmployability": "1-3_months",
            "descriptionFa": "کمک به تیم مارکتینگ در تولید محتوا و گزارش‌گیری.",
            "coreTasksFa": ["گزارش KPI", "ایده‌پردازی کمپین"],
            "skillWeights": {"content_marketing": 0.3, "analytics": 0.2, "bi_tools": 0.2},
            "portfolioIdeasFa": ["داشبورد ساده کمپین"],
        },
    ]


def _render_results_from_interview(interview_result: Dict[str, Any]) -> None:
    st.markdown(RESULTS_V2_CSS, unsafe_allow_html=True)

    raw_scores = interview_result.get("scores", {}) if isinstance(interview_result, dict) else {}
    scores = _normalize_scores(raw_scores)
    time_per_week = interview_result.get("timePerWeek")
    goal_horizon = interview_result.get("goalHorizon", "")

    jobs_catalog = _load_jobs_catalog()
    recommended = _select_top_jobs(jobs_catalog, scores)
    if not recommended:
        recommended = _select_top_jobs(_fallback_jobs(), scores)

    top_job = recommended[0] if recommended else {}
    top_title = top_job.get("titleFa") or top_job.get("title_fa") or "???? ????? AI"
    top_label = top_job.get("chanceLabel") or "??"

    level = ""
    gap = st.session_state.get("gap")
    if isinstance(gap, dict):
        level = str(gap.get("training_level") or "")
    level_label = LEVEL_LABELS.get(level, "")

    if st.session_state.get("debug", False):
        weights = top_job.get("skillWeights", {}) if isinstance(top_job, dict) else {}
        overlap = len(set(scores.keys()) & set(weights.keys()))
        st.write("__file__", __file__)
        st.write("cwd", os.getcwd())
        st.write("jobs_count", len(recommended))
        st.write("first_job_skillWeights_keys", list(weights.keys()))
        st.write("score_keys", list(scores.keys()))
        st.write("overlap_count", overlap)

    overall_gap_keys = _overall_gaps(scores, 6)

    st.markdown("<div class='rv2-title'>????? ????? ???? ????</div>", unsafe_allow_html=True)
    st.markdown(
        "<div class='rv2-subtitle'>???????? ????? ? ???? ????? ???? ???? ???</div>",
        unsafe_allow_html=True,
    )
    st.caption("??? ????????? ?? ???? ????? ???? ??? ?? ????? ????? ?????? ??????? ? ?? ?????? ???????? ??????????? ???????.")

    badge_items = []
    if goal_horizon:
        badge_items.append(f"???: {goal_horizon}")
    if time_per_week:
        badge_items.append(f"???? ???? ?????: {time_per_week} ????")
    if level:
        if level_label:
            badge_items.append(f"??? ????: {level} ({level_label})")
        else:
            badge_items.append(f"??? ????: {level}")

    for item in badge_items:
        _badge(item)

    with card_container():
        st.subheader("???????? ?????")
        if level_label:
            st.write(f"??? ???? ???: **{level}** ? {level_label}.")
        st.write("?? ???? ?? ????? ??????? ???? ???????? ??? ?? ????? ????? ???? ??? ???.")
        st.write("?? ????? ?????? ?? ? ?? ? ???? ????????? ?? ??? ???????????? ?????.")
        st.caption("???????? ?????")
        st.write(f"?????? ???? ??? ???: {top_label}")
        st.write(f"?????? ?????? ?????: {len(overall_gap_keys)} ????")
        st.write("???????? ???? ???? ????????: ? ???? ?????")

    if not recommended:
        recommended = _select_top_jobs(_fallback_jobs(), scores)

    with card_container():
        st.subheader("?????? ?? ?? ????? ????? ??????? ???? ?? ?????")
        for job in recommended[:3]:
            title = job.get("titleFa") or job.get("title_fa") or ""
            category = JOB_LABELS.get(job.get("category"), job.get("category", ""))
            label = job.get("chanceLabel", "")
            time_to_ready = JOB_TIME_FA.get(job.get("timeToEmployability", ""), "-")
            st.write(f"?? {title}")
            st.caption(f"???: {category} | ???? ????: {label} | ???? ??????????: {time_to_ready}")

    with card_container():
        st.subheader("??? ???? ??? (?? ?????)")
        st.write("???? ????? ????? ?? ????? ????? ????? ???? ?? ?? ????? ???? ????? ??????.")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("???? ????? ?? ????????"):
                st.session_state["next_step"] = "ten_minute_exercise"
                st.rerun()
        with col_b:
            if st.button("????? ???? ?????? ???? ???"):
                st.session_state["next_step"] = "skill_map"
                st.rerun()

    tabs = st.tabs(
        [
            safe_text("?????"),
            safe_text("?????"),
            safe_text("???????"),
            safe_text("??????"),
            safe_text("??????"),
        ]
    )

    with tabs[1]:
        st.subheader("????? (Skill Gaps)")
        if overall_gap_keys:
            st.write("? ?? ?????? ???? ?? ??????? ??? ?? ?????:")
            for key in overall_gap_keys:
                meta = _skill_meta(key)
                st.write(f"- {meta['title']}: {meta['desc']}")
        for job in recommended:
            title = job.get("titleFa") or job.get("title_fa") or ""
            gaps = _compute_main_gaps(job, scores)
            st.write(f"**{title}**")
            for gap in gaps:
                meta = _skill_meta(gap)
                st.write(f"- {meta['title']}")

    with tabs[2]:
        st.subheader("??????? (Quick Courses)")
        st.write("???? ???????? ? ???????? (???? ????)")
        st.write("**????**")
        st.write("- ???? AI ???? ??? ? ????????")
        st.write("- ???????????? ??????? ? ???????")
        st.write("**???????**")
        st.write("- ????? ????? ?? AI (???/????/????)")
        st.write("- ?????????? ???? ?? Excel + AI")
        st.write("**????? ????**")
        st.write("- ???? ? ????????? ????? (???/???)")
        st.write("- ?????????? ????? ????? ????????")

    with tabs[3]:
        st.subheader("??????")
        for job in recommended:
            title = job.get("titleFa") or job.get("title_fa") or ""
            category = JOB_LABELS.get(job.get("category"), job.get("category", ""))
            label = job.get("chanceLabel", "")
            time_to_ready = JOB_TIME_FA.get(job.get("timeToEmployability", ""), "-")
            st.write(f"**{title}**")
            st.caption(f"???: {category} | ???? ????: {label} | ???? ??????????: {time_to_ready}")
            with st.expander("??? ????? ??????"):
                for reason in _compute_why_fit(job, scores)[:2]:
                    st.write(f"- {reason}")
            with st.expander("?????? ????"):
                for gap in _compute_main_gaps(job, scores)[:3]:
                    meta = _skill_meta(gap)
                    st.write(f"- {meta['title']}")
            with st.expander("????????? ????????"):
                for item in (job.get("portfolioIdeasFa") or [])[:2]:
                    st.write(f"- {item}")
            with st.expander("?????? ???? ?? ??? ???"):
                for item in (job.get("coreTasksFa") or [])[:3]:
                    st.write(f"- {item}")

    with tabs[4]:
        st.json(interview_result)
def render_results_page_v2(
    profile: Dict[str, Any],
    scores: Dict[str, Any],
    skill_gaps: Any,
    courses: Dict[str, Any],
    jobs: Dict[str, Any],
    course_catalog: Optional[Dict[str, Any]] = None,
    debug: bool = False,
) -> None:
    interview_result = st.session_state.get("interview_result")
    if isinstance(interview_result, dict):
        _render_results_from_interview(interview_result)
        return
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
