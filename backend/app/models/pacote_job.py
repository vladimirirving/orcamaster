from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class PacoteJob(Base):
    __tablename__ = "pacote_job"

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(Integer)  # denormalized for concurrency check
    versao_id: Mapped[int] = mapped_column(ForeignKey("versao.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String(20), default="pendente")
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    url_download: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    erro_mensagem: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    gerado_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    versao: Mapped["Versao"] = relationship(back_populates="pacote_jobs")
