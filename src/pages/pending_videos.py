from __future__ import annotations

import streamlit as st

from src.components.cards.common import render_metric_cards
from src.components.tables.company_pending_table import render_company_pending_table
from src.components.tables.pending_video_table import render_pending_video_table
from src.components.video.video_player import render_video_player
from src.services.assignment_service import get_assignment, list_assignments, mark_assignment_as_watched
from src.shared.ui import render_empty_state, render_page_intro
from src.utils.permissions import is_employee


def _safe_get_assignment(current_user: dict, assignment_id: str | None) -> dict | None:
    if not assignment_id:
        return None
    try:
        return get_assignment(current_user, assignment_id)
    except PermissionError:
        st.session_state["pending_open_assignment"] = None
        st.warning("A inspecao selecionada nao esta mais disponivel para este perfil.")
        return None


def render_page(current_user: dict) -> None:
    render_page_intro(
        "Videos pendentes",
        "Fila dedicada de pendencias ate a confirmacao manual de visualizacao.",
        kicker="Modulo 10",
    )
    st.session_state.setdefault("pending_open_assignment", None)

    if is_employee(current_user):
        assignments = list_assignments(current_user, status_filter="pending")
        overdue_count = sum(1 for item in assignments if int(item.get("delay_days", 0)) > 0)
        render_metric_cards(
            [
                {"label": "Pendentes", "value": len(assignments), "help": "Fila individual do colaborador."},
                {"label": "Em atraso", "value": overdue_count, "help": "Itens de dias anteriores."},
                {"label": "Acao primaria", "value": "Concluir", "help": "Botao sempre visivel no player."},
                {"label": "Privacidade", "value": "Minha conta", "help": "Sem acesso a dados de terceiros."},
            ]
        )
        action = render_pending_video_table(assignments, action_prefix="employee-pending-table")
        if action:
            verb, assignment_id = action
            if verb == "open":
                st.session_state["pending_open_assignment"] = assignment_id
            if verb == "complete":
                mark_assignment_as_watched(current_user, assignment_id)
                st.session_state["pending_open_assignment"] = None
                st.success("Pendencia concluida com sucesso.")
                st.rerun()

        open_assignment_id = st.session_state.get("pending_open_assignment")
        if open_assignment_id:
            assignment = _safe_get_assignment(current_user, open_assignment_id)
            if assignment:
                st.markdown("### Reproducao selecionada")
                if render_video_player(assignment):
                    mark_assignment_as_watched(current_user, assignment["id"])
                    st.session_state["pending_open_assignment"] = None
                    st.success("Pendencia concluida com sucesso.")
                    st.rerun()
        elif not assignments:
            render_empty_state("Nenhuma pendencia aberta", "Seu historico foi atualizado e a fila esta limpa.")
    else:
        assignments = list_assignments(current_user, status_filter="pending")
        render_metric_cards(
            [
                {"label": "Pendencias da empresa", "value": len(assignments), "help": "Visao consolidada da operacao."},
                {"label": "Colaboradores afetados", "value": len({item.get('funcionario_id') for item in assignments}), "help": "Base do filtro atual."},
                {"label": "Inspecao", "value": "Permitida", "help": "Sem conclusao manual por esta tela."},
                {"label": "Escopo", "value": "Minha empresa", "help": "Isolamento estrito no servico."},
            ]
        )
        action = render_company_pending_table(assignments, action_prefix="company-pending-list")
        if action:
            _, assignment_id = action
            st.session_state["pending_open_assignment"] = assignment_id
        open_assignment_id = st.session_state.get("pending_open_assignment")
        if open_assignment_id:
            assignment = _safe_get_assignment(current_user, open_assignment_id)
            if assignment:
                st.markdown("### Inspecao do video")
                render_video_player(
                    assignment,
                    action_label="Marcar como conferido futuramente",
                    show_action=False,
                    compact=True,
                )
