from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel


class InsumoItemCreate(BaseModel):
    codigo: str
    descricao: str
    unidade: str
    tipo: str
    preco_nao_desonerado: Decimal
    preco_desonerado: Decimal
    estado: Optional[str] = None
    data_referencia: date


class InsumoItemUpdate(BaseModel):
    codigo: Optional[str] = None
    descricao: Optional[str] = None
    unidade: Optional[str] = None
    tipo: Optional[str] = None
    preco_nao_desonerado: Optional[Decimal] = None
    preco_desonerado: Optional[Decimal] = None
    estado: Optional[str] = None
    data_referencia: Optional[date] = None


class InsumoItemOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    banco: str
    codigo: str
    descricao: str
    unidade: str
    tipo: str
    preco_nao_desonerado: Decimal
    preco_desonerado: Decimal
    estado: Optional[str]
    data_referencia: date
    empresa_id: Optional[int]


class InsumoItemListOut(BaseModel):
    items: List[InsumoItemOut]
    total: int
