from __future__ import annotations

import streamlit as st

from src.components.cards.common import render_metric_cards
from src.components.forms.company_form import render_company_form
from src.components.tables.company_table import render_company_table
from src.services.company_service import get_company, list_companies, save_company, toggle_company_status
from src.shared.ui import render_feedback, render_page_intro
from src.utils.permissions import is_platform_admin


def render_page(current_user: dict) -> None:
    render_page_intro(
        "Empresas",
        "Cadastro, consulta e controle de status com isolamento por perfil.",
        kicker="Modulo 02",
    )
    st.session_state.setdefault("companies_edit_id", None)

    search = st.text_input("Buscar empresa", key="companies-search")
    status_filter = st.selectbox(
        "Status",
        options=["all", "active", "inactive"],
        format_func=lambda item: {"all": "Todas", "active": "Ativas", "inactive": "Inativas"}[item],
    )
    companies = list_companies(current_user, search=search, status_filter=status_filter)
    active_count = sum(1 for company in companies if company.get("status_ativo", True))
    render_metric_cards(
        [
            {"label": "Empresas visiveis", "value": len(companies), "help": "Resultado apos filtros aplicados."},
            {"label": "Ativas", "value": active_count, "help": "Disponiveis para operacao."},
            {"label": "Inativas", "value": len(companies) - active_count, "help": "Bloqueadas para novos acessos."},
            {
                "label": "Escopo",
                "value": "Global" if is_platform_admin(current_user) else "Minha empresa",
                "help": "Permissao aplicada na camada de servico.",
            },
        ]
    )

    left, right = st.columns([0.42, 0.58], gap="large")

    with left:
        editing_id = st.session_state.get("companies_edit_id")
        if not is_platform_admin(current_user):
            editing_id = str(current_user.get("company_id"))
            st.session_state["companies_edit_id"] = editing_id
        elif st.button("Nova empresa", use_container_width=True, key="companies-new"):
            st.session_state["companies_edit_id"] = None
            st.rerun()
        initial_data = get_company(current_user, editing_id) if editing_id else {}
        submitted, payload = render_company_form(
            initial_data=initial_data,
            form_key="company-form",
            allow_status_edit=is_platform_admin(current_user),
        )
        if submitted:
            saved, errors = save_company(current_user, payload, company_id=editing_id)
            if errors:
                render_feedback(errors)
            elif saved:
                st.session_state["companies_edit_id"] = saved["id"]
                st.success("Empresa salva com sucesso.")
                st.rerun()

    with right:
        action = render_company_table(
            companies,
            action_prefix="companies-table",
            allow_toggle=is_platform_admin(current_user),
        )
        if action:
            verb, company_id = action
            if verb == "edit":
                st.session_state["companies_edit_id"] = company_id
                st.rerun()
            if verb == "toggle":
                toggle_company_status(current_user, company_id)
                st.success("Status da empresa atualizado.")
                st.rerun()
