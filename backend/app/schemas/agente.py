from pydantic import BaseModel


class AgenteRequest(BaseModel):
    descricao: str


class PropostaItem(BaseModel):
    composicao_id: int
    descricao: str
    codigo: str
    unidade: str
    quantidade: float


class PropostaGrupo(BaseModel):
    nome: str
    itens: list[PropostaItem]


class ImportarRequest(BaseModel):
    grupos: list[PropostaGrupo]


class ImportarResult(BaseModel):
    grupos_criados: int
    itens_criados: int
