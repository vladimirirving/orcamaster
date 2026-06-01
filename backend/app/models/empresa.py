from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Empresa(Base):
    __tablename__ = "empresa"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200))
    cnpj: Mapped[str] = mapped_column(String(18), unique=True)

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="empresa")
    obras: Mapped[list["Obra"]] = relationship(back_populates="empresa")
