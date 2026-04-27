from __future__ import annotations

import streamlit as st

from src.utils.formatters import format_date, format_origin


def render_company_pending_table(assignments: list[dict], action_prefix: str = "company-pending") -> tuple[str, str] | None:
    if not assignments:
        st.info("Nenhuma pendencia encontrada no filtro atual.")
        return None

    st.dataframe(
        [
            {
                "Video": assignment.get("video_titulo", "-"),
                "Colaborador": assignment.get("funcionario_nome", "-"),
                "Empresa": assignment.get("empresa_nome", "-"),
                "Origem": format_origin(assignment.get("origem_video")),
                "Referencia": format_date(assignment.get("data_referencia")),
                "Atraso": f"{assignment.get('delay_days', 0)} dia(s)",
            }
            for assignment in assignments
        ],
        use_container_width=True,
        hide_index=True,
    )

    selectable_ids = [str(assignment.get("id")) for assignment in assignments if assignment.get("video_url")]
    selected_assignment_id = st.selectbox(
        "Selecionar pendencia",
        options=[""] + selectable_ids,
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

    if st.button("Abrir video", key=f"{action_prefix}-open", use_container_width=True):
        return ("open", selected_assignment_id)
    return None
