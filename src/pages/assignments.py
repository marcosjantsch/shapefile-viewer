from __future__ import annotations

import streamlit as st

from src.components.cards.common import render_metric_cards
from src.components.forms.assignment_form import render_assignment_form
from src.components.tables.assignment_table import render_assignment_table
from src.services.assignment_service import build_video_options_for_company, get_assignment, list_assignments, save_assignment
from src.services.company_service import list_companies
from src.services.employee_service import list_employees
from src.shared.ui import render_feedback, render_page_intro
from src.utils.permissions import is_company_admin


def render_page(current_user: dict) -> None:
    render_page_intro(
        "Atribuicao diaria de videos",
        "Vincula o video obrigatorio por data, empresa e colaborador, preservando pendencias.",
        kicker="Modulo 06",
    )
    st.session_state.setdefault("assignments_inspect_id", None)

    companies = list_companies(current_user)
    company_lookup = {company["id"]: company["nome_fantasia"] for company in companies}

    col_filter_1, col_filter_2, col_filter_3, col_filter_4 = st.columns([0.30, 0.28, 0.20, 0.22])
    with col_filter_1:
        if is_company_admin(current_user):
            company_filter = str(current_user.get("company_id"))
            st.info(f"Empresa: {company_lookup.get(company_filter, '-')}")
        else:
            company_filter = st.selectbox(
                "Empresa",
                options=list(company_lookup.keys()),
                format_func=lambda item: company_lookup.get(item, item),
            ) if company_lookup else ""
    with col_filter_2:
        employee_options = list_employees(current_user, company_filter=company_filter) if company_filter else []
        employee_lookup = {employee["id"]: employee["nome_completo"] for employee in employee_options}
        employee_filter = st.selectbox(
            "Funcionario",
            options=[""] + list(employee_lookup.keys()),
            format_func=lambda item: "Todos" if not item else employee_lookup.get(item, item),
        )
    with col_filter_3:
        status_filter = st.selectbox(
            "Status",
            options=["all", "pending", "completed"],
            format_func=lambda item: {"all": "Todos", "pending": "Pendentes", "completed": "Concluidos"}[item],
        )
    with col_filter_4:
        reference_date = st.date_input("Data", value=None, format="DD/MM/YYYY")

    resolved_reference_date = getattr(reference_date, "isoformat", lambda: "")()
    assignments = list_assignments(
        current_user,
        company_id=company_filter,
        employee_id=employee_filter,
        status_filter=status_filter,
        reference_date=resolved_reference_date,
    )
    pending_count = sum(1 for item in assignments if item.get("status") == "pending")
    render_metric_cards(
        [
            {"label": "Atribuicoes", "value": len(assignments), "help": "Registros filtrados."},
            {"label": "Pendentes", "value": pending_count, "help": "Mantidos ate conclusao."},
            {"label": "Concluidas", "value": len(assignments) - pending_count, "help": "Historico do filtro atual."},
            {"label": "Empresa foco", "value": company_lookup.get(company_filter, "-"), "help": "Escopo do formulario."},
        ]
    )

    left, right = st.columns([0.42, 0.58], gap="large")

    with left:
        video_options = build_video_options_for_company(current_user, company_filter) if company_filter else {"platform": [], "company": []}
        submitted, payload = render_assignment_form(
            initial_data=None,
            companies=companies,
            employees=employee_options,
            video_options=video_options,
            form_key="assignment-form",
            fixed_company_id=company_filter,
        )
        if submitted:
            saved, errors = save_assignment(current_user, payload)
            if errors:
                render_feedback(errors)
            elif saved:
                st.success("Atribuicao registrada com sucesso.")
                st.rerun()

    with right:
        action = render_assignment_table(assignments, action_prefix="assignments-table")
        if action:
            _, assignment_id = action
            st.session_state["assignments_inspect_id"] = assignment_id

        inspect_id = st.session_state.get("assignments_inspect_id")
        if inspect_id:
            assignment = get_assignment(current_user, inspect_id)
            st.info(
                f"Inspecao atual: {assignment.get('funcionario_nome')} · "
                f"{assignment.get('video_titulo')} · {assignment.get('data_referencia')}"
            )
