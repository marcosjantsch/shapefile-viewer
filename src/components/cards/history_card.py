from __future__ import annotations

import streamlit as st

from src.shared.ui import render_empty_state
from src.utils.formatters import format_date, format_datetime


def render_history_card(history_items: list[dict]) -> None:
    st.markdown("#### Historico recente")
    if not history_items:
        render_empty_state("Sem historico recente", "Conclucoes futuras aparecerao nesta area.")
        return

    for item in history_items[:5]:
        st.markdown(
            f"""
            <div class="seg-record-card">
                <div class="seg-record-title">{item.get("video_titulo", "-")}</div>
                <div class="seg-record-meta">
                    Referencia: {format_date(item.get("data_referencia"))}<br>
                    Conclusao: {format_datetime(item.get("data_visualizacao"))}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
