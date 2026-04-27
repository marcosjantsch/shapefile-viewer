from __future__ import annotations

import uuid
from datetime import date, datetime

from src.models.billing_record import BillingRecord
from src.services.storage_service import get_storage_service
from src.utils.permissions import can_access_billing, ensure_permission, is_company_admin
from src.utils.validators import validate_required


def _timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def list_billing_records(current_user: dict, company_id: str = "", status_filter: str = "all") -> list[dict]:
    records = get_storage_service().list_records("billing_records")
    if is_company_admin(current_user):
        company_id = str(current_user.get("company_id"))

    if company_id:
        records = [item for item in records if str(item.get("empresa_id")) == str(company_id)]

    filtered = [item for item in records if can_access_billing(current_user, item.get("empresa_id"))]
    if status_filter != "all":
        filtered = [item for item in filtered if str(item.get("status")) == str(status_filter)]
    return sorted(filtered, key=lambda item: str(item.get("data_geracao", "")), reverse=True)


def save_billing_record(current_user: dict, payload: dict, record_id: str | None = None) -> tuple[dict | None, list[str]]:
    storage = get_storage_service()
    existing = storage.get_record("billing_records", record_id) if record_id else None
    company_id = str(payload.get("empresa_id") or (existing or {}).get("empresa_id") or "")
    if is_company_admin(current_user):
        company_id = str(current_user.get("company_id"))

    ensure_permission(can_access_billing(current_user, company_id), "Acesso negado a cobranca desta empresa.")
    errors = [
        error
        for error in [
            validate_required(company_id, "Empresa"),
            validate_required(payload.get("descricao"), "Descricao"),
            validate_required(payload.get("valor"), "Valor"),
        ]
        if error
    ]
    if errors:
        return None, errors

    timestamp = _timestamp()
    record = BillingRecord(
        id=(existing or {}).get("id") or f"billing-{uuid.uuid4().hex[:10]}",
        empresa_id=company_id,
        descricao=str(payload.get("descricao", "")).strip(),
        valor=float(payload.get("valor") or 0),
        status=str((existing or {}).get("status") or payload.get("status") or "pending"),
        data_geracao=str(payload.get("data_geracao") or (existing or {}).get("data_geracao") or date.today().isoformat()),
        data_pagamento=str((existing or {}).get("data_pagamento") or payload.get("data_pagamento") or ""),
        observacoes=str(payload.get("observacoes", "")).strip(),
    )
    saved = storage.upsert_record("billing_records", record.to_dict(), record_id=record.id)
    return saved, []


def simulate_payment(current_user: dict, record_id: str) -> dict:
    storage = get_storage_service()
    record = storage.get_record("billing_records", record_id)
    ensure_permission(record is not None, "Cobranca nao encontrada.")
    ensure_permission(can_access_billing(current_user, record.get("empresa_id")), "Acesso negado a cobranca selecionada.")
    record["status"] = "paid"
    record["data_pagamento"] = date.today().isoformat()
    record["observacoes"] = f"{str(record.get('observacoes', '')).strip()} Pagamento simulado em ambiente demo.".strip()
    return storage.upsert_record("billing_records", record, record_id=record["id"])
