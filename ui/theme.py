from __future__ import annotations

from contextlib import contextmanager

import streamlit as st


THEME_CSS = """
<style>
.stApp {
    direction: rtl;
    font-family: "Vazirmatn", "Segoe UI", Tahoma, sans-serif;
    background-color: #F9FAFB;
    color: #111827;
}
.block-container {
    padding-top: 16px;
    padding-bottom: 24px;
    padding-left: 16px;
    padding-right: 16px;
}
h1, h2, h3, p, li {
    line-height: 1.7;
}
h1 { font-size: 24px; }
h2 { font-size: 18px; }
h3 { font-size: 16px; }
.sm-topbar-anchor,
.sm-card-anchor,
.sm-steps-anchor,
.sm-sticky-anchor {
    display: none;
}
div[data-testid="stVerticalBlock"]:has(> .sm-topbar-anchor) {
    position: sticky;
    top: 0;
    z-index: 1000;
    background: #F9FAFB;
    border-bottom: 1px solid #E5E7EB;
    padding: 12px 0 12px 0;
    margin-bottom: 12px;
    min-height: 72px;
}
div[data-testid="stVerticalBlock"]:has(> .sm-card-anchor) {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 16px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}
div[data-testid="stVerticalBlock"]:has(> .sm-steps-anchor) {
    position: sticky;
    top: 88px;
    background: #F9FAFB;
    max-width: 260px;
}
div[data-testid="stVerticalBlock"]:has(> .sm-steps-anchor) button {
    background: transparent;
    border: none;
    color: #2563EB;
    padding: 2px 4px;
    font-size: 12px;
    text-align: right;
}
div[data-testid="stVerticalBlock"]:has(> .sm-steps-anchor) button:hover {
    text-decoration: underline;
}
div[data-testid="stVerticalBlock"]:has(> .sm-sticky-anchor) {
    position: sticky;
    top: 0;
    z-index: 900;
    background: #F9FAFB;
    padding: 8px 0 12px 0;
    border-bottom: 1px solid #E5E7EB;
    margin-bottom: 16px;
}
.sm-wrap {
    direction: rtl;
}
.sm-h1 {
    font-size: 24px;
    font-weight: 600;
    margin-bottom: 8px;
}
.sm-title {
    font-size: 18px;
    font-weight: 600;
    margin: 0 0 4px 0;
}
.sm-subtitle {
    font-size: 13px;
    color: #6B7280;
    margin: 0;
}
.sm-stage {
    font-size: 12px;
    color: #2563EB;
    background: #DBEAFE;
    border: 1px solid #BFDBFE;
    border-radius: 999px;
    padding: 4px 10px;
    display: inline-block;
}
.sm-body {
    font-size: 14px;
    line-height: 1.7;
}
.sm-steps-title {
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
}
.sm-step {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 8px 10px;
    border: 1px solid #E5E7EB;
    border-radius: 10px;
    margin-bottom: 8px;
    background: #FFFFFF;
}
.sm-step.current {
    background: #DBEAFE;
    border-color: #BFDBFE;
}
.sm-step.locked {
    opacity: 0.6;
}
.sm-step-label {
    font-size: 13px;
    color: #111827;
    display: flex;
    align-items: center;
    gap: 6px;
}
.sm-step-status {
    font-size: 11px;
    color: #6B7280;
}
.sm-card-title {
    font-size: 16px;
    font-weight: 500;
    margin-bottom: 6px;
}
.sm-section-title {
    font-size: 18px;
    font-weight: 500;
    margin-bottom: 12px;
}
.sm-section {
    margin-top: 32px;
}
.sm-badge {
    display: inline-flex;
    align-items: center;
    padding: 4px 10px;
    border-radius: 999px;
    font-size: 12px;
    margin: 0 0 6px 6px;
    border: 1px solid transparent;
}
.sm-badge-primary { background: #DBEAFE; color: #1D4ED8; border-color: #BFDBFE; }
.sm-badge-success { background: #DCFCE7; color: #166534; border-color: #BBF7D0; }
.sm-badge-warning { background: #FEF3C7; color: #92400E; border-color: #FDE68A; }
</style>
"""


def apply_theme() -> None:
    st.markdown(THEME_CSS, unsafe_allow_html=True)


@contextmanager
def card_container():
    with st.container():
        st.markdown("<div class='sm-card-anchor'></div>", unsafe_allow_html=True)
        yield


def render_top_bar(stage_label: str, collapsed: bool) -> None:
    with st.container():
        st.markdown("<div class='sm-topbar-anchor'></div>", unsafe_allow_html=True)
        col_left, col_mid, col_right = st.columns([6, 2, 1])
        with col_left:
            st.markdown(
                "<div class='sm-title'>AI Skill Map | \u0639\u06cc\u0627\u0631 \u0645\u0647\u0627\u0631\u062a\u06cc</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div class='sm-subtitle'>\u0645\u0633\u06cc\u0631 \u06cc\u0627\u062f\u06af\u06cc\u0631\u06cc \u0648 \u0645\u0647\u0627\u0631\u062a\u200c\u0647\u0627\u06cc \u06a9\u0644\u06cc\u062f\u06cc \u0628\u0631\u0627\u06cc \u0646\u0642\u0634\u200c\u0647\u0627\u06cc AI</div>",
                unsafe_allow_html=True,
            )
        with col_mid:
            st.markdown(
                f"<div class='sm-stage'>\u0645\u0631\u062d\u0644\u0647: {stage_label}</div>",
                unsafe_allow_html=True,
            )
        with col_right:
            label = "\u00ab" if not collapsed else "\u00bb"
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            st.button(label, key="toggle_steps")
