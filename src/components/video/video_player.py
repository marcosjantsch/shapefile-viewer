from __future__ import annotations

from pathlib import Path

import streamlit as st

from src.config.settings import BASE_DIR
from src.utils.formatters import format_date, format_origin, format_video_source_label


def _resolve_video_source(video_url: str, assignment: dict) -> str:
    value = str(video_url or "").strip()
    if value.startswith("gs://"):
        try:
            from src.services.gcs_video_service import resolve_gcs_video_url

            return resolve_gcs_video_url(value)
        except Exception:
            return value
    if not value or "://" in value:
        return value
    path = Path(value)
    if path.exists():
        return str(path)

    relative_path = str(assignment.get("caminho_relativo_video") or "").strip()
    candidates = []
    if relative_path:
        candidates.append(BASE_DIR / "Videos" / Path(relative_path.replace("\\", "/")))
    candidates.append(BASE_DIR / "Videos" / path.name)
    for candidate in candidates:
        if candidate.exists():
            return str(candidate.resolve())
    return value


def render_video_player(
    assignment: dict,
    action_label: str = "Marcar como assistido",
    show_action: bool = True,
    compact: bool = False,
) -> bool:
    st.markdown(
        f"""
        <div class="seg-video-frame">
            <strong>{assignment.get("video_titulo", "Video obrigatorio")}</strong><br>
            <span style="color:#96b6ae;">
                Referencia: {format_date(assignment.get("data_referencia"))} |
                Origem: {format_origin(assignment.get("origem_video"))}
            </span>
            <div style="margin-top:0.45rem;color:#6f8e86;font-size:0.9rem;">
                {format_video_source_label(assignment)}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    video_url = assignment.get("video_url") or assignment.get("url_video_ou_arquivo")
    if video_url:
        video_source = _resolve_video_source(video_url, assignment)
        if str(video_source).startswith("gs://"):
            st.warning(
                "Nao foi possivel gerar a URL temporaria do video no Google Storage. "
                "Confira as credenciais e o acesso ao bucket."
            )
            return False
        if "://" not in str(video_source) and not Path(str(video_source)).exists():
            st.warning(
                "O arquivo de video nao foi encontrado na pasta local. Reenvie o arquivo pela Central de videos "
                "ou confira se ele esta em Videos com o mesmo nome."
            )
            return False
        if compact:
            _, center_column, _ = st.columns([0.28, 0.44, 0.28])
            with center_column:
                st.video(video_source)
        else:
            st.video(video_source)
    else:
        st.info("Nenhuma URL de video foi configurada para este registro.")
    if not show_action:
        return False
    return st.button(action_label, use_container_width=True, type="primary", key=f"watch-{assignment.get('id')}")
