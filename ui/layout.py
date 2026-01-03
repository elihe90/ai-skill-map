import streamlit as st


def render_header() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            direction: rtl;
            font-family: "Vazirmatn", "Noto Naskh Arabic", Tahoma, sans-serif;
            background: #f8fafc;
        }
        .skill-card {
            border: 1px solid #e5e7eb;
            padding: 16px;
            border-radius: 12px;
            background: #ffffff;
            box-shadow: 0 1px 2px rgba(15, 23, 42, 0.08);
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
            gap: 16px;
        }
        .muted {
            color: #64748b;
            font-size: 0.9rem;
            margin-bottom: 6px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.title("نقشه مهارت‌های هوش مصنوعی")
    st.caption("مسیر یادگیری و مهارت‌های کلیدی را برای نقش‌های AI دنبال کنید.")
