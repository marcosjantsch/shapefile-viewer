from __future__ import annotations

import streamlit as st

from src.utils.formatters import format_date, format_origin


def render_pending_video_table(assignments: list[dict], action_prefix: str) -> tuple[str, str] | None:
    if not assignments:
        st.info("Nenhum video pendente encontrado.")
        return None

    st.dataframe(
        [
            {
                "Video": assignment.get("video_titulo", "-"),
                "Origem": format_origin(assignment.get("origem_video")),
                "Referencia": format_date(assignment.get("data_referencia")),
                "Atraso": f"{assignment.get('delay_days', 0)} dia(s)",
            }
            for assignment in assignments
        ],
        use_container_width=True,
        hide_index=True,
    )

    selected_assignment_id = st.selectbox(
        "Selecionar video pendente",
        options=[""] + [str(assignment.get("id")) for assignment in assignments],
        format_func=lambda item: "Selecione" if not item else next(
            (
                f"{assignment.get('video_titulo', item)} | {format_date(assignment.get('data_referencia'))}"
                for assignment in assignments
                if str(assignment.get("id")) == str(item)
            ),
            str(item),
        ),
        key=f"{action_prefix}-selector",
    )
    if not selected_assignment_id:
        return None

    col_watch, col_mark = st.columns(2)
    with col_watch:
        if st.button("Abrir", key=f"{action_prefix}-open", use_container_width=True):
            return ("open", selected_assignment_id)
    with col_mark:
        if st.button("Concluir", key=f"{action_prefix}-done", use_container_width=True):
            return ("complete", selected_assignment_id)
    return None
