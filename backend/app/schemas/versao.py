from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class VersaoOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    obra_id: int
    numero: int
    nome: Optional[str] = None
    criada_em: datetime
    criada_por: Optional[int] = None
    bloqueada: bool
    total_sem_bdi: Decimal
    total_com_bdi: Decimal
    deletada_em: Optional[datetime] = None
