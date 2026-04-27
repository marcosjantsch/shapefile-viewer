from __future__ import annotations

import streamlit as st

from src.utils.formatters import resolve_date_input_value


def render_company_video_form(
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
        st.markdown("### Biblioteca da empresa")
        if not fixed_company_id:
            selected_company = st.selectbox(
                "Empresa",
                options=company_ids,
                index=company_ids.index(selected_company) if selected_company in company_ids else 0,
                format_func=lambda item: company_lookup.get(item, item),
            ) if company_ids else ""
        titulo = st.text_input("Titulo", value=initial.get("titulo", ""))
        descricao = st.text_area("Descricao", value=initial.get("descricao", ""), height=90)
        col_tema, col_categoria = st.columns(2)
        with col_tema:
            tema = st.text_input("Tema", value=initial.get("tema", ""))
        with col_categoria:
            categoria = st.text_input("Categoria", value=initial.get("categoria", ""))
        url_video_ou_arquivo = st.text_input("URL do video ou arquivo", value=initial.get("url_video_ou_arquivo", ""))
        uploaded_video = st.file_uploader(
            "Ou carregue um video",
            type=["mp4", "mov", "m4v", "webm", "avi", "mkv"],
            accept_multiple_files=False,
            help="Nesta fase MVP, o arquivo enviado sera salvo localmente e usado no player.",
        )
        col_thumb, col_dur = st.columns(2)
        with col_thumb:
            thumbnail = st.text_input("Thumbnail", value=initial.get("thumbnail", ""))
        with col_dur:
            duracao = st.text_input("Duracao", value=initial.get("duracao", ""))
        data_disponibilizacao = st.date_input(
            "Data de disponibilizacao",
            value=resolve_date_input_value(initial.get("data_disponibilizacao")),
            format="DD/MM/YYYY",
        )
        status_publicado = st.toggle("Publicado", value=bool(initial.get("status_publicado", True)))
        obrigatorio_por_padrao = st.toggle(
            "Obrigatorio por padrao",
            value=bool(initial.get("obrigatorio_por_padrao", False)),
        )
        submitted = st.form_submit_button("Salvar video da empresa", use_container_width=True)

    payload = {
        "empresa_id": selected_company,
        "titulo": titulo,
        "descricao": descricao,
        "tema": tema,
        "categoria": categoria,
        "url_video_ou_arquivo": url_video_ou_arquivo,
        "uploaded_video": uploaded_video,
        "thumbnail": thumbnail,
        "duracao": duracao,
        "data_disponibilizacao": getattr(data_disponibilizacao, "isoformat", lambda: "")(),
        "status_publicado": status_publicado,
        "obrigatorio_por_padrao": obrigatorio_por_padrao,
    }
    return submitted, payload
