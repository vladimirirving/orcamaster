from decimal import Decimal
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.grupo import Grupo
from app.models.item import Item


async def aplicar_bdi_versao(versao_id: int, bdi_composto: Decimal, db: AsyncSession) -> None:
    subq = select(Grupo.id).where(Grupo.versao_id == versao_id)
    await db.execute(
        update(Item)
        .where(Item.grupo_id.in_(subq), Item.preco_unitario_sem_bdi.is_not(None))
        .values(preco_unitario_com_bdi=Item.preco_unitario_sem_bdi * (1 + bdi_composto))
        .execution_options(synchronize_session=False)
    )


async def zerar_bdi_versao(versao_id: int, db: AsyncSession) -> None:
    subq = select(Grupo.id).where(Grupo.versao_id == versao_id)
    await db.execute(
        update(Item)
        .where(Item.grupo_id.in_(subq))
        .values(preco_unitario_com_bdi=None)
        .execution_options(synchronize_session=False)
    )
