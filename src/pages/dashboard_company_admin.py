from __future__ import annotations

import streamlit as st

from src.components.cards.company_metrics_card import render_company_metrics_card
from src.components.tables.company_pending_table import render_company_pending_table
from src.services.assignment_service import get_assignment, list_assignments
from src.services.company_context_service import get_active_company_id, set_active_company_id
from src.services.company_service import get_company
from src.services.company_service import list_companies
from src.services.company_video_service import list_company_videos
from src.services.platform_video_service import list_platform_videos
from src.services.storage_service import get_storage_service
from src.shared.ui import render_page_intro


def render_page(current_user: dict) -> None:
    render_page_intro(
        "Painel do administrador da empresa",
        "Resumo operacional da empresa, pendencias abertas e acessos prioritarios.",
        kicker="Modulo 08",
    )
    st.session_state.setdefault("company_dashboard_open_assignment", None)

    companies = list_companies(current_user, status_filter="active")
    active_company_id = get_active_company_id(current_user)
    if companies:
        company_ids = [str(company.get("id")) for company in companies]
        selected_company_id = st.selectbox(
            "Empresa",
            options=company_ids,
            index=company_ids.index(active_company_id) if active_company_id in company_ids else 0,
            format_func=lambda item: next(
                (
                    str(company.get("nome_fantasia", item))
                    for company in companies
                    if str(company.get("id")) == str(item)
                ),
                str(item),
            ),
            key="company-dashboard-company-select",
        )
        if selected_company_id != active_company_id:
            set_active_company_id(selected_company_id)
            st.rerun()
        active_company_id = selected_company_id

    company = get_company(current_user, active_company_id)
    employees = [
        employee
        for employee in get_storage_service().list_records("employees")
        if str(employee.get("empresa_id")) == str(active_company_id)
    ]
    pending_assignments = list_assignments(current_user, company_id=active_company_id, status_filter="pending")
    completed_assignments = list_assignments(current_user, company_id=active_company_id, status_filter="completed")
    company_videos = list_company_videos(current_user, company_id=active_company_id)
    platform_videos = [item for item in list_platform_videos(current_user) if item.get("status_publicado", True)]

    render_company_metrics_card(
        [
            {"label": "Empresa", "value": company.get("nome_fantasia", "-"), "help": "Escopo administrativo atual."},
            {"label": "Colaboradores", "value": len(employees), "help": "Base cadastrada nesta empresa."},
            {"label": "Pendentes", "value": len(pending_assignments), "help": "Fila total ainda aberta."},
            {"label": "Concluidos", "value": len(completed_assignments), "help": "Historico confirmado."},
        ]
    )
    render_company_metrics_card(
        [
            {"label": "Videos da empresa", "value": len(company_videos), "help": "Conteudo proprio publicado ou rascunho."},
            {"label": "Biblioteca global", "value": len(platform_videos), "help": "Opcoes publicadas pela plataforma."},
            {"label": "Responsavel", "value": company.get("nome_responsavel", "-"), "help": "Contato principal cadastrado."},
            {"label": "Billing demo", "value": "Disponivel", "help": "Modulo financeiro demonstrativo liberado."},
        ]
    )

    col_filter, col_list = st.columns([0.28, 0.72], gap="large")
    with col_filter:
        employee_lookup = {employee["id"]: employee["nome_completo"] for employee in employees}
        selected_employee = st.selectbox(
            "Filtrar pendencias por colaborador",
            options=[""] + list(employee_lookup.keys()),
            format_func=lambda item: "Todos os colaboradores" if not item else employee_lookup.get(item, item),
        )
        filtered_assignments = [
            item
            for item in pending_assignments
            if not selected_employee or str(item.get("funcionario_id")) == str(selected_employee)
        ]
        st.info(
            "A area de cobranca permanece explicitamente marcada como demo e a selecao de videos globais segue disponivel na operacao diaria."
        )

    with col_list:
        action = render_company_pending_table(filtered_assignments, action_prefix="company-dashboard-pending")
        if action:
            _, assignment_id = action
            st.session_state["company_dashboard_open_assignment"] = assignment_id

        inspect_id = st.session_state.get("company_dashboard_open_assignment")
        if inspect_id:
            assignment = get_assignment(current_user, inspect_id)
            st.info(
                f"Video inspecionado: {assignment.get('funcionario_nome')} · "
                f"{assignment.get('video_titulo')} · referencia {assignment.get('data_referencia')}"
            )
