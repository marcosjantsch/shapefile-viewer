from __future__ import annotations

import uuid
from datetime import datetime

from src.models.employee import Employee
from src.models.user import User
from src.services.storage_service import get_storage_service
from src.utils.permissions import can_manage_employees, can_view_employee, ensure_permission, is_company_admin
from src.utils.security import create_password_hash
from src.utils.validators import (
    validate_document,
    validate_email,
    validate_password_for_creation,
    validate_required,
)


def _timestamp() -> str:
    return datetime.now().isoformat(timespec="seconds")


def list_employees(
    current_user: dict,
    search: str = "",
    company_filter: str = "",
    status_filter: str = "all",
) -> list[dict]:
    storage = get_storage_service()
    employees = storage.list_records("employees")

    if is_company_admin(current_user):
        employees = [item for item in employees if str(item.get("empresa_id")) == str(current_user.get("company_id"))]

    if company_filter:
        employees = [item for item in employees if str(item.get("empresa_id")) == str(company_filter)]

    if status_filter != "all":
        expected = status_filter == "active"
        employees = [item for item in employees if bool(item.get("status_ativo", True)) == expected]

    search_text = str(search or "").strip().casefold()
    if search_text:
        employees = [
            item
            for item in employees
            if search_text in " ".join(
                [
                    str(item.get("nome_completo", "")),
                    str(item.get("matricula", "")),
                    str(item.get("funcao", "")),
                    str(item.get("cpf_ou_identificador", "")),
                    str(item.get("login", "")),
                ]
            ).casefold()
        ]

    company_lookup = {company["id"]: company for company in storage.list_records("companies")}
    enriched = []
    for employee in employees:
        if not can_view_employee(current_user, employee):
            continue
        employee_copy = dict(employee)
        employee_copy["empresa_nome"] = (company_lookup.get(employee.get("empresa_id")) or {}).get("nome_fantasia", "-")
        enriched.append(employee_copy)
    return sorted(enriched, key=lambda item: str(item.get("nome_completo", "")).casefold())


def get_employee(current_user: dict, employee_id: str) -> dict:
    employee = get_storage_service().get_record("employees", employee_id)
    ensure_permission(employee is not None, "Colaborador nao encontrado.")
    ensure_permission(can_view_employee(current_user, employee), "Acesso negado ao colaborador selecionado.")
    return employee


def save_employee(current_user: dict, payload: dict, employee_id: str | None = None) -> tuple[dict | None, list[str]]:
    storage = get_storage_service()
    existing = storage.get_record("employees", employee_id) if employee_id else None

    company_id = str(payload.get("empresa_id") or (existing or {}).get("empresa_id") or "")
    if is_company_admin(current_user):
        company_id = str(current_user.get("company_id"))

    ensure_permission(can_manage_employees(current_user, company_id), "Voce nao pode alterar colaboradores desta empresa.")

    errors = [
        error
        for error in [
            validate_required(company_id, "Empresa"),
            validate_required(payload.get("nome_completo"), "Nome completo"),
            validate_required(payload.get("matricula"), "Matricula"),
            validate_required(payload.get("funcao"), "Funcao"),
            validate_required(payload.get("login"), "Login"),
            validate_email(payload.get("email")),
            validate_document(payload.get("cpf_ou_identificador"), "CPF ou identificador"),
            None if existing else validate_password_for_creation(payload.get("senha")),
        ]
        if error
    ]
    if errors:
        return None, errors

    login = str(payload.get("login", "")).strip()
    conflicting_user = next(
        (
            user
            for user in storage.list_records("users")
            if str(user.get("username", "")).strip().casefold() == login.casefold()
            and str(user.get("employee_id") or "") != str(employee_id or "")
        ),
        None,
    )
    if conflicting_user:
        return None, ["Ja existe um usuario com este login."]

    timestamp = _timestamp()
    password_hash = existing.get("senha_hash") if existing else ""
    if payload.get("senha"):
        password_hash = create_password_hash(str(payload.get("senha")))

    employee = Employee(
        id=(existing or {}).get("id") or f"employee-{uuid.uuid4().hex[:10]}",
        empresa_id=company_id,
        nome_completo=str(payload.get("nome_completo", "")).strip(),
        matricula=str(payload.get("matricula", "")).strip(),
        cpf_ou_identificador=str(payload.get("cpf_ou_identificador", "")).strip(),
        funcao=str(payload.get("funcao", "")).strip(),
        email=str(payload.get("email", "")).strip(),
        telefone=str(payload.get("telefone", "")).strip(),
        login=login,
        senha_hash=password_hash,
        status_ativo=bool(payload.get("status_ativo", True)),
        data_admissao=str(payload.get("data_admissao", "")).strip(),
        observacoes=str(payload.get("observacoes", "")).strip(),
        data_criacao=(existing or {}).get("data_criacao", timestamp),
        data_atualizacao=timestamp,
    )
    saved_employee = storage.upsert_record("employees", employee.to_dict(), record_id=employee.id)

    existing_user = next(
        (user for user in storage.list_records("users") if str(user.get("employee_id")) == str(saved_employee["id"])),
        None,
    )
    user = User(
        id=(existing_user or {}).get("id") or f"user-employee-{uuid.uuid4().hex[:10]}",
        username=employee.login,
        password_hash=employee.senha_hash,
        profile="employee",
        full_name=employee.nome_completo,
        company_id=employee.empresa_id,
        employee_id=employee.id,
        status_ativo=employee.status_ativo,
        created_at=(existing_user or {}).get("created_at", timestamp),
        updated_at=timestamp,
    )
    storage.upsert_record("users", user.to_dict(), record_id=user.id)
    return saved_employee, []


def toggle_employee_status(current_user: dict, employee_id: str) -> dict:
    storage = get_storage_service()
    employee = get_employee(current_user, employee_id)
    ensure_permission(can_manage_employees(current_user, employee.get("empresa_id")), "Acesso negado ao colaborador.")

    employee["status_ativo"] = not bool(employee.get("status_ativo", True))
    employee["data_atualizacao"] = _timestamp()
    saved_employee = storage.upsert_record("employees", employee, record_id=employee["id"])

    linked_user = next(
        (user for user in storage.list_records("users") if str(user.get("employee_id")) == str(employee_id)),
        None,
    )
    if linked_user:
        linked_user["status_ativo"] = saved_employee["status_ativo"]
        linked_user["updated_at"] = _timestamp()
        storage.upsert_record("users", linked_user, record_id=linked_user["id"])
    return saved_employee
