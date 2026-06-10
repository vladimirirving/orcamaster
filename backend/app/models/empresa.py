from typing import Optional
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Empresa(Base):
    __tablename__ = "empresa"

    id:   Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200))
    cnpj: Mapped[str] = mapped_column(String(18), unique=True)
    representante_nome: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    representante_cpf:  Mapped[Optional[str]] = mapped_column(String(14),  nullable=True)
    declaracoes_padrao: Mapped[Optional[str]] = mapped_column(Text,         nullable=True)

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="empresa")
    obras:    Mapped[list["Obra"]]    = relationship(back_populates="empresa")
