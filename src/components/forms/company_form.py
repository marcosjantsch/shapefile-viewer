from __future__ import annotations

import streamlit as st


def render_company_form(initial_data: dict | None, form_key: str, allow_status_edit: bool = True) -> tuple[bool, dict]:
    initial = initial_data or {}
    with st.form(form_key, clear_on_submit=False):
        st.markdown("### Dados da empresa")
        nome_fantasia = st.text_input("Nome fantasia", value=initial.get("nome_fantasia", ""))
        razao_social = st.text_input("Razao social", value=initial.get("razao_social", ""))
        cnpj = st.text_input("CNPJ", value=initial.get("cnpj", ""))
        nome_responsavel = st.text_input("Responsavel", value=initial.get("nome_responsavel", ""))
        telefone = st.text_input("Telefone", value=initial.get("telefone", ""))
        email = st.text_input("E-mail", value=initial.get("email", ""))
        endereco = st.text_input("Endereco", value=initial.get("endereco", ""))
        col_city, col_uf = st.columns([0.72, 0.28])
        with col_city:
            cidade = st.text_input("Cidade", value=initial.get("cidade", ""))
        with col_uf:
            uf = st.text_input("UF", value=initial.get("uf", ""))
        status_ativo = st.toggle("Empresa ativa", value=bool(initial.get("status_ativo", True)), disabled=not allow_status_edit)
        observacoes = st.text_area("Observacoes", value=initial.get("observacoes", ""), height=100)
        submitted = st.form_submit_button("Salvar empresa", use_container_width=True)

    payload = {
        "nome_fantasia": nome_fantasia,
        "razao_social": razao_social,
        "cnpj": cnpj,
        "nome_responsavel": nome_responsavel,
        "telefone": telefone,
        "email": email,
        "endereco": endereco,
        "cidade": cidade,
        "uf": uf,
        "status_ativo": status_ativo,
        "observacoes": observacoes,
    }
    return submitted, payload
