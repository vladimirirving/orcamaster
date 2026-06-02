from decimal import Decimal
from pydantic import BaseModel


class BDICreate(BaseModel):
    ac: Decimal
    sg: Decimal
    r: Decimal
    df: Decimal
    lucro: Decimal
    iss: Decimal
    pis: Decimal
    cofins: Decimal


class BDIOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    versao_id: int
    ac: Decimal
    sg: Decimal
    r: Decimal
    df: Decimal
    lucro: Decimal
    iss: Decimal
    pis: Decimal
    cofins: Decimal
    bdi_composto: Decimal
