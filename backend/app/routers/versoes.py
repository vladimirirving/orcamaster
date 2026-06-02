from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.schemas.versao import VersaoOut
from app.models.bdi import BDI
from app.models.grupo import Grupo
from app.models.item import Item
from app.services.totais_service import recalc_totais_versao

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


@router.post("/{versao_id}/duplicar", response_model=VersaoOut, status_code=status.HTTP_201_CREATED)
async def duplicar_versao(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    versao_orig = await _get_versao_da_empresa(versao_id, current_user, db)
    if versao_orig.bloqueada or versao_orig.deletada_em is not None:
        raise HTTPException(status_code=409, detail="Versão não está ativa")

    r_max = await db.execute(
        select(func.max(Versao.numero)).where(Versao.obra_id == versao_orig.obra_id)
    )
    proximo_numero = (r_max.scalar() or 0) + 1

    nova_versao = Versao(
        obra_id=versao_orig.obra_id,
        numero=proximo_numero,
        nome=versao_orig.nome,
        criada_por=current_user.id,
        bloqueada=False,
    )
    db.add(nova_versao)
    await db.flush()

    r_raizes = await db.execute(
        select(Grupo)
        .where(Grupo.versao_id == versao_id, Grupo.pai_id.is_(None))
        .order_by(Grupo.ordem)
    )
    for grupo_orig in r_raizes.scalars().all():
        novo_grupo = Grupo(
            versao_id=nova_versao.id,
            pai_id=None,
            nome=grupo_orig.nome,
            codigo=grupo_orig.codigo,
            ordem=grupo_orig.ordem,
        )
        db.add(novo_grupo)
        await db.flush()

        r_filhos = await db.execute(
            select(Grupo).where(Grupo.pai_id == grupo_orig.id).order_by(Grupo.ordem)
        )
        for sub_orig in r_filhos.scalars().all():
            novo_sub = Grupo(
                versao_id=nova_versao.id,
                pai_id=novo_grupo.id,
                nome=sub_orig.nome,
                codigo=sub_orig.codigo,
                ordem=sub_orig.ordem,
            )
            db.add(novo_sub)
            await db.flush()

            r_itens_sub = await db.execute(
                select(Item).where(Item.grupo_id == sub_orig.id).order_by(Item.ordem)
            )
            for item_orig in r_itens_sub.scalars().all():
                db.add(Item(
                    grupo_id=novo_sub.id,
                    ordem=item_orig.ordem,
                    composicao_id=item_orig.composicao_id,
                    quantidade=item_orig.quantidade,
                    unidade=item_orig.unidade,
                    preco_unitario_sem_bdi=item_orig.preco_unitario_sem_bdi,
                    preco_unitario_com_bdi=item_orig.preco_unitario_com_bdi,
                    etiqueta_revisao=item_orig.etiqueta_revisao,
                    requer_revisao=item_orig.requer_revisao,
                ))
                # CronogramaLinha not copied — Plan 5 scope

        r_itens_raiz = await db.execute(
            select(Item).where(Item.grupo_id == grupo_orig.id).order_by(Item.ordem)
        )
        for item_orig in r_itens_raiz.scalars().all():
            db.add(Item(
                grupo_id=novo_grupo.id,
                ordem=item_orig.ordem,
                composicao_id=item_orig.composicao_id,
                quantidade=item_orig.quantidade,
                unidade=item_orig.unidade,
                preco_unitario_sem_bdi=item_orig.preco_unitario_sem_bdi,
                preco_unitario_com_bdi=item_orig.preco_unitario_com_bdi,
                etiqueta_revisao=item_orig.etiqueta_revisao,
                requer_revisao=item_orig.requer_revisao,
            ))
            # CronogramaLinha not copied — Plan 5 scope

    r_bdi = await db.execute(select(BDI).where(BDI.versao_id == versao_id))
    bdi_orig = r_bdi.scalar_one_or_none()
    if bdi_orig is not None:
        # historico_json intentionally omitted — reserved for future audit (Plan 4a spec)
        db.add(BDI(
            versao_id=nova_versao.id,
            ac=bdi_orig.ac, sg=bdi_orig.sg, r=bdi_orig.r, df=bdi_orig.df,
            lucro=bdi_orig.lucro, iss=bdi_orig.iss, pis=bdi_orig.pis,
            cofins=bdi_orig.cofins, bdi_composto=bdi_orig.bdi_composto,
        ))

    await db.flush()
    await recalc_totais_versao(nova_versao.id, db)
    await db.refresh(nova_versao)
    await db.commit()
    return nova_versao
