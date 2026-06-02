from calendar import monthrange
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.medicao import Medicao
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.schemas.medicao import MedicaoIn, MedicaoOut, MedicaoPatch

router = APIRouter(tags=["medicoes"])


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


@router.get("/versoes/{versao_id}/medicoes", response_model=list[MedicaoOut])
async def list_medicoes(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao_acesso(versao_id, current_user, db)
    result = await db.execute(
        select(Medicao)
        .where(Medicao.versao_id == versao_id)
        .order_by(Medicao.periodo_inicio.desc())
    )
    return result.scalars().all()


@router.post(
    "/versoes/{versao_id}/medicoes",
    response_model=MedicaoOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_medicao(
    versao_id: int,
    body: MedicaoIn,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao_ativa(versao_id, current_user, db)

    year, month = int(body.mes.split("-")[0]), int(body.mes.split("-")[1])
    periodo_inicio = date(year, month, 1)
    _, last_day = monthrange(year, month)
    periodo_fim = date(year, month, last_day)

    dup = await db.execute(
        select(Medicao).where(
            Medicao.versao_id == versao_id,
            Medicao.periodo_inicio == periodo_inicio,
        )
    )
    if dup.scalar_one_or_none():
        raise HTTPException(status_code=422, detail="Já existe uma medição para este mês")

    last = await db.execute(
        select(Medicao)
        .where(
            Medicao.versao_id == versao_id,
            Medicao.periodo_inicio < periodo_inicio,
        )
        .order_by(Medicao.periodo_inicio.desc())
        .limit(1)
    )
    last_medicao = last.scalar_one_or_none()
    linhas_json = dict(last_medicao.linhas_json) if last_medicao else {}

    medicao = Medicao(
        versao_id=versao_id,
        periodo_inicio=periodo_inicio,
        periodo_fim=periodo_fim,
        criada_por=current_user.id,
        linhas_json=linhas_json,
    )
    db.add(medicao)
    await db.commit()
    await db.refresh(medicao)
    return medicao


@router.patch(
    "/versoes/{versao_id}/medicoes/{medicao_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def update_medicao(
    versao_id: int,
    medicao_id: int,
    body: MedicaoPatch,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao_ativa(versao_id, current_user, db)

    result = await db.execute(
        select(Medicao).where(
            Medicao.id == medicao_id,
            Medicao.versao_id == versao_id,
        )
    )
    medicao = result.scalar_one_or_none()
    if medicao is None:
        raise HTTPException(status_code=404, detail="Medição não encontrada")

    medicao.linhas_json = body.linhas_json
    await db.commit()
