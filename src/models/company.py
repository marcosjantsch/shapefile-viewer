from __future__ import annotations

from dataclasses import dataclass

from src.models.base import BaseModel


@dataclass(slots=True)
class Company(BaseModel):
    id: str
    nome_fantasia: str
    razao_social: str
    cnpj: str
    nome_responsavel: str
    telefone: str
    email: str
    endereco: str
    cidade: str
    uf: str
    status_ativo: bool = True
    observacoes: str = ""
    data_criacao: str = ""
    data_atualizacao: str = ""
