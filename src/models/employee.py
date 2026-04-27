from __future__ import annotations

from dataclasses import dataclass

from src.models.base import BaseModel


@dataclass(slots=True)
class Employee(BaseModel):
    id: str
    empresa_id: str
    nome_completo: str
    matricula: str
    cpf_ou_identificador: str
    funcao: str
    email: str
    telefone: str
    login: str
    senha_hash: str
    status_ativo: bool = True
    data_admissao: str = ""
    observacoes: str = ""
    data_criacao: str = ""
    data_atualizacao: str = ""
