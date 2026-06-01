from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.schemas.versao import VersaoOut

router = APIRouter(prefix="/versoes", tags=["versoes"])


async def _get_versao_da_empresa(versao_id: int, current_user: Usuario, db: AsyncSession) -> Versao:
    result = await db.execute(
        select(Versao)
        .join(Obra, Versao.obra_id == Obra.id)
        .where(Versao.id == versao_id, Obra.empresa_id == current_user.empresa_id)
    )
    v = result.scalar_one_or_none()
    if v is None:
        raise HTTPException(status_code=404, detail="Versão não encontrada")
    return v


@router.delete("/{versao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_versao(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    versao = await _get_versao_da_empresa(versao_id, current_user, db)
    versao.deletada_em = datetime.utcnow()
    await db.commit()


@router.post("/{versao_id}/restore", response_model=VersaoOut)
async def restore_versao(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    versao = await _get_versao_da_empresa(versao_id, current_user, db)

    if versao.deletada_em is None:
        raise HTTPException(status_code=409, detail="Versão não está soft-deleted")

    r = await db.execute(
        select(Versao).where(
            Versao.obra_id == versao.obra_id,
            Versao.bloqueada == False,
            Versao.deletada_em == None,
        )
    )
    if r.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=409,
            detail="Obra já possui versão ativa; bloqueie-a antes de restaurar",
        )

    versao.deletada_em = None
    await db.commit()
    await db.refresh(versao)
    return versao
