from pathlib import Path
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.obra import Obra
from app.models.pacote_job import PacoteJob
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.schemas.pacote import PacoteJobOut
from app.services.pacote_service import processar_pacote

router = APIRouter(tags=["pacote"])


async def _get_versao(versao_id: int, current_user: Usuario, db: AsyncSession) -> Versao:
    result = await db.execute(
        select(Versao)
        .join(Obra, Versao.obra_id == Obra.id)
        .where(Versao.id == versao_id, Obra.empresa_id == current_user.empresa_id)
    )
    versao = result.scalar_one_or_none()
    if versao is None:
        raise HTTPException(status_code=404, detail="Versão não encontrada")
    return versao


@router.post("/versoes/{versao_id}/pacote", response_model=PacoteJobOut, status_code=201)
async def create_pacote(
    versao_id: int,
    background_tasks: BackgroundTasks,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao(versao_id, current_user, db)

    result = await db.execute(
        select(PacoteJob).where(
            PacoteJob.versao_id == versao_id,
            PacoteJob.status.in_(["pendente", "processando"]),
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Job já em andamento para esta versão")

    job = PacoteJob(
        versao_id=versao_id,
        empresa_id=current_user.empresa_id,
        status="pendente",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)

    background_tasks.add_task(processar_pacote, job.id, versao_id)
    return job


@router.get("/versoes/{versao_id}/pacote", response_model=PacoteJobOut)
async def get_pacote(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao(versao_id, current_user, db)
    result = await db.execute(
        select(PacoteJob)
        .where(PacoteJob.versao_id == versao_id)
        .order_by(PacoteJob.criado_em.desc())
        .limit(1)
    )
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Nenhum job encontrado")
    return job


@router.get("/versoes/{versao_id}/pacote/download")
async def download_pacote(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao(versao_id, current_user, db)
    result = await db.execute(
        select(PacoteJob)
        .where(PacoteJob.versao_id == versao_id)
        .order_by(PacoteJob.criado_em.desc())
        .limit(1)
    )
    job = result.scalar_one_or_none()
    if job is None or job.status != "pronto":
        raise HTTPException(status_code=404, detail="Pacote não disponível")

    base = Path(settings.pacotes_dir).resolve()
    filepath = (base / job.url_download).resolve()
    if not filepath.is_relative_to(base):
        raise HTTPException(status_code=400, detail="Caminho inválido")
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor")

    return FileResponse(
        path=str(filepath),
        media_type="application/zip",
        filename=f"pacote-v{versao_id}.zip",
    )
