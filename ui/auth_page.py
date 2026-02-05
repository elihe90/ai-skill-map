from __future__ import annotations

import uuid
from datetime import datetime, timezone

import streamlit as st

from core.admin_store import get_user_record, load_users, upsert_user_record

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

    st.session_state.setdefault("auth_mode", "register")
    st.session_state.setdefault("registered", isinstance(st.session_state.get("user"), dict))
    st.session_state.setdefault("logged_in", False)

    if st.session_state.get("registered") and not st.session_state.get("logged_in"):
        if st.session_state.get("auth_mode") == "register":
            st.session_state["auth_mode"] = "login"

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
            mode = st.session_state.get("auth_mode", "register")
            if mode == "login":
                st.markdown(
                    "<div class='auth-form-title'>\u0648\u0631\u0648\u062f</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    "<div class='auth-form-subtitle'>\u0627\u0637\u0644\u0627\u0639\u0627\u062a \u062e\u0648\u062f \u0631\u0627 \u0648\u0627\u0631\u062f \u06a9\u0646\u06cc\u062f \u062a\u0627 \u0627\u062f\u0627\u0645\u0647 \u062f\u0647\u06cc\u062f.</div>",
                    unsafe_allow_html=True,
                )
                name = st.text_input("\u0646\u0627\u0645 \u0648 \u0646\u0627\u0645\u200c\u062e\u0627\u0646\u0648\u0627\u062f\u06af\u06cc *", key="login_name")
                contact = st.text_input("\u062a\u0644\u0641\u0646 \u06cc\u0627 \u0627\u06cc\u0645\u06cc\u0644 (\u0627\u062e\u062a\u06cc\u0627\u0631\u06cc)", key="login_contact")
                submitted = st.button("\u0648\u0631\u0648\u062f", type="primary", key="login_submit")
                if st.button("\u062b\u0628\u062a\u200c\u0646\u0627\u0645 \u062c\u062f\u06cc\u062f", key="go_register"):
                    st.session_state["auth_mode"] = "register"
                    if hasattr(st, "rerun"):
                        st.rerun()
                    else:
                        st.experimental_rerun()
            else:
                st.markdown(
                    "<div class='auth-form-title'>\u062b\u0628\u062a\u200c\u0646\u0627\u0645 \u0633\u0631\u06cc\u0639</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(
                    "<div class='auth-form-subtitle'>\u0628\u0631\u0627\u06cc \u0634\u0631\u0648\u0639 \u0645\u0633\u06cc\u0631\u060c \u0627\u0637\u0644\u0627\u0639\u0627\u062a \u0632\u06cc\u0631 \u0631\u0627 \u0648\u0627\u0631\u062f \u06a9\u0646.</div>",
                    unsafe_allow_html=True,
                )
                name = st.text_input("\u0646\u0627\u0645 \u0648 \u0646\u0627\u0645\u200c\u062e\u0627\u0646\u0648\u0627\u062f\u06af\u06cc *", key="register_name")
                contact = st.text_input("\u062a\u0644\u0641\u0646 \u06cc\u0627 \u0627\u06cc\u0645\u06cc\u0644 (\u0627\u062e\u062a\u06cc\u0627\u0631\u06cc)", key="register_contact")
                submitted = st.button("\u062b\u0628\u062a \u0646\u0627\u0645", type="primary", key="register_submit")
                if st.button("\u0642\u0628\u0644\u0627 \u062b\u0628\u062a\u200c\u0646\u0627\u0645 \u06a9\u0631\u062f\u0647\u200c\u0627\u0645", key="go_login"):
                    st.session_state["auth_mode"] = "login"
                    if hasattr(st, "rerun"):
                        st.rerun()
                    else:
                        st.experimental_rerun()

    if submitted:
        if not name.strip():
            st.warning("\u0644\u0637\u0641\u0627 \u0646\u0627\u0645 \u062e\u0648\u062f \u0631\u0627 \u0648\u0627\u0631\u062f \u06a9\u0646\u06cc\u062f.")
            return False

        mode = st.session_state.get("auth_mode", "register")
        if mode == "login":
            stored_user = st.session_state.get("user", {})
            name_clean = name.strip()
            contact_clean = contact.strip()
            if not isinstance(stored_user, dict) or not stored_user.get("name"):
                stored_user = {}
            name_ok = stored_user.get("name", "").strip() == name_clean
            contact_ok = True
            if stored_user.get("contact"):
                contact_ok = stored_user.get("contact", "").strip() == contact_clean
            if not (name_ok and contact_ok):
                users = load_users()
                matched_id = None
                matched_user = None
                for user_id, record in users.items():
                    if not isinstance(record, dict):
                        continue
                    if record.get("name", "").strip() != name_clean:
                        continue
                    record_contact = (record.get("contact") or "").strip()
                    if record_contact and contact_clean and record_contact != contact_clean:
                        continue
                    matched_id = user_id
                    matched_user = record
                    break
                if not matched_user:
                    st.warning("\u0627\u0637\u0644\u0627\u0639\u0627\u062a \u0648\u0627\u0631\u062f \u0634\u062f\u0647 \u0635\u062d\u06cc\u062d \u0646\u06cc\u0633\u062a.")
                    return False
                st.session_state["user_id"] = matched_id
                st.session_state["user"] = {
                    "name": matched_user.get("name", "").strip(),
                    "contact": (matched_user.get("contact") or "").strip(),
                }
                matched_record = matched_user
            if "matched_record" not in locals():
                matched_record = stored_user if isinstance(stored_user, dict) else {}
            st.session_state["logged_in"] = True
            st.session_state["auth_completed"] = True
            user_id = st.session_state.get("user_id")
            if user_id:
                upsert_user_record(
                    str(user_id),
                    {
                        "current_step": "auth",
                        "auth_completed": True,
                        "last_login_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
                record = get_user_record(str(user_id))
                if isinstance(record, dict) and record:
                    matched_record = record
            if isinstance(matched_record, dict) and matched_record:
                profile = matched_record.get("profile")
                if isinstance(profile, dict):
                    st.session_state["profile"] = profile
                    st.session_state["profile_completed"] = True
                if matched_record.get("interview_result"):
                    st.session_state["interview_result"] = matched_record.get("interview_result")
                    st.session_state["interview_completed"] = True
                if matched_record.get("interview_answers"):
                    st.session_state["interview_v2_answers"] = matched_record.get("interview_answers")
                if matched_record.get("interview_scores"):
                    st.session_state["interview_scores"] = matched_record.get("interview_scores")
                if matched_record.get("gap"):
                    st.session_state["gap"] = matched_record.get("gap")
                if matched_record.get("skill_gaps"):
                    st.session_state["skill_gaps"] = matched_record.get("skill_gaps")
                if matched_record.get("job_mapping"):
                    st.session_state["job_mapping"] = matched_record.get("job_mapping")
                if matched_record.get("user_feedback"):
                    st.session_state["user_feedback"] = matched_record.get("user_feedback")
                if matched_record.get("course_recommendation"):
                    st.session_state["course_recommendation"] = matched_record.get("course_recommendation")
                if matched_record.get("interview_completed"):
                    st.session_state["interview_completed"] = True
                if matched_record.get("results_generated"):
                    st.session_state["current_step"] = "results"
                elif matched_record.get("interview_result"):
                    st.session_state["current_step"] = "results"
            return True

        user_id = st.session_state.get("user_id")
        if not user_id:
            user_id = str(uuid.uuid4())
            st.session_state["user_id"] = user_id
        st.session_state["user"] = {"name": name.strip(), "contact": contact.strip()}
        st.session_state["registered"] = True
        st.session_state["logged_in"] = False
        st.session_state["auth_completed"] = False
        st.session_state["auth_mode"] = "login"
        upsert_user_record(
            user_id,
            {
                "name": name.strip(),
                "has_contact": bool(contact.strip()),
                "contact": contact.strip(),
                "current_step": "auth",
                "auth_completed": False,
                "registered": True,
            },
        )
        st.success("\u062b\u0628\u062a\u200c\u0646\u0627\u0645 \u0627\u0646\u062c\u0627\u0645 \u0634\u062f. \u0644\u0637\u0641\u0627 \u0648\u0627\u0631\u062f \u0634\u0648\u06cc\u062f.")
        return False
    return False
