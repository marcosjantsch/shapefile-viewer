from __future__ import annotations

from src.components.cards.common import render_record_summary
from src.utils.formatters import format_date, format_origin


def render_today_video_card(assignment: dict) -> None:
    render_record_summary(
        title=assignment.get("video_titulo", "Video do dia"),
        meta_lines=[
            f"Data de referencia: {format_date(assignment.get('data_referencia'))}",
            f"Origem: {format_origin(assignment.get('origem_video'))}",
            f"Tema: {assignment.get('video_tema', '-')}",
            f"Categoria: {assignment.get('video_categoria', '-')}",
        ],
        badges=[
            {"label": "Obrigatorio hoje", "variant": "warning"},
            {"label": assignment.get("funcionario_nome", ""), "variant": "muted"},
        ],
        footer=assignment.get("video_url", ""),
    )
