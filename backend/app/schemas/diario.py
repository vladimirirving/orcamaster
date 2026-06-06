from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel


class DiarioFotoOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    diario_id: int
    nome_original: str
    tamanho_bytes: int
    criado_em: datetime


class DiarioCreate(BaseModel):
    data: date
    clima: str  # ensolarado | parcialmente_nublado | nublado | chuvoso
    turnos: Optional[str] = None  # CSV: 'manha,tarde,noite'
    efetivo: int = 0
    equipes: Optional[str] = None
    equipamentos: Optional[str] = None
    atividades: str
    ocorrencias: Optional[str] = None


class DiarioUpdate(BaseModel):
    clima: Optional[str] = None
    turnos: Optional[str] = None
    efetivo: Optional[int] = None
    equipes: Optional[str] = None
    equipamentos: Optional[str] = None
    atividades: Optional[str] = None
    ocorrencias: Optional[str] = None


class DiarioOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    obra_id: int
    empresa_id: int
    data: date
    clima: str
    turnos: Optional[str] = None
    efetivo: int
    equipes: Optional[str] = None
    equipamentos: Optional[str] = None
    atividades: str
    ocorrencias: Optional[str] = None
    criado_por: Optional[int] = None
    created_at: datetime
    fotos: List[DiarioFotoOut] = []


class DiarioListItem(BaseModel):
    """Versão leve usada na listagem (sem fotos completas, só contagem)."""
    model_config = {"from_attributes": True}
    id: int
    obra_id: int
    data: date
    clima: str
    turnos: Optional[str] = None
    efetivo: int
    atividades: str
    qtd_fotos: int = 0
