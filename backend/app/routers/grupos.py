from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select, delete as sql_delete
from pydantic import BaseModel
from app.models.composicao import Composicao
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value
from app.database import get_db
from app.dependencies import get_current_user
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.schemas.grupo import GrupoCreate, GrupoOut, GrupoUpdate
from app.schemas.item import ItemCreate, ItemOut, ItemUpdate
from app.services.totais_service import recalc_totais_versao

router = APIRouter(tags=["grupos"])


async def _get_versao_ativa(versao_id: int, current_user: Usuario, db: AsyncSession) -> Versao:
    """Returns versão only if active (not blocked, not deleted) and belongs to empresa."""
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
    """Returns versão (any state) — for read-only operations."""
    result = await db.execute(
        select(Versao)
        .join(Obra, Versao.obra_id == Obra.id)
        .where(Versao.id == versao_id, Obra.empresa_id == current_user.empresa_id)
    )
    v = result.scalar_one_or_none()
    if v is None:
        raise HTTPException(status_code=404, detail="Versão não encontrada")
    return v


async def _get_grupo_da_empresa(grupo_id: int, current_user: Usuario, db: AsyncSession) -> Grupo:
    result = await db.execute(
        select(Grupo)
        .join(Versao, Grupo.versao_id == Versao.id)
        .join(Obra, Versao.obra_id == Obra.id)
        .where(Grupo.id == grupo_id, Obra.empresa_id == current_user.empresa_id)
    )
    g = result.scalar_one_or_none()
    if g is None:
        raise HTTPException(status_code=404, detail="Grupo não encontrado")
    return g


# ── Grupos ─────────────────────────────────────────────────────────────────

@router.get("/versoes/{versao_id}/grupos", response_model=List[GrupoOut])
async def list_grupos(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao_acesso(versao_id, current_user, db)

    r_roots = await db.execute(
        select(Grupo)
        .where(Grupo.versao_id == versao_id, Grupo.pai_id.is_(None))
        .order_by(Grupo.ordem)
    )
    roots = r_roots.scalars().all()

    for g in roots:
        r_filhos = await db.execute(
            select(Grupo).where(Grupo.pai_id == g.id).order_by(Grupo.ordem)
        )
        filhos = r_filhos.scalars().all()
        for filho in filhos:
            set_committed_value(filho, "filhos", [])
        set_committed_value(g, "filhos", filhos)

    return roots


@router.post("/versoes/{versao_id}/grupos", response_model=GrupoOut, status_code=status.HTTP_201_CREATED)
async def create_grupo(
    versao_id: int,
    body: GrupoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao_ativa(versao_id, current_user, db)

    grupo = Grupo(versao_id=versao_id, pai_id=None, nome=body.nome, codigo=body.codigo, ordem=body.ordem)
    db.add(grupo)
    await db.commit()
    await db.refresh(grupo)
    set_committed_value(grupo, "filhos", [])
    return grupo


@router.post("/grupos/{grupo_id}/subgrupos", response_model=GrupoOut, status_code=status.HTTP_201_CREATED)
async def create_subgrupo(
    grupo_id: int,
    body: GrupoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pai = await _get_grupo_da_empresa(grupo_id, current_user, db)

    if pai.pai_id is not None:
        raise HTTPException(status_code=422, detail="Profundidade máxima de 2 níveis excedida")

    await _get_versao_ativa(pai.versao_id, current_user, db)

    sg = Grupo(
        versao_id=pai.versao_id, pai_id=grupo_id,
        nome=body.nome, codigo=body.codigo, ordem=body.ordem,
    )
    db.add(sg)
    await db.commit()
    await db.refresh(sg)
    set_committed_value(sg, "filhos", [])
    return sg


@router.patch("/grupos/{grupo_id}", response_model=GrupoOut)
async def update_grupo(
    grupo_id: int,
    body: GrupoUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    grupo = await _get_grupo_da_empresa(grupo_id, current_user, db)
    await _get_versao_ativa(grupo.versao_id, current_user, db)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(grupo, field, value)
    await db.commit()
    await db.refresh(grupo)

    r_filhos = await db.execute(select(Grupo).where(Grupo.pai_id == grupo.id).order_by(Grupo.ordem))
    set_committed_value(grupo, "filhos", r_filhos.scalars().all())
    return grupo


@router.delete("/grupos/{grupo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_grupo(
    grupo_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    grupo = await _get_grupo_da_empresa(grupo_id, current_user, db)
    versao = await _get_versao_ativa(grupo.versao_id, current_user, db)

    r_filhos = await db.execute(select(Grupo).where(Grupo.pai_id == grupo_id))
    for filho in r_filhos.scalars().all():
        await db.execute(sql_delete(Item).where(Item.grupo_id == filho.id))
        await db.delete(filho)

    await db.execute(sql_delete(Item).where(Item.grupo_id == grupo_id))
    await db.delete(grupo)
    await db.flush()
    await recalc_totais_versao(versao.id, db)
    await db.refresh(versao)
    await db.commit()


# ── Itens ──────────────────────────────────────────────────────────────────

@router.get("/grupos/{grupo_id}/itens", response_model=List[ItemOut])
async def list_itens(
    grupo_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_grupo_da_empresa(grupo_id, current_user, db)
    result = await db.execute(
        select(Item).where(Item.grupo_id == grupo_id).order_by(Item.ordem)
    )
    return result.scalars().all()


@router.post("/grupos/{grupo_id}/itens", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
async def create_item(
    grupo_id: int,
    body: ItemCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    grupo = await _get_grupo_da_empresa(grupo_id, current_user, db)
    versao = await _get_versao_ativa(grupo.versao_id, current_user, db)

    # Do NOT set total= (GENERATED ALWAYS column)
    item = Item(
        grupo_id=grupo_id,
        ordem=body.ordem,
        quantidade=body.quantidade,
        unidade=body.unidade,
    )
    db.add(item)
    await db.flush()
    await recalc_totais_versao(versao.id, db)
    await db.refresh(versao)
    await db.commit()
    await db.refresh(item)
    return item


@router.patch("/itens/{item_id}", response_model=ItemOut)
async def update_item(
    item_id: int,
    body: ItemUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Item)
        .join(Grupo, Item.grupo_id == Grupo.id)
        .join(Versao, Grupo.versao_id == Versao.id)
        .join(Obra, Versao.obra_id == Obra.id)
        .where(Item.id == item_id, Obra.empresa_id == current_user.empresa_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    r_g = await db.execute(select(Grupo).where(Grupo.id == item.grupo_id))
    grupo = r_g.scalar_one()
    versao = await _get_versao_ativa(grupo.versao_id, current_user, db)

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)

    await db.flush()
    await recalc_totais_versao(versao.id, db)
    await db.refresh(versao)
    await db.commit()
    await db.refresh(item)
    return item


@router.delete("/itens/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Item)
        .join(Grupo, Item.grupo_id == Grupo.id)
        .join(Versao, Grupo.versao_id == Versao.id)
        .join(Obra, Versao.obra_id == Obra.id)
        .where(Item.id == item_id, Obra.empresa_id == current_user.empresa_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    r_g = await db.execute(select(Grupo).where(Grupo.id == item.grupo_id))
    grupo = r_g.scalar_one()
    versao = await _get_versao_ativa(grupo.versao_id, current_user, db)

    await db.delete(item)
    await db.flush()
    await recalc_totais_versao(versao.id, db)
    await db.refresh(versao)
    await db.commit()


class _ComposicaoLink(BaseModel):
    composicao_id: int


@router.patch("/itens/{item_id}/composicao", response_model=ItemOut)
async def vincular_composicao_ao_item(
    item_id: int,
    body: _ComposicaoLink,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Item)
        .join(Grupo, Item.grupo_id == Grupo.id)
        .join(Versao, Grupo.versao_id == Versao.id)
        .join(Obra, Versao.obra_id == Obra.id)
        .where(Item.id == item_id, Obra.empresa_id == current_user.empresa_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    r_g = await db.execute(select(Grupo).where(Grupo.id == item.grupo_id))
    grupo = r_g.scalar_one()
    versao = await _get_versao_ativa(grupo.versao_id, current_user, db)

    r_c = await db.execute(
        select(Composicao).where(
            Composicao.id == body.composicao_id,
            or_(
                Composicao.empresa_id.is_(None),
                Composicao.empresa_id == current_user.empresa_id,
            ),
        )
    )
    composicao = r_c.scalar_one_or_none()
    if composicao is None:
        raise HTTPException(status_code=404, detail="Composição não encontrada")

    item.composicao_id = composicao.id
    item.preco_unitario_sem_bdi = composicao.preco_unitario
    item.requer_revisao = False

    await db.flush()
    await recalc_totais_versao(versao.id, db)
    await db.refresh(versao)
    await db.commit()
    await db.refresh(item)
    return item


@router.post("/itens/{item_id}/atualizar-preco", response_model=ItemOut)
async def atualizar_preco_item(
    item_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Item)
        .join(Grupo, Item.grupo_id == Grupo.id)
        .join(Versao, Grupo.versao_id == Versao.id)
        .join(Obra, Versao.obra_id == Obra.id)
        .where(Item.id == item_id, Obra.empresa_id == current_user.empresa_id)
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Item não encontrado")

    if item.composicao_id is None:
        raise HTTPException(
            status_code=422, detail="Item não possui composição vinculada"
        )

    r_g = await db.execute(select(Grupo).where(Grupo.id == item.grupo_id))
    grupo = r_g.scalar_one()
    versao = await _get_versao_ativa(grupo.versao_id, current_user, db)

    r_c = await db.execute(
        select(Composicao.preco_unitario).where(Composicao.id == item.composicao_id)
    )
    item.preco_unitario_sem_bdi = r_c.scalar_one()
    item.requer_revisao = False

    await db.flush()
    await recalc_totais_versao(versao.id, db)
    await db.refresh(versao)
    await db.commit()
    await db.refresh(item)
    return item
