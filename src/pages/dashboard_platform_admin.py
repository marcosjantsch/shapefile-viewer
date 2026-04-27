from __future__ import annotations

import streamlit as st

from src.components.cards.platform_metrics_card import render_platform_metrics_card
from src.services.assignment_service import list_assignments
from src.services.company_service import list_companies
from src.services.employee_service import list_employees
from src.services.platform_video_service import list_platform_videos
from src.shared.ui import render_page_intro


def render_page(current_user: dict) -> None:
    render_page_intro(
        "Painel da plataforma",
        "Visao consolidada de empresas, colaboradores, biblioteca global e operacao aberta.",
        kicker="Modulo 09",
    )
    companies = list_companies(current_user)
    employees = list_employees(current_user)
    platform_videos = list_platform_videos(current_user)
    pending_assignments = list_assignments(current_user, status_filter="pending")

    render_platform_metrics_card(
        [
            {"label": "Empresas", "value": len(companies), "help": "Base cadastrada na plataforma."},
            {"label": "Colaboradores", "value": len(employees), "help": "Usuarios finais ativos e inativos."},
            {"label": "Videos globais", "value": len(platform_videos), "help": "Biblioteca central compartilhada."},
            {"label": "Pendencias abertas", "value": len(pending_assignments), "help": "Fila consolidada da operacao."},
        ]
    )

    overview_rows = []
    pending_by_company = {}
    for assignment in pending_assignments:
        pending_by_company.setdefault(assignment.get("empresa_id"), 0)
        pending_by_company[assignment.get("empresa_id")] += 1

    employees_by_company = {}
    for employee in employees:
        employees_by_company.setdefault(employee.get("empresa_id"), 0)
        employees_by_company[employee.get("empresa_id")] += 1

    for company in companies:
        overview_rows.append(
            {
                "Empresa": company.get("nome_fantasia"),
                "UF": company.get("uf"),
                "Responsavel": company.get("nome_responsavel"),
                "Colaboradores": employees_by_company.get(company.get("id"), 0),
                "Pendentes": pending_by_company.get(company.get("id"), 0),
                "Status": "Ativa" if company.get("status_ativo", True) else "Inativa",
            }
        )

    st.markdown("### Visao geral operacional")
    st.dataframe(overview_rows, use_container_width=True, hide_index=True)
