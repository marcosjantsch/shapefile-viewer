from __future__ import annotations

from dataclasses import dataclass

from src.models.base import BaseModel


@dataclass(slots=True)
class BillingRecord(BaseModel):
    id: str
    empresa_id: str
    descricao: str
    valor: float
    status: str = "pending"
    data_geracao: str = ""
    data_pagamento: str = ""
    observacoes: str = ""
