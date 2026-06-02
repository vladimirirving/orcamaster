from typing import Optional
from pydantic import BaseModel, EmailStr


class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str
    papel: str  # admin|orcamentista|visualizador


class UsuarioOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    empresa_id: int
    nome: str
    email: str
    papel: str
    ativo: bool


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    papel: Optional[str] = None
    ativo: Optional[bool] = None
