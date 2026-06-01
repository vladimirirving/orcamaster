from typing import Optional, List
from pydantic import BaseModel


class GrupoCreate(BaseModel):
    nome: str
    codigo: Optional[str] = None
    ordem: int = 0


class GrupoUpdate(BaseModel):
    nome: Optional[str] = None
    codigo: Optional[str] = None
    ordem: Optional[int] = None


class GrupoOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    versao_id: int
    pai_id: Optional[int] = None
    ordem: int
    nome: str
    codigo: Optional[str] = None
    filhos: List["GrupoOut"] = []


GrupoOut.model_rebuild()
