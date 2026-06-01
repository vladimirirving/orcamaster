from decimal import Decimal
from sqlalchemy import ForeignKey, String, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Insumo(Base):
    __tablename__ = "insumo"

    id: Mapped[int] = mapped_column(primary_key=True)
    composicao_id: Mapped[int] = mapped_column(ForeignKey("composicao.id"))
    tipo: Mapped[str] = mapped_column(String(20))  # mao_obra|material|equipamento
    descricao: Mapped[str] = mapped_column(String(300))
    unidade: Mapped[str] = mapped_column(String(20))
    coeficiente: Mapped[Decimal] = mapped_column(Numeric(15, 6))
    preco_unitario: Mapped[Decimal] = mapped_column(Numeric(15, 6))

    composicao: Mapped["Composicao"] = relationship(back_populates="insumos")
