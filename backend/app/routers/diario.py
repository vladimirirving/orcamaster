import os
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.diario import DiarioObra, DiarioFoto
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.schemas.diario import (
    DiarioCreate, DiarioUpdate, DiarioOut, DiarioListItem,
)

router = APIRouter(tags=["diario"])


async def _get_obra(obra_id: int, current_user: Usuario, db: AsyncSession) -> Obra:
    result = await db.execute(
        select(Obra).where(Obra.id == obra_id, Obra.empresa_id == current_user.empresa_id)
    )
    obra = result.scalar_one_or_none()
    if obra is None:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    return obra


async def _get_entrada(
    obra_id: int, entry_id: int, current_user: Usuario, db: AsyncSession
) -> DiarioObra:
    await _get_obra(obra_id, current_user, db)
    result = await db.execute(
        select(DiarioObra).where(
            DiarioObra.id == entry_id,
            DiarioObra.obra_id == obra_id,
        )
    )
    entry = result.scalar_one_or_none()
    if entry is None:
        raise HTTPException(status_code=404, detail="Entrada não encontrada")
    return entry


@router.get("/obras/{obra_id}/diario", response_model=List[DiarioListItem])
async def list_entradas(
    obra_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_obra(obra_id, current_user, db)
    result = await db.execute(
        select(DiarioObra).where(DiarioObra.obra_id == obra_id)
        .order_by(DiarioObra.data.desc())
    )
    entradas = result.scalars().all()
    items = []
    for e in entradas:
        count_r = await db.execute(
            select(func.count()).select_from(DiarioFoto).where(DiarioFoto.diario_id == e.id)
        )
        item = DiarioListItem(
            id=e.id, obra_id=e.obra_id, data=e.data, clima=e.clima,
            turnos=e.turnos, efetivo=e.efetivo, atividades=e.atividades[:100],
            qtd_fotos=count_r.scalar() or 0,
        )
        items.append(item)
    return items


@router.post("/obras/{obra_id}/diario", response_model=DiarioOut, status_code=status.HTTP_201_CREATED)
async def create_entrada(
    obra_id: int,
    body: DiarioCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    obra = await _get_obra(obra_id, current_user, db)
    dup = await db.execute(
        select(DiarioObra).where(DiarioObra.obra_id == obra_id, DiarioObra.data == body.data)
    )
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Já existe uma entrada para esta data")
    entry = DiarioObra(
        obra_id=obra_id,
        empresa_id=obra.empresa_id,
        criado_por=current_user.id,
        **body.model_dump(),
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    set_committed_value(entry, "fotos", [])
    return entry


@router.get("/obras/{obra_id}/diario/{entry_id}", response_model=DiarioOut)
async def get_entrada(
    obra_id: int,
    entry_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = await _get_entrada(obra_id, entry_id, current_user, db)
    fotos_r = await db.execute(
        select(DiarioFoto).where(DiarioFoto.diario_id == entry_id).order_by(DiarioFoto.id)
    )
    set_committed_value(entry, "fotos", fotos_r.scalars().all())
    return entry


@router.patch("/obras/{obra_id}/diario/{entry_id}", response_model=DiarioOut)
async def update_entrada(
    obra_id: int,
    entry_id: int,
    body: DiarioUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = await _get_entrada(obra_id, entry_id, current_user, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(entry, field, value)
    await db.commit()
    await db.refresh(entry)
    fotos_r = await db.execute(
        select(DiarioFoto).where(DiarioFoto.diario_id == entry_id).order_by(DiarioFoto.id)
    )
    set_committed_value(entry, "fotos", fotos_r.scalars().all())
    return entry


@router.delete("/obras/{obra_id}/diario/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_entrada(
    obra_id: int,
    entry_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    entry = await _get_entrada(obra_id, entry_id, current_user, db)
    fotos_r = await db.execute(
        select(DiarioFoto).where(DiarioFoto.diario_id == entry_id)
    )
    for foto in fotos_r.scalars().all():
        path = os.path.join(settings.diario_dir, foto.caminho)
        if os.path.exists(path):
            os.remove(path)
    await db.delete(entry)
    await db.commit()
