from __future__ import annotations

import uuid
from datetime import datetime

from src.models.company import Company
from src.services.storage_service import get_storage_service
from src.utils.permissions import can_manage_all_companies, can_manage_company_record, ensure_permission, is_company_admin
from src.utils.validators import validate_cnpj, validate_email, validate_required


def _timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def list_companies(current_user: dict, search: str = "", status_filter: str = "all") -> list[dict]:
    records = get_storage_service().list_records("companies")
    if not can_manage_all_companies(current_user) and not is_company_admin(current_user):
        records = [record for record in records if str(record.get("id")) == str(current_user.get("company_id"))]

    if status_filter != "all":
        expected_status = status_filter == "active"
        records = [record for record in records if bool(record.get("status_ativo", True)) == expected_status]

    search_text = str(search or "").strip().casefold()
    if search_text:
        records = [
            record
            for record in records
            if search_text in " ".join(
                [
                    str(record.get("nome_fantasia", "")),
                    str(record.get("razao_social", "")),
                    str(record.get("cnpj", "")),
                    str(record.get("cidade", "")),
                    str(record.get("uf", "")),
                ]
            ).casefold()
        ]

    return sorted(records, key=lambda item: str(item.get("nome_fantasia", "")).casefold())


def get_company(current_user: dict, company_id: str) -> dict:
    company = get_storage_service().get_record("companies", company_id)
    ensure_permission(company is not None, "Empresa nao encontrada.")
    ensure_permission(can_manage_company_record(current_user, company_id), "Acesso negado para esta empresa.")
    return company


def save_company(current_user: dict, payload: dict, company_id: str | None = None) -> tuple[dict | None, list[str]]:
    storage = get_storage_service()
    existing = storage.get_record("companies", company_id) if company_id else None

    target_company_id = existing["id"] if existing else company_id
    if existing:
        ensure_permission(can_manage_company_record(current_user, existing["id"]), "Voce nao pode editar esta empresa.")
    else:
        ensure_permission(can_manage_all_companies(current_user), "Somente a plataforma pode cadastrar novas empresas.")

    errors = [
        error
        for error in [
            validate_required(payload.get("nome_fantasia"), "Nome fantasia"),
            validate_required(payload.get("razao_social"), "Razao social"),
            validate_required(payload.get("cnpj"), "CNPJ"),
            validate_required(payload.get("nome_responsavel"), "Responsavel"),
            validate_email(payload.get("email")),
            validate_cnpj(payload.get("cnpj")),
        ]
        if error
    ]
    if errors:
        return None, errors

    duplicate = next(
        (
            company
            for company in storage.list_records("companies")
            if str(company.get("cnpj")) == str(payload.get("cnpj"))
            and str(company.get("id")) != str(target_company_id or "")
        ),
        None,
    )
    if duplicate:
        return None, ["Ja existe uma empresa cadastrada com este CNPJ."]

    timestamp = _timestamp()
    company = Company(
        id=target_company_id or f"company-{uuid.uuid4().hex[:10]}",
        nome_fantasia=str(payload.get("nome_fantasia", "")).strip(),
        razao_social=str(payload.get("razao_social", "")).strip(),
        cnpj=str(payload.get("cnpj", "")).strip(),
        nome_responsavel=str(payload.get("nome_responsavel", "")).strip(),
        telefone=str(payload.get("telefone", "")).strip(),
        email=str(payload.get("email", "")).strip(),
        endereco=str(payload.get("endereco", "")).strip(),
        cidade=str(payload.get("cidade", "")).strip(),
        uf=str(payload.get("uf", "")).strip().upper(),
        status_ativo=bool(payload.get("status_ativo", True)),
        observacoes=str(payload.get("observacoes", "")).strip(),
        data_criacao=(existing or {}).get("data_criacao", timestamp),
        data_atualizacao=timestamp,
    )
    saved = storage.upsert_record("companies", company.to_dict(), record_id=company.id)
    return saved, []


def toggle_company_status(current_user: dict, company_id: str) -> dict:
    company = get_company(current_user, company_id)
    company["status_ativo"] = not bool(company.get("status_ativo", True))
    company["data_atualizacao"] = _timestamp()
    return get_storage_service().upsert_record("companies", company, record_id=company["id"])
