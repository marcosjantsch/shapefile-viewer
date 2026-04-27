from __future__ import annotations

from dataclasses import dataclass

from src.models.base import BaseModel


@dataclass(slots=True)
class CompanyVideo(BaseModel):
    id: str
    empresa_id: str
    origem: str
    titulo: str
    descricao: str
    tema: str
    categoria: str
    url_video_ou_arquivo: str
    thumbnail: str
    duracao: str
    status_publicado: bool = True
    data_disponibilizacao: str = ""
    tipo_exibicao: str = "periodo"
    data_exibicao: str = ""
    data_inicio_vigencia: str = ""
    data_fim_vigencia: str = ""
    obrigatorio_por_padrao: bool = False
    criado_por: str = ""
    data_criacao: str = ""
    data_atualizacao: str = ""
