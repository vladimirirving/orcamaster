from decimal import Decimal
from sqlalchemy import ForeignKey, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class BDI(Base):
    __tablename__ = "bdi"
    __table_args__ = (UniqueConstraint("versao_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    versao_id: Mapped[int] = mapped_column(ForeignKey("versao.id"))
    ac: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    sg: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    r: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    df: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    lucro: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    iss: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    pis: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    cofins: Mapped[Decimal] = mapped_column(Numeric(8, 4))
    bdi_composto: Mapped[Decimal] = mapped_column(Numeric(8, 6))
    historico_json: Mapped[list] = mapped_column(JSONB, default=list)

    versao: Mapped["Versao"] = relationship(back_populates="bdi")
