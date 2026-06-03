from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class PropostaConfigIn(BaseModel):
    validade_dias: int = 60
    data_proposta: date
    declaracoes: Optional[str] = None


class PropostaConfigOut(PropostaConfigIn):
    id: int
    versao_id: int
    criado_em: datetime
    atualizado_em: datetime
    model_config = {"from_attributes": True}


class EmpresaConfigIn(BaseModel):
    representante_nome: Optional[str] = None
    representante_cpf:  Optional[str] = None
    declaracoes_padrao: Optional[str] = None


class EmpresaConfigOut(EmpresaConfigIn):
    id: int
    nome: str
    cnpj: str
    model_config = {"from_attributes": True}
