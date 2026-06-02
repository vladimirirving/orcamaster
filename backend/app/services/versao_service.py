from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.versao import Versao


async def clone_versao(obra_id: int, criada_por: int, db: AsyncSession) -> Versao:
    """Clone the active versão, block the source, return the new versão.

    Active versão = bloqueada=False AND deletada_em IS None.
    Raises HTTP 409 if no active versão exists.
    """
    r = await db.execute(
        select(Versao).where(
            Versao.obra_id == obra_id,
            Versao.bloqueada == False,
            Versao.deletada_em == None,
        )
    )
    fonte = r.scalar_one_or_none()
    if fonte is None:
        raise HTTPException(status_code=409, detail="Sem versão ativa para clonar")

    fonte.bloqueada = True

    r2 = await db.execute(
        select(func.max(Versao.numero)).where(Versao.obra_id == obra_id)
    )
    novo_numero = (r2.scalar() or 0) + 1

    nova = Versao(obra_id=obra_id, numero=novo_numero, criada_por=criada_por)
    db.add(nova)
    await db.flush()

    # Clone root grupos first to build id mapping
    grupo_map: dict[int, int] = {}

    r3 = await db.execute(
        select(Grupo)
        .where(Grupo.versao_id == fonte.id, Grupo.pai_id == None)
        .order_by(Grupo.ordem)
    )
    for g in r3.scalars().all():
        ng = Grupo(versao_id=nova.id, pai_id=None, ordem=g.ordem, nome=g.nome, codigo=g.codigo)
        db.add(ng)
        await db.flush()
        grupo_map[g.id] = ng.id

    # Clone subgrupos (max depth 1 — spec enforces max 2 levels)
    r4 = await db.execute(
        select(Grupo)
        .where(Grupo.versao_id == fonte.id, Grupo.pai_id != None)
        .order_by(Grupo.ordem)
    )
    for g in r4.scalars().all():
        ng = Grupo(
            versao_id=nova.id,
            pai_id=grupo_map[g.pai_id],
            ordem=g.ordem,
            nome=g.nome,
            codigo=g.codigo,
        )
        db.add(ng)
        await db.flush()
        grupo_map[g.id] = ng.id

    # Clone items — never set total= (GENERATED column)
    r5 = await db.execute(
        select(Item).join(Grupo).where(Grupo.versao_id == fonte.id)
    )
    for item in r5.scalars().all():
        ni = Item(
            grupo_id=grupo_map[item.grupo_id],
            ordem=item.ordem,
            composicao_id=item.composicao_id,
            quantidade=item.quantidade,
            unidade=item.unidade,
            preco_unitario_sem_bdi=item.preco_unitario_sem_bdi,
            preco_unitario_com_bdi=item.preco_unitario_com_bdi,
            etiqueta_revisao=item.etiqueta_revisao,  # verbatim per spec
            requer_revisao=False,                     # reset per spec
        )
        db.add(ni)

    await db.commit()
    await db.refresh(nova)
    return nova
