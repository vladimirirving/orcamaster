from typing import Optional
from pydantic import BaseModel


class CronogramaLinhaOut(BaseModel):
    item_id: int
    descricao: str
    unidade: str
    quantidade: str
    total_sem_bdi: str
    distribuicao_json: dict[str, float]


class CronogramaOut(BaseModel):
    cronograma_inicio: Optional[str]
    cronograma_fim: Optional[str]
    linhas: list[CronogramaLinhaOut]


class CronogramaConfigIn(BaseModel):
    cronograma_inicio: str
    cronograma_fim: str


class CronogramaLinhaIn(BaseModel):
    distribuicao_json: dict[str, float]
