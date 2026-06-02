from typing import Optional
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Grupo(Base):
    __tablename__ = "grupo"

    id: Mapped[int] = mapped_column(primary_key=True)
    versao_id: Mapped[int] = mapped_column(ForeignKey("versao.id"))
    pai_id: Mapped[Optional[int]] = mapped_column(ForeignKey("grupo.id"), nullable=True)
    ordem: Mapped[int] = mapped_column(Integer, default=0)
    nome: Mapped[str] = mapped_column(String(300))
    codigo: Mapped[Optional[str]] = mapped_column(String(50))

    versao: Mapped["Versao"] = relationship(back_populates="grupos")
    filhos: Mapped[list["Grupo"]] = relationship("Grupo", back_populates="pai")
    pai: Mapped[Optional["Grupo"]] = relationship("Grupo", back_populates="filhos", remote_side="Grupo.id")
    itens: Mapped[list["Item"]] = relationship(back_populates="grupo")
