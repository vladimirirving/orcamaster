from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ClienteCreate(BaseModel):
    tipo: str  # 'pf' | 'pj'
    nome: str
    cpf_cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    observacoes: Optional[str] = None


class ClienteUpdate(BaseModel):
    tipo: Optional[str] = None
    nome: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    observacoes: Optional[str] = None


class ClienteOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    empresa_id: int
    tipo: str
    nome: str
    cpf_cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    observacoes: Optional[str] = None
    created_at: datetime
