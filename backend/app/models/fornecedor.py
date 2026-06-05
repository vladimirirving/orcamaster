from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Fornecedor(Base):
    __tablename__ = "fornecedor"

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"))
    nome: Mapped[str] = mapped_column(String(200))
    cnpj: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    telefone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    endereco: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    cidade: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    estado: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    categorias: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
