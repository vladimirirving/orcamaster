import io

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.schemas.planilha_import import ImportarPlanilhaResult
from app.services.importar_planilha_service import gerar_template_bytes, importar_planilha

router = APIRouter(tags=["planilha_import"])


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
        .with_for_update()
    )
    versao = result.scalar_one_or_none()
    if versao is None:
        raise HTTPException(status_code=409, detail="Versão não encontrada ou não está ativa")
    return versao


@router.get("/versoes/{versao_id}/planilha/template")
async def download_template(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
):
    content = gerar_template_bytes()
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="template-planilha-v{versao_id}.xlsx"'},
    )


@router.post("/versoes/{versao_id}/planilha/importar", response_model=ImportarPlanilhaResult)
async def importar(
    versao_id: int,
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    _XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    _MAX_BYTES = 10 * 1024 * 1024  # 10 MB

    if file.content_type not in (_XLSX_MIME, "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Somente arquivos .xlsx são aceitos.")

    await _get_versao_ativa(versao_id, current_user, db)
    conteudo = await file.read(_MAX_BYTES + 1)
    if len(conteudo) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="Arquivo muito grande. Limite: 10 MB.")
    return await importar_planilha(
        versao_id=versao_id,
        empresa_id=current_user.empresa_id,
        conteudo=conteudo,
        db=db,
    )
