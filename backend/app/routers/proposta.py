import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.empresa import Empresa
from app.models.obra import Obra
from app.models.proposta_config import PropostaConfig
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.schemas.proposta import PropostaConfigIn, PropostaConfigOut
from app.services.proposta_pdf import gerar_pdf_bytes

router = APIRouter(tags=["proposta"])


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


@router.get("/versoes/{versao_id}/proposta", response_model=PropostaConfigOut)
async def get_proposta(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao(versao_id, current_user, db)
    result = await db.execute(
        select(PropostaConfig).where(PropostaConfig.versao_id == versao_id)
    )
    pc = result.scalar_one_or_none()
    if pc is None:
        raise HTTPException(status_code=404, detail="Proposta não configurada")
    return pc


@router.put("/versoes/{versao_id}/proposta", response_model=PropostaConfigOut)
async def upsert_proposta(
    versao_id: int,
    body: PropostaConfigIn,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao(versao_id, current_user, db)
    result = await db.execute(
        select(PropostaConfig).where(PropostaConfig.versao_id == versao_id)
    )
    pc = result.scalar_one_or_none()

    if pc is None:
        empresa_result = await db.execute(
            select(Empresa).where(Empresa.id == current_user.empresa_id)
        )
        empresa = empresa_result.scalar_one()
        pc = PropostaConfig(
            versao_id=versao_id,
            validade_dias=body.validade_dias,
            data_proposta=body.data_proposta,
            declaracoes=body.declaracoes if body.declaracoes is not None else empresa.declaracoes_padrao,
        )
        db.add(pc)
    else:
        pc.validade_dias = body.validade_dias
        pc.data_proposta = body.data_proposta
        if 'declaracoes' in body.model_fields_set:
            pc.declaracoes = body.declaracoes

    await db.commit()
    await db.refresh(pc)
    return pc


@router.get("/versoes/{versao_id}/proposta/export")
async def export_proposta(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao(versao_id, current_user, db)
    pdf_bytes = await gerar_pdf_bytes(versao_id, db)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="proposta-v{versao_id}.pdf"'},
    )
