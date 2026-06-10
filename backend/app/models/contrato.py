from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import ForeignKey, String, Text, Date, Numeric, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Contrato(Base):
    __tablename__ = "contrato"

    id: Mapped[int] = mapped_column(primary_key=True)
    obra_id: Mapped[int] = mapped_column(ForeignKey("obra.id", ondelete="CASCADE"))
    numero: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    objeto: Mapped[str] = mapped_column(Text)
    valor_original: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    data_assinatura: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    data_inicio: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    data_fim: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    contratante_nome: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contratante_cnpj: Mapped[Optional[str]] = mapped_column(String(18), nullable=True)
    contratado_nome: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    contratado_cnpj: Mapped[Optional[str]] = mapped_column(String(18), nullable=True)
    arquivo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    aditivos: Mapped[list["Aditivo"]] = relationship(
        back_populates="contrato", cascade="all, delete-orphan"
    )


class Aditivo(Base):
    __tablename__ = "aditivo"

    id: Mapped[int] = mapped_column(primary_key=True)
    contrato_id: Mapped[int] = mapped_column(ForeignKey("contrato.id", ondelete="CASCADE"))
    numero: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tipo: Mapped[str] = mapped_column(String(20))  # valor | prazo | valor_prazo
    delta_valor: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    nova_data_fim: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    justificativa: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    data_assinatura: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    arquivo_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contrato: Mapped["Contrato"] = relationship(back_populates="aditivos")
