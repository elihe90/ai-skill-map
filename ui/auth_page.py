from __future__ import annotations

import uuid

import streamlit as st

from core.admin_store import upsert_user_record

AUTH_CSS = """
<style>
.auth-hero-anchor,
.auth-form-anchor {
    display: none;
}
div[data-testid="stVerticalBlock"]:has(> .auth-hero-anchor) {
    position: relative;
    overflow: hidden;
    background: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 18px;
    padding: 28px;
    min-height: 420px;
}
div[data-testid="stVerticalBlock"]:has(> .auth-hero-anchor)::before {
    content: "";
    position: absolute;
    inset: 0;
    background:
        radial-gradient(circle at 20% 20%, rgba(37, 99, 235, 0.08), transparent 45%),
        radial-gradient(circle at 80% 10%, rgba(37, 99, 235, 0.06), transparent 40%),
        radial-gradient(circle at 30% 80%, rgba(17, 24, 39, 0.06), transparent 40%);
    opacity: 0.9;
}
.auth-hero-content {
    position: relative;
    z-index: 1;
}
.auth-hero-title {
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 8px;
}
.auth-hero-subtitle {
    font-size: 14px;
    color: #6B7280;
    line-height: 1.7;
    max-width: 320px;
}
.auth-hero-mark {
    margin-top: 36px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.auth-hero-badge {
    width: 68px;
    height: 68px;
    border-radius: 16px;
    background: #DBEAFE;
    border: 1px solid #BFDBFE;
}
.auth-hero-brand {
    font-size: 26px;
    font-weight: 800;
}
.auth-hero-tagline {
    font-size: 12px;
    color: #6B7280;
}
div[data-testid="stVerticalBlock"]:has(> .auth-form-anchor) {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 18px;
    padding: 24px 26px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}
.auth-form-title {
    font-size: 20px;
    font-weight: 600;
    margin-bottom: 8px;
}
.auth-form-subtitle {
    font-size: 13px;
    color: #6B7280;
    margin-bottom: 18px;
}
div[data-testid="stVerticalBlock"]:has(> .auth-form-anchor) [data-testid="stTextInput"] label {
    font-size: 12px;
    color: #374151;
}
div[data-testid="stVerticalBlock"]:has(> .auth-form-anchor) [data-testid="stTextInput"] input {
    border-radius: 10px;
    border: 1px solid #E5E7EB;
    padding: 10px 12px;
}
div[data-testid="stVerticalBlock"]:has(> .auth-form-anchor) .stButton > button {
    width: 100%;
    border-radius: 12px;
    background: #2563EB;
    color: #FFFFFF;
    border: none;
    padding: 10px 12px;
    font-size: 14px;
}
div[data-testid="stVerticalBlock"]:has(> .auth-form-anchor) .stButton > button:hover {
    background: #1D4ED8;
    color: #FFFFFF;
}
.auth-form-link {
    margin-top: 10px;
    font-size: 12px;
    color: #2563EB;
    text-align: center;
}
@media (max-width: 900px) {
    div[data-testid="stVerticalBlock"]:has(> .auth-hero-anchor) {
        min-height: 280px;
    }
}
</style>
"""


def render_auth_page() -> bool:
    """Render a styled auth/register form and store user in session_state."""
    st.markdown(AUTH_CSS, unsafe_allow_html=True)

    col_left, col_right = st.columns([1.1, 0.9], gap="large")
    with col_left:
        with st.container():
            st.markdown("<div class='auth-hero-anchor'></div>", unsafe_allow_html=True)
            st.markdown(
                """
                <div class="auth-hero-content">
                    <div class="auth-hero-title">\u0628\u0647 \u0639\u06cc\u0627\u0631 \u0645\u0647\u0627\u0631\u062a\u06cc \u062e\u0648\u0634 \u0622\u0645\u062f\u06cc\u062f</div>
                    <div class="auth-hero-subtitle">\u06cc\u06a9 \u0631\u0627\u0647 \u0633\u0627\u062f\u0647 \u0628\u0631\u0627\u06cc \u0634\u0631\u0648\u0639 \u0645\u0633\u06cc\u0631 \u0634\u063a\u0644\u06cc \u062f\u0631 \u0647\u0648\u0634 \u0645\u0635\u0646\u0648\u0639\u06cc.</div>
                    <div class="auth-hero-mark">
                        <div class="auth-hero-badge"></div>
                        <div>
                            <div class="auth-hero-brand">AI Skill Map</div>
                            <div class="auth-hero-tagline">\u0639\u06cc\u0627\u0631 \u0645\u0647\u0627\u0631\u062a\u06cc \u0628\u0631\u0627\u06cc \u0646\u0642\u0634\u200c\u0647\u0627\u06cc AI</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with col_right:
        with st.container():
            st.markdown("<div class='auth-form-anchor'></div>", unsafe_allow_html=True)
            st.markdown(
                "<div class='auth-form-title'>\u062b\u0628\u062a\u200c\u0646\u0627\u0645 \u0633\u0631\u06cc\u0639</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                "<div class='auth-form-subtitle'>\u0628\u0631\u0627\u06cc \u0634\u0631\u0648\u0639 \u0645\u0633\u06cc\u0631\u060c \u0627\u0637\u0644\u0627\u0639\u0627\u062a \u0632\u06cc\u0631 \u0631\u0627 \u0648\u0627\u0631\u062f \u06a9\u0646.</div>",
                unsafe_allow_html=True,
            )
            name = st.text_input("\u0646\u0627\u0645 \u0648 \u0646\u0627\u0645\u200c\u062e\u0627\u0646\u0648\u0627\u062f\u06af\u06cc *")
            contact = st.text_input("\u062a\u0644\u0641\u0646 \u06cc\u0627 \u0627\u06cc\u0645\u06cc\u0644 (\u0627\u062e\u062a\u06cc\u0627\u0631\u06cc)")
            submitted = st.button("\u062b\u0628\u062a \u0646\u0627\u0645", type="primary")
            st.markdown(
                "<div class='auth-form-link'>\u0642\u0628\u0644\u0627 \u062b\u0628\u062a\u200c\u0646\u0627\u0645 \u06a9\u0631\u062f\u0647\u200c\u0627\u0645</div>",
                unsafe_allow_html=True,
            )

    if submitted:
        if not name.strip():
            st.warning("\u0644\u0637\u0641\u0627 \u0646\u0627\u0645 \u062e\u0648\u062f \u0631\u0627 \u0648\u0627\u0631\u062f \u06a9\u0646\u06cc\u062f.")
            return False
        user_id = st.session_state.get("user_id")
        if not user_id:
            user_id = str(uuid.uuid4())
            st.session_state["user_id"] = user_id
        st.session_state["user"] = {"name": name.strip(), "contact": contact.strip()}
        upsert_user_record(
            user_id,
            {
                "name": name.strip(),
                "has_contact": bool(contact.strip()),
                "current_step": "auth",
                "auth_completed": True,
            },
        )
        return True
    return False
