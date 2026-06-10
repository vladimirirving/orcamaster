import io
import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse, StreamingResponse
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
    DiarioCreate, DiarioUpdate, DiarioOut, DiarioListItem, DiarioFotoOut,
)

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FOTO_BYTES = 5 * 1024 * 1024  # 5 MB
MAX_FOTOS_POR_ENTRADA = 5

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


@router.post(
    "/obras/{obra_id}/diario/{entry_id}/fotos",
    response_model=DiarioFotoOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_foto(
    obra_id: int,
    entry_id: int,
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_entrada(obra_id, entry_id, current_user, db)

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=422, detail="Tipo de arquivo não suportado. Use JPEG, PNG ou WebP.")

    count_r = await db.execute(
        select(func.count()).select_from(DiarioFoto).where(DiarioFoto.diario_id == entry_id)
    )
    if (count_r.scalar() or 0) >= MAX_FOTOS_POR_ENTRADA:
        raise HTTPException(status_code=422, detail=f"Limite de {MAX_FOTOS_POR_ENTRADA} fotos por entrada atingido")

    contents = await file.read()
    if len(contents) > MAX_FOTO_BYTES:
        raise HTTPException(status_code=422, detail="Arquivo muito grande. Máximo 5MB.")

    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "jpg"
    filename = f"{entry_id}_{uuid.uuid4().hex}.{ext}"
    diario_dir = settings.diario_dir
    os.makedirs(diario_dir, exist_ok=True)
    path = os.path.join(diario_dir, filename)
    with open(path, "wb") as f:
        f.write(contents)

    foto = DiarioFoto(
        diario_id=entry_id,
        nome_original=file.filename or filename,
        caminho=filename,
        tamanho_bytes=len(contents),
    )
    db.add(foto)
    await db.commit()
    await db.refresh(foto)
    return foto


@router.get("/obras/{obra_id}/diario/{entry_id}/fotos/{foto_id}")
async def get_foto(
    obra_id: int,
    entry_id: int,
    foto_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_entrada(obra_id, entry_id, current_user, db)
    result = await db.execute(
        select(DiarioFoto).where(DiarioFoto.id == foto_id, DiarioFoto.diario_id == entry_id)
    )
    foto = result.scalar_one_or_none()
    if foto is None:
        raise HTTPException(status_code=404, detail="Foto não encontrada")
    path = os.path.join(settings.diario_dir, foto.caminho)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    return FileResponse(path, filename=foto.nome_original)


@router.delete(
    "/obras/{obra_id}/diario/{entry_id}/fotos/{foto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_foto(
    obra_id: int,
    entry_id: int,
    foto_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_entrada(obra_id, entry_id, current_user, db)
    result = await db.execute(
        select(DiarioFoto).where(DiarioFoto.id == foto_id, DiarioFoto.diario_id == entry_id)
    )
    foto = result.scalar_one_or_none()
    if foto is None:
        raise HTTPException(status_code=404, detail="Foto não encontrada")
    path = os.path.join(settings.diario_dir, foto.caminho)
    if os.path.exists(path):
        os.remove(path)
    await db.delete(foto)
    await db.commit()


@router.get("/obras/{obra_id}/diario/{entry_id}/rdo.pdf")
async def download_rdo(
    obra_id: int,
    entry_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.diario_pdf import gerar_rdo_bytes
    entry = await _get_entrada(obra_id, entry_id, current_user, db)
    pdf_bytes = await gerar_rdo_bytes(entry_id, db)
    nome = f"RDO_{entry.data.strftime('%Y-%m-%d')}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{nome}"'},
    )
