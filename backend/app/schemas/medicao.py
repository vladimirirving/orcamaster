import re
from datetime import date
from typing import Optional
from pydantic import BaseModel, ConfigDict, model_validator

_MES_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class MedicaoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    periodo_inicio: date
    periodo_fim: date
    linhas_json: dict[str, float]
    criada_por: Optional[int]


class MedicaoIn(BaseModel):
    mes: str

    @model_validator(mode="after")
    def validar_mes(self) -> "MedicaoIn":
        if not _MES_RE.match(self.mes):
            raise ValueError("mes deve estar no formato YYYY-MM com mês entre 01 e 12")
        return self


class MedicaoPatch(BaseModel):
    linhas_json: dict[str, float]
