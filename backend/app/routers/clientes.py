from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.cliente import Cliente
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.schemas.cliente import ClienteCreate, ClienteOut, ClienteUpdate
from app.schemas.obra import ObraOut

router = APIRouter(prefix="/clientes", tags=["clientes"])


async def _get_cliente(cliente_id: int, current_user: Usuario, db: AsyncSession) -> Cliente:
    result = await db.execute(
        select(Cliente).where(
            Cliente.id == cliente_id,
            Cliente.empresa_id == current_user.empresa_id,
        )
    )
    c = result.scalar_one_or_none()
    if c is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return c


@router.get("", response_model=List[ClienteOut])
async def list_clientes(
    q: Optional[str] = Query(None),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Cliente).where(Cliente.empresa_id == current_user.empresa_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(Cliente.nome.ilike(like), Cliente.cpf_cnpj.ilike(like))
        )
    stmt = stmt.order_by(Cliente.nome)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
async def create_cliente(
    body: ClienteCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.cpf_cnpj:
        dup = await db.execute(
            select(Cliente).where(
                Cliente.empresa_id == current_user.empresa_id,
                Cliente.cpf_cnpj == body.cpf_cnpj,
            )
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="CPF/CNPJ já cadastrado")
    c = Cliente(empresa_id=current_user.empresa_id, **body.model_dump())
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


@router.get("/{cliente_id}", response_model=ClienteOut)
async def get_cliente(
    cliente_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_cliente(cliente_id, current_user, db)


@router.patch("/{cliente_id}", response_model=ClienteOut)
async def update_cliente(
    cliente_id: int,
    body: ClienteUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c = await _get_cliente(cliente_id, current_user, db)
    if body.cpf_cnpj and body.cpf_cnpj != c.cpf_cnpj:
        dup = await db.execute(
            select(Cliente).where(
                Cliente.empresa_id == current_user.empresa_id,
                Cliente.cpf_cnpj == body.cpf_cnpj,
            )
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="CPF/CNPJ já cadastrado")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(c, field, value)
    await db.commit()
    await db.refresh(c)
    return c


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cliente(
    cliente_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c = await _get_cliente(cliente_id, current_user, db)
    count_result = await db.execute(
        select(func.count()).select_from(Obra).where(Obra.cliente_id == cliente_id)
    )
    if count_result.scalar() > 0:
        raise HTTPException(
            status_code=409,
            detail="Cliente possui obras vinculadas e não pode ser excluído",
        )
    await db.delete(c)
    await db.commit()


@router.get("/{cliente_id}/obras", response_model=List[ObraOut])
async def get_cliente_obras(
    cliente_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_cliente(cliente_id, current_user, db)
    result = await db.execute(
        select(Obra).where(
            Obra.cliente_id == cliente_id,
            Obra.empresa_id == current_user.empresa_id,
        ).order_by(Obra.data_criacao.desc())
    )
    return result.scalars().all()
