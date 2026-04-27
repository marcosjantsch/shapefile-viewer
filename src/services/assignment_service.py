from __future__ import annotations

import uuid
from datetime import date, datetime
from pathlib import Path

from src.models.video_assignment import VideoAssignment
from src.services.storage_service import get_storage_service
from src.utils.formatters import parse_iso_date
from src.utils.permissions import can_assign_videos, can_view_assignment, ensure_permission, is_company_admin, is_employee
from src.utils.validators import validate_required


def _timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _resolve_video_lookup(storage) -> dict[tuple[str, str], dict]:
    lookup: dict[tuple[str, str], dict] = {}
    for video in storage.list_records("platform_videos"):
        lookup[("platform", str(video.get("id")))] = video
    for video in storage.list_records("company_videos"):
        lookup[("company", str(video.get("id")))] = video
    return lookup


def _is_video_available_today(video: dict) -> bool:
    if not bool(video.get("status_publicado", True)):
        return False

    today = date.today()
    display_type = str(video.get("tipo_exibicao") or "periodo")
    if display_type == "data_unica":
        display_date = parse_iso_date(video.get("data_exibicao") or video.get("data_inicio_vigencia"))
        return display_date == today

    start_date = parse_iso_date(video.get("data_inicio_vigencia") or video.get("data_disponibilizacao"))
    end_date = parse_iso_date(video.get("data_fim_vigencia"))
    if start_date and today < start_date:
        return False
    if end_date and today > end_date:
        return False
    return True


def _is_local_video_missing(video_url: str) -> bool:
    value = str(video_url or "").strip()
    if not value or "://" in value:
        return False
    return not Path(value).exists()


def _enrich_assignment(record: dict, storage, video_lookup: dict[tuple[str, str], dict]) -> dict:
    employees = {employee["id"]: employee for employee in storage.list_records("employees")}
    companies = {company["id"]: company for company in storage.list_records("companies")}
    video = video_lookup.get((str(record.get("origem_video")), str(record.get("video_id"))), {})
    reference_date = parse_iso_date(record.get("data_referencia"))
    delay_days = 0
    if reference_date and str(record.get("status")) == "pending":
        delay_days = max((date.today() - reference_date).days, 0)
    return {
        **record,
        "funcionario_nome": (employees.get(record.get("funcionario_id")) or {}).get("nome_completo", "-"),
        "empresa_nome": (companies.get(record.get("empresa_id")) or {}).get("nome_fantasia", "-"),
        "video_titulo": video.get("titulo", "Video nao encontrado"),
        "video_url": video.get("url_video_ou_arquivo", ""),
        "video_disponivel_hoje": _is_video_available_today(video) if video else False,
        "arquivo_video_ausente": _is_local_video_missing(video.get("url_video_ou_arquivo", "")) if video else False,
        "video_categoria": video.get("categoria", ""),
        "video_tema": video.get("tema", ""),
        "caminho_relativo_video": video.get("caminho_relativo_video", ""),
        "nome_arquivo_local": video.get("nome_arquivo_local", ""),
        "arquivo_tamanho_label": video.get("arquivo_tamanho_label", ""),
        "delay_days": delay_days,
    }


def list_assignments(
    current_user: dict,
    company_id: str = "",
    employee_id: str = "",
    status_filter: str = "all",
    reference_date: str = "",
) -> list[dict]:
    storage = get_storage_service()
    assignments = storage.list_records("video_assignments")

    if is_company_admin(current_user) and not company_id:
        company_id = str(current_user.get("company_id"))
    if is_employee(current_user):
        employee_id = str(current_user.get("employee_id"))

    if company_id:
        assignments = [item for item in assignments if str(item.get("empresa_id")) == str(company_id)]
    if employee_id:
        assignments = [item for item in assignments if str(item.get("funcionario_id")) == str(employee_id)]
    if status_filter != "all":
        assignments = [item for item in assignments if str(item.get("status")) == str(status_filter)]
    if reference_date:
        assignments = [item for item in assignments if str(item.get("data_referencia")) == str(reference_date)]

    video_lookup = _resolve_video_lookup(storage)
    enriched = [
        _enrich_assignment(item, storage=storage, video_lookup=video_lookup)
        for item in assignments
        if can_view_assignment(current_user, item)
    ]
    if is_employee(current_user) and status_filter == "pending":
        enriched = [item for item in enriched if bool(item.get("video_disponivel_hoje", True))]
    return sorted(
        enriched,
        key=lambda item: (str(item.get("status")) != "pending", str(item.get("data_referencia", ""))),
        reverse=True,
    )


def get_assignment(current_user: dict, assignment_id: str) -> dict:
    storage = get_storage_service()
    assignment = storage.get_record("video_assignments", assignment_id)
    ensure_permission(assignment is not None, "Vinculo de video nao encontrado.")
    ensure_permission(can_view_assignment(current_user, assignment), "Acesso negado ao vinculo selecionado.")
    return _enrich_assignment(assignment, storage, _resolve_video_lookup(storage))


def save_assignment(current_user: dict, payload: dict, assignment_id: str | None = None) -> tuple[dict | None, list[str]]:
    storage = get_storage_service()
    existing = storage.get_record("video_assignments", assignment_id) if assignment_id else None
    company_id = str(payload.get("empresa_id") or (existing or {}).get("empresa_id") or "")
    if is_company_admin(current_user) and not company_id:
        company_id = str(current_user.get("company_id"))

    ensure_permission(can_assign_videos(current_user, company_id), "Voce nao pode criar atribuicoes para esta empresa.")
    errors = [
        error
        for error in [
            validate_required(company_id, "Empresa"),
            validate_required(payload.get("funcionario_id"), "Funcionario"),
            validate_required(payload.get("video_id"), "Video"),
            validate_required(payload.get("origem_video"), "Origem do video"),
            validate_required(payload.get("data_referencia"), "Data de referencia"),
        ]
        if error
    ]
    if errors:
        return None, errors

    timestamp = _timestamp()
    assignment = VideoAssignment(
        id=(existing or {}).get("id") or f"assignment-{uuid.uuid4().hex[:10]}",
        empresa_id=company_id,
        funcionario_id=str(payload.get("funcionario_id", "")).strip(),
        video_id=str(payload.get("video_id", "")).strip(),
        origem_video=str(payload.get("origem_video", "")).strip(),
        data_referencia=str(payload.get("data_referencia", "")).strip(),
        status=str((existing or {}).get("status") or payload.get("status") or "pending"),
        data_visualizacao=str((existing or {}).get("data_visualizacao") or ""),
        confirmado_manual=bool((existing or {}).get("confirmado_manual", False)),
        percentual_visualizado_future=(existing or {}).get("percentual_visualizado_future"),
        criado_em=(existing or {}).get("criado_em", timestamp),
        atualizado_em=timestamp,
    )
    saved = storage.upsert_record("video_assignments", assignment.to_dict(), record_id=assignment.id)
    return saved, []


def mark_assignment_as_watched(current_user: dict, assignment_id: str) -> dict:
    storage = get_storage_service()
    assignment = storage.get_record("video_assignments", assignment_id)
    ensure_permission(assignment is not None, "Video atribuido nao encontrado.")
    ensure_permission(can_view_assignment(current_user, assignment), "Acesso negado ao video atribuido.")
    assignment["status"] = "completed"
    assignment["data_visualizacao"] = _timestamp()
    assignment["confirmado_manual"] = True
    assignment["atualizado_em"] = _timestamp()
    return storage.upsert_record("video_assignments", assignment, record_id=assignment["id"])


def build_video_options_for_company(current_user: dict, company_id: str) -> dict[str, list[dict]]:
    ensure_permission(can_assign_videos(current_user, company_id), "Acesso negado as opcoes de video.")
    storage = get_storage_service()
    platform_videos = [item for item in storage.list_records("platform_videos") if item.get("status_publicado", True)]
    company_videos = [
        item
        for item in storage.list_records("company_videos")
        if item.get("status_publicado", True) and str(item.get("empresa_id")) == str(company_id)
    ]
    return {"platform": platform_videos, "company": company_videos}
