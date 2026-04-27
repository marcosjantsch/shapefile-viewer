from __future__ import annotations

import streamlit as st

from src.components.cards.common import render_metric_cards
from src.components.forms.employee_form import render_employee_form
from src.components.tables.employee_table import render_employee_table
from src.services.company_service import list_companies
from src.services.employee_service import get_employee, list_employees, save_employee, toggle_employee_status
from src.shared.ui import render_feedback, render_page_intro
from src.utils.permissions import is_company_admin


def render_page(current_user: dict) -> None:
    render_page_intro(
        "Colaboradores",
        "Cadastro vinculado por empresa, com controle de acesso e login sincronizado.",
        kicker="Modulo 03",
    )
    st.session_state.setdefault("employees_edit_id", None)

    companies = list_companies(current_user)
    company_lookup = {company["id"]: company["nome_fantasia"] for company in companies}

    col_filter_1, col_filter_2, col_filter_3 = st.columns([0.45, 0.27, 0.28])
    with col_filter_1:
        search = st.text_input("Buscar colaborador", key="employees-search")
    with col_filter_2:
        status_filter = st.selectbox(
            "Status",
            options=["all", "active", "inactive"],
            format_func=lambda item: {"all": "Todos", "active": "Ativos", "inactive": "Inativos"}[item],
        )
    with col_filter_3:
        if is_company_admin(current_user):
            company_filter = str(current_user.get("company_id"))
            st.info(f"Empresa: {company_lookup.get(company_filter, '-')}")
        else:
            company_filter = st.selectbox(
                "Empresa",
                options=[""] + list(company_lookup.keys()),
                format_func=lambda item: "Todas as empresas" if not item else company_lookup.get(item, item),
            )

    employees = list_employees(
        current_user,
        search=search,
        company_filter=company_filter,
        status_filter=status_filter,
    )
    active_count = sum(1 for employee in employees if employee.get("status_ativo", True))
    render_metric_cards(
        [
            {"label": "Colaboradores", "value": len(employees), "help": "Listagem apos filtros."},
            {"label": "Ativos", "value": active_count, "help": "Aptos a receber atribuicoes."},
            {"label": "Inativos", "value": len(employees) - active_count, "help": "Bloqueados para login."},
            {
                "label": "Empresa foco",
                "value": company_lookup.get(company_filter, "Multiplas"),
                "help": "Escopo atual do formulario e da grade.",
            },
        ]
    )

    left, right = st.columns([0.42, 0.58], gap="large")

    with left:
        editing_id = st.session_state.get("employees_edit_id")
        if st.button("Novo colaborador", use_container_width=True, key="employees-new"):
            st.session_state["employees_edit_id"] = None
            st.rerun()
        initial_data = get_employee(current_user, editing_id) if editing_id else {}
        submitted, payload = render_employee_form(
            initial_data=initial_data,
            companies=companies,
            form_key="employee-form",
            fixed_company_id=str(current_user.get("company_id")) if is_company_admin(current_user) else "",
        )
        if submitted:
            saved, errors = save_employee(current_user, payload, employee_id=editing_id)
            if errors:
                render_feedback(errors)
            elif saved:
                st.session_state["employees_edit_id"] = saved["id"]
                st.success("Colaborador salvo com sucesso.")
                st.rerun()

    with right:
        action = render_employee_table(employees, action_prefix="employees-table")
        if action:
            verb, employee_id = action
            if verb == "edit":
                st.session_state["employees_edit_id"] = employee_id
                st.rerun()
            if verb == "toggle":
                toggle_employee_status(current_user, employee_id)
                st.success("Status do colaborador atualizado.")
                st.rerun()
