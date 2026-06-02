from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.dependencies import get_current_user
from app.models.cronograma_linha import CronogramaLinha
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.schemas.cronograma import (
    CronogramaConfigIn, CronogramaLinhaIn, CronogramaLinhaOut, CronogramaOut,
)

router = APIRouter(tags=["cronograma"])


async def _get_versao_ativa(versao_id: int, current_user: Usuario, db: AsyncSession) -> Versao:
    result = await db.execute(
        select(Versao)
        .join(Obra, Versao.obra_id == Obra.id)
        .where(
            Versao.id == versao_id,
            Obra.empresa_id == current_user.empresa_id,
            Versao.bloqueada == False,
            Versao.deletada_em.is_(None),
        )
    )
    v = result.scalar_one_or_none()
    if v is None:
        raise HTTPException(status_code=409, detail="Versão não encontrada ou não está ativa")
    return v


async def _get_versao_acesso(versao_id: int, current_user: Usuario, db: AsyncSession) -> Versao:
    result = await db.execute(
        select(Versao)
        .join(Obra, Versao.obra_id == Obra.id)
        .where(Versao.id == versao_id, Obra.empresa_id == current_user.empresa_id)
    )
    v = result.scalar_one_or_none()
    if v is None:
        raise HTTPException(status_code=404, detail="Versão não encontrada")
    return v


@router.get("/versoes/{versao_id}/cronograma", response_model=CronogramaOut)
async def get_cronograma(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    versao = await _get_versao_acesso(versao_id, current_user, db)

    stmt = (
        select(Item)
        .join(Grupo, Item.grupo_id == Grupo.id)
        .where(Grupo.versao_id == versao_id)
        .order_by(Grupo.ordem, Item.ordem)
        .options(
            selectinload(Item.cronograma_linha),
            selectinload(Item.composicao),
        )
    )
    itens = (await db.execute(stmt)).scalars().all()

    linhas = []
    for item in itens:
        cl = item.cronograma_linha
        linhas.append(CronogramaLinhaOut(
            item_id=item.id,
            descricao=item.composicao.descricao if item.composicao else "",
            unidade=item.unidade,
            quantidade=str(item.quantidade),
            total_sem_bdi=str(item.total),
            distribuicao_json=dict(cl.distribuicao_json) if cl else {},
        ))

    return CronogramaOut(
        cronograma_inicio=versao.cronograma_inicio,
        cronograma_fim=versao.cronograma_fim,
        linhas=linhas,
    )


@router.patch("/versoes/{versao_id}/cronograma/config", status_code=status.HTTP_204_NO_CONTENT)
async def patch_cronograma_config(
    versao_id: int,
    body: CronogramaConfigIn,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    versao = await _get_versao_ativa(versao_id, current_user, db)
    versao.cronograma_inicio = body.cronograma_inicio
    versao.cronograma_fim = body.cronograma_fim
    await db.commit()


@router.patch(
    "/versoes/{versao_id}/cronograma/linhas/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def patch_cronograma_linha(
    versao_id: int,
    item_id: int,
    body: CronogramaLinhaIn,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao_ativa(versao_id, current_user, db)

    r = await db.execute(
        select(Item)
        .join(Grupo, Item.grupo_id == Grupo.id)
        .where(Item.id == item_id, Grupo.versao_id == versao_id)
    )
    item = r.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Item não encontrado nesta versão")

    cleaned = {k: v for k, v in body.distribuicao_json.items() if v != 0}

    r2 = await db.execute(select(CronogramaLinha).where(CronogramaLinha.item_id == item_id))
    cl = r2.scalar_one_or_none()
    if cl is None:
        cl = CronogramaLinha(item_id=item_id, distribuicao_json=cleaned)
        db.add(cl)
    else:
        cl.distribuicao_json = cleaned
    await db.commit()
