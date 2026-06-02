from decimal import Decimal
from sqlalchemy import Numeric, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.versao import Versao

_ZERO = Decimal("0")
_NUM = Numeric(15, 6)


async def recalc_totais_versao(versao_id: int, db: AsyncSession) -> None:
    """Recalculate and persist Versao.total_sem_bdi and total_com_bdi.

    Callers must db.flush() before calling so in-flight inserts/updates are
    visible to these queries. Callers must db.refresh(versao) afterwards if
    they hold a loaded Versao ORM object — the bulk UPDATE does not sync the
    identity map.
    """
    r1 = await db.execute(
        select(
            func.coalesce(func.sum(Item.total), _ZERO).cast(_NUM)
        )
        .join(Grupo, Item.grupo_id == Grupo.id)
        .where(Grupo.versao_id == versao_id)
    )
    total_sem = r1.scalar() or _ZERO

    r2 = await db.execute(
        select(
            func.coalesce(
                func.sum(
                    Item.quantidade * func.coalesce(Item.preco_unitario_com_bdi, _ZERO)
                ),
                _ZERO,
            ).cast(_NUM)
        )
        .join(Grupo, Item.grupo_id == Grupo.id)
        .where(Grupo.versao_id == versao_id)
    )
    total_com = r2.scalar() or _ZERO

    await db.execute(
        update(Versao)
        .where(Versao.id == versao_id)
        .values(total_sem_bdi=Decimal(str(total_sem)), total_com_bdi=Decimal(str(total_com)))
        .execution_options(synchronize_session=False)
    )
