from pydantic import BaseModel


class ImportarPlanilhaResult(BaseModel):
    grupos_criados: int
    itens_criados: int
    itens_sem_composicao: int
