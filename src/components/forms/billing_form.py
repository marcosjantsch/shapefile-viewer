from __future__ import annotations

import streamlit as st


def render_billing_form(
    initial_data: dict | None,
    companies: list[dict],
    form_key: str,
    fixed_company_id: str = "",
) -> tuple[bool, dict]:
    initial = initial_data or {}
    company_lookup = {company["id"]: company["nome_fantasia"] for company in companies}
    company_ids = list(company_lookup.keys())
    selected_company = fixed_company_id or initial.get("empresa_id") or (company_ids[0] if company_ids else "")

    with st.form(form_key, clear_on_submit=False):
        st.markdown("### Registro demo de cobranca")
        if fixed_company_id:
            st.info(f"Empresa vinculada: {company_lookup.get(fixed_company_id, '-')}")
        else:
            selected_company = st.selectbox(
                "Empresa",
                options=company_ids,
                index=company_ids.index(selected_company) if selected_company in company_ids else 0,
                format_func=lambda item: company_lookup.get(item, item),
            ) if company_ids else ""
        descricao = st.text_input("Descricao", value=initial.get("descricao", ""))
        valor = st.number_input("Valor", min_value=0.0, step=10.0, value=float(initial.get("valor") or 0.0))
        observacoes = st.text_area("Observacoes", value=initial.get("observacoes", ""), height=90)
        submitted = st.form_submit_button("Salvar cobranca demo", use_container_width=True)

    payload = {
        "empresa_id": selected_company,
        "descricao": descricao,
        "valor": valor,
        "observacoes": observacoes,
    }
    return submitted, payload
