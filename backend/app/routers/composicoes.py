from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value
from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.composicao import Composicao
from app.models.insumo import Insumo
from app.models.usuario import Usuario
from app.schemas.composicao import (
    ComposicaoCreate, ComposicaoOut, ComposicaoUpdate,
    ImportResultOut, InsumoCreate, InsumoOut, InsumoUpdate,
)

router = APIRouter(prefix="/composicoes", tags=["composicoes"])


async def _get_composicao_acesso(
    composicao_id: int, current_user: Usuario, db: AsyncSession
) -> Composicao:
    result = await db.execute(select(Composicao).where(Composicao.id == composicao_id))
    comp = result.scalar_one_or_none()
    if comp is None:
        raise HTTPException(status_code=404, detail="Composição não encontrada")
    if comp.empresa_id is not None and comp.empresa_id != current_user.empresa_id:
        raise HTTPException(status_code=403, detail="Composição não pertence à empresa")
    return comp


async def _get_composicao_propria(
    composicao_id: int, current_user: Usuario, db: AsyncSession
) -> Composicao:
    comp = await _get_composicao_acesso(composicao_id, current_user, db)
    if comp.empresa_id is None:
        raise HTTPException(
            status_code=403, detail="Composições SINAPI/SICRO não podem ser editadas"
        )
    return comp


async def _load_insumos(comp: Composicao, db: AsyncSession) -> None:
    r = await db.execute(
        select(Insumo).where(Insumo.composicao_id == comp.id).order_by(Insumo.id)
    )
    set_committed_value(comp, "insumos", r.scalars().all())


@router.get("", response_model=List[ComposicaoOut])
async def list_composicoes(
    q: Optional[str] = Query(None),
    origem: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Composicao).where(
        or_(Composicao.empresa_id == None, Composicao.empresa_id == current_user.empresa_id)
    )
    if origem:
        stmt = stmt.where(Composicao.origem == origem)
    if q:
        q_like = f"%{q}%"
        stmt = stmt.where(
            or_(Composicao.codigo.ilike(q_like), Composicao.descricao.ilike(q_like))
        )
    stmt = stmt.order_by(Composicao.codigo).limit(limit).offset(offset)
    result = await db.execute(stmt)
    composicoes = result.scalars().all()
    for comp in composicoes:
        set_committed_value(comp, "insumos", [])
    return composicoes


@router.post("", response_model=ComposicaoOut, status_code=status.HTTP_201_CREATED)
async def create_composicao(
    body: ComposicaoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comp = Composicao(
        empresa_id=current_user.empresa_id,
        origem="propria",
        codigo=body.codigo,
        descricao=body.descricao,
        unidade=body.unidade,
        preco_unitario=body.preco_unitario,
        data_referencia=body.data_referencia,
        base_origem_id=body.base_origem_id,
    )
    db.add(comp)
    await db.commit()
    await db.refresh(comp)
    set_committed_value(comp, "insumos", [])
    return comp


# NOTE: /importar must be defined BEFORE /{composicao_id} to avoid path conflict
@router.post("/importar", response_model=ImportResultOut)
async def importar_composicoes(
    origem: str = Form(...),
    file: UploadFile = File(...),
    admin: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if origem not in ("sinapi", "sicro"):
        raise HTTPException(status_code=422, detail="origem deve ser 'sinapi' ou 'sicro'")
    from app.services.composicao_service import import_composicoes_csv
    conteudo = await file.read()
    return await import_composicoes_csv(origem=origem, conteudo=conteudo, db=db)


@router.get("/{composicao_id}", response_model=ComposicaoOut)
async def get_composicao(
    composicao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comp = await _get_composicao_acesso(composicao_id, current_user, db)
    await _load_insumos(comp, db)
    return comp


@router.patch("/{composicao_id}", response_model=ComposicaoOut)
async def update_composicao(
    composicao_id: int,
    body: ComposicaoUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comp = await _get_composicao_propria(composicao_id, current_user, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(comp, field, value)
    await db.commit()
    await db.refresh(comp)
    await _load_insumos(comp, db)
    return comp


@router.delete("/{composicao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_composicao(
    composicao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comp = await _get_composicao_propria(composicao_id, current_user, db)
    await db.delete(comp)
    await db.commit()


# ── Insumos ────────────────────────────────────────────────────────────────

@router.get("/{composicao_id}/insumos", response_model=List[InsumoOut])
async def list_insumos(
    composicao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_composicao_acesso(composicao_id, current_user, db)
    result = await db.execute(
        select(Insumo).where(Insumo.composicao_id == composicao_id).order_by(Insumo.id)
    )
    return result.scalars().all()


@router.post(
    "/{composicao_id}/insumos",
    response_model=InsumoOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_insumo(
    composicao_id: int,
    body: InsumoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_composicao_propria(composicao_id, current_user, db)
    from app.services.composicao_service import recalc_preco_composicao
    insumo = Insumo(
        composicao_id=composicao_id,
        tipo=body.tipo,
        descricao=body.descricao,
        unidade=body.unidade,
        coeficiente=body.coeficiente,
        preco_unitario=body.preco_unitario,
    )
    db.add(insumo)
    await db.flush()
    await recalc_preco_composicao(composicao_id, db)
    await db.commit()
    await db.refresh(insumo)
    return insumo


@router.patch("/{composicao_id}/insumos/{insumo_id}", response_model=InsumoOut)
async def update_insumo(
    composicao_id: int,
    insumo_id: int,
    body: InsumoUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_composicao_propria(composicao_id, current_user, db)
    from app.services.composicao_service import recalc_preco_composicao
    result = await db.execute(
        select(Insumo).where(Insumo.id == insumo_id, Insumo.composicao_id == composicao_id)
    )
    insumo = result.scalar_one_or_none()
    if insumo is None:
        raise HTTPException(status_code=404, detail="Insumo não encontrado")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(insumo, field, value)
    await db.flush()
    await recalc_preco_composicao(composicao_id, db)
    await db.commit()
    await db.refresh(insumo)
    return insumo


@router.delete("/{composicao_id}/insumos/{insumo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_insumo(
    composicao_id: int,
    insumo_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_composicao_propria(composicao_id, current_user, db)
    from app.services.composicao_service import recalc_preco_composicao
    result = await db.execute(
        select(Insumo).where(Insumo.id == insumo_id, Insumo.composicao_id == composicao_id)
    )
    insumo = result.scalar_one_or_none()
    if insumo is None:
        raise HTTPException(status_code=404, detail="Insumo não encontrado")
    await db.delete(insumo)
    await db.flush()
    await recalc_preco_composicao(composicao_id, db)
    await db.commit()
