from __future__ import annotations

import streamlit as st

from src.services.company_service import list_companies
from src.utils.permissions import is_company_admin

ACTIVE_COMPANY_KEY = "active_company_context_id"


def get_active_company_id(current_user: dict) -> str:
    companies = list_companies(current_user)
    company_ids = [str(company.get("id")) for company in companies if company.get("id")]
    default_company_id = str(current_user.get("company_id") or (company_ids[0] if company_ids else ""))

    if not is_company_admin(current_user):
        return default_company_id

    current_company_id = str(st.session_state.get(ACTIVE_COMPANY_KEY) or default_company_id)
    if current_company_id not in company_ids and company_ids:
        current_company_id = company_ids[0]
    st.session_state[ACTIVE_COMPANY_KEY] = current_company_id
    return current_company_id


def set_active_company_id(company_id: str) -> None:
    st.session_state[ACTIVE_COMPANY_KEY] = str(company_id or "")
