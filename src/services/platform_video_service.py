from __future__ import annotations

from pathlib import Path
import uuid
from datetime import datetime

from src.models.platform_video import PlatformVideo
from src.services.local_video_service import build_managed_record_id, build_managed_video_path, sanitize_filename
from src.services.storage_service import get_storage_service
from src.utils.permissions import can_manage_platform_videos, ensure_permission
from src.utils.validators import validate_required


def _timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def list_platform_videos(
    current_user: dict,
    search: str = "",
    theme_filter: str = "",
    category_filter: str = "",
    status_filter: str = "all",
) -> list[dict]:
    videos = get_storage_service().list_records("platform_videos")

    if status_filter != "all":
        expected = status_filter == "published"
        videos = [item for item in videos if bool(item.get("status_publicado", True)) == expected]

    if theme_filter:
        videos = [item for item in videos if str(item.get("tema", "")).strip() == str(theme_filter).strip()]
    if category_filter:
        videos = [item for item in videos if str(item.get("categoria", "")).strip() == str(category_filter).strip()]

    search_text = str(search or "").strip().casefold()
    if search_text:
        videos = [
            item
            for item in videos
            if search_text in " ".join(
                [
                    str(item.get("titulo", "")),
                    str(item.get("descricao", "")),
                    str(item.get("tema", "")),
                    str(item.get("categoria", "")),
                ]
            ).casefold()
        ]
    return sorted(videos, key=lambda item: str(item.get("data_disponibilizacao", "")), reverse=True)


def get_platform_video(video_id: str) -> dict | None:
    return get_storage_service().get_record("platform_videos", video_id)


def _save_uploaded_video(uploaded_video, existing: dict | None = None) -> tuple[str, str, str, str, str]:
    preserve_relative_path = str((existing or {}).get("caminho_relativo_video", "")).strip()
    preferred_name = Path(preserve_relative_path).name if preserve_relative_path else sanitize_filename(getattr(uploaded_video, "name", "video.mp4"))
    target_path, relative_path = build_managed_video_path(
        "platform",
        preferred_name,
        preserve_relative_path=preserve_relative_path,
    )
    target_path.write_bytes(uploaded_video.getvalue())
    size_bytes = target_path.stat().st_size
    size_label = f"{(size_bytes / (1024 * 1024)):.1f} MB"
    record_id = build_managed_record_id("platform", relative_path)
    return str(target_path.resolve()), target_path.name, size_label, relative_path, record_id


def save_platform_video(current_user: dict, payload: dict, video_id: str | None = None) -> tuple[dict | None, list[str]]:
    ensure_permission(can_manage_platform_videos(current_user), "Somente a plataforma pode alterar a biblioteca global.")
    existing = get_platform_video(video_id) if video_id else None
    uploaded_video = payload.get("uploaded_video")
    raw_video_source = str(payload.get("url_video_ou_arquivo", "")).strip()
    existing_video_source = str((existing or {}).get("url_video_ou_arquivo", "")).strip()
    errors = [
        error
        for error in [
            validate_required(payload.get("titulo"), "Titulo"),
            validate_required(payload.get("tema"), "Tema"),
            validate_required(payload.get("categoria"), "Categoria"),
            None if (raw_video_source or uploaded_video is not None or existing_video_source) else "Informe uma URL de video ou carregue um arquivo.",
        ]
        if error
    ]
    if errors:
        return None, errors

    video_source = raw_video_source or existing_video_source
    local_file_name = str((existing or {}).get("nome_arquivo_local", "")).strip()
    local_size_label = str((existing or {}).get("arquivo_tamanho_label", "")).strip()
    relative_path = str((existing or {}).get("caminho_relativo_video", "")).strip()
    managed_record_id = str((existing or {}).get("id", "")).strip()
    is_managed_upload = bool((existing or {}).get("sincronizado_da_pasta"))
    if uploaded_video is not None:
        video_source, local_file_name, local_size_label, relative_path, managed_record_id = _save_uploaded_video(
            uploaded_video,
            existing=existing,
        )
        is_managed_upload = True
    elif is_managed_upload:
        video_source = existing_video_source

    timestamp = _timestamp()
    video = PlatformVideo(
        id=managed_record_id or f"platform-video-{uuid.uuid4().hex[:10]}",
        origem="platform",
        titulo=str(payload.get("titulo", "")).strip(),
        descricao=str(payload.get("descricao", "")).strip(),
        tema=str(payload.get("tema", "")).strip(),
        categoria=str(payload.get("categoria", "")).strip(),
        url_video_ou_arquivo=video_source,
        thumbnail=str(payload.get("thumbnail", "")).strip(),
        duracao=str(payload.get("duracao", "")).strip(),
        status_publicado=bool(payload.get("status_publicado", True)),
        data_disponibilizacao=str(payload.get("data_disponibilizacao", "")).strip(),
        tipo_exibicao=str(payload.get("tipo_exibicao") or "periodo").strip(),
        data_exibicao=str(payload.get("data_exibicao", "")).strip(),
        data_inicio_vigencia=str(payload.get("data_inicio_vigencia", "")).strip(),
        data_fim_vigencia=str(payload.get("data_fim_vigencia", "")).strip(),
        obrigatorio_por_padrao=bool(payload.get("obrigatorio_por_padrao", True)),
        criado_por=(existing or {}).get("criado_por") or str(current_user.get("username", "")),
        data_criacao=(existing or {}).get("data_criacao", timestamp),
        data_atualizacao=timestamp,
    )
    video_data = video.to_dict()
    if local_file_name:
        video_data["nome_arquivo_local"] = local_file_name
    if local_size_label:
        video_data["arquivo_tamanho_label"] = local_size_label
    if relative_path:
        video_data["caminho_relativo_video"] = relative_path
    if is_managed_upload:
        video_data["sincronizado_da_pasta"] = True
        video_data["arquivo_ausente"] = False
    saved = get_storage_service().upsert_record("platform_videos", video_data, record_id=video.id)
    return saved, []


def toggle_platform_video_status(current_user: dict, video_id: str) -> dict:
    ensure_permission(can_manage_platform_videos(current_user), "Somente a plataforma pode publicar videos globais.")
    storage = get_storage_service()
    video = storage.get_record("platform_videos", video_id)
    ensure_permission(video is not None, "Video global nao encontrado.")
    video["status_publicado"] = not bool(video.get("status_publicado", True))
    video["data_atualizacao"] = _timestamp()
    return storage.upsert_record("platform_videos", video, record_id=video["id"])
