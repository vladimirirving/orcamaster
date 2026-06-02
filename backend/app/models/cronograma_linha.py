from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class CronogramaLinha(Base):
    __tablename__ = "cronograma_linha"

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id", ondelete="CASCADE"), unique=True)
    # {mes: percentual} e.g. {"2024-01": 20.0, "2024-02": 30.0}
    distribuicao_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    item: Mapped["Item"] = relationship(back_populates="cronograma_linha")
