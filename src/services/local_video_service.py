from __future__ import annotations

import copy
import hashlib
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path

from src.config.settings import GOOGLE_VIDEO_BUCKET, LOCAL_VIDEO_DIR_CANDIDATES, SUPPORTED_VIDEO_EXTENSIONS, VIDEO_LIBRARY_SOURCE

PUBLIC_FOLDER_ALIASES = {
    "public",
    "publico",
    "publicos",
    "video_publico",
    "videos_publicos",
    "videopublico",
    "videospublicos",
}
IGNORED_TOP_LEVEL_FOLDERS = {"uploads", "__pycache__"}
INVALID_WINDOWS_SEGMENT_CHARS = r'[<>:"/\\|?*]'


def _timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", str(value or ""))
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", ascii_text.casefold())


def _humanize_filename(file_stem: str) -> str:
    text = re.sub(r"[_\-]+", " ", str(file_stem or "")).strip()
    text = re.sub(r"\s+", " ", text)
    if not text:
        return "Video local"
    if text.isdigit():
        return f"Video demonstracao {text.zfill(2)}"
    return text.title()


def _build_stable_hash(value: str) -> str:
    return hashlib.sha1(str(value).encode("utf-8")).hexdigest()[:16]


def _build_sync_key(relative_path: str, size_bytes: int, modified_ns: int) -> str:
    raw_key = f"{relative_path}|{size_bytes}|{modified_ns}"
    return hashlib.sha1(raw_key.encode("utf-8")).hexdigest()[:16]


def sanitize_path_segment(value: str, fallback: str = "item") -> str:
    cleaned = re.sub(INVALID_WINDOWS_SEGMENT_CHARS, "_", str(value or "").strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned or fallback


def sanitize_filename(value: str, fallback: str = "video.mp4") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._ -]+", "_", str(value or "").strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return cleaned or fallback


def resolve_local_videos_dir() -> Path:
    for candidate in LOCAL_VIDEO_DIR_CANDIDATES:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return LOCAL_VIDEO_DIR_CANDIDATES[0]


def get_public_videos_dir() -> Path:
    directory = resolve_local_videos_dir() / "publicos"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_company_videos_dir(company_name: str) -> Path:
    directory = resolve_local_videos_dir() / sanitize_path_segment(company_name, fallback="Empresa")
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def build_managed_video_path(
    origin_type: str,
    filename: str,
    company_name: str = "",
    preserve_relative_path: str = "",
) -> tuple[Path, str]:
    if preserve_relative_path:
        relative_path = Path(str(preserve_relative_path).replace("\\", "/"))
        target_path = resolve_local_videos_dir() / relative_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        return target_path, relative_path.as_posix()

    safe_filename = sanitize_filename(filename)
    if origin_type == "platform":
        target_path = get_public_videos_dir() / safe_filename
        relative_path = Path("publicos") / safe_filename
        return target_path, relative_path.as_posix()

    company_directory = get_company_videos_dir(company_name)
    target_path = company_directory / safe_filename
    relative_path = Path(company_directory.name) / safe_filename
    return target_path, relative_path.as_posix()


def build_managed_record_id(origin_type: str, relative_path: str, company_id: str = "") -> str:
    stable_key = _build_stable_hash(relative_path)
    if origin_type == "platform":
        return f"platform-local-{stable_key}"
    return f"company-local-{company_id}-{stable_key}"


def _build_company_lookup(companies: list[dict] | None) -> dict[str, dict]:
    lookup: dict[str, dict] = {}
    for company in companies or []:
        for candidate in (
            company.get("id"),
            company.get("nome_fantasia"),
            company.get("razao_social"),
        ):
            normalized = _normalize_text(str(candidate or ""))
            if normalized:
                lookup[normalized] = company
    return lookup


def _classify_relative_path(relative_path: Path, company_lookup: dict[str, dict]) -> tuple[str | None, dict | None]:
    folder_parts = list(relative_path.parts[:-1])
    if not folder_parts:
        return "platform", None

    top_level = _normalize_text(folder_parts[0])
    if top_level in IGNORED_TOP_LEVEL_FOLDERS:
        return None, None
    if top_level in PUBLIC_FOLDER_ALIASES:
        return "platform", None
    if top_level in company_lookup:
        return "company", company_lookup[top_level]
    return None, None


def scan_local_video_files(companies: list[dict] | None = None) -> list[dict]:
    videos_dir = resolve_local_videos_dir()
    if not videos_dir.exists():
        return []

    company_lookup = _build_company_lookup(companies)
    files = [
        path
        for path in sorted(videos_dir.rglob("*"), key=lambda item: str(item.relative_to(videos_dir)).casefold())
        if path.is_file() and path.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS
    ]
    video_entries: list[dict] = []
    for index, path in enumerate(files, start=1):
        relative_path = path.relative_to(videos_dir)
        origin_type, company = _classify_relative_path(relative_path, company_lookup)
        if origin_type is None:
            continue

        stats = path.stat()
        relative_string = relative_path.as_posix()
        sync_key = _build_sync_key(relative_string, stats.st_size, stats.st_mtime_ns)
        stable_key = _build_stable_hash(relative_string)
        if origin_type == "platform":
            record_id = f"platform-local-{stable_key}"
            description = "Video publico sincronizado automaticamente da pasta local."
        else:
            company_id = str((company or {}).get("id", ""))
            record_id = f"company-local-{company_id}-{stable_key}"
            description = f"Video sincronizado automaticamente para a empresa {(company or {}).get('nome_fantasia', '-') }."

        video_entries.append(
            {
                "sequence": index,
                "origin_type": origin_type,
                "record_id": record_id,
                "stable_key": stable_key,
                "sync_key": sync_key,
                "match_key": f"{origin_type}|{str((company or {}).get('id', ''))}|{_normalize_text(relative_string)}",
                "file_name": path.name,
                "file_stem": path.stem,
                "relative_path": relative_string,
                "absolute_path": str(path.resolve()),
                "title": _humanize_filename(path.stem),
                "description": description,
                "tema": "DDS local",
                "categoria": "Arquivo local",
                "duracao": "Arquivo local",
                "data_disponibilizacao": date.today().isoformat(),
                "size_bytes": stats.st_size,
                "size_label": f"{(stats.st_size / (1024 * 1024)):.1f} MB",
                "empresa_id": str((company or {}).get("id", "")),
                "empresa_nome": str((company or {}).get("nome_fantasia", "")),
            }
        )
    return video_entries


def build_local_video_summary(companies: list[dict] | None = None) -> dict:
    files = scan_local_video_files(companies=companies)
    gcs_files = []
    if VIDEO_LIBRARY_SOURCE in {"gcs", "google", "bucket", "both"}:
        try:
            from src.services.gcs_video_service import scan_gcs_video_files

            gcs_files = scan_gcs_video_files(companies=companies)
        except Exception:
            gcs_files = []
    videos_dir = resolve_local_videos_dir()
    all_files = files + gcs_files
    public_count = sum(1 for file_info in all_files if file_info.get("origin_type") == "platform")
    company_count = sum(1 for file_info in all_files if file_info.get("origin_type") == "company")
    return {
        "count": len(all_files),
        "local_count": len(files),
        "gcs_count": len(gcs_files),
        "public_count": public_count,
        "company_count": company_count,
        "directory": str(videos_dir),
        "bucket": GOOGLE_VIDEO_BUCKET,
        "files": all_files,
    }


def _is_auto_synced(record: dict) -> bool:
    return bool(record.get("sincronizado_da_pasta"))


def _record_match_key(record: dict, collection: str) -> str:
    origin_type = "company" if collection == "company_videos" else "platform"
    company_id = str(record.get("empresa_id", "")) if origin_type == "company" else ""
    relative_path = str(record.get("caminho_relativo_video", "")).strip()
    if relative_path:
        return f"{origin_type}|{company_id}|{_normalize_text(relative_path)}"
    local_name = str(record.get("nome_arquivo_local", "")).strip()
    return f"{origin_type}|{company_id}|{_normalize_text(local_name)}"


def _sync_video_collection(data: dict, collection: str, files: list[dict], timestamp: str) -> list[dict]:
    records = data.setdefault(collection, [])
    manual_records = [copy.deepcopy(record) for record in records if not _is_auto_synced(record)]
    auto_records = [copy.deepcopy(record) for record in records if _is_auto_synced(record)]
    auto_lookup = {_record_match_key(record, collection): record for record in auto_records}

    synced_records: list[dict] = []
    active_ids: set[str] = set()
    for file_info in files:
        base_record = copy.deepcopy(auto_lookup.get(file_info["match_key"], {}))
        record_id = str(base_record.get("id") or file_info["record_id"])
        active_ids.add(record_id)
        base_record.update(
            {
                "id": record_id,
                "origem": "company" if collection == "company_videos" else "platform",
                "empresa_id": file_info.get("empresa_id", "") if collection == "company_videos" else base_record.get("empresa_id"),
                "titulo": base_record.get("titulo") or file_info["title"],
                "descricao": base_record.get("descricao") or file_info["description"],
                "tema": base_record.get("tema") or file_info["tema"],
                "categoria": base_record.get("categoria") or file_info["categoria"],
                "url_video_ou_arquivo": file_info["absolute_path"],
                "thumbnail": base_record.get("thumbnail", ""),
                "duracao": base_record.get("duracao") or file_info["duracao"],
                "status_publicado": True,
                "data_disponibilizacao": base_record.get("data_disponibilizacao") or file_info["data_disponibilizacao"],
                "tipo_exibicao": base_record.get("tipo_exibicao") or "periodo",
                "data_exibicao": base_record.get("data_exibicao", ""),
                "data_inicio_vigencia": base_record.get("data_inicio_vigencia") or file_info["data_disponibilizacao"],
                "data_fim_vigencia": base_record.get("data_fim_vigencia", ""),
                "obrigatorio_por_padrao": bool(base_record.get("obrigatorio_por_padrao", True)),
                "criado_por": base_record.get("criado_por", "sistema"),
                "data_criacao": base_record.get("data_criacao", timestamp),
                "data_atualizacao": timestamp,
                "sincronizado_da_pasta": True,
                "arquivo_ausente": False,
                "arquivo_sync_key": file_info["sync_key"],
                "caminho_relativo_video": file_info["relative_path"],
                "nome_arquivo_local": file_info["file_name"],
                "arquivo_tamanho_label": file_info["size_label"],
                "origem_armazenamento": file_info.get("storage_origin", "local"),
                "bucket_video": file_info.get("bucket_name", ""),
            }
        )
        synced_records.append(base_record)

    for stale_record in auto_records:
        if str(stale_record.get("id")) in active_ids:
            continue
        stale_copy = copy.deepcopy(stale_record)
        stale_copy["status_publicado"] = False
        stale_copy["arquivo_ausente"] = True
        stale_copy["data_atualizacao"] = timestamp
        synced_records.append(stale_copy)

    data[collection] = manual_records + synced_records
    return [record for record in synced_records if not bool(record.get("arquivo_ausente")) and bool(record.get("status_publicado", True))]


def _build_assignment_key(employee_id: str, origin_type: str, video_id: str, sync_key: str) -> str:
    return f"{employee_id}|{origin_type}|{video_id}|{sync_key}"


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


def _is_video_active_today(video: dict) -> bool:
    if not bool(video.get("status_publicado", True)):
        return False
    if not bool(video.get("obrigatorio_por_padrao", True)):
        return False

    today = date.today()
    if str(video.get("tipo_exibicao") or "periodo") == "data_unica":
        display_date = _parse_date(str(video.get("data_exibicao") or video.get("data_inicio_vigencia") or ""))
        return display_date == today

    start_date = _parse_date(str(video.get("data_inicio_vigencia") or video.get("data_disponibilizacao") or ""))
    end_date = _parse_date(str(video.get("data_fim_vigencia") or ""))
    if start_date and today < start_date:
        return False
    if end_date and today > end_date:
        return False
    return True


def _sync_automatic_assignments(
    data: dict,
    platform_videos: list[dict],
    company_videos: list[dict],
    timestamp: str,
) -> int:
    assignments = data.setdefault("video_assignments", [])
    active_company_ids = {
        str(company.get("id"))
        for company in data.get("companies", [])
        if bool(company.get("status_ativo", True))
    }
    active_employees = [
        employee
        for employee in data.get("employees", [])
        if bool(employee.get("status_ativo", True)) and str(employee.get("empresa_id")) in active_company_ids
    ]

    existing_keys = {
        _build_assignment_key(
            str(assignment.get("funcionario_id", "")),
            str(assignment.get("origem_video", "")),
            str(assignment.get("video_id", "")),
            str(assignment.get("arquivo_sync_key", "")),
        )
        for assignment in assignments
        if str(assignment.get("arquivo_sync_key", "")).strip()
    }

    created_count = 0
    reference_date = date.today().isoformat()

    def ensure_for_employee(employee: dict, video: dict, origin_type: str) -> None:
        nonlocal created_count
        sync_key = str(video.get("arquivo_sync_key", "")).strip()
        if not sync_key:
            return
        assignment_key = _build_assignment_key(str(employee.get("id")), origin_type, str(video.get("id")), sync_key)
        if assignment_key in existing_keys:
            return
        assignment_id = f"assignment-auto-{_build_stable_hash(assignment_key)}"
        assignments.append(
            {
                "id": assignment_id,
                "empresa_id": str(employee.get("empresa_id", "")),
                "funcionario_id": str(employee.get("id", "")),
                "video_id": str(video.get("id", "")),
                "origem_video": origin_type,
                "data_referencia": reference_date,
                "status": "pending",
                "data_visualizacao": "",
                "confirmado_manual": False,
                "percentual_visualizado_future": None,
                "criado_em": timestamp,
                "atualizado_em": timestamp,
                "gerado_automaticamente": True,
                "arquivo_sync_key": sync_key,
            }
        )
        existing_keys.add(assignment_key)
        created_count += 1

    for video in platform_videos:
        if not _is_video_active_today(video):
            continue
        for employee in active_employees:
            ensure_for_employee(employee, video, "platform")

    for video in company_videos:
        if not _is_video_active_today(video):
            continue
        company_id = str(video.get("empresa_id", ""))
        for employee in active_employees:
            if str(employee.get("empresa_id")) == company_id:
                ensure_for_employee(employee, video, "company")

    return created_count


def sync_local_folder_videos(data: dict) -> tuple[dict, bool]:
    files = []
    if VIDEO_LIBRARY_SOURCE in {"local", "both"}:
        files.extend(scan_local_video_files(companies=data.get("companies", [])))
    if VIDEO_LIBRARY_SOURCE in {"gcs", "google", "bucket", "both"}:
        try:
            from src.services.gcs_video_service import scan_gcs_video_files

            files.extend(scan_gcs_video_files(companies=data.get("companies", [])))
        except Exception:
            pass
    if not files:
        return data, False

    original_snapshot = copy.deepcopy(data)
    timestamp = _timestamp()
    platform_files = [file_info for file_info in files if file_info.get("origin_type") == "platform"]
    company_files = [file_info for file_info in files if file_info.get("origin_type") == "company"]

    active_platform_videos = _sync_video_collection(data, "platform_videos", platform_files, timestamp)
    active_company_videos = _sync_video_collection(data, "company_videos", company_files, timestamp)
    created_assignments = _sync_automatic_assignments(data, active_platform_videos, active_company_videos, timestamp)

    meta = data.setdefault("meta", {})
    meta["local_videos_last_sync"] = timestamp
    meta["local_videos_directory"] = str(resolve_local_videos_dir())
    meta["video_library_source"] = VIDEO_LIBRARY_SOURCE
    meta["local_videos_count"] = len([file_info for file_info in files if file_info.get("storage_origin", "local") == "local"])
    meta["gcs_videos_bucket"] = GOOGLE_VIDEO_BUCKET
    meta["gcs_videos_count"] = len([file_info for file_info in files if file_info.get("storage_origin") == "gcs"])
    meta["local_public_videos_count"] = len(platform_files)
    meta["local_company_videos_count"] = len(company_files)
    meta["local_auto_assignments_last_sync"] = created_assignments
    return data, original_snapshot != data
