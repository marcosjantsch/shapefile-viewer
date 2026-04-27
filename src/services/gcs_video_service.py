from __future__ import annotations

import hashlib
from datetime import date, timedelta
from pathlib import Path

from src.config.settings import (
    FIREBASE_CREDENTIALS_PATH,
    GOOGLE_PROJECT_ID,
    GOOGLE_VIDEO_BUCKET,
    SUPPORTED_VIDEO_EXTENSIONS,
)


def _build_stable_hash(value: str) -> str:
    return hashlib.sha1(str(value).encode("utf-8")).hexdigest()[:16]


def _build_sync_key(blob_name: str, generation: str, updated: str, size: int) -> str:
    raw_key = f"gcs|{blob_name}|{generation}|{updated}|{size}"
    return hashlib.sha1(raw_key.encode("utf-8")).hexdigest()[:16]


def _humanize_filename(file_stem: str) -> str:
    text = str(file_stem or "").replace("_", " ").replace("-", " ").strip()
    return " ".join(text.split()).title() or "Video do bucket"


def _get_storage_client():
    from google.cloud import storage

    if FIREBASE_CREDENTIALS_PATH:
        return storage.Client.from_service_account_json(
            FIREBASE_CREDENTIALS_PATH,
            project=GOOGLE_PROJECT_ID or None,
        )
    return storage.Client(project=GOOGLE_PROJECT_ID or None)


def is_gcs_uri(value: str) -> bool:
    return str(value or "").strip().startswith("gs://")


def build_gcs_uri(bucket_name: str, blob_name: str) -> str:
    return f"gs://{bucket_name}/{str(blob_name).lstrip('/')}"


def parse_gcs_uri(value: str) -> tuple[str, str]:
    raw_value = str(value or "").strip()
    if not raw_value.startswith("gs://"):
        return "", ""
    path = raw_value[5:]
    if "/" not in path:
        return path, ""
    bucket_name, blob_name = path.split("/", 1)
    return bucket_name, blob_name


def resolve_gcs_video_url(value: str, expires_minutes: int = 360) -> str:
    bucket_name, blob_name = parse_gcs_uri(value)
    if not bucket_name or not blob_name:
        return str(value or "")

    client = _get_storage_client()
    blob = client.bucket(bucket_name).blob(blob_name)
    public_url = blob.public_url
    try:
        if blob.exists() and public_url:
            return public_url
    except Exception:
        pass
    try:
        return blob.generate_signed_url(
            expiration=timedelta(minutes=expires_minutes),
            method="GET",
            version="v4",
        )
    except Exception:
        return public_url


def scan_gcs_video_files(companies: list[dict] | None = None, bucket_name: str = "") -> list[dict]:
    resolved_bucket = str(bucket_name or GOOGLE_VIDEO_BUCKET or "").strip()
    if not resolved_bucket:
        return []

    try:
        client = _get_storage_client()
        blobs = client.list_blobs(resolved_bucket)
    except Exception:
        return []

    from src.services.local_video_service import (
        _build_company_lookup,
        _classify_relative_path,
        _normalize_text,
    )

    company_lookup = _build_company_lookup(companies)
    video_entries: list[dict] = []
    for index, blob in enumerate(blobs, start=1):
        blob_name = str(blob.name or "").strip()
        suffix = Path(blob_name).suffix.lower()
        if not blob_name or blob_name.endswith("/") or suffix not in SUPPORTED_VIDEO_EXTENSIONS:
            continue

        relative_path = Path(blob_name)
        origin_type, company = _classify_relative_path(relative_path, company_lookup)
        if origin_type is None:
            continue

        relative_string = relative_path.as_posix()
        generation = str(getattr(blob, "generation", "") or "")
        updated = str(getattr(blob, "updated", "") or "")
        size_bytes = int(getattr(blob, "size", 0) or 0)
        sync_key = _build_sync_key(relative_string, generation, updated, size_bytes)
        stable_key = _build_stable_hash(f"{resolved_bucket}/{relative_string}")
        gcs_uri = build_gcs_uri(resolved_bucket, relative_string)
        if origin_type == "platform":
            record_id = f"platform-gcs-{stable_key}"
            description = "Video publico sincronizado automaticamente do Google Cloud Storage."
        else:
            company_id = str((company or {}).get("id", ""))
            record_id = f"company-gcs-{company_id}-{stable_key}"
            description = f"Video sincronizado automaticamente do Google Cloud Storage para a empresa {(company or {}).get('nome_fantasia', '-') }."

        video_entries.append(
            {
                "sequence": index,
                "origin_type": origin_type,
                "record_id": record_id,
                "stable_key": stable_key,
                "sync_key": sync_key,
                "match_key": f"{origin_type}|{str((company or {}).get('id', ''))}|{_normalize_text(relative_string)}",
                "file_name": Path(blob_name).name,
                "file_stem": Path(blob_name).stem,
                "relative_path": relative_string,
                "absolute_path": gcs_uri,
                "storage_origin": "gcs",
                "bucket_name": resolved_bucket,
                "title": _humanize_filename(Path(blob_name).stem),
                "description": description,
                "tema": "DDS storage",
                "categoria": "Arquivo storage",
                "duracao": "Arquivo storage",
                "data_disponibilizacao": date.today().isoformat(),
                "size_bytes": size_bytes,
                "size_label": f"{(size_bytes / (1024 * 1024)):.1f} MB" if size_bytes else "-",
                "empresa_id": str((company or {}).get("id", "")),
                "empresa_nome": str((company or {}).get("nome_fantasia", "")),
            }
        )
    return video_entries
