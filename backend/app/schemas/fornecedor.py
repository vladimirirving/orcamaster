from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FornecedorCreate(BaseModel):
    nome: str
    cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    categorias: Optional[str] = None  # CSV: 'material,mao_obra,equipamento,servico'
    observacoes: Optional[str] = None


class FornecedorUpdate(BaseModel):
    nome: Optional[str] = None
    cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    categorias: Optional[str] = None
    observacoes: Optional[str] = None


class FornecedorOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    empresa_id: int
    nome: str
    cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    categorias: Optional[str] = None
    observacoes: Optional[str] = None
    created_at: datetime
