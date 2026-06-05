from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.fornecedor import Fornecedor
from app.models.usuario import Usuario
from app.schemas.fornecedor import FornecedorCreate, FornecedorOut, FornecedorUpdate

router = APIRouter(prefix="/fornecedores", tags=["fornecedores"])


async def _get_fornecedor(forn_id: int, current_user: Usuario, db: AsyncSession) -> Fornecedor:
    result = await db.execute(
        select(Fornecedor).where(
            Fornecedor.id == forn_id,
            Fornecedor.empresa_id == current_user.empresa_id,
        )
    )
    f = result.scalar_one_or_none()
    if f is None:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    return f


@router.get("", response_model=List[FornecedorOut])
async def list_fornecedores(
    q: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Fornecedor).where(Fornecedor.empresa_id == current_user.empresa_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(Fornecedor.nome.ilike(like), Fornecedor.cnpj.ilike(like))
        )
    if categoria:
        stmt = stmt.where(Fornecedor.categorias.ilike(f"%{categoria}%"))
    stmt = stmt.order_by(Fornecedor.nome)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=FornecedorOut, status_code=status.HTTP_201_CREATED)
async def create_fornecedor(
    body: FornecedorCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.cnpj:
        dup = await db.execute(
            select(Fornecedor).where(
                Fornecedor.empresa_id == current_user.empresa_id,
                Fornecedor.cnpj == body.cnpj,
            )
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="CNPJ já cadastrado")
    f = Fornecedor(empresa_id=current_user.empresa_id, **body.model_dump())
    db.add(f)
    await db.commit()
    await db.refresh(f)
    return f


@router.get("/{fornecedor_id}", response_model=FornecedorOut)
async def get_fornecedor(
    fornecedor_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_fornecedor(fornecedor_id, current_user, db)


@router.patch("/{fornecedor_id}", response_model=FornecedorOut)
async def update_fornecedor(
    fornecedor_id: int,
    body: FornecedorUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    f = await _get_fornecedor(fornecedor_id, current_user, db)
    if body.cnpj and body.cnpj != f.cnpj:
        dup = await db.execute(
            select(Fornecedor).where(
                Fornecedor.empresa_id == current_user.empresa_id,
                Fornecedor.cnpj == body.cnpj,
            )
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="CNPJ já cadastrado")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(f, field, value)
    await db.commit()
    await db.refresh(f)
    return f


@router.delete("/{fornecedor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fornecedor(
    fornecedor_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    f = await _get_fornecedor(fornecedor_id, current_user, db)
    await db.delete(f)
    await db.commit()
