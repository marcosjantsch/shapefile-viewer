from __future__ import annotations

import streamlit as st

from src.components.cards.common import render_metric_cards
from src.components.forms.video_admin_form import render_video_admin_form
from src.components.tables.video_admin_table import render_video_admin_table
from src.services.company_service import list_companies
from src.services.local_video_service import build_local_video_summary
from src.services.video_admin_service import (
    get_managed_video,
    list_managed_videos,
    save_managed_video,
    toggle_managed_video_status,
)
from src.shared.ui import render_feedback, render_page_intro


def _parse_edit_ref(edit_ref: str) -> tuple[str, str]:
    if "::" not in str(edit_ref):
        return "", ""
    scope, video_id = str(edit_ref).split("::", 1)
    return scope, video_id


def render_page(current_user: dict) -> None:
    render_page_intro(
        "Central de videos",
        "Cadastro com upload, definicao de destino e administracao do acervo em uma unica tela.",
        kicker="Conteudo",
    )
    st.session_state.setdefault("video_admin_edit_ref", "")

    companies = list_companies(current_user)
    company_lookup = {company["id"]: company["nome_fantasia"] for company in companies}
    local_summary = build_local_video_summary(companies=companies)
    col_filter_1, col_filter_2, col_filter_3 = st.columns([0.42, 0.28, 0.30])
    with col_filter_1:
        search = st.text_input("Buscar video", key="video-admin-search")
    with col_filter_2:
        scope_filter = st.selectbox(
            "Destino",
            options=["all", "platform", "company"],
            format_func=lambda item: {
                "all": "Todos",
                "platform": "Todas as empresas",
                "company": "Empresas especificas",
            }[item],
        )
    with col_filter_3:
        company_filter = st.selectbox(
            "Empresa",
            options=[""] + list(company_lookup.keys()),
            format_func=lambda item: "Todas as empresas" if not item else company_lookup.get(item, item),
        )

    videos = list_managed_videos(
        current_user,
        company_id=company_filter,
        search=search,
        scope_filter=scope_filter,
    )
    platform_count = sum(1 for video in videos if video.get("scope") == "platform")
    company_count = sum(1 for video in videos if video.get("scope") == "company")
    render_metric_cards(
        [
            {"label": "Videos listados", "value": len(videos), "help": "Acervo no filtro atual."},
            {"label": "Publicos", "value": platform_count, "help": "Disponiveis para todas as empresas."},
            {"label": "Por empresa", "value": company_count, "help": "Conteudo isolado por cliente."},
            {"label": "Arquivos locais", "value": local_summary.get("local_count", 0), "help": "Arquivos monitorados em Videos."},
            {"label": "Storage Google", "value": local_summary.get("gcs_count", 0), "help": f"Bucket {local_summary.get('bucket', '-') }."},
        ]
    )
    st.info(
        "O sistema sincroniza videos da pasta local `Videos\\` e tambem do bucket Google Storage "
        f"`{local_summary.get('bucket', '-')}` quando as credenciais estiverem configuradas."
    )

    left, right = st.columns([0.42, 0.58], gap="large")
    with left:
        edit_scope, edit_id = _parse_edit_ref(st.session_state.get("video_admin_edit_ref", ""))
        initial_data = get_managed_video(current_user, edit_scope, edit_id) if edit_scope and edit_id else {}
        if initial_data:
            initial_data = {**initial_data, "scope": edit_scope}

        if st.button("Novo cadastro de video", use_container_width=True, key="video-admin-new"):
            st.session_state["video_admin_edit_ref"] = ""
            st.rerun()

        submitted, payload = render_video_admin_form(
            current_user=current_user,
            initial_data=initial_data,
            companies=companies,
            form_key="video-admin-form",
        )
        if submitted:
            saved, errors, saved_scope = save_managed_video(
                current_user,
                payload,
                editing_scope=edit_scope,
                editing_id=edit_id,
            )
            if errors:
                render_feedback(errors)
            elif saved:
                st.session_state["video_admin_edit_ref"] = f"{saved_scope}::{saved['id']}"
                st.success("Video salvo com sucesso.")
                st.rerun()

    with right:
        action = render_video_admin_table(videos, action_prefix="video-admin-table")
        if action:
            verb, scope, video_id = action
            if verb == "edit":
                st.session_state["video_admin_edit_ref"] = f"{scope}::{video_id}"
                st.rerun()
            if verb == "toggle":
                toggle_managed_video_status(current_user, scope, video_id)
                st.success("Status do video atualizado.")
                st.rerun()
