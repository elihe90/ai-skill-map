from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]


JOB_TIME_FA = {
    "2-6_weeks": "۲ تا ۶ هفته",
    "2-8_weeks": "۲ تا ۸ هفته",
    "1-3_months": "۱ تا ۳ ماه",
    "2-4_months": "۲ تا ۴ ماه",
    "3-6_months": "۳ تا ۶ ماه",
    "6-12_months": "۶ تا ۱۲ ماه",
}

CATEGORY_FA = {
    "general": "عمومی",
    "semi_specialized": "نیمه‌تخصصی",
    "specialized": "تخصصی",
}

SKILL_FA = {
    "ai_literacy": "سواد مفهومی هوش مصنوعی",
    "prompting": "پرامپت‌نویسی",
    "office_tools": "ابزارهای آفیس",
    "data_basics": "مبانی داده",
    "bi_tools": "Power BI/داشبورد",
    "sql": "SQL",
    "programming": "برنامه‌نویسی",
    "english": "انگلیسی",
    "soft_skills": "مهارت‌های نرم",
    "content_marketing": "بازاریابی محتوا",
    "automation_tools": "ابزارهای اتوماسیون",
    "api_basics": "مبانی API",
    "process_thinking": "تفکر فرایندی",
    "sales_crm": "فروش و CRM",
    "analytics": "تحلیل‌گری",
    "design_tools": "ابزارهای طراحی",
    "math_stats": "آمار و ریاضی",
    "ml_basics": "مبانی یادگیری ماشین",
    "communication": "ارتباطات",
    "portfolio": "نمونه‌کار",
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

SKILL_KEYS = set(SKILL_FA.keys()) | set(SKILL_MAP_FA.keys())

COURSE_BUCKETS = {
    "پایه": ["ai_literacy", "prompting", "office_tools", "english"],
    "کاربردی": [
        "content_marketing",
        "bi_tools",
        "analytics",
        "sales_crm",
        "design_tools",
        "automation_tools",
    ],
    "خروجی‌محور": ["portfolio", "process_thinking"],
}

LEVEL_META = {
    "A": {
        "title": "آماده ورود به مشاغل عمومی AI",
        "desc": "با تمرکز کوتاه‌مدت و ساخت نمونه‌کار، می‌توانید وارد بازار شوید.",
        "color": "#16A34A",
        "bg": "#DCFCE7",
        "border": "#BBF7D0",
    },
    "B": {
        "title": "نزدیک به ورود؛ نیازمند تقویت چند مهارت کلیدی",
        "desc": "با ۴ تا ۸ هفته تمرین هدفمند می‌توانید به سطح قابل‌استخدام برسید.",
        "color": "#2563EB",
        "bg": "#DBEAFE",
        "border": "#BFDBFE",
    },
    "C": {
        "title": "مرحله آشنایی؛ نیازمند پیش‌نیازهای مهم",
        "desc": "بهتر است ابتدا مسیر پایه را تکمیل کنید تا مسیر شغلی شما تثبیت شود.",
        "color": "#D97706",
        "bg": "#FEF3C7",
        "border": "#FDE68A",
    },
    "D": {
        "title": "شروع از پایه",
        "desc": "از مسیرهای مقدماتی شروع کنید تا سواد AI و مهارت‌های دیجیتال شکل بگیرد.",
        "color": "#6B7280",
        "bg": "#F3F4F6",
        "border": "#E5E7EB",
    },
}

CSS = """
<style>
.stApp { direction: rtl; background: #F9FAFB; }
.block-container { max-width: 1100px; margin: 0 auto; padding: 16px 20px 32px; }
.kpi-card { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 14px 16px; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 999px; background: #DBEAFE; color: #1D4ED8; font-size: 12px; margin-right: 6px; }
.card { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 16px 18px; margin-bottom: 12px; }
.subtle { color: #6B7280; font-size: 13px; }
.cta-box { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 16px 18px; }
.level-chip { display: inline-block; padding: 6px 12px; border-radius: 999px; font-size: 13px; font-weight: 600; }
.gap-card { background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; }
.gap-title { font-weight: 700; margin-bottom: 4px; }
.gap-desc { color: #4B5563; font-size: 13px; }
.gap-impact { color: #6B7280; font-size: 12px; margin-top: 4px; }
.gap-badge { display:inline-block; padding:2px 8px; border-radius:999px; font-size:11px; margin-left:6px; }
.gap-badge-low { background:#E5E7EB; color:#374151; }
.gap-badge-mid { background:#DBEAFE; color:#1D4ED8; }
.gap-badge-high { background:#FEF3C7; color:#92400E; }
</style>
"""


def load_jobs() -> List[Dict[str, Any]]:
    for path in (
        BASE_DIR / "data" / "jobs.ir.ai.v1.json",
        BASE_DIR / "jobs.ir.ai.v1.json",
        Path("data/jobs.ir.ai.v1.json"),
        Path("jobs.ir.ai.v1.json"),
    ):
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


def normalize_scores(scores: Dict[str, Any]) -> Dict[str, int]:
    normalized: Dict[str, int] = {key: 0 for key in SKILL_KEYS}

    for key, value in scores.items():
        canonical = SCORE_ALIASES.get(key, key)
        try:
            normalized[canonical] = int(value)
        except (TypeError, ValueError):
            normalized[canonical] = 0

    for key in list(normalized.keys()):
        normalized[key] = int(normalized.get(key, 0) or 0)

    return normalized


def compute_chance(job: Dict[str, Any], scores: Dict[str, int]) -> int:
    weights = job.get("skillWeights", {}) if isinstance(job.get("skillWeights"), dict) else {}
    total = 0.0
    for key, weight in weights.items():
        try:
            w = float(weight)
        except (TypeError, ValueError):
            w = 0.0
        total += scores.get(key, 0) * w
    return max(0, min(100, int(round(total))))


def chance_label(score: int) -> str:
    if score <= 39:
        return "کم"
    if score <= 59:
        return "متوسط"
    if score <= 79:
        return "خوب"
    return "بسیار خوب"


def pick_recommended_jobs(jobs: List[Dict[str, Any]], scores: Dict[str, int]) -> List[Dict[str, Any]]:
    scored = []
    for job in jobs:
        score = compute_chance(job, scores)
        scored.append({**job, "chanceScore": score, "chanceLabel": chance_label(score)})

    def cat_rank(cat: str) -> int:
        if cat == "general":
            return 0
        if cat == "semi_specialized":
            return 1
        return 2

    scored.sort(key=lambda item: (-item.get("chanceScore", 0), cat_rank(item.get("category", ""))))
    general = [j for j in scored if j.get("category") == "general"]
    specialized = [j for j in scored if j.get("category") == "specialized"]
    semi = [j for j in scored if j.get("category") == "semi_specialized"]

    selected: List[Dict[str, Any]] = []
    selected.extend(general[:2])
    remaining_slots = max(0, 5 - len(selected) - min(2, len(specialized)))
    selected.extend(semi[:remaining_slots])
    selected.extend(specialized[:2])

    if not selected:
        return scored[:5]
    return selected[:5]


def key_to_fa(key: str) -> str:
    return SKILL_FA.get(key, key.replace("_", " "))


def skill_meta(key: str) -> Dict[str, str]:
    if key in SKILL_MAP_FA:
        return SKILL_MAP_FA[key]
    return {"title": key.replace("_", " "), "desc": "مهارت مرتبط"}


def compute_job_gaps(job: Dict[str, Any], scores: Dict[str, int]) -> List[str]:
    weights = job.get("skillWeights", {}) if isinstance(job.get("skillWeights"), dict) else {}
    gaps: List[Tuple[str, float]] = []
    for key, weight in weights.items():
        try:
            w = float(weight)
        except (TypeError, ValueError):
            w = 0.0
        if w <= 0:
            continue
        gap_score = w * (100 - scores.get(key, 0))
        gaps.append((key, gap_score))
    gaps.sort(key=lambda item: item[1], reverse=True)
    return [item[0] for item in gaps[:3]]


def _gap_priority(weight: float, score: int) -> str:
    impact = weight * (100 - score)
    if impact >= 30:
        return "مهم"
    if impact >= 15:
        return "متوسط"
    return "کم"


def _gap_badge_class(label: str) -> str:
    if label == "مهم":
        return "gap-badge gap-badge-high"
    if label == "متوسط":
        return "gap-badge gap-badge-mid"
    return "gap-badge gap-badge-low"


def _gap_micro_action(title: str) -> str:
    title = title or ""
    if "پرامپت" in title:
        return "یک پرامپت کوتاه با نقش، هدف و خروجی بنویسید."
    if "Power BI" in title or "داشبورد" in title:
        return "یک فایل نمونه بسازید و یک نمودار ساده بکشید."
    if "SQL" in title:
        return "یک SELECT ساده با WHERE بنویسید."
    if "انگلیسی" in title:
        return "یک پاراگراف از یک راهنمای AI را بخوانید و خلاصه کنید."
    if "محتوا" in title:
        return "برای یک موضوع، ۳ کپشن کوتاه بنویسید."
    if "طراحی" in title or "Canva" in title:
        return "یک کاور ساده در Canva بسازید."
    if "Office" in title or "آفیس" in title or "Excel" in title:
        return "یک جدول ساده بسازید و یک نمودار اضافه کنید."
    if "نمونه‌کار" in title or "نمونه کار" in title:
        return "یک خروجی واقعی بسازید و در یک فایل ذخیره کنید."
    if "اتوماسیون" in title:
        return "یک سناریوی ساده را روی کاغذ بنویسید."
    return "یک تمرین ۱۰ دقیقه‌ای مرتبط با این مهارت انجام دهید."


def _job_gap_items(job: Dict[str, Any], scores: Dict[str, int], top_n: int = 4) -> List[Dict[str, Any]]:
    weights = job.get("skillWeights", {}) if isinstance(job.get("skillWeights"), dict) else {}
    items = []
    for key, weight in weights.items():
        try:
            w = float(weight)
        except (TypeError, ValueError):
            w = 0.0
        if w <= 0:
            continue
        score = int(scores.get(key, 0))
        impact = w * (100 - score)
        items.append({"key": key, "weight": w, "score": score, "impact": impact})
    items.sort(key=lambda item: item["impact"], reverse=True)
    return items[:top_n]


def compute_why_fit(job: Dict[str, Any], scores: Dict[str, int]) -> List[str]:
    weights = job.get("skillWeights", {}) if isinstance(job.get("skillWeights"), dict) else {}
    matches: List[Tuple[str, float]] = []
    for key, weight in weights.items():
        try:
            w = float(weight)
        except (TypeError, ValueError):
            w = 0.0
        match_score = w * scores.get(key, 0)
        matches.append((key, match_score))
    matches.sort(key=lambda item: item[1], reverse=True)
    reasons = []
    for key, _ in matches[:2]:
        reasons.append(f"امتیاز خوب شما در «{key_to_fa(key)}» با نیاز این شغل هم‌خوان است.")
    return reasons


def compute_level_code(scores: Dict[str, int]) -> str:
    core_keys = ["ai_literacy", "prompting", "office_tools", "data_basics", "english"]
    practical_keys = ["portfolio", "soft_skills"]
    core = sum(scores.get(k, 0) for k in core_keys) / len(core_keys)
    practical = sum(scores.get(k, 0) for k in practical_keys) / len(practical_keys)

    if core >= 60 and practical >= 40:
        return "A"
    if core >= 50:
        return "B"
    if core >= 35:
        return "C"
    return "D"


def level_to_user_friendly(level_code: str) -> Dict[str, str]:
    return LEVEL_META.get(level_code, LEVEL_META["D"])


def compute_goal_probability(best_chance: int, goal_horizon: str, time_per_week: int, level_code: str) -> Tuple[int, str]:
    time_factor = {
        "درآمد سریع": 0.9,
        "3 ماه": 1.0,
        "6 ماه": 1.1,
        "12 ماه": 1.2,
    }.get(goal_horizon, 1.0)

    if time_per_week <= 3:
        effort_factor = 0.85
    elif time_per_week <= 6:
        effort_factor = 1.0
    elif time_per_week <= 10:
        effort_factor = 1.1
    else:
        effort_factor = 1.15

    probability = int(round(best_chance * time_factor * effort_factor))
    probability = max(0, min(100, probability))

    if level_code == "A" and probability < 50 and best_chance >= 45:
        probability = 50

    if probability >= 70:
        label = "بالا"
    elif probability >= 50:
        label = "متوسط"
    else:
        label = "کم"

    return probability, label


def render_level_badge(level_code: str, title: str) -> None:
    meta = level_to_user_friendly(level_code)
    st.markdown(
        f"<span class='level-chip' style='background:{meta['bg']};color:{meta['color']};border:1px solid {meta['border']}'>"
        f"{title}</span>",
        unsafe_allow_html=True,
    )


def build_summary_text(level_title: str, time_per_week: int, goal_horizon: str) -> str:
    if time_per_week <= 3:
        window = "۸ تا ۱۲ هفته"
        effort = "کم"
    elif time_per_week <= 6:
        window = "۴ تا ۸ هفته"
        effort = "متوسط"
    else:
        window = "۴ تا ۶ هفته"
        effort = "خوب"

    return (
        f"وضعیت فعلی شما: «{level_title}». "
        f"با زمان آزاد {time_per_week} ساعت در هفته و هدف «{goal_horizon}»، "
        f"اگر برنامه منظم داشته باشید، در بازه {window} می‌توانید به خروجی قابل ارائه برسید. "
        f"پیشنهادهای این صفحه بر اساس بازار ایران و میزان تلاش {effort} طراحی شده‌اند."
    )


def build_course_buckets(scores: Dict[str, int]) -> Dict[str, List[str]]:
    output: Dict[str, List[str]] = {"پایه": [], "کاربردی": [], "خروجی‌محور": []}
    for bucket, keys in COURSE_BUCKETS.items():
        gaps = [key for key in keys if scores.get(key, 0) < 60]
        for key in gaps[:4]:
            if key == "prompting":
                output[bucket].append("پرامپت‌نویسی کاربردی برای کار [پرامپت‌نویسی]")
            elif key == "office_tools":
                output[bucket].append("Excel/Power BI مقدماتی برای گزارش‌سازی [Power BI]")
            elif key == "ai_literacy":
                output[bucket].append("مبانی مفهومی هوش مصنوعی [سواد AI]")
            elif key == "english":
                output[bucket].append("انگلیسی کاربردی برای منابع AI [انگلیسی]")
            elif key == "programming":
                output[bucket].append("پایتون مقدماتی برای مسیر AI [برنامه‌نویسی]")
            elif key == "sql":
                output[bucket].append("SQL پایه برای تحلیل داده [SQL]")
            elif key == "ml_basics":
                output[bucket].append("مبانی یادگیری ماشین [ML]")
            else:
                output[bucket].append(f"تقویت {key_to_fa(key)}")
    return output


def render_results() -> None:
    st.markdown(CSS, unsafe_allow_html=True)

    interview_result = st.session_state.get("interview_result")
    if not isinstance(interview_result, dict):
        st.warning("نتایج مصاحبه هنوز ثبت نشده است.")
        if st.button("رفتن به مصاحبه"):
            st.session_state["current_step"] = "interview"
            st.rerun()
        return

    scores = normalize_scores(interview_result.get("scores", {}))
    goal_horizon = str(interview_result.get("goalHorizon") or "3 ماه")
    time_per_week = int(interview_result.get("timePerWeek") or 0)

    jobs = st.session_state.get("recommended_jobs")
    if not isinstance(jobs, list) or not jobs:
        jobs = load_jobs()
        if not jobs:
            st.error("فایل مشاغل پیدا نشد. لطفاً jobs.ir.ai.v1.json را در data/ قرار دهید.")
            jobs = []
        if jobs:
            jobs = pick_recommended_jobs(jobs, scores)
        st.session_state["recommended_jobs"] = jobs
    elif jobs and (not isinstance(jobs[0], dict) or "chanceScore" not in jobs[0]):
        jobs = pick_recommended_jobs(jobs, scores)
        st.session_state["recommended_jobs"] = jobs

    if not jobs:
        fallback_jobs = [
            {
                "jobKey": "ai_generalist",
                "titleFa": "اپراتور ابزارهای هوش مصنوعی در کسب‌وکار",
                "category": "general",
                "timeToEmployability": "2-6_weeks",
                "descriptionFa": "استفاده عملی از ابزارهای AI برای کارهای روزمره کسب‌وکار.",
                "coreTasksFa": ["تولید متن و گزارش", "بهبود خروجی محتوا"],
                "skillWeights": {"ai_literacy": 0.3, "prompting": 0.3, "office_tools": 0.2},
                "mustHaveSkillsFa": ["پرامپت‌نویسی", "سواد AI"],
                "niceToHaveSkillsFa": ["آفیس"],
                "portfolioIdeasFa": ["نمونه خروجی AI برای یک کار واقعی"],
            },
            {
                "jobKey": "ai_content_assistant",
                "titleFa": "تولیدکننده محتوا با هوش مصنوعی",
                "category": "general",
                "timeToEmployability": "2-8_weeks",
                "descriptionFa": "تولید کپشن، سناریو و محتوای کوتاه با ابزارهای AI.",
                "coreTasksFa": ["تولید محتوای متنی", "بهینه‌سازی لحن و ساختار"],
                "skillWeights": {"prompting": 0.35, "content_marketing": 0.25, "ai_literacy": 0.2},
                "mustHaveSkillsFa": ["پرامپت‌نویسی", "تولید محتوا"],
                "niceToHaveSkillsFa": ["ابزارهای طراحی"],
                "portfolioIdeasFa": ["۳ نمونه پست برای یک برند واقعی"],
            },
            {
                "jobKey": "ai_marketing_support",
                "titleFa": "دستیار دیجیتال مارکتینگ مبتنی بر AI",
                "category": "semi_specialized",
                "timeToEmployability": "1-3_months",
                "descriptionFa": "کمک به تیم مارکتینگ در تولید محتوا و گزارش‌گیری.",
                "coreTasksFa": ["گزارش ساده KPI", "ایده‌پردازی کمپین"],
                "skillWeights": {"content_marketing": 0.3, "analytics": 0.2, "bi_tools": 0.2},
                "mustHaveSkillsFa": ["تولید محتوا", "تحلیل KPI"],
                "niceToHaveSkillsFa": ["Power BI"],
                "portfolioIdeasFa": ["داشبورد ساده یک کمپین"],
            },
        ]
        jobs = pick_recommended_jobs(fallback_jobs, scores)

    best_job = jobs[0] if jobs else {"titleFa": "مسیر پیشنهادی عمومی AI", "chanceScore": 0, "chanceLabel": "کم"}
    best_chance = int(best_job.get("chanceScore", 0)) if isinstance(best_job, dict) else 0

    level_code = st.session_state.get("levelCode")
    if not isinstance(level_code, str) or not level_code:
        level_code = compute_level_code(scores)
        st.session_state["levelCode"] = level_code

    level_meta = level_to_user_friendly(level_code)
    goal_probability, goal_label = compute_goal_probability(best_chance, goal_horizon, time_per_week, level_code)

    summary_text = build_summary_text(level_meta["title"], time_per_week, goal_horizon)

    if st.session_state.get("debug", False):
        weights = best_job.get("skillWeights", {}) if isinstance(best_job, dict) else {}
        overlap = len(set(scores.keys()) & set(weights.keys()))
        st.write("__file__", __file__)
        st.write("cwd", os.getcwd())
        st.write("jobs_count", len(jobs))
        st.write("first_job_skillWeights_keys", list(weights.keys()))
        st.write("score_keys", list(scores.keys()))
        st.write("overlap_count", overlap)

    overall_gaps: List[Dict[str, Any]] = []
    weights_for_priority = (
        best_job.get("skillWeights", {}) if isinstance(best_job.get("skillWeights"), dict) else {}
    )
    for key, weight in weights_for_priority.items():
        try:
            w = float(weight)
        except (TypeError, ValueError):
            w = 0.0
        if w <= 0:
            continue
        score = int(scores.get(key, 0))
        impact = w * (100 - score)
        overall_gaps.append({"key": key, "weight": w, "score": score, "impact": impact})
    if overall_gaps:
        overall_gaps.sort(key=lambda item: item["impact"], reverse=True)
        overall_gaps = overall_gaps[:6]
    else:
        overall_gaps = [
            {"key": key, "weight": 0.2, "score": score, "impact": 0.2 * (100 - score)}
            for key, score in sorted(scores.items(), key=lambda item: item[1])[:6]
        ]
    course_buckets = build_course_buckets(scores)

    st.title("نتایج تحلیل مسیر شغلی")
    st.caption("خلاصه‌ای کوتاه، روشن و قابل اقدام برای مسیر شما")
    st.caption("نسخه نتایج: 2.1")

    with st.container():
        render_level_badge(level_code, f"وضعیت فعلی شما: {level_meta['title']}")
        st.caption(level_meta["desc"])

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(
            f"<div class='kpi-card'>احتمال تحقق هدف<br><strong>{goal_label} ({goal_probability}٪)</strong></div>",
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f"<div class='kpi-card'>شغل پیشنهادی اصلی<br><strong>{best_job.get('titleFa','مسیر عمومی AI')}</strong></div>",
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f"<div class='kpi-card'>گپ‌های مهارتی کلیدی<br><strong>{len(overall_gaps)}</strong></div>",
            unsafe_allow_html=True,
        )
    with col4:
        st.markdown(
            f"<div class='kpi-card'>دوره‌های شروع سریع<br><strong>{max(3, min(6, len(overall_gaps)))}</strong></div>",
            unsafe_allow_html=True,
        )

    tab_summary, tab_jobs, tab_gaps, tab_courses, tab_details = st.tabs(
        ["خلاصه", "شغل‌ها", "گپ‌ها", "دوره‌ها", "جزئیات"]
    )

    with tab_summary:
        st.markdown(f"<div class='card'><p>{summary_text}</p></div>", unsafe_allow_html=True)
        st.subheader("مشاغلی که در بازار ایران بیشترین شانس را دارند")
        for job in jobs[:3]:
            st.markdown(
                f"<div class='card'><strong>{job.get('titleFa','')}</strong>"
                f" <span class='badge'>{CATEGORY_FA.get(job.get('category'), '')}</span>"
                f"<div class='subtle'>شانس ورود: {job.get('chanceLabel','')} | زمان: {JOB_TIME_FA.get(job.get('timeToEmployability',''), '-') }</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

        st.markdown("<div class='cta-box'>", unsafe_allow_html=True)
        st.subheader("قدم بعدی شما (۱۰ دقیقه)")
        st.write("برای تثبیت مسیر، یک تمرین کوتاه انجام دهید تا یک خروجی قابل ارائه بسازید.")
        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("شروع تمرین ۱۰ دقیقه‌ای"):
                st.session_state["next_step"] = "ten_minute_exercise"
                st.rerun()
        with col_b:
            if st.button("نمایش نقشه مهارتی"):
                st.session_state["next_step"] = "skill_map"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with tab_jobs:
        for job in jobs:
            with st.container():
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                title = job.get("titleFa", "")
                category = CATEGORY_FA.get(job.get("category"), "")
                st.write(f"{title} — {category}")
                st.progress(int(job.get("chanceScore", 0)))
                st.caption(
                    f"شانس ورود: {job.get('chanceLabel','')} | زمان تا آماده‌سازی: {JOB_TIME_FA.get(job.get('timeToEmployability',''), '-')}"
                )
                description = job.get("descriptionFa", "")
                if description:
                    st.caption(description)
                with st.expander("چرا مناسب شماست؟"):
                    for reason in compute_why_fit(job, scores):
                        st.write(f"- {reason}")
                with st.expander("گپ‌های اصلی"):
                    gap_items = _job_gap_items(job, scores)
                    if not gap_items:
                        st.caption("گپ شاخصی برای این شغل پیدا نشد.")
                    for gap_item in gap_items:
                        info = skill_meta(gap_item["key"])
                        label = _gap_priority(gap_item.get("weight", 0.2), gap_item.get("score", 0))
                        st.write(f"- {info['title']} ({label})")
                with st.expander("مهارت‌های موردنیاز"):
                    weights = job.get("skillWeights", {}) if isinstance(job.get("skillWeights"), dict) else {}
                    if not weights:
                        st.caption("مهارت مشخصی ثبت نشده است.")
                    else:
                        for key, weight in weights.items():
                            if float(weight or 0) <= 0:
                                continue
                            info = skill_meta(key)
                            st.write(f"- {info['title']}")
                with st.expander("نمونه‌کار پیشنهادی"):
                    for item in (job.get("portfolioIdeasFa") or [])[:2]:
                        st.write(f"- {item}")
                with st.expander("کارهای رایج در این نقش"):
                    for item in (job.get("coreTasksFa") or [])[:3]:
                        st.write(f"- {item}")
                st.markdown("</div>", unsafe_allow_html=True)

    with tab_gaps:
        st.subheader("گپ‌های کلی (قابل اقدام)")
        st.caption("برای هر گپ یک اقدام کوچک پیشنهاد شده است تا سریع‌تر پیش بروید.")
        for item in overall_gaps:
            info = skill_meta(item["key"])
            label = _gap_priority(item.get("weight", 0.2), item.get("score", 0))
            badge_class = _gap_badge_class(label)
            micro = _gap_micro_action(info["title"])
            st.markdown(
                f"<div class='gap-card'><div class='gap-title'>{info['title']}"
                f"<span class='{badge_class}'>{label}</span></div>"
                f"<div class='gap-desc'>{info['desc']}</div>"
                f"<div class='gap-impact'><strong>اقدام کوچک امروز:</strong> {micro}</div></div>",
                unsafe_allow_html=True,
            )

    with tab_courses:
        st.caption("این مسیر بر اساس گپ‌های مهارتی شما پیشنهاد شده است.")
        for bucket, items in course_buckets.items():
            st.markdown(f"**{bucket}**")
            if items:
                for item in items:
                    st.write(f"- {item}")
            else:
                st.caption("فعلاً موردی پیشنهاد نمی‌شود.")

    with tab_details:
        st.json(interview_result)
        st.caption(f"کد سطح (برای دیباگ): {level_code}")


if __name__ == "__main__":
    render_results()
