import os
from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import set_committed_value
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models.contrato import Contrato, Aditivo
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.schemas.contrato import (
    ContratoCreate, ContratoUpdate, ContratoOut,
    AditivoCreate, AditivoUpdate, AditivoOut,
)

router = APIRouter(tags=["contratos"])

MAX_PDF_BYTES = 20 * 1024 * 1024  # 20 MB


async def _get_obra(obra_id: int, current_user: Usuario, db: AsyncSession) -> Obra:
    result = await db.execute(
        select(Obra).where(Obra.id == obra_id, Obra.empresa_id == current_user.empresa_id)
    )
    obra = result.scalar_one_or_none()
    if obra is None:
        raise HTTPException(status_code=404, detail="Obra não encontrada")
    return obra


async def _get_contrato(contrato_id: int, current_user: Usuario, db: AsyncSession) -> Contrato:
    result = await db.execute(
        select(Contrato)
        .join(Obra, Obra.id == Contrato.obra_id)
        .where(Contrato.id == contrato_id, Obra.empresa_id == current_user.empresa_id)
    )
    contrato = result.scalar_one_or_none()
    if contrato is None:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
    return contrato


async def _get_aditivo(aditivo_id: int, current_user: Usuario, db: AsyncSession) -> Aditivo:
    result = await db.execute(
        select(Aditivo)
        .join(Contrato, Contrato.id == Aditivo.contrato_id)
        .join(Obra, Obra.id == Contrato.obra_id)
        .where(Aditivo.id == aditivo_id, Obra.empresa_id == current_user.empresa_id)
    )
    aditivo = result.scalar_one_or_none()
    if aditivo is None:
        raise HTTPException(status_code=404, detail="Aditivo não encontrado")
    return aditivo


def _build_contrato_out(contrato: Contrato, aditivos: list[Aditivo]) -> ContratoOut:
    valor_atual = contrato.valor_original + sum(
        (a.delta_valor or Decimal("0")) for a in aditivos
    )
    data_fim_atual = contrato.data_fim
    for a in sorted(aditivos, key=lambda x: x.id):
        if a.nova_data_fim is not None:
            data_fim_atual = a.nova_data_fim
    set_committed_value(contrato, "aditivos", aditivos)
    data = {
        "id": contrato.id,
        "obra_id": contrato.obra_id,
        "numero": contrato.numero,
        "objeto": contrato.objeto,
        "valor_original": contrato.valor_original,
        "valor_atual": valor_atual,
        "data_assinatura": contrato.data_assinatura,
        "data_inicio": contrato.data_inicio,
        "data_fim": contrato.data_fim,
        "data_fim_atual": data_fim_atual,
        "contratante_nome": contrato.contratante_nome,
        "contratante_cnpj": contrato.contratante_cnpj,
        "contratado_nome": contrato.contratado_nome,
        "contratado_cnpj": contrato.contratado_cnpj,
        "arquivo_path": contrato.arquivo_path,
        "criado_em": contrato.criado_em,
        "aditivos": aditivos,
    }
    return ContratoOut.model_validate(data)


@router.get("/obras/{obra_id}/contratos", response_model=List[ContratoOut])
async def list_contratos(
    obra_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_obra(obra_id, current_user, db)
    result = await db.execute(
        select(Contrato)
        .where(Contrato.obra_id == obra_id)
        .order_by(Contrato.id)
        .options(selectinload(Contrato.aditivos))
    )
    contratos = result.scalars().all()
    return [_build_contrato_out(c, sorted(c.aditivos, key=lambda x: x.id)) for c in contratos]


@router.post("/obras/{obra_id}/contratos", response_model=ContratoOut, status_code=status.HTTP_201_CREATED)
async def create_contrato(
    obra_id: int,
    body: ContratoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_obra(obra_id, current_user, db)
    contrato = Contrato(obra_id=obra_id, **body.model_dump())
    db.add(contrato)
    await db.commit()
    await db.refresh(contrato)
    return _build_contrato_out(contrato, [])


@router.patch("/contratos/{contrato_id}", response_model=ContratoOut)
async def update_contrato(
    contrato_id: int,
    body: ContratoUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contrato = await _get_contrato(contrato_id, current_user, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(contrato, field, value)
    await db.commit()
    await db.refresh(contrato)
    ads_r = await db.execute(select(Aditivo).where(Aditivo.contrato_id == contrato_id).order_by(Aditivo.id))
    return _build_contrato_out(contrato, list(ads_r.scalars().all()))


@router.delete("/contratos/{contrato_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contrato(
    contrato_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contrato = await _get_contrato(contrato_id, current_user, db)
    # Collect file paths before commit so cascade doesn't lose aditivo IDs
    paths_to_delete = []
    contrato_pdf = os.path.join(settings.contratos_dir, f"c{contrato.id}.pdf")
    if os.path.exists(contrato_pdf):
        paths_to_delete.append(contrato_pdf)
    ads_r = await db.execute(select(Aditivo).where(Aditivo.contrato_id == contrato_id))
    for a in ads_r.scalars().all():
        path = os.path.join(settings.contratos_dir, f"a{a.id}.pdf")
        if os.path.exists(path):
            paths_to_delete.append(path)
    # Commit DB first — only delete files if DB succeeds
    await db.delete(contrato)
    await db.commit()
    for path in paths_to_delete:
        try:
            os.remove(path)
        except OSError:
            pass


@router.post("/contratos/{contrato_id}/upload", response_model=ContratoOut)
async def upload_contrato_pdf(
    contrato_id: int,
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=422, detail="Apenas arquivos PDF são aceitos")
    contrato = await _get_contrato(contrato_id, current_user, db)
    content = await file.read()
    if len(content) > MAX_PDF_BYTES:
        raise HTTPException(status_code=422, detail="Arquivo muito grande (máx. 20 MB)")
    os.makedirs(settings.contratos_dir, exist_ok=True)
    filename = f"c{contrato_id}.pdf"
    filepath = os.path.join(settings.contratos_dir, filename)
    with open(filepath, "wb") as f:
        f.write(content)
    contrato.arquivo_path = filename
    try:
        await db.commit()
    except Exception:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise
    await db.refresh(contrato)
    ads_r = await db.execute(select(Aditivo).where(Aditivo.contrato_id == contrato_id).order_by(Aditivo.id))
    return _build_contrato_out(contrato, list(ads_r.scalars().all()))


@router.get("/contratos/{contrato_id}/download")
async def download_contrato_pdf(
    contrato_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    contrato = await _get_contrato(contrato_id, current_user, db)
    if not contrato.arquivo_path:
        raise HTTPException(status_code=404, detail="Nenhum arquivo anexado")
    filepath = os.path.join(settings.contratos_dir, contrato.arquivo_path)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor")
    return FileResponse(filepath, media_type="application/pdf", filename=f"contrato-{contrato_id}.pdf")


@router.post("/contratos/{contrato_id}/aditivos", response_model=AditivoOut, status_code=status.HTTP_201_CREATED)
async def create_aditivo(
    contrato_id: int,
    body: AditivoCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_contrato(contrato_id, current_user, db)
    aditivo = Aditivo(contrato_id=contrato_id, **body.model_dump())
    db.add(aditivo)
    await db.commit()
    await db.refresh(aditivo)
    return aditivo


@router.patch("/aditivos/{aditivo_id}", response_model=AditivoOut)
async def update_aditivo(
    aditivo_id: int,
    body: AditivoUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    aditivo = await _get_aditivo(aditivo_id, current_user, db)
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(aditivo, field, value)
    await db.commit()
    await db.refresh(aditivo)
    return aditivo


@router.delete("/aditivos/{aditivo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_aditivo(
    aditivo_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    aditivo = await _get_aditivo(aditivo_id, current_user, db)
    pdf_path = os.path.join(settings.contratos_dir, aditivo.arquivo_path) if aditivo.arquivo_path else None
    # Commit DB first
    await db.delete(aditivo)
    await db.commit()
    if pdf_path and os.path.exists(pdf_path):
        try:
            os.remove(pdf_path)
        except OSError:
            pass


@router.post("/aditivos/{aditivo_id}/upload", response_model=AditivoOut)
async def upload_aditivo_pdf(
    aditivo_id: int,
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=422, detail="Apenas arquivos PDF são aceitos")
    aditivo = await _get_aditivo(aditivo_id, current_user, db)
    content = await file.read()
    if len(content) > MAX_PDF_BYTES:
        raise HTTPException(status_code=422, detail="Arquivo muito grande (máx. 20 MB)")
    os.makedirs(settings.contratos_dir, exist_ok=True)
    filename = f"a{aditivo_id}.pdf"
    filepath = os.path.join(settings.contratos_dir, filename)
    with open(filepath, "wb") as f:
        f.write(content)
    aditivo.arquivo_path = filename
    try:
        await db.commit()
    except Exception:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise
    await db.refresh(aditivo)
    return aditivo


@router.get("/aditivos/{aditivo_id}/download")
async def download_aditivo_pdf(
    aditivo_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    aditivo = await _get_aditivo(aditivo_id, current_user, db)
    if not aditivo.arquivo_path:
        raise HTTPException(status_code=404, detail="Nenhum arquivo anexado")
    filepath = os.path.join(settings.contratos_dir, aditivo.arquivo_path)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado no servidor")
    return FileResponse(filepath, media_type="application/pdf", filename=f"aditivo-{aditivo_id}.pdf")
