from __future__ import annotations

from src.utils.formatters import parse_iso_date
from src.services.company_video_service import (
    get_company_video,
    list_company_videos,
    save_company_video,
    toggle_company_video_status,
)
from src.services.platform_video_service import (
    get_platform_video,
    list_platform_videos,
    save_platform_video,
    toggle_platform_video_status,
)
def list_managed_videos(
    current_user: dict,
    company_id: str = "",
    search: str = "",
    scope_filter: str = "all",
) -> list[dict]:
    videos: list[dict] = []

    include_platform = scope_filter in {"all", "platform"}
    include_company = scope_filter in {"all", "company"}

    if include_platform:
        platform_videos = list_platform_videos(current_user, search=search, status_filter="all")
        videos.extend(
            [
                {
                    **video,
                    "scope": "platform",
                    "scope_label": "Publico",
                    "destination_label": "Todas as empresas",
                }
                for video in platform_videos
            ]
        )

    if include_company:
        company_videos = list_company_videos(current_user, company_id=company_id, search=search, status_filter="all")
        videos.extend(
            [
                {
                    **video,
                    "scope": "company",
                    "scope_label": "Empresa",
                    "destination_label": video.get("empresa_nome", "-"),
                }
                for video in company_videos
            ]
        )

    return sorted(videos, key=lambda item: str(item.get("data_atualizacao") or item.get("data_disponibilizacao", "")), reverse=True)


def get_managed_video(current_user: dict, scope: str, video_id: str) -> dict:
    if scope == "platform":
        return get_platform_video(video_id) or {}
    return get_company_video(current_user, video_id)


def save_managed_video(
    current_user: dict,
    payload: dict,
    editing_scope: str = "",
    editing_id: str = "",
) -> tuple[dict | None, list[str], str]:
    normalized_payload = dict(payload)
    display_type = str(normalized_payload.get("tipo_exibicao") or "periodo")
    if display_type == "data_unica":
        display_date = str(normalized_payload.get("data_exibicao") or "").strip()
        if not display_date:
            return None, ["Informe a data unica de exibicao do video."], str(payload.get("scope") or "platform")
        normalized_payload["data_inicio_vigencia"] = display_date
        normalized_payload["data_fim_vigencia"] = display_date

    start_date = parse_iso_date(normalized_payload.get("data_inicio_vigencia"))
    end_date = parse_iso_date(normalized_payload.get("data_fim_vigencia"))
    if start_date and end_date and end_date < start_date:
        return None, ["A data final da campanha nao pode ser menor que a data inicial."], str(payload.get("scope") or "platform")

    scope = editing_scope or str(normalized_payload.get("scope") or "platform")
    if scope == "platform":
        saved, errors = save_platform_video(current_user, normalized_payload, video_id=editing_id or None)
        return saved, errors, "platform"
    company_ids = [str(company_id) for company_id in normalized_payload.get("company_ids", []) if str(company_id).strip()]
    if editing_id:
        saved, errors = save_company_video(current_user, normalized_payload, video_id=editing_id or None)
        return saved, errors, "company"
    if not company_ids:
        return None, ["Selecione ao menos uma empresa para esta campanha."], "company"

    first_saved = None
    for company_id in company_ids:
        company_payload = {**normalized_payload, "empresa_id": company_id}
        saved, errors = save_company_video(current_user, company_payload, video_id=None)
        if errors:
            return None, errors, "company"
        if not first_saved:
            first_saved = saved
    return first_saved, [], "company"


def toggle_managed_video_status(current_user: dict, scope: str, video_id: str) -> dict:
    if scope == "platform":
        return toggle_platform_video_status(current_user, video_id)
    return toggle_company_video_status(current_user, video_id)
