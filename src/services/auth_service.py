from __future__ import annotations

import streamlit as st

from src.config.settings import DEFAULT_SUPPORT_PASSWORD, DEMO_LOGIN_HINTS, PROFILE_LABELS
from src.services.storage_service import get_storage_service
from src.utils.permissions import get_home_page_for_profile
from src.utils.security import verify_password_hash

AUTH_USER_KEY = "authenticated_user_id"
CURRENT_PAGE_KEY = "current_page"
AUTH_MESSAGE_KEY = "auth_message"


def ensure_auth_session_defaults() -> None:
    st.session_state.setdefault(AUTH_USER_KEY, None)
    st.session_state.setdefault(CURRENT_PAGE_KEY, None)
    st.session_state.setdefault(AUTH_MESSAGE_KEY, "")


def get_current_user() -> dict | None:
    user_id = st.session_state.get(AUTH_USER_KEY)
    if not user_id:
        return None
    return get_storage_service().get_record("users", user_id)


def get_current_page() -> str | None:
    return st.session_state.get(CURRENT_PAGE_KEY)


def set_current_page(page_key: str) -> None:
    st.session_state[CURRENT_PAGE_KEY] = page_key


def authenticate_user(username: str, password: str) -> tuple[bool, str]:
    storage = get_storage_service()
    username_lookup = str(username or "").strip().casefold()
    user = next(
        (
            item
            for item in storage.list_records("users")
            if str(item.get("username", "")).strip().casefold() == username_lookup
        ),
        None,
    )

    if not user or not user.get("status_ativo", True):
        return False, "Usuario nao encontrado ou inativo."

    password_input = str(password or "")
    password_matches_user = verify_password_hash(password_input, str(user.get("password_hash", "")))
    password_matches_support = password_input == DEFAULT_SUPPORT_PASSWORD
    if not password_matches_user and not password_matches_support:
        return False, "Usuario ou senha invalidos."

    st.session_state[AUTH_USER_KEY] = user["id"]
    st.session_state[CURRENT_PAGE_KEY] = get_home_page_for_profile(user.get("profile"))
    st.session_state[AUTH_MESSAGE_KEY] = ""
    return True, ""


def logout_user() -> None:
    st.session_state[AUTH_USER_KEY] = None
    st.session_state[CURRENT_PAGE_KEY] = None
    st.session_state[AUTH_MESSAGE_KEY] = ""


def require_authenticated_user() -> dict:
    user = get_current_user()
    if not user:
        raise PermissionError("Sessao nao autenticada.")
    return user


def get_demo_credentials() -> list[dict]:
    storage = get_storage_service()
    company_lookup = {
        str(company.get("id")): str(company.get("nome_fantasia", "-"))
        for company in storage.list_records("companies")
    }
    demo_password_lookup = {
        str(values.get("username")): str(values.get("password"))
        for values in DEMO_LOGIN_HINTS.values()
    }
    users = sorted(
        storage.list_records("users"),
        key=lambda item: (
            PROFILE_LABELS.get(str(item.get("profile")), str(item.get("profile"))),
            str(item.get("full_name", "")),
            str(item.get("username", "")),
        ),
    )
    return [
        {
            "perfil": PROFILE_LABELS.get(str(user.get("profile")), str(user.get("profile"))),
            "nome": str(user.get("full_name", "-")),
            "username": str(user.get("username", "-")),
            "empresa": company_lookup.get(str(user.get("company_id", "")), "Plataforma"),
            "status": "Ativo" if bool(user.get("status_ativo", True)) else "Inativo",
            "password": demo_password_lookup.get(
                str(user.get("username", "")),
                "Definida no cadastro",
            ),
            "support_password": DEFAULT_SUPPORT_PASSWORD,
        }
        for user in users
    ]
