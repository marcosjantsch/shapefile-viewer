from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from src.config.settings import (
    ASSIGNMENT_STATUS_LABELS,
    BILLING_STATUS_LABELS,
    DATE_FORMAT,
    DATETIME_FORMAT,
    PROFILE_LABELS,
    VIDEO_ORIGIN_LABELS,
)


def safe_text(value: Any, fallback: str = "-") -> str:
    text = str(value or "").strip()
    return text if text else fallback


def parse_iso_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def parse_iso_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def resolve_date_input_value(value: str | date | None) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return parse_iso_date(value)


def format_date(value: str | date | None, fallback: str = "-") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        parsed = parse_iso_date(value)
        return parsed.strftime(DATE_FORMAT) if parsed else fallback
    return value.strftime(DATE_FORMAT)


def format_period(start_value: str | date | None, end_value: str | date | None) -> str:
    start_label = format_date(start_value, fallback="")
    end_label = format_date(end_value, fallback="")
    if start_label and end_label:
        return f"{start_label} a {end_label}"
    if start_label:
        return f"A partir de {start_label}"
    if end_label:
        return f"Ate {end_label}"
    return "Sem periodo"


def format_datetime(value: str | datetime | None, fallback: str = "-") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        parsed = parse_iso_datetime(value)
        return parsed.strftime(DATETIME_FORMAT) if parsed else fallback
    return value.strftime(DATETIME_FORMAT)


def format_currency(value: float | int | None) -> str:
    amount = float(value or 0)
    formatted = f"{amount:,.2f}"
    return f"R$ {formatted}".replace(",", "X").replace(".", ",").replace("X", ".")


def only_digits(value: str | None) -> str:
    return "".join(ch for ch in str(value or "") if ch.isdigit())


def format_cnpj(value: str | None) -> str:
    digits = only_digits(value)
    if len(digits) != 14:
        return safe_text(value)
    return f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"


def format_phone(value: str | None) -> str:
    digits = only_digits(value)
    if len(digits) == 11:
        return f"({digits[0:2]}) {digits[2:7]}-{digits[7:11]}"
    if len(digits) == 10:
        return f"({digits[0:2]}) {digits[2:6]}-{digits[6:10]}"
    return safe_text(value)


def format_profile(profile: str | None) -> str:
    return PROFILE_LABELS.get(str(profile or ""), safe_text(profile))


def format_origin(origin: str | None) -> str:
    return VIDEO_ORIGIN_LABELS.get(str(origin or ""), safe_text(origin))


def format_assignment_status(status: str | None) -> str:
    return ASSIGNMENT_STATUS_LABELS.get(str(status or ""), safe_text(status))


def format_billing_status(status: str | None) -> str:
    return BILLING_STATUS_LABELS.get(str(status or ""), safe_text(status))


def badge_variant_for_status(status: str | None) -> str:
    normalized = str(status or "").strip().casefold()
    if normalized in {"completed", "paid", "ativo", "published"}:
        return "success"
    if normalized in {"pending", "inativo"}:
        return "warning"
    return "muted"


def format_video_source_label(video: dict | None) -> str:
    payload = video or {}
    local_name = str(payload.get("nome_arquivo_local") or "").strip()
    if local_name:
        size_label = str(payload.get("arquivo_tamanho_label") or "").strip()
        suffix = f" · {size_label}" if size_label else ""
        if str(payload.get("origem_armazenamento") or "").strip() == "gcs":
            bucket = str(payload.get("bucket_video") or "").strip()
            bucket_suffix = f" · bucket {bucket}" if bucket else ""
            return f"Google Storage: {local_name}{suffix}{bucket_suffix}"
        return f"Arquivo local: {local_name}{suffix}"

    raw_source = str(payload.get("url_video_ou_arquivo") or "").strip()
    if not raw_source:
        return "-"
    if raw_source.startswith("gs://"):
        return f"Google Storage: {Path(raw_source).name}"

    possible_path = Path(raw_source)
    if possible_path.suffix:
        return f"Arquivo local: {possible_path.name}"
    return raw_source
