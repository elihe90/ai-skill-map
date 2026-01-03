from __future__ import annotations

import csv
import io
from typing import Any, Dict, List

import streamlit as st

from core.admin_store import load_users


def _load_admin_password() -> str:
    try:
        return str(st.secrets.get("ADMIN_PASSWORD", "")).strip()
    except Exception:
        return ""


def _users_table_rows(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []
    for record in records:
        gap = record.get("gap", {}) if isinstance(record.get("gap"), dict) else {}
        rows.append(
            {
                "user_id": record.get("user_id", ""),
                "name": record.get("name", ""),
                "current_step": record.get("current_step", ""),
                "track": gap.get("track", "") or record.get("track", ""),
                "created_at": record.get("created_at", ""),
            }
        )
    return rows


def _download_csv(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    st.download_button(
        "\u062f\u0627\u0646\u0644\u0648\u062f CSV",
        data=buffer.getvalue(),
        file_name="users.csv",
        mime="text/csv",
    )


def _metric_cards(total: int, interview_reached: int, results_reached: int) -> None:
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        st.metric("\u06a9\u0644 \u06a9\u0627\u0631\u0628\u0631\u0627\u0646", total)
    with col_b:
        st.metric("\u0631\u0633\u06cc\u062f\u0647 \u0628\u0647 \u0645\u0635\u0627\u062d\u0628\u0647", interview_reached)
    with col_c:
        st.metric("\u0631\u0633\u06cc\u062f\u0647 \u0628\u0647 \u0646\u062a\u0627\u06cc\u062c", results_reached)


def _render_user_detail(record: Dict[str, Any]) -> None:
    profile = record.get("profile")
    if not isinstance(profile, dict):
        gap_profile = record.get("gap", {}).get("profile") if isinstance(record.get("gap"), dict) else {}
        profile = gap_profile if isinstance(gap_profile, dict) else {}

    with st.expander("\u067e\u0631\u0648\u0641\u0627\u06cc\u0644"):
        if profile:
            st.json(profile)
        else:
            st.caption("\u0647\u0646\u0648\u0632 \u062f\u0627\u062f\u0647\u200c\u0627\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \U0001F331")

    with st.expander("\u067e\u0627\u0633\u062e\u200c\u0647\u0627\u06cc \u0645\u0635\u0627\u062d\u0628\u0647"):
        answers = record.get("interview_answers", {})
        if isinstance(answers, dict) and answers:
            st.json(answers)
        else:
            st.caption("\u0647\u0646\u0648\u0632 \u062f\u0627\u062f\u0647\u200c\u0627\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \U0001F331")

    with st.expander("\u0648\u0636\u0639\u06cc\u062a \u06af\u067e\u200c\u0647\u0627"):
        gaps = record.get("skill_gaps", {})
        if isinstance(gaps, dict) and gaps:
            st.json(gaps)
        else:
            st.caption("\u0647\u0646\u0648\u0632 \u062f\u0627\u062f\u0647\u200c\u0627\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \U0001F331")

    with st.expander("\u0634\u063a\u0644\u200c\u0647\u0627\u06cc \u067e\u06cc\u0634\u0646\u0647\u0627\u062f\u06cc"):
        mapping = record.get("job_mapping", {})
        reachable = mapping.get("reachable_jobs", []) if isinstance(mapping, dict) else []
        if reachable:
            for job in reachable:
                st.markdown(f"- {job.get('title_fa', '')}")
        else:
            st.caption("\u0647\u0646\u0648\u0632 \u062f\u0627\u062f\u0647\u200c\u0627\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \U0001F331")


def main() -> None:
    st.set_page_config(page_title="Admin | AI Skill Map", layout="wide")
    st.title("\u062f\u0627\u0634\u0628\u0648\u0631\u062f \u0645\u062f\u06cc\u0631")

    admin_password = _load_admin_password()
    if not admin_password:
        st.error("\u0631\u0645\u0632 \u0645\u062f\u06cc\u0631 \u062f\u0631 secrets \u062a\u0646\u0638\u06cc\u0645 \u0646\u0634\u062f\u0647 \u0627\u0633\u062a.")
        st.stop()

    entered = st.text_input("\u0631\u0645\u0632 \u0645\u062f\u06cc\u0631", type="password")
    if not entered:
        st.stop()
    if entered != admin_password:
        st.error("\u0631\u0645\u0632 \u0646\u0627\u062f\u0631\u0633\u062a \u0627\u0633\u062a.")
        st.stop()

    users = load_users()
    records = list(users.values()) if isinstance(users, dict) else []

    total = len(records)
    interview_reached = sum(
        1
        for record in records
        if record.get("interview_completed")
        or record.get("current_step") in ("interview", "skill_map", "results")
    )
    results_reached = sum(
        1
        for record in records
        if record.get("results_generated") or record.get("current_step") == "results"
    )

    _metric_cards(total, interview_reached, results_reached)

    st.markdown("### \u0644\u06cc\u0633\u062a \u06a9\u0627\u0631\u0628\u0631\u0627\u0646")
    rows = _users_table_rows(records)
    if rows:
        st.dataframe(rows, use_container_width=True)
        _download_csv(rows)
    else:
        st.info("\u0647\u0646\u0648\u0632 \u06a9\u0627\u0631\u0628\u0631\u06cc \u062b\u0628\u062a \u0646\u0634\u062f\u0647 \u0627\u0633\u062a.")

    st.markdown("### \u062c\u0632\u0626\u06cc\u0627\u062a \u06a9\u0627\u0631\u0628\u0631")
    user_ids = [row.get("user_id", "") for row in rows]
    if not user_ids:
        return
    selected = st.selectbox("\u0627\u0646\u062a\u062e\u0627\u0628 \u06a9\u0627\u0631\u0628\u0631", options=user_ids)
    record = users.get(selected, {}) if isinstance(users, dict) else {}
    if record:
        _render_user_detail(record)
    else:
        st.info("\u062f\u0627\u062f\u0647\u200c\u0627\u06cc \u067e\u06cc\u062f\u0627 \u0646\u0634\u062f.")


if __name__ == "__main__":
    main()
