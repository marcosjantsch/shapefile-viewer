from __future__ import annotations

import streamlit as st

from src.config.settings import APP_LOGO_PATH, APP_TITLE, APP_VERSION
from src.utils.formatters import format_profile
from src.utils.permissions import is_company_admin, is_employee


def render_header(current_user: dict, page_title: str, page_description: str, company_name: str = "") -> None:
    context_parts = [format_profile(current_user.get("profile"))]
    if company_name and (is_company_admin(current_user) or is_employee(current_user)):
        context_parts.append(company_name)
    context_text = " | ".join(context_parts)

    st.markdown('<div class="seg-header">', unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="seg-header-card">', unsafe_allow_html=True)
        left, right = st.columns([0.68, 0.32], vertical_alignment="center")
        with left:
            logo_col, text_col = st.columns([0.16, 0.84], vertical_alignment="center")
            with logo_col:
                st.image(str(APP_LOGO_PATH), width=84)
            with text_col:
                st.markdown(
                    f"""
                    <div>
                        <div class="seg-header-title">{APP_TITLE}</div>
                        <div class="seg-header-subtitle">{page_title} · {page_description}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        with right:
            st.markdown(
                f"""
                <div class="seg-header-session">
                    <span class="seg-badge seg-badge--muted">{APP_VERSION}</span>
                    <span class="seg-badge seg-badge--success">{current_user.get("full_name", "Sessao ativa")}</span>
                    <span class="seg-badge seg-badge--muted">{context_text}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
