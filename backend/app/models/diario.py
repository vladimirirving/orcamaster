from datetime import date, datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Text, Date, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class DiarioObra(Base):
    __tablename__ = "diario_obra"

    id: Mapped[int] = mapped_column(primary_key=True)
    obra_id: Mapped[int] = mapped_column(ForeignKey("obra.id", ondelete="CASCADE"))
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"))
    data: Mapped[date] = mapped_column(Date)
    clima: Mapped[str] = mapped_column(String(25))
    turnos: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    efetivo: Mapped[int] = mapped_column(Integer, default=0)
    equipes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    equipamentos: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    atividades: Mapped[str] = mapped_column(Text)
    ocorrencias: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criado_por: Mapped[Optional[int]] = mapped_column(
        ForeignKey("usuario.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    fotos: Mapped[list["DiarioFoto"]] = relationship(
        back_populates="entrada", cascade="all, delete-orphan"
    )


class DiarioFoto(Base):
    __tablename__ = "diario_foto"

    id: Mapped[int] = mapped_column(primary_key=True)
    diario_id: Mapped[int] = mapped_column(
        ForeignKey("diario_obra.id", ondelete="CASCADE")
    )
    nome_original: Mapped[str] = mapped_column(String(255))
    caminho: Mapped[str] = mapped_column(String(500))
    tamanho_bytes: Mapped[int] = mapped_column(Integer)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    entrada: Mapped["DiarioObra"] = relationship(back_populates="fotos")
