from typing import Optional
from pydantic import BaseModel


class AlertaOut(BaseModel):
    tipo: str        # contrato_vencido | contrato_vencendo | desvio_orcamento
                     # | medicao_atrasada | item_revisao
    severidade: str  # alta | media | baixa
    obra_id: int
    obra_nome: str
    titulo: str
    detalhe: Optional[str] = None
    link: str
