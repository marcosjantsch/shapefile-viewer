from __future__ import annotations

import streamlit as st

from src.utils.formatters import format_cnpj, format_phone


def render_company_table(companies: list[dict], action_prefix: str, allow_toggle: bool = True) -> tuple[str, str] | None:
    if not companies:
        st.info("Nenhuma empresa encontrada no filtro atual.")
        return None

    st.dataframe(
        [
            {
                "Nome fantasia": company.get("nome_fantasia", "-"),
                "Razao social": company.get("razao_social", "-"),
                "CNPJ": format_cnpj(company.get("cnpj")),
                "Responsavel": company.get("nome_responsavel", "-"),
                "Telefone": format_phone(company.get("telefone")),
                "E-mail": company.get("email", "-"),
                "Cidade": company.get("cidade", "-"),
                "UF": company.get("uf", "-"),
                "Status": "Ativa" if company.get("status_ativo", True) else "Inativa",
            }
            for company in companies
        ],
        use_container_width=True,
        hide_index=True,
    )

    selected_company_id = st.selectbox(
        "Selecionar empresa",
        options=[""] + [str(company.get("id")) for company in companies],
        format_func=lambda item: "Selecione" if not item else next(
            (
                f"{company.get('nome_fantasia', item)} | {format_cnpj(company.get('cnpj'))}"
                for company in companies
                if str(company.get("id")) == str(item)
            ),
            str(item),
        ),
        key=f"{action_prefix}-selector",
    )
    if not selected_company_id:
        return None

    if allow_toggle:
        col_edit, col_toggle = st.columns(2)
        with col_edit:
            if st.button("Editar", key=f"{action_prefix}-edit", use_container_width=True):
                return ("edit", selected_company_id)
        with col_toggle:
            selected_company = next((company for company in companies if str(company.get("id")) == str(selected_company_id)), {})
            toggle_label = "Inativar" if selected_company.get("status_ativo", True) else "Ativar"
            if st.button(toggle_label, key=f"{action_prefix}-toggle", use_container_width=True):
                return ("toggle", selected_company_id)
        return None

    if st.button("Editar", key=f"{action_prefix}-edit", use_container_width=True):
        return ("edit", selected_company_id)
    return None
