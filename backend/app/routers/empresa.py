from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.schemas.proposta import EmpresaConfigIn, EmpresaConfigOut

router = APIRouter(tags=["empresa"])


@router.get("/empresa", response_model=EmpresaConfigOut)
async def get_empresa(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Empresa).where(Empresa.id == current_user.empresa_id))
    return result.scalar_one()


@router.patch("/empresa", response_model=EmpresaConfigOut)
async def update_empresa(
    body: EmpresaConfigIn,
    admin: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Empresa).where(Empresa.id == admin.empresa_id))
    empresa = result.scalar_one()
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(empresa, field, value)
    await db.commit()
    await db.refresh(empresa)
    return empresa
