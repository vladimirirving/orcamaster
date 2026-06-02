from datetime import date
from decimal import Decimal
from typing import Optional
from sqlalchemy import ForeignKey, String, Date, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Composicao(Base):
    __tablename__ = "composicao"

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[Optional[int]] = mapped_column(ForeignKey("empresa.id"), nullable=True)
    origem: Mapped[str] = mapped_column(String(10))  # sinapi|sicro|propria
    codigo: Mapped[str] = mapped_column(String(50))
    descricao: Mapped[str] = mapped_column(String(500))
    unidade: Mapped[str] = mapped_column(String(20))
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(15, 6))
    data_referencia: Mapped[Optional[date]] = mapped_column(Date)
    base_origem_id: Mapped[Optional[int]] = mapped_column(ForeignKey("composicao.id"), nullable=True)
    requer_revisao: Mapped[bool] = mapped_column(default=False)

    insumos: Mapped[list["Insumo"]] = relationship(back_populates="composicao")
