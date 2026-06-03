from datetime import date, datetime
from typing import Optional
from sqlalchemy import ForeignKey, Integer, Date, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class PropostaConfig(Base):
    __tablename__ = "proposta_config"
    __table_args__ = (UniqueConstraint("versao_id"),)

    id:            Mapped[int]           = mapped_column(primary_key=True)
    versao_id:     Mapped[int]           = mapped_column(ForeignKey("versao.id", ondelete="CASCADE"))
    validade_dias: Mapped[int]           = mapped_column(Integer, default=60)
    data_proposta: Mapped[date]          = mapped_column(Date)
    declaracoes:   Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criado_em:     Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow,
                                                          onupdate=datetime.utcnow)

    versao: Mapped["Versao"] = relationship(back_populates="proposta_config")
