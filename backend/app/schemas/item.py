from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class ItemCreate(BaseModel):
    ordem: int = 0
    quantidade: Decimal
    unidade: str


class ItemUpdate(BaseModel):
    ordem: Optional[int] = None
    quantidade: Optional[Decimal] = None
    unidade: Optional[str] = None
    etiqueta_revisao: Optional[bool] = None


class ItemOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    grupo_id: int
    ordem: int
    composicao_id: Optional[int] = None
    quantidade: Decimal
    unidade: str
    preco_unitario_sem_bdi: Optional[Decimal] = None
    preco_unitario_com_bdi: Optional[Decimal] = None
    total: Decimal
    etiqueta_revisao: bool
    requer_revisao: bool
