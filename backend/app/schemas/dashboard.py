from typing import Literal, Optional
from pydantic import BaseModel


class DashboardResumoItem(BaseModel):
    obra_id: int
    obra_nome: str
    versao_id: Optional[int]
    total_sem_bdi: Optional[str]
    planejado_pct_hoje: Optional[float]
    realizado_pct: Optional[float]
    desvio: Optional[float]
    status: Literal["adiantado", "no_prazo", "atrasado", "sem_dados"]


class CurvaSPonto(BaseModel):
    mes: str            # "2025-01"
    planejado_acum: float
    realizado_acum: Optional[float]


class ObraDashboardData(BaseModel):
    versao_id: Optional[int]
    total_sem_bdi: Optional[str]
    planejado_pct_hoje: Optional[float]
    realizado_pct: Optional[float]
    desvio: Optional[float]
    status: Literal["adiantado", "no_prazo", "atrasado", "sem_dados"]
    curva_s: list[CurvaSPonto]
