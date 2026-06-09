from typing import Literal, List, Optional
from decimal import Decimal
from pydantic import BaseModel


class DashboardResumoItem(BaseModel):
    obra_id: int
    obra_nome: str
    versao_id: Optional[int]
    total_sem_bdi: Optional[str]
    total_com_bdi: Optional[str]       # novo
    estado: str                         # novo: "em_elaboracao" | "concluido" | "arquivado"
    tem_alertas: bool                   # novo: True se algum item tem requer_revisao=True
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
    total_com_bdi: Optional[str]       # novo
    planejado_pct_hoje: Optional[float]
    realizado_pct: Optional[float]
    desvio: Optional[float]
    status: Literal["adiantado", "no_prazo", "atrasado", "sem_dados"]
    curva_s: List[CurvaSPonto]


class GrupoDistribuicao(BaseModel):
    grupo_id: int
    grupo_nome: str
    total: Decimal
    participacao_pct: float


class DistribuicaoGruposOut(BaseModel):
    versao_id: Optional[int]
    total_versao: Decimal
    grupos: List[GrupoDistribuicao]
