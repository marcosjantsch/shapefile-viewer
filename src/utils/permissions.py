from __future__ import annotations

from src.config.settings import COMPANY_ADMIN, EMPLOYEE, PLATFORM_ADMIN

PAGE_ACCESS_RULES = {
    "dashboard_platform_admin": {PLATFORM_ADMIN},
    "dashboard_company_admin": set(),
    "dashboard_employee": {EMPLOYEE},
    "companies": {PLATFORM_ADMIN},
    "active_companies": {PLATFORM_ADMIN},
    "employees": {PLATFORM_ADMIN},
    "platform_videos": {PLATFORM_ADMIN, COMPANY_ADMIN},
    "company_videos": {PLATFORM_ADMIN, COMPANY_ADMIN},
    "video_admin": {PLATFORM_ADMIN, COMPANY_ADMIN},
    "assignments": {PLATFORM_ADMIN},
    "pending_videos": {EMPLOYEE},
    "billing_demo": set(),
}


def ensure_permission(condition: bool, message: str = "Voce nao tem permissao para esta acao.") -> None:
    if not condition:
        raise PermissionError(message)


def has_profile(user: dict | None, *profiles: str) -> bool:
    if not user:
        return False
    return str(user.get("profile")) in set(profiles)


def is_platform_admin(user: dict | None) -> bool:
    return has_profile(user, PLATFORM_ADMIN)


def is_company_admin(user: dict | None) -> bool:
    return has_profile(user, COMPANY_ADMIN)


def is_employee(user: dict | None) -> bool:
    return has_profile(user, EMPLOYEE)


def can_manage_all_companies(user: dict | None) -> bool:
    return is_platform_admin(user)


def can_access_company(user: dict | None, company_id: str | None) -> bool:
    if is_platform_admin(user):
        return True
    if is_company_admin(user):
        return True
    if not user or not company_id:
        return False
    return str(user.get("company_id") or "") == str(company_id)


def can_manage_company_record(user: dict | None, company_id: str | None) -> bool:
    if is_platform_admin(user):
        return True
    if is_company_admin(user):
        return can_access_company(user, company_id)
    return False


def can_manage_employees(user: dict | None, company_id: str | None) -> bool:
    return can_manage_company_record(user, company_id)


def can_manage_platform_videos(user: dict | None) -> bool:
    return is_platform_admin(user) or is_company_admin(user)


def can_manage_company_videos(user: dict | None, company_id: str | None) -> bool:
    return can_manage_company_record(user, company_id)


def can_assign_videos(user: dict | None, company_id: str | None) -> bool:
    return can_manage_company_record(user, company_id)


def can_access_billing(user: dict | None, company_id: str | None) -> bool:
    return False


def can_view_employee(user: dict | None, employee: dict) -> bool:
    if is_platform_admin(user):
        return True
    if is_company_admin(user):
        return can_access_company(user, employee.get("empresa_id"))
    if is_employee(user):
        return str(user.get("employee_id")) == str(employee.get("id"))
    return False


def can_view_assignment(user: dict | None, assignment: dict) -> bool:
    if is_platform_admin(user):
        return True
    if is_company_admin(user):
        return can_access_company(user, assignment.get("empresa_id"))
    if is_employee(user):
        return str(user.get("employee_id")) == str(assignment.get("funcionario_id"))
    return False


def is_page_allowed(user: dict | None, page_key: str) -> bool:
    if not user:
        return False
    return str(user.get("profile")) in PAGE_ACCESS_RULES.get(page_key, set())


def get_home_page_for_profile(profile: str | None) -> str:
    if profile == PLATFORM_ADMIN:
        return "dashboard_platform_admin"
    if profile == COMPANY_ADMIN:
        return "video_admin"
    return "dashboard_employee"
