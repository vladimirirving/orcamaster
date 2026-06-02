from datetime import date
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel


class InsumoCreate(BaseModel):
    tipo: str  # mao_obra|material|equipamento
    descricao: str
    unidade: str
    coeficiente: Decimal
    preco_unitario: Decimal


class InsumoUpdate(BaseModel):
    tipo: Optional[str] = None
    descricao: Optional[str] = None
    unidade: Optional[str] = None
    coeficiente: Optional[Decimal] = None
    preco_unitario: Optional[Decimal] = None


class InsumoOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    composicao_id: int
    tipo: str
    descricao: str
    unidade: str
    coeficiente: Decimal
    preco_unitario: Decimal


class ComposicaoCreate(BaseModel):
    codigo: str
    descricao: str
    unidade: str
    preco_unitario: Decimal
    data_referencia: Optional[date] = None
    base_origem_id: Optional[int] = None


class ComposicaoUpdate(BaseModel):
    codigo: Optional[str] = None
    descricao: Optional[str] = None
    unidade: Optional[str] = None
    preco_unitario: Optional[Decimal] = None
    data_referencia: Optional[date] = None


class ComposicaoOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    empresa_id: Optional[int] = None
    origem: str
    codigo: str
    descricao: str
    unidade: str
    preco_unitario: Decimal
    data_referencia: Optional[date] = None
    base_origem_id: Optional[int] = None
    requer_revisao: bool
    insumos: List[InsumoOut] = []


class ImportResultOut(BaseModel):
    criadas: int
    atualizadas: int
    itens_marcados: int
