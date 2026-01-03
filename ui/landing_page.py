from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st


BASE_DIR = Path(__file__).resolve().parents[1]


def _asset_path(filename: str) -> str:
    return str(BASE_DIR / "images" / filename)


def _img_data_uri(filename: str) -> str:
    path = BASE_DIR / "images" / filename
    if not path.exists():
        return ""
    suffix = path.suffix.lower()
    mime = "image/png" if suffix == ".png" else "image/jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


LANDING_CSS = """
<style>
.lp-section {
    margin: 32px 0;
}
.lp-hero-title {
    font-size: 32px;
    font-weight: 700;
    margin-bottom: 12px;
    line-height: 1.6;
}
.lp-subtitle {
    font-size: 18px;
    color: #6B7280;
    line-height: 1.7;
}
.lp-trust {
    font-size: 18px;
    color: #6B7280;
    margin-top: 8px;
}
.lp-card-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
    gap: 16px;
}
.lp-card {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}
.lp-card h4 {
    margin: 8px 0 6px 0;
    font-size: 18px;
}
.lp-card p {
    margin: 0;
    font-size: 18px;
    color: #6B7280;
    line-height: 1.7;
}
.lp-card-icon {
    width: 56px;
    height: 56px;
    border-radius: 999px;
    background: #DBEAFE;
    display: flex;
    align-items: center;
    justify-content: center;
}
.lp-benefit-icon,
.lp-pain-icon {
    width: 36px;
    height: 36px;
    border-radius: 999px;
    background: #DBEAFE;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
}
.lp-card-icon img {
    width: 56px;
    height: 56px;
    object-fit: contain;
    display: block;
}
.lp-steps {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
}
.lp-step {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 16px 20px;
    text-align: center;
    font-size: 18px;
}
.lp-step span {
    font-size: 22px;
    display: block;
    margin-bottom: 8px;
}
.lp-mock {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 16px;
    padding: 24px;
    min-height: 240px;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
}
.lp-mock .lp-mock-row {
    height: 14px;
    background: #F3F4F6;
    border-radius: 999px;
    margin-bottom: 12px;
}
.lp-mock .lp-mock-card {
    height: 64px;
    background: #DBEAFE;
    border-radius: 12px;
    margin-top: 16px;
}
.lp-output {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 16px;
}
.lp-output-item {
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 12px;
    padding: 16px 20px;
}
.lp-output-item ul {
    padding-right: 18px;
    margin: 8px 0 0 0;
    color: #6B7280;
    font-size: 18px;
    line-height: 1.7;
}
.lp-output-item strong {
    font-size: 18px;
}
.lp-cta-anchor {
    display: none;
}
div[data-testid="stVerticalBlock"]:has(> .lp-cta-anchor) {
    text-align: center;
}
div[data-testid="stVerticalBlock"]:has(> .lp-cta-anchor) .stButton > button {
    background: #2563EB;
    color: #FFFFFF;
    border: none;
    border-radius: 999px;
    padding: 10px 22px;
    font-size: 15px;
}
div[data-testid="stVerticalBlock"]:has(> .lp-cta-anchor) .stButton > button:hover {
    background: #1D4ED8;
    color: #FFFFFF;
}
@media (max-width: 900px) {
    .lp-hero-title { font-size: 26px; }
    .lp-subtitle { font-size: 16px; }
    .lp-trust { font-size: 16px; }
    .lp-card h4 { font-size: 16px; }
    .lp-card p { font-size: 16px; }
    .lp-step { font-size: 16px; }
    .lp-output-item ul { font-size: 16px; }
    .lp-output-item strong { font-size: 16px; }
    .lp-card-grid,
    .lp-steps,
    .lp-output {
        grid-template-columns: 1fr;
    }
    .lp-card {
        padding: 14px 16px;
    }
}
</style>
"""


def _cta_button(key: str) -> None:
    with st.container():
        st.markdown("<div class='lp-cta-anchor'></div>", unsafe_allow_html=True)
        if st.button("\u0634\u0631\u0648\u0639 \u0631\u0627\u06cc\u06af\u0627\u0646", key=key):
            st.session_state["page"] = "register"
            if "current_step" in st.session_state:
                st.session_state["current_step"] = "auth"
            if "auth_completed" in st.session_state:
                st.session_state["auth_completed"] = False
            if hasattr(st, "rerun"):
                st.rerun()
            else:
                st.experimental_rerun()


def render_landing_page() -> None:
    st.markdown(LANDING_CSS, unsafe_allow_html=True)

    top_left, top_right = st.columns([0.88, 0.12])
    with top_right:
        st.image(_asset_path("عیارمهارت.jpg"), width=90)

    col_left, col_right = st.columns([1.2, 1])
    with col_left:
        st.markdown(
            "<div class='lp-hero-title'>\u0645\u0633\u06cc\u0631 \u0634\u063a\u0644\u06cc \u0647\u0648\u0634 \u0645\u0635\u0646\u0648\u0639\u06cc \u0631\u0627 \u0634\u0641\u0627\u0641 \u0648 \u0633\u0631\u06cc\u0639 \u0628\u0633\u0627\u0632</div>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<div class='lp-subtitle'>\u0627\u06af\u0631 \u0646\u0645\u06cc\u200c\u062f\u0627\u0646\u06cc \u0627\u0632 \u06a9\u062c\u0627 \u0634\u0631\u0648\u0639 \u06a9\u0646\u06cc\u060c \u0639\u06cc\u0627\u0631 \u0645\u0647\u0627\u0631\u062a\u06cc \u0628\u0627 \u0686\u0646\u062f \u0633\u0648\u0627\u0644 \u06a9\u0648\u062a\u0627\u0647\u060c \u06af\u067e\u200c\u0647\u0627\u060c \u062f\u0648\u0631\u0647\u200c\u0647\u0627 \u0648 \u0634\u063a\u0644\u200c\u0647\u0627\u06cc \u0642\u0627\u0628\u0644 \u062f\u0633\u062a\u0631\u0633 \u0631\u0627 \u0628\u0631\u0627\u06cc\u062a \u0631\u0648\u0634\u0646 \u0645\u06cc\u200c\u06a9\u0646\u062f.</div>",
            unsafe_allow_html=True,
        )
        _cta_button("lp_hero_cta")
        st.markdown(
            "<div class='lp-trust'>\u0628\u0631 \u067e\u0627\u06cc\u0647 \u0627\u0633\u062a\u0627\u0646\u062f\u0627\u0631\u062f\u0647\u0627\u06cc \u0645\u0647\u0627\u0631\u062a\u06cc \u0645\u0644\u06cc \u0648 \u062a\u062c\u0631\u0628\u0647 \u0645\u0631\u0628\u06cc\u0627\u0646 \u0628\u0627\u0632\u0627\u0631</div>",
            unsafe_allow_html=True,
        )

    with col_right:
        st.markdown(
            """
            <div class="lp-mock">
                <div class="lp-mock-row" style="width: 70%;"></div>
                <div class="lp-mock-row" style="width: 55%;"></div>
                <div class="lp-mock-row" style="width: 80%;"></div>
                <div class="lp-mock-card"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    confusion_img = _img_data_uri("سردرگمی مسیر.png")
    cost_img = _img_data_uri("هزینه‌های اشتباه.png")
    market_img = _img_data_uri("فاصله تا بازار.png")

    st.markdown(
        f"""
        <div class="lp-section">
            <div class="lp-card-grid">
                <div class="lp-card">
                    <div class="lp-card-icon"><img src="{confusion_img}" alt="سردرگمی مسیر"></div>
                    <h4>\u0633\u0631\u062f\u0631\u06af\u0645\u06cc \u0645\u0633\u06cc\u0631</h4>
                    <p>\u0627\u0632 \u0645\u06cc\u0627\u0646 \u062f\u0647\u200c\u0647\u0627 \u0645\u0633\u06cc\u0631\u060c \u06a9\u062f\u0627\u0645 \u0628\u0631\u0627\u06cc \u062a\u0648 \u0645\u0646\u0627\u0633\u0628 \u0627\u0633\u062a\u061f</p>
                </div>
                <div class="lp-card">
                    <div class="lp-card-icon"><img src="{cost_img}" alt="هزینه‌های اشتباه"></div>
                    <h4>\u0647\u0632\u06cc\u0646\u0647\u200c\u0647\u0627\u06cc \u0627\u0634\u062a\u0628\u0627\u0647</h4>
                    <p>\u062f\u0648\u0631\u0647\u200c\u0647\u0627\u06cc \u063a\u06cc\u0631\u0645\u0631\u062a\u0628\u0637 \u0648 \u0628\u06cc\u200c\u0628\u0627\u0632\u062f\u0647 \u0648\u0642\u062a \u0648 \u067e\u0648\u0644 \u0631\u0627 \u0647\u062f\u0631 \u0645\u06cc\u200c\u062f\u0647\u062f.</p>
                </div>
                <div class="lp-card">
                    <div class="lp-card-icon"><img src="{market_img}" alt="فاصله تا بازار"></div>
                    <h4>\u0641\u0627\u0635\u0644\u0647 \u062a\u0627 \u0628\u0627\u0632\u0627\u0631</h4>
                    <p>\u06cc\u0627\u062f\u06af\u06cc\u0631\u06cc \u0628\u0627\u06cc\u062f \u0628\u0647 \u0634\u063a\u0644 \u0628\u0631\u0633\u062f\u060c \u0646\u0647 \u0641\u0642\u0637 \u0628\u0647 \u062f\u0627\u0646\u0634.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="lp-section">
            <h2>\u0686\u0631\u0627 \u0639\u06cc\u0627\u0631 \u0645\u0647\u0627\u0631\u062a\u06cc\u061f</h2>
            <div class="lp-card-grid">
                <div class="lp-card">
                    <div class="lp-benefit-icon">\U0001F9E9</div>
                    <h4>\u0646\u0642\u0634\u0647 \u0631\u0627\u0647 \u0634\u062e\u0635\u06cc</h4>
                    <p>\u0645\u0633\u06cc\u0631 \u06cc\u0627\u062f\u06af\u06cc\u0631\u06cc \u0645\u062a\u0646\u0627\u0633\u0628 \u0628\u0627 \u0632\u0645\u0627\u0646 \u0648 \u0647\u062f\u0641 \u062a\u0648.</p>
                </div>
                <div class="lp-card">
                    <div class="lp-benefit-icon">\U0001F4CA</div>
                    <h4>\u06af\u067e\u200c\u0647\u0627\u06cc \u0648\u0627\u0642\u0639\u06cc</h4>
                    <p>\u0648\u0627\u0642\u0639\u06cc \u0648 \u0642\u0627\u0628\u0644 \u0627\u0642\u062f\u0627\u0645\u061b \u0646\u0647 \u0627\u0628\u0647\u0627\u0645\u06cc \u0648 \u062a\u0648\u0647\u0645.</p>
                </div>
                <div class="lp-card">
                    <div class="lp-benefit-icon">\U0001F9ED</div>
                    <h4>\u062f\u0648\u0631\u0647\u200c\u0647\u0627\u06cc \u062f\u0642\u06cc\u0642</h4>
                    <p>\u0641\u0642\u0637 \u062f\u0648\u0631\u0647\u200c\u0647\u0627\u06cc\u06cc \u06a9\u0647 \u0628\u0647 \u0634\u063a\u0644 \u0646\u0632\u062f\u06cc\u06a9 \u0645\u06cc\u200c\u06a9\u0646\u0646\u062f.</p>
                </div>
                <div class="lp-card">
                    <div class="lp-benefit-icon">\U0001F9E0</div>
                    <h4>\u0645\u0633\u06cc\u0631 \u0634\u063a\u0644\u06cc \u0642\u0627\u0628\u0644 \u062f\u0633\u062a\u0631\u0633</h4>
                    <p>\u0645\u06cc\u200c\u062f\u0627\u0646\u06cc \u0628\u0647 \u06a9\u062f\u0627\u0645 \u0646\u0642\u0634 \u0645\u06cc\u200c\u062a\u0648\u0627\u0646\u06cc \u0628\u0631\u0633\u06cc.</p>
                </div>
                <div class="lp-card">
                    <div class="lp-benefit-icon">\u23F1\ufe0f</div>
                    <h4>\u0628\u0631\u0646\u0627\u0645\u0647 \u06f7 \u0648 \u06f1\u06f4 \u0631\u0648\u0632\u0647</h4>
                    <p>\u0627\u0642\u062f\u0627\u0645\u200c\u0647\u0627\u06cc \u0627\u0633\u062a\u0627\u062f\u0627\u0646\u0647 \u0648 \u0642\u0627\u0628\u0644 \u0627\u0646\u062c\u0627\u0645 \u0628\u0631\u0627\u06cc \u0634\u0631\u0648\u0639.</p>
                </div>
                <div class="lp-card">
                    <div class="lp-benefit-icon">\U0001F465</div>
                    <h4>\u0645\u0646\u0627\u0633\u0628 \u0628\u0631\u0627\u06cc \u0645\u0628\u062a\u062f\u06cc \u062a\u0627 \u062d\u0631\u0641\u0647\u200c\u0627\u06cc</h4>
                    <p>\u0647\u0645 \u0628\u0631\u0627\u06cc \u0634\u0631\u0648\u0639 \u06a9\u0646\u0646\u062f\u0647\u200c\u0647\u0627 \u0648 \u0647\u0645 \u0628\u0631\u0627\u06cc \u0627\u0631\u062a\u0642\u0627\u06cc \u0645\u0647\u0627\u0631\u062a.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="lp-section">
            <div class="lp-steps">
                <div class="lp-step"><span>1</span>\u067e\u0627\u0633\u062e \u0628\u0647 \u0686\u0646\u062f \u0633\u0648\u0627\u0644 \u06a9\u0648\u062a\u0627\u0647</div>
                <div class="lp-step"><span>2</span>\u062a\u062d\u0644\u06cc\u0644 \u06af\u067e\u200c\u0647\u0627\u06cc \u0645\u0647\u0627\u0631\u062a\u06cc</div>
                <div class="lp-step"><span>3</span>\u0645\u0633\u06cc\u0631 \u0622\u0645\u0648\u0632\u0634 + \u0634\u063a\u0644 \u0642\u0627\u0628\u0644 \u062f\u0633\u062a\u0631\u0633</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="lp-section">
            <div class="lp-output">
                <div class="lp-output-item">
                    <strong>\u06af\u067e\u200c\u0647\u0627\u06cc \u0645\u0647\u0627\u0631\u062a\u06cc</strong>
                    <ul>
                        <li>\u062f\u0631\u06a9 \u0648\u0627\u0642\u0639\u06cc \u0645\u0633\u06cc\u0631</li>
                        <li>\u0645\u0631\u062d\u0644\u0647\u200c\u0628\u0646\u062f\u06cc \u0627\u0642\u062f\u0627\u0645\u200c\u0647\u0627</li>
                    </ul>
                </div>
                <div class="lp-output-item">
                    <strong>\u062f\u0648\u0631\u0647\u200c\u0647\u0627\u06cc \u067e\u06cc\u0634\u0646\u0647\u0627\u062f\u06cc</strong>
                    <ul>
                        <li>\u06a9\u062f \u062f\u0648\u0631\u0647 \u0648 \u0639\u0646\u0648\u0627\u0646</li>
                        <li>\u0627\u0648\u0644\u0648\u06cc\u062a \u0648 \u062f\u0644\u06cc\u0644 \u0627\u0646\u062a\u062e\u0627\u0628</li>
                    </ul>
                </div>
                <div class="lp-output-item">
                    <strong>\u0634\u063a\u0644\u200c\u0647\u0627\u06cc \u0642\u0627\u0628\u0644 \u062f\u0633\u062a\u0631\u0633</strong>
                    <ul>
                        <li>\u0634\u063a\u0644 \u0647\u062f\u0641 \u0648 \u0645\u0633\u06cc\u0631 \u0628\u0639\u062f\u06cc</li>
                        <li>\u0645\u0634\u0627\u063a\u0644 \u0645\u0631\u062a\u0628\u0637</li>
                    </ul>
                </div>
                <div class="lp-output-item">
                    <strong>\u0628\u0631\u0646\u0627\u0645\u0647 \u0627\u0642\u062f\u0627\u0645</strong>
                    <ul>
                        <li>\u0628\u0631\u0646\u0627\u0645\u0647 \u06f7 \u0631\u0648\u0632\u0647</li>
                        <li>\u0628\u0631\u0646\u0627\u0645\u0647 \u06f1\u06f4 \u0631\u0648\u0632\u0647</li>
                    </ul>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div class='lp-section'><div class='lp-card'><strong>\u0645\u0639\u062a\u0628\u0631 \u0648 \u0627\u062a\u06a9\u0627\u067e\u0630\u06cc\u0631</strong><p>\u0628\u0631 \u067e\u0627\u06cc\u0647 \u0627\u0633\u062a\u0627\u0646\u062f\u0627\u0631\u062f\u0647\u0627\u06cc \u0645\u0647\u0627\u0631\u062a\u06cc \u0645\u0644\u06cc \u0648 \u0637\u0631\u0627\u062d\u06cc \u0634\u062f\u0647 \u062a\u0648\u0633\u0637 \u0645\u0631\u0628\u06cc \u0647\u0648\u0634 \u0645\u0635\u0646\u0648\u0639\u06cc.</p></div></div>",
        unsafe_allow_html=True,
    )

    _cta_button("lp_final_cta")
