from datetime import date
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel


class RelatorioMedicaoGrupo(BaseModel):
    grupo_id: int
    grupo_nome: str
    planejado_pct: float
    realizado_pct: float
    desvio_pct: float
    valor_medido: Decimal
    valor_total: Decimal


class RelatorioMedicaoOut(BaseModel):
    versao_id: int
    ultima_medicao_id: Optional[int]
    periodo_fim: Optional[date]
    grupos: List[RelatorioMedicaoGrupo]


class ComparativoItem(BaseModel):
    status: Literal["novo", "removido", "alterado", "igual"]
    grupo_nome: str
    descricao: str
    unidade: str
    v1_preco_unit: Optional[Decimal]
    v2_preco_unit: Optional[Decimal]
    v1_quantidade: Optional[Decimal]
    v2_quantidade: Optional[Decimal]
    v1_total: Optional[Decimal]
    v2_total: Optional[Decimal]
    delta_total: Decimal


class ComparativoOut(BaseModel):
    obra_id: int
    v1_id: int
    v2_id: int
    v1_nome: str
    v2_nome: str
    v1_total: Decimal
    v2_total: Decimal
    delta_total: Decimal
    delta_pct: float
    qtd_novos: int
    qtd_removidos: int
    qtd_alterados: int
    itens: List[ComparativoItem]
