from __future__ import annotations

from contextlib import contextmanager
from typing import Optional

import streamlit as st


THEME_CSS = """
<style>
:root {
    --sm-primary: #2563EB;
    --sm-primary-soft: #DBEAFE;
    --sm-success: #16A34A;
    --sm-warning: #F59E0B;
    --sm-danger: #EF4444;
    --sm-bg: #F9FAFB;
    --sm-card: #FFFFFF;
    --sm-border: #E5E7EB;
    --sm-text: #111827;
    --sm-muted: #6B7280;
}
.stApp {
    direction: rtl;
    background: var(--sm-bg);
    color: var(--sm-text);
    font-family: "Vazirmatn", "Segoe UI", Tahoma, sans-serif;
}
.block-container {
    max-width: 1100px;
    margin: 0 auto;
    padding: 12px 20px 28px 20px;
}
h1 {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 8px;
}
h2 {
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 6px;
}
p, li, div, span {
    font-size: 16px;
    line-height: 1.7;
}
.sm-small {
    font-size: 14px;
    color: var(--sm-muted);
}
.sm-card-anchor,
.sm-badge-anchor,
.sm-topbar-anchor,
.sm-nav-anchor {
    display: none;
}
div[data-testid="stVerticalBlock"]:has(> .sm-card-anchor) {
    background: var(--sm-card);
    border: 1px solid var(--sm-border);
    border-radius: 14px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}
div[data-testid="stVerticalBlock"]:has(> .sm-topbar-anchor) {
    background: var(--sm-card);
    border: 1px solid var(--sm-border);
    border-radius: 14px;
    padding: 12px 16px;
    margin-bottom: 16px;
}
div[data-testid="stVerticalBlock"]:has(> .sm-nav-anchor) {
    background: var(--sm-card);
    border: 1px solid var(--sm-border);
    border-radius: 14px;
    padding: 12px 14px;
    max-width: 260px;
}
.sm-nav-title {
    font-size: 13px;
    font-weight: 600;
    margin-bottom: 8px;
}
.sm-step {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 8px 10px;
    border: 1px solid var(--sm-border);
    border-radius: 10px;
    margin-bottom: 8px;
    background: #FFFFFF;
    font-size: 12px;
}
.sm-step.current {
    background: var(--sm-primary-soft);
    border-color: #BFDBFE;
}
.sm-step.locked {
    opacity: 0.6;
}
.sm-step-label {
    display: flex;
    align-items: center;
    gap: 6px;
    color: var(--sm-text);
}
.sm-step-status {
    font-size: 11px;
    color: var(--sm-muted);
}
div[data-testid="stVerticalBlock"]:has(> .sm-badge-anchor) {
    display: inline-block;
    border-radius: 999px;
    padding: 4px 10px;
    margin: 0 6px 6px 0;
    border: 1px solid transparent;
}
div[data-testid="stVerticalBlock"]:has(> .sm-badge-primary) {
    background: var(--sm-primary-soft);
    color: #1D4ED8;
    border-color: #BFDBFE;
}
div[data-testid="stVerticalBlock"]:has(> .sm-badge-success) {
    background: #DCFCE7;
    color: #166534;
    border-color: #BBF7D0;
}
div[data-testid="stVerticalBlock"]:has(> .sm-badge-warn) {
    background: #FEF3C7;
    color: #92400E;
    border-color: #FDE68A;
}
div[data-testid="stVerticalBlock"]:has(> .sm-badge-muted) {
    background: #F3F4F6;
    color: var(--sm-muted);
    border-color: #E5E7EB;
}
button[data-testid="baseButton-primary"] {
    background: var(--sm-primary);
    color: #FFFFFF;
    border: none;
    border-radius: 10px;
    padding: 8px 14px;
}
button[data-testid="baseButton-primary"]:hover {
    background: #1D4ED8;
    color: #FFFFFF;
}
.stButton > button {
    border-radius: 10px;
}
header[data-testid="stHeader"] {
    display: none !important;
}
#MainMenu {
    visibility: hidden !important;
}
footer {
    visibility: hidden !important;
}
section[data-testid="stSidebar"] {
    display: none !important;
    width: 0 !important;
}
div[data-testid="stSidebarNav"] {
    display: none !important;
}
div[data-testid="stSidebarNavItems"] {
    display: none !important;
}
div[data-testid="stSidebarUserContent"] {
    display: none !important;
}
button[data-testid="collapsedControl"] {
    display: none !important;
}
@media (max-width: 900px) {
    .block-container {
        padding: 10px 12px 20px 12px;
    }
    h1 {
        font-size: 26px;
    }
    h2 {
        font-size: 20px;
    }
    p, li, div, span {
        font-size: 15px;
    }
    div[data-testid="stVerticalBlock"]:has(> .sm-nav-anchor) {
        display: none;
    }
    .sm-step {
        font-size: 11px;
    }
}
</style>
"""


def safe_text(value: Optional[str]) -> str:
    if value is None:
        return ""
    return str(value).encode("utf-8", "ignore").decode("utf-8")


def apply_global_theme() -> None:
    st.set_page_config(page_title="AI Skill Map", layout="wide", initial_sidebar_state="collapsed")
    st.markdown(THEME_CSS, unsafe_allow_html=True)


@contextmanager
def card_container():
    with st.container():
        st.markdown("<div class='sm-card-anchor'></div>", unsafe_allow_html=True)
        yield


def render_top_bar(stage_label: str = "", show_reset: bool = True) -> bool:
    reset_clicked = False
    with st.container():
        st.markdown("<div class='sm-topbar-anchor'></div>", unsafe_allow_html=True)
        col_left, col_mid, col_right = st.columns([3, 2, 1])
        with col_left:
            st.write("\u0639\u06cc\u0627\u0631 \u0645\u0647\u0627\u0631\u062a\u06cc | AI Skill Map")
            st.caption("\u0645\u0633\u06cc\u0631 \u06cc\u0627\u062f\u06af\u06cc\u0631\u06cc \u0648 \u0645\u0647\u0627\u0631\u062a\u200c\u0647\u0627\u06cc \u06a9\u0644\u06cc\u062f\u06cc \u0628\u0631\u0627\u06cc \u0646\u0642\u0634\u200c\u0647\u0627\u06cc AI")
        with col_mid:
            if stage_label:
                st.caption(f"\u0645\u0631\u062d\u0644\u0647: {safe_text(stage_label)}")
        with col_right:
            if show_reset:
                reset_clicked = st.button(safe_text("\u0634\u0631\u0648\u0639 \u0627\u0632 \u0627\u0628\u062a\u062f\u0627"))
    return reset_clicked
