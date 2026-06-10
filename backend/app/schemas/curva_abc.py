from typing import Literal
from pydantic import BaseModel


class CurvaAbcItem(BaseModel):
    rank: int
    grupo_nome: str
    descricao: str
    unidade: str
    quantidade: str
    total: str
    participacao_pct: float
    acumulado_pct: float
    faixa: Literal["A", "B", "C"]


class CurvaAbcData(BaseModel):
    total_versao: str
    itens: list[CurvaAbcItem]
