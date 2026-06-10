from datetime import date
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel


class ObraCreate(BaseModel):
    nome: str
    numero_processo: Optional[str] = None
    cliente: Optional[str] = None
    uf: Optional[str] = None
    municipio: Optional[str] = None
    tipo_obra: str  # rodovia|saneamento|ponte|rede_eletrica|outro
    responsavel_id: Optional[int] = None
    data_prazo: Optional[date] = None
    cliente_id: Optional[int] = None


class ObraUpdate(BaseModel):
    nome: Optional[str] = None
    numero_processo: Optional[str] = None
    cliente: Optional[str] = None
    uf: Optional[str] = None
    municipio: Optional[str] = None
    tipo_obra: Optional[str] = None
    estado: Optional[str] = None  # em_elaboracao|concluido|arquivado
    responsavel_id: Optional[int] = None
    data_prazo: Optional[date] = None
    cliente_id: Optional[int] = None


class ObraOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    empresa_id: int
    nome: str
    numero_processo: Optional[str] = None
    cliente: Optional[str] = None
    uf: Optional[str] = None
    municipio: Optional[str] = None
    tipo_obra: str
    estado: str
    responsavel_id: Optional[int] = None
    data_criacao: date
    data_prazo: Optional[date] = None
    cliente_id: Optional[int] = None
    cliente_nome: Optional[str] = None
