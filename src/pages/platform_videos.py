from __future__ import annotations

import streamlit as st

from src.components.cards.common import render_metric_cards
from src.components.tables.platform_video_table import render_platform_video_table
from src.services.company_service import list_companies
from src.services.local_video_service import build_local_video_summary
from src.services.platform_video_service import list_platform_videos
from src.shared.ui import render_page_intro


def render_page(current_user: dict) -> None:
    render_page_intro(
        "Biblioteca global de videos",
        "A plataforma publica conteudo reutilizavel para evitar falta de material diario.",
        kicker="Modulo 04",
    )
    local_summary = build_local_video_summary(companies=list_companies(current_user))

    col_filter_1, col_filter_2, col_filter_3 = st.columns([0.45, 0.27, 0.28])
    with col_filter_1:
        search = st.text_input("Buscar video global", key="platform-videos-search")
    with col_filter_2:
        status_filter = st.selectbox(
            "Status",
            options=["all", "published", "draft"],
            format_func=lambda item: {"all": "Todos", "published": "Publicados", "draft": "Rascunhos"}[item],
        )
    with col_filter_3:
        theme_filter = st.text_input("Tema", key="platform-videos-theme")

    videos = list_platform_videos(
        current_user,
        search=search,
        theme_filter=theme_filter,
        category_filter="",
        status_filter=status_filter,
    )
    published_count = sum(1 for video in videos if video.get("status_publicado", True))
    render_metric_cards(
        [
            {"label": "Videos listados", "value": len(videos), "help": "Biblioteca global no escopo atual."},
            {"label": "Publicados", "value": published_count, "help": "Disponiveis para selecao nas empresas."},
            {"label": "Videos publicos", "value": local_summary["public_count"], "help": "Arquivos lidos da pasta publica."},
            {"label": "Obrigatorios", "value": sum(1 for video in videos if video.get("obrigatorio_por_padrao", True)), "help": "Campanhas que exigem visualizacao."},
        ]
    )
    st.info(
        "Sincronizacao automatica ativa: "
        f"{local_summary['public_count']} video(s) publicos e {local_summary['company_count']} video(s) em pastas de empresa "
        f"encontrados em `{local_summary['directory']}`."
    )

    st.info("Esta aba mostra a lista global em tabela. Novos cadastros e edicoes ficam concentrados na Central de videos.")
    render_platform_video_table(videos, action_prefix="platform-videos-readonly", allow_edit=False)
