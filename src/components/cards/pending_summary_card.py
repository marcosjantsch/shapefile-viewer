from __future__ import annotations

from src.components.cards.common import render_record_summary


def render_pending_summary_card(total_pending: int, overdue_count: int) -> None:
    render_record_summary(
        title="Resumo de pendencias",
        meta_lines=[
            f"Videos pendentes: {total_pending}",
            f"Itens em atraso: {overdue_count}",
        ],
        badges=[
            {"label": "Fila obrigatoria", "variant": "warning"},
        ],
        footer="Pendencias permanecem visiveis ate a confirmacao manual do colaborador.",
    )
