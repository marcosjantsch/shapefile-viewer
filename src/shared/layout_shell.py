from __future__ import annotations

import streamlit as st

from src.components.header.header import render_header
from src.components.sidebar.sidebar import render_sidebar
from src.config.settings import APP_ICON, APP_TITLE, LAYOUT, SIDEBAR_STATE
from src.pages import (
    assignments,
    billing_demo,
    active_companies,
    companies,
    company_videos,
    dashboard_company_admin,
    dashboard_employee,
    dashboard_platform_admin,
    employees,
    login,
    pending_videos,
    platform_videos,
    video_admin,
)
from src.services.auth_service import ensure_auth_session_defaults, get_current_page, get_current_user, logout_user, set_current_page
from src.services.storage_service import get_storage_service
from src.shared.styles import apply_global_styles
from src.utils.permissions import get_home_page_for_profile, is_page_allowed

PAGE_REGISTRY = {
    "dashboard_platform_admin": {
        "label": "Painel da plataforma",
        "description": "Visao global de empresas, colaboradores e conteudo central.",
        "section": "Inicio",
        "renderer": dashboard_platform_admin.render_page,
    },
    "dashboard_company_admin": {
        "label": "Painel da empresa",
        "description": "Resumo operacional da empresa e suas pendencias.",
        "section": "Inicio",
        "renderer": dashboard_company_admin.render_page,
    },
    "dashboard_employee": {
        "label": "Meu painel",
        "description": "Video do dia, fila pendente e historico individual.",
        "section": "Inicio",
        "renderer": dashboard_employee.render_page,
    },
    "companies": {
        "label": "Empresas",
        "description": "Cadastro e governanca das empresas da plataforma.",
        "section": "Cadastros",
        "renderer": companies.render_page,
    },
    "active_companies": {
        "label": "Empresas ativas",
        "description": "Tabela de empresas ativas com abertura direta do cadastro.",
        "section": "Cadastros",
        "renderer": active_companies.render_page,
    },
    "employees": {
        "label": "Colaboradores",
        "description": "Cadastro de colaboradores por empresa.",
        "section": "Cadastros",
        "renderer": employees.render_page,
    },
    "platform_videos": {
        "label": "Videos globais",
        "description": "Biblioteca global publicada pela plataforma.",
        "section": "Conteudo",
        "renderer": platform_videos.render_page,
    },
    "company_videos": {
        "label": "Videos da empresa",
        "description": "Conteudo interno de cada empresa.",
        "section": "Conteudo",
        "renderer": company_videos.render_page,
    },
    "video_admin": {
        "label": "Central de videos",
        "description": "Upload, destino e publicacao do acervo de videos.",
        "section": "Conteudo",
        "renderer": video_admin.render_page,
    },
    "assignments": {
        "label": "Atribuicoes diarias",
        "description": "Vinculo de videos por data e colaborador.",
        "section": "Operacao",
        "renderer": assignments.render_page,
    },
    "pending_videos": {
        "label": "Pendencias",
        "description": "Fila aberta de videos obrigatorios.",
        "section": "Operacao",
        "renderer": pending_videos.render_page,
    },
    "billing_demo": {
        "label": "Billing demo",
        "description": "Cobrancas simuladas para a empresa.",
        "section": "Financeiro",
        "renderer": billing_demo.render_page,
    },
}


def bootstrap_app() -> None:
    st.set_page_config(
        page_title=APP_TITLE,
        page_icon=APP_ICON,
        layout=LAYOUT,
        initial_sidebar_state=SIDEBAR_STATE,
    )
    apply_global_styles()
    ensure_auth_session_defaults()


def _build_navigation_sections(current_user: dict) -> list[dict]:
    sections_order = ["Inicio", "Cadastros", "Conteudo", "Operacao", "Financeiro"]
    sections = []
    for section_name in sections_order:
        items = [
            {"key": key, "label": meta["label"]}
            for key, meta in PAGE_REGISTRY.items()
            if meta["section"] == section_name and is_page_allowed(current_user, key)
        ]
        if items:
            sections.append({"title": section_name, "items": items})
    return sections


def _resolve_company_name(current_user: dict) -> str:
    company_id = current_user.get("company_id")
    if not company_id:
        return ""
    company = get_storage_service().get_record("companies", company_id)
    return (company or {}).get("nome_fantasia", "")


def render_application() -> None:
    current_user = get_current_user()
    if not current_user:
        login.render_page()
        return

    if not current_user.get("status_ativo", True):
        logout_user()
        st.error("Seu acesso esta inativo. Entre em contato com a administracao.")
        login.render_page()
        return

    current_page = get_current_page() or get_home_page_for_profile(current_user.get("profile"))
    if current_page not in PAGE_REGISTRY or not is_page_allowed(current_user, current_page):
        current_page = get_home_page_for_profile(current_user.get("profile"))
        set_current_page(current_page)

    sections = _build_navigation_sections(current_user)
    selected_page = render_sidebar(current_user, sections=sections, current_page=current_page)
    if selected_page and selected_page != current_page:
        set_current_page(selected_page)
        st.rerun()

    page_meta = PAGE_REGISTRY[current_page]
    render_header(
        current_user=current_user,
        page_title=page_meta["label"],
        page_description=page_meta["description"],
        company_name=_resolve_company_name(current_user),
    )
    page_meta["renderer"](current_user)
