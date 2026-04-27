from __future__ import annotations

import streamlit as st

from src.components.forms.company_form import render_company_form
from src.services.company_service import get_company, list_companies, save_company
from src.shared.ui import render_feedback, render_page_intro
from src.utils.formatters import format_cnpj, format_phone


def _build_table_rows(companies: list[dict]) -> list[dict]:
    return [
        {
            "ID": company.get("id", ""),
            "Nome fantasia": company.get("nome_fantasia", "-"),
            "Razao social": company.get("razao_social", "-"),
            "CNPJ": format_cnpj(company.get("cnpj")),
            "Responsavel": company.get("nome_responsavel", "-"),
            "Telefone": format_phone(company.get("telefone")),
            "E-mail": company.get("email", "-"),
            "Cidade": company.get("cidade", "-"),
            "UF": company.get("uf", "-"),
            "Atualizacao": company.get("data_atualizacao", "-"),
        }
        for company in companies
    ]


def render_page(current_user: dict) -> None:
    render_page_intro(
        "Empresas ativas",
        "Tabela operacional com os dados das empresas ativas e acesso direto ao cadastro.",
        kicker="Cadastros",
    )
    st.session_state.setdefault("active_companies_edit_id", None)

    search = st.text_input("Buscar empresa ativa", key="active-companies-search")
    companies = list_companies(current_user, search=search, status_filter="active")
    if not companies:
        st.info("Nenhuma empresa ativa encontrada.")
        return

    rows = _build_table_rows(companies)
    event = st.dataframe(
        rows,
        use_container_width=True,
        hide_index=True,
        column_config={"ID": None},
        on_select="rerun",
        selection_mode="single-row",
        key="active-companies-table",
    )
    if isinstance(event, dict):
        selected_rows = event.get("selection", {}).get("rows", [])
    else:
        selected_rows = getattr(getattr(event, "selection", None), "rows", []) or []
    if selected_rows:
        selected_index = int(selected_rows[0])
        selected_company_id = str(rows[selected_index].get("ID", ""))
        if selected_company_id and selected_company_id != st.session_state.get("active_companies_edit_id"):
            st.session_state["active_companies_edit_id"] = selected_company_id
            st.rerun()

    editing_id = st.session_state.get("active_companies_edit_id") or str(companies[0].get("id", ""))
    company = get_company(current_user, editing_id)
    submitted, payload = render_company_form(
        initial_data=company,
        form_key="active-company-form",
        allow_status_edit=True,
    )
    if submitted:
        saved, errors = save_company(current_user, payload, company_id=editing_id)
        if errors:
            render_feedback(errors)
        elif saved:
            st.session_state["active_companies_edit_id"] = saved["id"]
            st.success("Cadastro da empresa atualizado.")
            st.rerun()
