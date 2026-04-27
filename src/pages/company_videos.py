from __future__ import annotations

import streamlit as st

from src.components.cards.common import render_metric_cards
from src.components.tables.company_video_table import render_company_video_table
from src.services.company_context_service import get_active_company_id
from src.services.company_service import list_companies
from src.services.company_video_service import list_company_videos
from src.services.local_video_service import build_local_video_summary
from src.shared.ui import render_page_intro
from src.utils.permissions import is_company_admin


def render_page(current_user: dict) -> None:
    render_page_intro(
        "Biblioteca da empresa",
        "Videos internos publicados por empresa, sem compartilhamento cruzado.",
        kicker="Modulo 05",
    )
    companies = list_companies(current_user)
    local_summary = build_local_video_summary(companies=companies)
    company_lookup = {company["id"]: company["nome_fantasia"] for company in companies}
    active_company_id = get_active_company_id(current_user) if is_company_admin(current_user) else ""

    col_filter_1, col_filter_2, col_filter_3 = st.columns([0.45, 0.27, 0.28])
    with col_filter_1:
        search = st.text_input("Buscar video da empresa", key="company-videos-search")
    with col_filter_2:
        status_filter = st.selectbox(
            "Status",
            options=["all", "published", "draft"],
            format_func=lambda item: {"all": "Todos", "published": "Publicados", "draft": "Rascunhos"}[item],
        )
    with col_filter_3:
        if is_company_admin(current_user):
            company_filter = active_company_id
            st.info(f"Empresa em foco: {company_lookup.get(company_filter, '-')}")
        else:
            company_filter = st.selectbox(
                "Empresa",
                options=[""] + list(company_lookup.keys()),
                format_func=lambda item: "Todas as empresas" if not item else company_lookup.get(item, item),
            )

    videos = list_company_videos(current_user, company_id=company_filter, search=search, status_filter=status_filter)
    published_count = sum(1 for video in videos if video.get("status_publicado", True))
    render_metric_cards(
        [
            {"label": "Videos listados", "value": len(videos), "help": "Biblioteca filtrada da empresa."},
            {"label": "Publicados", "value": published_count, "help": "Disponiveis para atribuicao."},
            {"label": "Videos da pasta", "value": local_summary["company_count"], "help": "Arquivos reconhecidos em pastas de empresa."},
            {"label": "Empresa foco", "value": company_lookup.get(company_filter, "Multiplas"), "help": "Escopo atual."},
        ]
    )
    st.info(
        "Leitura automatica ativa. "
        f"Use `Videos\\publicos` para conteudo geral e `Videos\\Nome da Empresa` para conteudo isolado. "
        f"Caminho atual: `{local_summary['directory']}`."
    )
    st.info("Esta aba mostra a lista por empresa em tabela. Novos cadastros e edicoes ficam concentrados na Central de videos.")
    render_company_video_table(videos, action_prefix="company-videos-readonly", allow_edit=False)
