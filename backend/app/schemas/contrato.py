from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel


class AditivoCreate(BaseModel):
    tipo: Literal['valor', 'prazo', 'valor_prazo']
    numero: Optional[str] = None
    delta_valor: Optional[Decimal] = None
    nova_data_fim: Optional[date] = None
    justificativa: Optional[str] = None
    data_assinatura: Optional[date] = None


class AditivoUpdate(BaseModel):
    numero: Optional[str] = None
    tipo: Optional[Literal['valor', 'prazo', 'valor_prazo']] = None
    delta_valor: Optional[Decimal] = None
    nova_data_fim: Optional[date] = None
    justificativa: Optional[str] = None
    data_assinatura: Optional[date] = None


class AditivoOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    contrato_id: int
    numero: Optional[str] = None
    tipo: str
    delta_valor: Optional[Decimal] = None
    nova_data_fim: Optional[date] = None
    justificativa: Optional[str] = None
    data_assinatura: Optional[date] = None
    arquivo_path: Optional[str] = None
    criado_em: datetime


class ContratoCreate(BaseModel):
    objeto: str
    valor_original: Decimal
    numero: Optional[str] = None
    data_assinatura: Optional[date] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    contratante_nome: Optional[str] = None
    contratante_cnpj: Optional[str] = None
    contratado_nome: Optional[str] = None
    contratado_cnpj: Optional[str] = None


class ContratoUpdate(BaseModel):
    objeto: Optional[str] = None
    valor_original: Optional[Decimal] = None
    numero: Optional[str] = None
    data_assinatura: Optional[date] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    contratante_nome: Optional[str] = None
    contratante_cnpj: Optional[str] = None
    contratado_nome: Optional[str] = None
    contratado_cnpj: Optional[str] = None


class ContratoOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    obra_id: int
    numero: Optional[str] = None
    objeto: str
    valor_original: Decimal
    valor_atual: Decimal
    data_assinatura: Optional[date] = None
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    data_fim_atual: Optional[date] = None
    contratante_nome: Optional[str] = None
    contratante_cnpj: Optional[str] = None
    contratado_nome: Optional[str] = None
    contratado_cnpj: Optional[str] = None
    arquivo_path: Optional[str] = None
    criado_em: datetime
    aditivos: list[AditivoOut] = []
