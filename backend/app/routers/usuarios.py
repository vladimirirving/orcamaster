from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioOut, UsuarioUpdate
from app.services.auth_service import hash_password

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


@router.get("", response_model=List[UsuarioOut])
async def list_usuarios(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Usuario).where(Usuario.empresa_id == current_user.empresa_id)
    )
    return result.scalars().all()


@router.post("", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
async def create_usuario(
    body: UsuarioCreate,
    admin: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    existing = await db.execute(select(Usuario).where(Usuario.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email já cadastrado")

    user = Usuario(
        empresa_id=admin.empresa_id,
        nome=body.nome,
        email=body.email,
        senha_hash=hash_password(body.senha),
        papel=body.papel,
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    await db.refresh(user)
    return user


@router.patch("/{usuario_id}", response_model=UsuarioOut)
async def update_usuario(
    usuario_id: int,
    body: UsuarioUpdate,
    admin: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Usuario).where(Usuario.id == usuario_id, Usuario.empresa_id == admin.empresa_id)
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if body.nome is not None:
        user.nome = body.nome
    if body.papel is not None:
        user.papel = body.papel
    if body.ativo is not None:
        user.ativo = body.ativo

    await db.commit()
    await db.refresh(user)
    return user
