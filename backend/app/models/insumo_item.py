from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy import ForeignKey, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class InsumoItem(Base):
    __tablename__ = "insumo_item"
    __table_args__ = (
        Index("ix_insumo_item_banco_estado_data", "banco", "estado", "data_referencia"),
        Index("ix_insumo_item_empresa_id", "empresa_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    banco: Mapped[str] = mapped_column(String(10))          # sinapi|sicro|propria
    codigo: Mapped[str] = mapped_column(String(50))
    descricao: Mapped[str] = mapped_column(String(500))
    unidade: Mapped[str] = mapped_column(String(20))
    tipo: Mapped[str] = mapped_column(String(20))           # mao_obra|material|equipamento
    preco_nao_desonerado: Mapped[Decimal] = mapped_column(Numeric(15, 6))
    preco_desonerado: Mapped[Decimal] = mapped_column(Numeric(15, 6))
    estado: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    data_referencia: Mapped[date]
    empresa_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("empresa.id"), nullable=True
    )  # None = global (SINAPI/SICRO); preenchido = propria
