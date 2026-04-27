from __future__ import annotations

import streamlit as st

from src.config.settings import APP_LOGO_PATH


def render_page_intro(title: str, description: str, kicker: str = "") -> None:
    kicker_html = f"<span class='seg-page-kicker'>{kicker}</span>" if kicker else ""
    left, right = st.columns([0.10, 0.90], vertical_alignment="center")
    with left:
        st.image(str(APP_LOGO_PATH), width=64)
    with right:
        st.markdown(
            f"""
            <div class="seg-page-intro">
                {kicker_html}
                <h1>{title}</h1>
                <p>{description}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_feedback(messages: list[str], level: str = "error") -> None:
    for message in messages:
        if level == "success":
            st.success(message)
        elif level == "warning":
            st.warning(message)
        else:
            st.error(message)


def render_empty_state(title: str, description: str) -> None:
    st.markdown(
        f"""
        <div class="seg-empty-state">
            <strong>{title}</strong>
            <span>{description}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def status_badge_html(label: str, variant: str = "muted") -> str:
    return f"<span class='seg-badge seg-badge--{variant}'>{label}</span>"
