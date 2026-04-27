from __future__ import annotations

import streamlit as st

from src.utils.formatters import resolve_date_input_value


def render_assignment_form(
    initial_data: dict | None,
    companies: list[dict],
    employees: list[dict],
    video_options: dict[str, list[dict]],
    form_key: str,
    fixed_company_id: str = "",
) -> tuple[bool, dict]:
    initial = initial_data or {}
    company_lookup = {company["id"]: company["nome_fantasia"] for company in companies}
    company_ids = list(company_lookup.keys())
    selected_company = fixed_company_id or initial.get("empresa_id") or (company_ids[0] if company_ids else "")

    employees_for_company = [item for item in employees if str(item.get("empresa_id")) == str(selected_company)]
    employee_lookup = {item["id"]: item["nome_completo"] for item in employees_for_company}
    employee_ids = list(employee_lookup.keys())

    origin_options = ["platform", "company"]
    selected_origin = initial.get("origem_video") or "platform"
    videos_for_origin = video_options.get(selected_origin, [])
    video_lookup = {item["id"]: item["titulo"] for item in videos_for_origin}
    video_ids = list(video_lookup.keys())

    with st.form(form_key, clear_on_submit=False):
        st.markdown("### Atribuicao diaria")
        if fixed_company_id:
            st.info(f"Empresa vinculada: {company_lookup.get(fixed_company_id, '-')}")
        else:
            selected_company = st.selectbox(
                "Empresa",
                options=company_ids,
                index=company_ids.index(selected_company) if selected_company in company_ids else 0,
                format_func=lambda item: company_lookup.get(item, item),
            ) if company_ids else ""

        funcionario_id = st.selectbox(
            "Funcionario",
            options=employee_ids,
            index=employee_ids.index(initial.get("funcionario_id")) if initial.get("funcionario_id") in employee_ids else 0,
            format_func=lambda item: employee_lookup.get(item, item),
        ) if employee_ids else ""

        origem_video = st.selectbox(
            "Origem do video",
            options=origin_options,
            index=origin_options.index(selected_origin) if selected_origin in origin_options else 0,
            format_func=lambda item: "Biblioteca da plataforma" if item == "platform" else "Biblioteca da empresa",
        )

        videos_for_origin = video_options.get(origem_video, [])
        video_lookup = {item["id"]: item["titulo"] for item in videos_for_origin}
        video_ids = list(video_lookup.keys())
        video_id = st.selectbox(
            "Video",
            options=video_ids,
            index=video_ids.index(initial.get("video_id")) if initial.get("video_id") in video_ids else 0,
            format_func=lambda item: video_lookup.get(item, item),
        ) if video_ids else ""

        data_referencia = st.date_input(
            "Data de referencia",
            value=resolve_date_input_value(initial.get("data_referencia")),
            format="DD/MM/YYYY",
        )
        submitted = st.form_submit_button("Salvar atribuicao", use_container_width=True)

    payload = {
        "empresa_id": selected_company,
        "funcionario_id": funcionario_id,
        "origem_video": origem_video,
        "video_id": video_id,
        "data_referencia": getattr(data_referencia, "isoformat", lambda: "")(),
    }
    return submitted, payload
