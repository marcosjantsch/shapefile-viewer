from __future__ import annotations

import streamlit as st

from src.utils.formatters import format_period, format_video_source_label


def _format_display_window(video: dict) -> str:
    if str(video.get("tipo_exibicao") or "periodo") == "data_unica":
        return f"Data unica: {video.get('data_exibicao') or video.get('data_inicio_vigencia') or '-'}"
    return format_period(video.get("data_inicio_vigencia"), video.get("data_fim_vigencia"))


def render_video_admin_table(videos: list[dict], action_prefix: str) -> tuple[str, str, str] | None:
    if not videos:
        st.info("Nenhum video encontrado no filtro atual.")
        return None

    st.dataframe(
        [
            {
                "Escopo": video.get("scope_label", "-"),
                "Destino": video.get("destination_label", "-"),
                "Titulo": video.get("titulo", "-"),
                "Tema": video.get("tema", "-"),
                "Categoria": video.get("categoria", "-"),
                "Exibicao": _format_display_window(video),
                "Publicado": "Sim" if video.get("status_publicado", True) else "Nao",
                "Obrigatorio": "Sim" if video.get("obrigatorio_por_padrao", True) else "Nao",
                "Fonte": format_video_source_label(video),
            }
            for video in videos
        ],
        use_container_width=True,
        hide_index=True,
    )

    options = [""] + [f"{video.get('scope')}::{video.get('id')}" for video in videos]
    selected_ref = st.selectbox(
        "Selecionar cadastro",
        options=options,
        format_func=lambda item: "Selecione" if not item else next(
            (
                f"{video.get('destination_label', '-')} | {video.get('titulo', item)}"
                for video in videos
                if f"{video.get('scope')}::{video.get('id')}" == str(item)
            ),
            str(item),
        ),
        key=f"{action_prefix}-selector",
    )
    if not selected_ref:
        return None

    selected_scope, selected_id = str(selected_ref).split("::", 1)
    selected_video = next(
        (
            video
            for video in videos
            if str(video.get("scope")) == selected_scope and str(video.get("id")) == selected_id
        ),
        {},
    )
    col_edit, col_toggle = st.columns(2)
    with col_edit:
        if st.button("Editar", key=f"{action_prefix}-edit", use_container_width=True):
            return ("edit", selected_scope, selected_id)
    with col_toggle:
        toggle_label = "Despublicar" if selected_video.get("status_publicado", True) else "Publicar"
        if st.button(toggle_label, key=f"{action_prefix}-toggle", use_container_width=True):
            return ("toggle", selected_scope, selected_id)
    return None
