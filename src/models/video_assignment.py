from __future__ import annotations

from dataclasses import dataclass

from src.models.base import BaseModel


@dataclass(slots=True)
class VideoAssignment(BaseModel):
    id: str
    empresa_id: str
    funcionario_id: str
    video_id: str
    origem_video: str
    data_referencia: str
    status: str = "pending"
    data_visualizacao: str = ""
    confirmado_manual: bool = False
    percentual_visualizado_future: float | None = None
    criado_em: str = ""
    atualizado_em: str = ""
