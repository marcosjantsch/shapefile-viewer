from __future__ import annotations

import streamlit as st

from src.config.settings import APP_LOGO_PATH
from src.services.auth_service import logout_user
from src.utils.formatters import format_profile


def render_sidebar(current_user: dict, sections: list[dict], current_page: str) -> str | None:
    selected_page = None
    with st.sidebar:
        st.image(str(APP_LOGO_PATH), width=140)
        st.markdown(
            f"""
            <div class="seg-sidebar-brand">
                <strong>SEG365</strong>
                <span>Seguranca do Trabalho · 365 dias</span><br>
                <span>{format_profile(current_user.get("profile"))}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        for section in sections:
            st.caption(section["title"])
            for item in section["items"]:
                button_type = "primary" if item["key"] == current_page else "secondary"
                if st.button(item["label"], key=f"nav-{item['key']}", use_container_width=True, type=button_type):
                    selected_page = item["key"]
            st.markdown(" ")

        st.divider()
        st.caption(current_user.get("username", ""))
        if st.button("Logout", use_container_width=True, key="sidebar-logout"):
            logout_user()
            st.rerun()
    return selected_page
