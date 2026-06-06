from datetime import date
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.cliente import Cliente as ClienteModel
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.schemas.obra import ObraCreate, ObraOut, ObraUpdate
from app.schemas.versao import VersaoOut
from app.services.versao_service import clone_versao

router = APIRouter(prefix="/obras", tags=["obras"])


async def _set_cliente_nome(obra, db) -> None:
    """Populate transient cliente_nome field for ObraOut serialization."""
    if obra.cliente_id:
        r = await db.execute(
            select(ClienteModel).where(
                ClienteModel.id == obra.cliente_id,
                ClienteModel.empresa_id == obra.empresa_id,
            )
        )
        c = r.scalar_one_or_none()
        obra.cliente_nome = c.nome if c else None
    else:
        obra.cliente_nome = None


async def _validate_cliente_id(cliente_id: int | None, empresa_id: int, db: AsyncSession) -> None:
    """Raise 422 if cliente_id is provided but doesn't belong to this empresa."""
    if cliente_id is None:
        return
    exists = await db.scalar(
        select(ClienteModel.id).where(
            ClienteModel.id == cliente_id,
            ClienteModel.empresa_id == empresa_id,
        )
    )
    if not exists:
        raise HTTPException(status_code=422, detail="cliente_id inválido")


@router.get("", response_model=List[ObraOut])
async def list_obras(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Obra).where(Obra.empresa_id == current_user.empresa_id)
    )
    obras = result.scalars().all()
    for o in obras:
        await _set_cliente_nome(o, db)
    return obras


@router.post("", response_model=ObraOut, status_code=status.HTTP_201_CREATED)
async def create_obra(
    body: ObraCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _validate_cliente_id(body.cliente_id, current_user.empresa_id, db)
    obra = Obra(
        empresa_id=current_user.empresa_id,
        nome=body.nome,
        numero_processo=body.numero_processo,
        cliente=body.cliente,
        uf=body.uf,
        municipio=body.municipio,
        tipo_obra=body.tipo_obra,
        estado="em_elaboracao",
        responsavel_id=body.responsavel_id,
        cliente_id=body.cliente_id,
        data_criacao=date.today(),
        data_prazo=body.data_prazo,
    )
    db.add(obra)
    await db.flush()

    versao = Versao(obra_id=obra.id, numero=1, criada_por=current_user.id)
    db.add(versao)
    await db.commit()
    await db.refresh(obra)
    await _set_cliente_nome(obra, db)
    return obra


@router.get("/{obra_id}", response_model=ObraOut)
async def get_obra(
    obra_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Obra).where(Obra.id == obra_id, Obra.empresa_id == current_user.empresa_id)
    )
    obra = result.scalar_one_or_none()
    if obra is None:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    await _set_cliente_nome(obra, db)
    return obra


@router.patch("/{obra_id}", response_model=ObraOut)
async def update_obra(
    obra_id: int,
    body: ObraUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Obra).where(Obra.id == obra_id, Obra.empresa_id == current_user.empresa_id)
    )
    obra = result.scalar_one_or_none()
    if obra is None:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    if body.cliente_id is not None:
        await _validate_cliente_id(body.cliente_id, current_user.empresa_id, db)
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(obra, field, value)
    await db.commit()
    await db.refresh(obra)
    await _set_cliente_nome(obra, db)
    return obra


@router.get("/{obra_id}/versoes", response_model=List[VersaoOut])
async def list_versoes(
    obra_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(
        select(Obra).where(Obra.id == obra_id, Obra.empresa_id == current_user.empresa_id)
    )
    if r.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    result = await db.execute(
        select(Versao)
        .where(Versao.obra_id == obra_id, Versao.deletada_em == None)
        .order_by(Versao.numero)
    )
    return result.scalars().all()


@router.post("/{obra_id}/versoes", response_model=VersaoOut, status_code=status.HTTP_201_CREATED)
async def create_versao(
    obra_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    r = await db.execute(
        select(Obra).where(Obra.id == obra_id, Obra.empresa_id == current_user.empresa_id)
    )
    if r.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    return await clone_versao(obra_id=obra_id, criada_por=current_user.id, db=db)
