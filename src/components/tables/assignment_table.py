from __future__ import annotations

import streamlit as st

from src.utils.formatters import format_assignment_status, format_date, format_origin


def render_assignment_table(assignments: list[dict], action_prefix: str) -> tuple[str, str] | None:
    if not assignments:
        st.info("Nenhuma atribuicao encontrada no filtro atual.")
        return None

    st.dataframe(
        [
            {
                "Video": assignment.get("video_titulo", "-"),
                "Empresa": assignment.get("empresa_nome", "-"),
                "Colaborador": assignment.get("funcionario_nome", "-"),
                "Origem": format_origin(assignment.get("origem_video")),
                "Referencia": format_date(assignment.get("data_referencia")),
                "Status": format_assignment_status(assignment.get("status")),
                "Atraso": f"{assignment.get('delay_days', 0)} dia(s)",
            }
            for assignment in assignments
        ],
        use_container_width=True,
        hide_index=True,
    )

    selected_assignment_id = st.selectbox(
        "Selecionar atribuicao",
        options=[""] + [str(assignment.get("id")) for assignment in assignments],
        format_func=lambda item: "Selecione" if not item else next(
            (
                f"{assignment.get('funcionario_nome', '-')} | {assignment.get('video_titulo', item)}"
                for assignment in assignments
                if str(assignment.get("id")) == str(item)
            ),
            str(item),
        ),
        key=f"{action_prefix}-selector",
    )
    if not selected_assignment_id:
        return None

    if st.button("Revisar atribuicao", key=f"{action_prefix}-inspect", use_container_width=True):
        return ("inspect", selected_assignment_id)
    return None
