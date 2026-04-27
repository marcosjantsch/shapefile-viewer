from __future__ import annotations

from dataclasses import dataclass

from src.models.base import BaseModel


@dataclass(slots=True)
class SafetyImage(BaseModel):
    id: str
    empresa_id: str | None
    titulo: str
    descricao: str
    url_imagem_ou_arquivo: str
    status_publicado: bool = False
    data_criacao: str = ""
