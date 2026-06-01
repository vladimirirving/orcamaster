from decimal import Decimal
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.versao import Versao


async def recalc_totais_versao(versao_id: int, db: AsyncSession) -> None:
    """Recalculate and persist Versao.total_sem_bdi and total_com_bdi."""
    r1 = await db.execute(
        select(func.coalesce(func.sum(Item.total), Decimal("0")))
        .join(Grupo, Item.grupo_id == Grupo.id)
        .where(Grupo.versao_id == versao_id)
    )
    total_sem = r1.scalar() or Decimal("0")

    r2 = await db.execute(
        select(
            func.coalesce(
                func.sum(Item.quantidade * func.coalesce(Item.preco_unitario_com_bdi, Decimal("0"))),
                Decimal("0"),
            )
        )
        .join(Grupo, Item.grupo_id == Grupo.id)
        .where(Grupo.versao_id == versao_id)
    )
    total_com = r2.scalar() or Decimal("0")

    await db.execute(
        update(Versao)
        .where(Versao.id == versao_id)
        .values(
            total_sem_bdi=Decimal(str(total_sem)),
            total_com_bdi=Decimal(str(total_com)),
        )
    )
