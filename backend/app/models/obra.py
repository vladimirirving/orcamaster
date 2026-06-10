from datetime import date
from typing import ClassVar, Optional
from sqlalchemy import ForeignKey, String, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Obra(Base):
    __tablename__ = "obra"

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"))
    nome: Mapped[str] = mapped_column(String(300))
    numero_processo: Mapped[Optional[str]] = mapped_column(String(100))
    cliente: Mapped[Optional[str]] = mapped_column(String(200))
    uf: Mapped[Optional[str]] = mapped_column(String(2))
    municipio: Mapped[Optional[str]] = mapped_column(String(100))
    tipo_obra: Mapped[str] = mapped_column(String(50))  # rodovia|saneamento|ponte|rede_eletrica|outro
    estado: Mapped[str] = mapped_column(String(20), default="em_elaboracao")  # em_elaboracao|concluido|arquivado
    responsavel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("usuario.id"))
    cliente_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("cliente.id", ondelete="SET NULL"), nullable=True
    )
    cliente_nome: ClassVar[Optional[str]]  # campo transiente, não persiste
    data_criacao: Mapped[date] = mapped_column(Date)
    data_prazo: Mapped[Optional[date]] = mapped_column(Date)

    empresa: Mapped["Empresa"] = relationship(back_populates="obras")
    versoes: Mapped[list["Versao"]] = relationship(back_populates="obra")
    cliente_obj: Mapped[Optional["Cliente"]] = relationship(back_populates="obras")
