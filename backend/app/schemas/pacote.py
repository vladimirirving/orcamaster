from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PacoteJobOut(BaseModel):
    id: int
    versao_id: int
    status: str          # pendente | processando | pronto | erro | expirado
    criado_em: datetime
    atualizado_em: datetime
    url_download: Optional[str] = None
    erro_mensagem: Optional[str] = None
    gerado_em: Optional[datetime] = None
    model_config = {"from_attributes": True}
