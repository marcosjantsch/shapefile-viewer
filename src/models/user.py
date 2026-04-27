from __future__ import annotations

from dataclasses import dataclass

from src.models.base import BaseModel


@dataclass(slots=True)
class User(BaseModel):
    id: str
    username: str
    password_hash: str
    profile: str
    full_name: str
    company_id: str | None = None
    employee_id: str | None = None
    status_ativo: bool = True
    created_at: str = ""
    updated_at: str = ""
