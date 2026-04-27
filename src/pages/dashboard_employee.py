from __future__ import annotations

from datetime import date

import streamlit as st

from src.components.cards.common import render_metric_cards
from src.components.cards.history_card import render_history_card
from src.components.cards.pending_summary_card import render_pending_summary_card
from src.components.cards.today_video_card import render_today_video_card
from src.components.tables.pending_video_table import render_pending_video_table
from src.components.video.video_player import render_video_player
from src.services.assignment_service import list_assignments, mark_assignment_as_watched
from src.services.safety_image_service import get_future_ready_message
from src.shared.ui import render_empty_state, render_page_intro


def render_page(current_user: dict) -> None:
    render_page_intro(
        "Painel do colaborador",
        "Acesso rapido ao video do dia, pendencias abertas e historico individual.",
        kicker="Modulo 07",
    )
    st.session_state.setdefault("employee_dashboard_open_assignment", None)
    st.session_state.setdefault("today_date_cache", date.today().isoformat())

    pending_items = list_assignments(current_user, status_filter="pending")
    completed_items = list_assignments(current_user, status_filter="completed")
    today_items = [item for item in pending_items if item.get("data_referencia") == st.session_state.get("today_date_cache")]

    highlighted_assignment = today_items[0] if today_items else (pending_items[0] if pending_items else None)
    overdue_count = sum(1 for item in pending_items if int(item.get("delay_days", 0)) > 0)

    st.markdown("### Video obrigatorio em destaque")
    if highlighted_assignment:
        render_today_video_card(highlighted_assignment)
        if render_video_player(highlighted_assignment, compact=True):
            mark_assignment_as_watched(current_user, highlighted_assignment["id"])
            st.success("Video marcado como assistido.")
            st.rerun()
    else:
        render_empty_state("Nada atribuido para hoje", "Quando um novo video for vinculado ele aparecera automaticamente aqui.")

    render_metric_cards(
        [
            {"label": "Video de hoje", "value": "Disponivel" if highlighted_assignment else "Sem atribuicao", "help": "Mostrado automaticamente no topo."},
            {"label": "Pendentes", "value": len(pending_items), "help": "Itens ainda nao concluidos."},
            {"label": "Concluidos", "value": len(completed_items), "help": "Historico individual registrado."},
            {"label": "Atrasos", "value": overdue_count, "help": "Pendencias anteriores ainda visiveis."},
        ]
    )

    top_left, top_right = st.columns([0.64, 0.36], gap="large")
    with top_left:
        st.markdown("### Videos pendentes")
        action = render_pending_video_table(pending_items, action_prefix="employee-dashboard-pending")
        if action:
            verb, assignment_id = action
            st.session_state["employee_dashboard_open_assignment"] = assignment_id
            if verb == "complete":
                mark_assignment_as_watched(current_user, assignment_id)
                st.session_state["employee_dashboard_open_assignment"] = None
                st.success("Video marcado como assistido.")
                st.rerun()

        open_assignment_id = st.session_state.get("employee_dashboard_open_assignment")
        selected_assignment = next(
            (item for item in pending_items if str(item.get("id")) == str(open_assignment_id)),
            None,
        )
        if selected_assignment and selected_assignment.get("id") != (highlighted_assignment or {}).get("id"):
            if render_video_player(selected_assignment, compact=True):
                mark_assignment_as_watched(current_user, selected_assignment["id"])
                st.session_state["employee_dashboard_open_assignment"] = None
                st.success("Video marcado como assistido.")
                st.rerun()

    with top_right:
        render_pending_summary_card(total_pending=len(pending_items), overdue_count=overdue_count)
        st.markdown("#### Imagem tecnica diaria")
        st.info(get_future_ready_message())

    render_history_card(completed_items)
