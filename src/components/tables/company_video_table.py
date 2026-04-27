from __future__ import annotations

import streamlit as st

from src.utils.formatters import format_period, format_video_source_label


def render_company_video_table(videos: list[dict], action_prefix: str, allow_edit: bool = True) -> tuple[str, str] | None:
    if not videos:
        st.info("Nenhum video por empresa encontrado no filtro atual.")
        return None

    st.dataframe(
        [
            {
                "Empresa": video.get("empresa_nome", "-"),
                "Titulo": video.get("titulo", "-"),
                "Tema": video.get("tema", "-"),
                "Categoria": video.get("categoria", "-"),
                "Periodo": format_period(video.get("data_inicio_vigencia"), video.get("data_fim_vigencia")),
                "Publicado": "Sim" if video.get("status_publicado", True) else "Nao",
                "Obrigatorio": "Sim" if video.get("obrigatorio_por_padrao", False) else "Nao",
                "Fonte": format_video_source_label(video),
            }
            for video in videos
        ],
        use_container_width=True,
        hide_index=True,
    )
    if not allow_edit:
        return None

    selected_video_id = st.selectbox(
        "Selecionar video da empresa",
        options=[""] + [str(video.get("id")) for video in videos],
        format_func=lambda item: "Selecione" if not item else next(
            (
                f"{video.get('empresa_nome', '-')} | {video.get('titulo', item)}"
                for video in videos
                if str(video.get("id")) == str(item)
            ),
            str(item),
        ),
        key=f"{action_prefix}-selector",
    )
    if not selected_video_id:
        return None

    col_edit, col_toggle = st.columns(2)
    with col_edit:
        if st.button("Editar", key=f"{action_prefix}-edit", use_container_width=True):
            return ("edit", selected_video_id)
    with col_toggle:
        selected_video = next((video for video in videos if str(video.get("id")) == str(selected_video_id)), {})
        toggle_label = "Despublicar" if selected_video.get("status_publicado", True) else "Publicar"
        if st.button(toggle_label, key=f"{action_prefix}-toggle", use_container_width=True):
            return ("toggle", selected_video_id)
    return None
