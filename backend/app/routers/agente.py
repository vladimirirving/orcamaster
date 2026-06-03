from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.composicao import Composicao
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.schemas.agente import AgenteRequest, ImportarRequest, ImportarResult
from app.services.agente_service import gerar_proposta_stream
from app.services.totais_service import recalc_totais_versao

router = APIRouter(tags=["agente"])


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
    versao = result.scalar_one_or_none()
    if versao is None:
        raise HTTPException(status_code=409, detail="Versão não encontrada ou não está ativa")
    return versao


@router.post("/versoes/{versao_id}/agente/gerar")
async def gerar(
    versao_id: int,
    body: AgenteRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao(versao_id, current_user, db)
    return StreamingResponse(
        gerar_proposta_stream(body.descricao, versao_id, current_user.empresa_id, db),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/versoes/{versao_id}/agente/importar", response_model=ImportarResult)
async def importar(
    versao_id: int,
    body: ImportarRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao_ativa(versao_id, current_user, db)

    all_ids = {item.composicao_id for grupo in body.grupos for item in grupo.itens}
    comp_map: dict[int, Composicao] = {}
    for comp_id in all_ids:
        result = await db.execute(
            select(Composicao).where(
                Composicao.id == comp_id,
                or_(Composicao.empresa_id.is_(None), Composicao.empresa_id == current_user.empresa_id),
            )
        )
        comp = result.scalar_one_or_none()
        if comp is None:
            raise HTTPException(status_code=422, detail=f"Composição {comp_id} não encontrada")
        comp_map[comp_id] = comp

    r_max = await db.execute(
        select(func.coalesce(func.max(Grupo.ordem), -1)).where(Grupo.versao_id == versao_id)
    )
    next_ordem = r_max.scalar() + 1

    grupos_criados = 0
    itens_criados = 0

    for i, grupo_req in enumerate(body.grupos):
        grupo = Grupo(versao_id=versao_id, nome=grupo_req.nome, ordem=next_ordem + i)
        db.add(grupo)
        await db.flush()

        for j, item_req in enumerate(grupo_req.itens):
            comp = comp_map[item_req.composicao_id]
            db.add(Item(
                grupo_id=grupo.id,
                composicao_id=comp.id,
                ordem=j,
                quantidade=Decimal(str(item_req.quantidade)),
                unidade=item_req.unidade,
                preco_unitario_sem_bdi=comp.preco_unitario,
            ))
            itens_criados += 1

        grupos_criados += 1

    await db.flush()
    await recalc_totais_versao(versao_id, db)
    await db.commit()

    return ImportarResult(grupos_criados=grupos_criados, itens_criados=itens_criados)
