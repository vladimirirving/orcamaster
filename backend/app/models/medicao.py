from datetime import date
from typing import Optional
from sqlalchemy import ForeignKey, Date
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Medicao(Base):
    __tablename__ = "medicao"

    id: Mapped[int] = mapped_column(primary_key=True)
    versao_id: Mapped[int] = mapped_column(ForeignKey("versao.id"))
    periodo_inicio: Mapped[date] = mapped_column(Date)
    periodo_fim: Mapped[date] = mapped_column(Date)
    criada_por: Mapped[Optional[int]] = mapped_column(ForeignKey("usuario.id"))
    # {item_id_str: percentual_executado_acumulado} e.g. {"42": 35.5}
    linhas_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    versao: Mapped["Versao"] = relationship(back_populates="medicoes")
