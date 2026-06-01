from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, Boolean, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Versao(Base):
    __tablename__ = "versao"

    id: Mapped[int] = mapped_column(primary_key=True)
    obra_id: Mapped[int] = mapped_column(ForeignKey("obra.id"))
    numero: Mapped[int] = mapped_column(Integer)
    nome: Mapped[Optional[str]] = mapped_column(String(200))
    criada_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    criada_por: Mapped[Optional[int]] = mapped_column(ForeignKey("usuario.id"))
    bloqueada: Mapped[bool] = mapped_column(Boolean, default=False)
    total_sem_bdi: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    total_com_bdi: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    deletada_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    obra: Mapped["Obra"] = relationship(back_populates="versoes")
    grupos: Mapped[list["Grupo"]] = relationship(back_populates="versao")
    bdi: Mapped[Optional["BDI"]] = relationship(back_populates="versao", uselist=False)
    medicoes: Mapped[list["Medicao"]] = relationship(back_populates="versao")
    pacote_jobs: Mapped[list["PacoteJob"]] = relationship(back_populates="versao")
