from typing import Optional

import streamlit as st

from core.schema import (
    DIGITAL_LEVELS,
    EDUCATION_LEVELS,
    EMPLOYMENT_STATUSES,
    GOAL_TYPES,
    Profile,
    normalize_profile,
)

EMPLOYMENT_LABELS = {
    "employed": "شاغل",
    "unemployed": "بیکار",
    "student": "دانشجو",
}
EDUCATION_LABELS = {
    "high_school": "دیپلم",
    "associate": "کاردانی",
    "bachelor": "کارشناسی",
    "master": "کارشناسی ارشد",
    "phd": "دکتری",
    "other": "سایر",
}
DIGITAL_LABELS = {
    "weak": "ضعیف",
    "medium": "متوسط",
    "good": "خوب",
}
GOAL_LABELS = {
    "quick_income": "درآمد سریع",
    "career_upgrade": "ارتقای شغلی",
    "technical_switch": "تغییر مسیر فنی",
}


def _index_for(options: tuple[str, ...], value: Optional[str]) -> int:
    if value in options:
        return options.index(value)
    return 0


def render_profile_form() -> bool:
    existing: Optional[Profile] = st.session_state.get("profile")

    with st.form("profile_form", clear_on_submit=False):
        age = st.number_input(
            "سن",
            min_value=0,
            max_value=120,
            step=1,
            value=int(existing["age"]) if existing else 22,
        )
        employment_status = st.selectbox(
            "وضعیت اشتغال",
            options=EMPLOYMENT_STATUSES,
            index=_index_for(EMPLOYMENT_STATUSES, existing["employment_status"] if existing else None),
            format_func=EMPLOYMENT_LABELS.get,
        )
        education_level = st.selectbox(
            "سطح تحصیلات",
            options=EDUCATION_LEVELS,
            index=_index_for(EDUCATION_LEVELS, existing["education_level"] if existing else None),
            format_func=EDUCATION_LABELS.get,
        )
        digital_level = st.selectbox(
            "سطح مهارت دیجیتال",
            options=DIGITAL_LEVELS,
            index=_index_for(DIGITAL_LEVELS, existing["digital_level"] if existing else None),
            format_func=DIGITAL_LABELS.get,
        )
        goal_type = st.selectbox(
            "هدف اصلی",
            options=GOAL_TYPES,
            index=_index_for(GOAL_TYPES, existing["goal_type"] if existing else None),
            format_func=GOAL_LABELS.get,
        )
        weekly_time_budget_hours = st.slider(
            "بودجه زمانی هفتگی (ساعت)",
            min_value=3,
            max_value=30,
            value=int(existing["weekly_time_budget_hours"]) if existing else 6,
        )
        submitted = st.form_submit_button("ذخیره پروفایل")

    if submitted:
        raw_profile = {
            "age": age,
            "employment_status": employment_status,
            "education_level": education_level,
            "digital_level": digital_level,
            "goal_type": goal_type,
            "weekly_time_budget_hours": weekly_time_budget_hours,
        }
        try:
            st.session_state["profile"] = normalize_profile(raw_profile)
        except ValueError as exc:
            st.error(str(exc))
            return False
        st.success("پروفایل ذخیره شد.")
        return True

    return "profile" in st.session_state
