from __future__ import annotations

import streamlit as st

from src.utils.formatters import resolve_date_input_value


def render_employee_form(
    initial_data: dict | None,
    companies: list[dict],
    form_key: str,
    fixed_company_id: str = "",
) -> tuple[bool, dict]:
    initial = initial_data or {}
    company_lookup = {company["id"]: company["nome_fantasia"] for company in companies}
    company_ids = list(company_lookup.keys())
    selected_company = fixed_company_id or initial.get("empresa_id") or (company_ids[0] if company_ids else "")
    if fixed_company_id:
        st.info(f"Empresa vinculada: {company_lookup.get(fixed_company_id, '-')}")
    with st.form(form_key, clear_on_submit=False):
        st.markdown("### Dados do colaborador")
        if not fixed_company_id:
            selected_company = st.selectbox(
                "Empresa",
                options=company_ids,
                index=company_ids.index(selected_company) if selected_company in company_ids else 0,
                format_func=lambda item: company_lookup.get(item, item),
            ) if company_ids else ""
        nome_completo = st.text_input("Nome completo", value=initial.get("nome_completo", ""))
        col_mat, col_funcao = st.columns(2)
        with col_mat:
            matricula = st.text_input("Matricula", value=initial.get("matricula", ""))
        with col_funcao:
            funcao = st.text_input("Funcao", value=initial.get("funcao", ""))
        cpf_ou_identificador = st.text_input(
            "CPF ou identificador",
            value=initial.get("cpf_ou_identificador", ""),
        )
        email = st.text_input("E-mail", value=initial.get("email", ""))
        telefone = st.text_input("Telefone", value=initial.get("telefone", ""))
        col_login, col_password = st.columns(2)
        with col_login:
            login = st.text_input("Login", value=initial.get("login", ""))
        with col_password:
            senha = st.text_input("Senha", value="", type="password")
        data_admissao = st.date_input(
            "Data de admissao",
            value=resolve_date_input_value(initial.get("data_admissao")),
            format="DD/MM/YYYY",
        )
        status_ativo = st.toggle("Colaborador ativo", value=bool(initial.get("status_ativo", True)))
        observacoes = st.text_area("Observacoes", value=initial.get("observacoes", ""), height=90)
        submitted = st.form_submit_button("Salvar colaborador", use_container_width=True)

    payload = {
        "empresa_id": selected_company,
        "nome_completo": nome_completo,
        "matricula": matricula,
        "cpf_ou_identificador": cpf_ou_identificador,
        "funcao": funcao,
        "email": email,
        "telefone": telefone,
        "login": login,
        "senha": senha,
        "status_ativo": status_ativo,
        "data_admissao": getattr(data_admissao, "isoformat", lambda: "")(),
        "observacoes": observacoes,
    }
    return submitted, payload
