from typing import Sequence

import streamlit as st

from core.models import Skill
from core.service import skill_level_label


def render_skill_list(skills: Sequence[Skill]) -> None:
    if not skills:
        st.info("مهارتی با این فیلترها پیدا نشد.")
        return

    st.markdown('<div class="grid">', unsafe_allow_html=True)
    for skill in skills:
        st.markdown(
            f"""
            <div class="skill-card">
              <div><strong>{skill.name}</strong></div>
              <div class="muted">{skill.category} • {skill_level_label(skill.level)}</div>
              <div>{skill.description}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)
