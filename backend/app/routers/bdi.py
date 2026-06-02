from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.bdi import BDI
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.schemas.bdi import BDICreate, BDIOut
from app.services.bdi_service import aplicar_bdi_versao, zerar_bdi_versao
from app.services.totais_service import recalc_totais_versao

router = APIRouter(tags=["bdi"])


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


@router.get("/versoes/{versao_id}/bdi", response_model=BDIOut)
async def get_bdi(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao_acesso(versao_id, current_user, db)
    r = await db.execute(select(BDI).where(BDI.versao_id == versao_id))
    bdi = r.scalar_one_or_none()
    if bdi is None:
        raise HTTPException(status_code=404, detail="BDI não configurado para esta versão")
    return bdi


@router.put("/versoes/{versao_id}/bdi", response_model=BDIOut)
async def upsert_bdi(
    versao_id: int,
    body: BDICreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    versao = await _get_versao_ativa(versao_id, current_user, db)

    denominador = 1 - body.iss - body.pis - body.cofins
    if denominador <= 0:
        raise HTTPException(
            status_code=422,
            detail="A soma de ISS + PIS + COFINS deve ser menor que 100%",
        )
    bdi_composto = ((1 + body.ac + body.sg + body.r + body.df + body.lucro) / denominador) - 1

    r = await db.execute(select(BDI).where(BDI.versao_id == versao_id))
    bdi = r.scalar_one_or_none()

    if bdi is None:
        bdi = BDI(
            versao_id=versao_id,
            ac=body.ac, sg=body.sg, r=body.r, df=body.df, lucro=body.lucro,
            iss=body.iss, pis=body.pis, cofins=body.cofins,
            bdi_composto=Decimal(str(bdi_composto)),
        )
        db.add(bdi)
    else:
        bdi.ac = body.ac
        bdi.sg = body.sg
        bdi.r = body.r
        bdi.df = body.df
        bdi.lucro = body.lucro
        bdi.iss = body.iss
        bdi.pis = body.pis
        bdi.cofins = body.cofins
        bdi.bdi_composto = Decimal(str(bdi_composto))

    await db.flush()
    await aplicar_bdi_versao(versao_id, Decimal(str(bdi_composto)), db)
    await recalc_totais_versao(versao_id, db)
    await db.refresh(versao)
    await db.commit()
    await db.refresh(bdi)
    return bdi


@router.delete("/versoes/{versao_id}/bdi", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bdi(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    versao = await _get_versao_ativa(versao_id, current_user, db)

    r = await db.execute(select(BDI).where(BDI.versao_id == versao_id))
    bdi = r.scalar_one_or_none()
    if bdi is None:
        raise HTTPException(status_code=404, detail="BDI não configurado para esta versão")

    await zerar_bdi_versao(versao_id, db)
    await db.flush()
    await db.delete(bdi)
    await db.flush()
    await recalc_totais_versao(versao_id, db)
    await db.refresh(versao)
    await db.commit()
