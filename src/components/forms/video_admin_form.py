from __future__ import annotations

import streamlit as st

from src.utils.formatters import resolve_date_input_value
from src.utils.permissions import is_company_admin


def render_video_admin_form(
    current_user: dict,
    initial_data: dict | None,
    companies: list[dict],
    form_key: str,
) -> tuple[bool, dict]:
    initial = initial_data or {}
    company_lookup = {company["id"]: company["nome_fantasia"] for company in companies}
    company_ids = list(company_lookup.keys())
    initial_company_ids = [str(initial.get("empresa_id"))] if initial.get("empresa_id") else []
    default_all_companies = str(initial.get("scope") or "") == "platform"
    default_selected_companies = initial_company_ids or company_ids[:1]
    default_start = initial.get("data_inicio_vigencia") or initial.get("data_disponibilizacao")
    default_display_type = str(initial.get("tipo_exibicao") or "periodo")
    default_display_date = initial.get("data_exibicao") or default_start

    with st.form(form_key, clear_on_submit=False):
        st.markdown("### Cadastro do video")
        all_companies = st.checkbox(
            "Todas as empresas",
            value=default_all_companies,
            help="Quando marcado, o cadastro entra como video global da plataforma.",
        )
        selected_companies = []
        if not all_companies:
            selected_companies = st.multiselect(
                "Selecionar empresas",
                options=company_ids,
                default=[company_id for company_id in default_selected_companies if company_id in company_ids],
                format_func=lambda item: company_lookup.get(item, item),
                help="Voce pode selecionar uma ou varias empresas para a mesma campanha.",
            )
        elif is_company_admin(current_user):
            st.info("Este cadastro ficara disponivel para todas as empresas.")

        titulo = st.text_input("Titulo", value=initial.get("titulo", ""))
        descricao = st.text_area("Descricao", value=initial.get("descricao", ""), height=90)
        col_meta_1, col_meta_2 = st.columns(2)
        with col_meta_1:
            tema = st.text_input("Tema", value=initial.get("tema", ""))
        with col_meta_2:
            categoria = st.text_input("Categoria", value=initial.get("categoria", ""))

        uploaded_video = st.file_uploader(
            "Arquivo de video",
            type=["mp4", "mov", "m4v", "webm", "avi", "mkv"],
            accept_multiple_files=False,
            help="O sistema salva o arquivo na pasta publica ou na pasta da empresa conforme o destino escolhido.",
        )
        url_video_ou_arquivo = st.text_input(
            "URL externa opcional",
            value="" if initial.get("sincronizado_da_pasta") else initial.get("url_video_ou_arquivo", ""),
            help="Use apenas se quiser manter um video externo sem arquivo local.",
        )
        if initial.get("caminho_relativo_video"):
            st.caption(f"Arquivo atual: {initial.get('caminho_relativo_video')}")

        tipo_exibicao = st.radio(
            "Exibicao do video",
            options=["periodo", "data_unica"],
            index=1 if default_display_type == "data_unica" else 0,
            format_func=lambda item: "Periodo de exibicao" if item == "periodo" else "Apenas em uma data",
            horizontal=True,
        )
        data_exibicao = ""
        data_inicio_vigencia = ""
        data_fim_vigencia = ""
        if tipo_exibicao == "data_unica":
            data_exibicao = st.date_input(
                "Data unica de exibicao",
                value=resolve_date_input_value(default_display_date),
                format="DD/MM/YYYY",
            )
        else:
            col_periodo_1, col_periodo_2 = st.columns(2)
            with col_periodo_1:
                data_inicio_vigencia = st.date_input(
                    "Data inicial da campanha",
                    value=resolve_date_input_value(default_start),
                    format="DD/MM/YYYY",
                )
            with col_periodo_2:
                data_fim_vigencia = st.date_input(
                    "Data final da campanha",
                    value=resolve_date_input_value(initial.get("data_fim_vigencia")),
                    format="DD/MM/YYYY",
                )
        status_publicado = st.toggle("Publicado", value=bool(initial.get("status_publicado", True)))
        obrigatorio_por_padrao = st.toggle(
            "Obrigatorio por padrao",
            value=bool(initial.get("obrigatorio_por_padrao", True)),
        )
        data_disponibilizacao = st.date_input(
            "Data de disponibilizacao",
            value=resolve_date_input_value(initial.get("data_disponibilizacao") or default_start),
            format="DD/MM/YYYY",
        )
        submitted = st.form_submit_button("Salvar video", use_container_width=True)

    payload = {
        "scope": "platform" if all_companies else "company",
        "all_companies": all_companies,
        "company_ids": selected_companies,
        "empresa_id": selected_companies[0] if selected_companies else "",
        "titulo": titulo,
        "descricao": descricao,
        "tema": tema,
        "categoria": categoria,
        "uploaded_video": uploaded_video,
        "url_video_ou_arquivo": url_video_ou_arquivo,
        "thumbnail": "",
        "duracao": "",
        "data_disponibilizacao": getattr(data_disponibilizacao, "isoformat", lambda: "")(),
        "tipo_exibicao": tipo_exibicao,
        "data_exibicao": getattr(data_exibicao, "isoformat", lambda: "")(),
        "data_inicio_vigencia": getattr(data_inicio_vigencia, "isoformat", lambda: "")(),
        "data_fim_vigencia": getattr(data_fim_vigencia, "isoformat", lambda: "")(),
        "status_publicado": status_publicado,
        "obrigatorio_por_padrao": obrigatorio_por_padrao,
    }
    return submitted, payload
