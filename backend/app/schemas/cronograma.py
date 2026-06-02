import re
from typing import Optional
from pydantic import BaseModel, model_validator

_MES_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


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

    @model_validator(mode="after")
    def validar_periodo(self) -> "CronogramaConfigIn":
        for campo, valor in [("cronograma_inicio", self.cronograma_inicio), ("cronograma_fim", self.cronograma_fim)]:
            if not _MES_RE.match(valor):
                raise ValueError(f"{campo} deve estar no formato YYYY-MM com mês entre 01 e 12")
        if self.cronograma_fim < self.cronograma_inicio:
            raise ValueError("cronograma_fim deve ser igual ou posterior a cronograma_inicio")
        return self


class CronogramaLinhaIn(BaseModel):
    distribuicao_json: dict[str, float]
