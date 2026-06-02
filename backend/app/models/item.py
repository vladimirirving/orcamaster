from decimal import Decimal
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, Boolean, Numeric, Computed
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Item(Base):
    __tablename__ = "item"

    id: Mapped[int] = mapped_column(primary_key=True)
    grupo_id: Mapped[int] = mapped_column(ForeignKey("grupo.id"))
    ordem: Mapped[int] = mapped_column(Integer, default=0)
    composicao_id: Mapped[Optional[int]] = mapped_column(ForeignKey("composicao.id"), nullable=True)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(15, 6))
    unidade: Mapped[str] = mapped_column(String(20))
    preco_unitario_sem_bdi: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 6), nullable=True)
    preco_unitario_com_bdi: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 6), nullable=True)
    # GENERATED ALWAYS AS STORED: quantidade * COALESCE(preco_unitario_sem_bdi, 0)
    total: Mapped[Decimal] = mapped_column(
        Numeric(15, 6),
        Computed("quantidade * COALESCE(preco_unitario_sem_bdi, 0)", persisted=True),
    )
    etiqueta_revisao: Mapped[bool] = mapped_column(Boolean, default=False)
    requer_revisao: Mapped[bool] = mapped_column(Boolean, default=False)

    grupo: Mapped["Grupo"] = relationship(back_populates="itens")
    cronograma_linha: Mapped[Optional["CronogramaLinha"]] = relationship(
        back_populates="item", uselist=False, cascade="all, delete-orphan"
    )
