from __future__ import annotations

import streamlit as st

from src.utils.formatters import format_phone


def render_employee_table(employees: list[dict], action_prefix: str) -> tuple[str, str] | None:
    if not employees:
        st.info("Nenhum colaborador encontrado no filtro atual.")
        return None

    st.dataframe(
        [
            {
                "Nome": employee.get("nome_completo", "-"),
                "Empresa": employee.get("empresa_nome", "-"),
                "Matricula": employee.get("matricula", "-"),
                "Funcao": employee.get("funcao", "-"),
                "Login": employee.get("login", "-"),
                "Telefone": format_phone(employee.get("telefone")),
                "E-mail": employee.get("email", "-"),
                "Status": "Ativo" if employee.get("status_ativo", True) else "Inativo",
            }
            for employee in employees
        ],
        use_container_width=True,
        hide_index=True,
    )

    selected_employee_id = st.selectbox(
        "Selecionar colaborador",
        options=[""] + [str(employee.get("id")) for employee in employees],
        format_func=lambda item: "Selecione" if not item else next(
            (
                f"{employee.get('nome_completo', item)} | {employee.get('empresa_nome', '-')}"
                for employee in employees
                if str(employee.get("id")) == str(item)
            ),
            str(item),
        ),
        key=f"{action_prefix}-selector",
    )
    if not selected_employee_id:
        return None

    col_edit, col_toggle = st.columns(2)
    with col_edit:
        if st.button("Editar", key=f"{action_prefix}-edit", use_container_width=True):
            return ("edit", selected_employee_id)
    with col_toggle:
        selected_employee = next((employee for employee in employees if str(employee.get("id")) == str(selected_employee_id)), {})
        toggle_label = "Inativar" if selected_employee.get("status_ativo", True) else "Ativar"
        if st.button(toggle_label, key=f"{action_prefix}-toggle", use_container_width=True):
            return ("toggle", selected_employee_id)
    return None
