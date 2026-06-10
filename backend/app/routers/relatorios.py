from datetime import datetime
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.dependencies import get_current_user
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.medicao import Medicao
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.schemas.relatorios import (
    ComparativoItem, ComparativoOut,
    RelatorioMedicaoGrupo, RelatorioMedicaoOut,
)

router = APIRouter(tags=["relatorios"])


async def _get_versao(versao_id: int, current_user: Usuario, db: AsyncSession) -> Versao:
    result = await db.execute(
        select(Versao)
        .join(Obra, Versao.obra_id == Obra.id)
        .where(Versao.id == versao_id, Obra.empresa_id == current_user.empresa_id)
    )
    v = result.scalar_one_or_none()
    if v is None:
        raise HTTPException(status_code=404, detail="Versão não encontrada")
    return v


@router.get("/versoes/{versao_id}/relatorio-medicao", response_model=RelatorioMedicaoOut)
async def get_relatorio_medicao(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao(versao_id, current_user, db)

    # Grupos raiz da versão
    grupos_r = await db.execute(
        select(Grupo).where(Grupo.versao_id == versao_id, Grupo.pai_id.is_(None))
    )
    grupos_raiz = grupos_r.scalars().all()
    grupos_raiz_ids = {g.id for g in grupos_raiz}

    # Todos os grupos da versão (para resolver subgrupo → raiz)
    todos_grupos_r = await db.execute(
        select(Grupo).where(Grupo.versao_id == versao_id)
    )
    todos_grupos = {g.id: g for g in todos_grupos_r.scalars().all()}

    # Todos os itens da versão com grupo e cronograma_linha
    todos_itens_r = await db.execute(
        select(Item)
        .join(Grupo, Item.grupo_id == Grupo.id)
        .where(Grupo.versao_id == versao_id)
        .options(selectinload(Item.grupo), selectinload(Item.cronograma_linha))
    )
    todos_itens = todos_itens_r.scalars().all()

    # Última medição: MAX(periodo_fim), desempate por MAX(id)
    med_r = await db.execute(
        select(Medicao)
        .where(Medicao.versao_id == versao_id)
        .order_by(Medicao.periodo_fim.desc(), Medicao.id.desc())
        .limit(1)
    )
    ultima_medicao = med_r.scalar_one_or_none()
    linhas_json: dict = ultima_medicao.linhas_json if ultima_medicao else {}

    # Mês atual no formato YYYY-MM
    mes_atual = datetime.now().strftime("%Y-%m")

    # Agrupar itens por grupo raiz (subgrupo → pai)
    itens_por_grupo: dict[int, list[Item]] = {g.id: [] for g in grupos_raiz}
    for item in todos_itens:
        g = todos_grupos.get(item.grupo_id)
        if g is None:
            continue
        raiz_id = g.id if g.pai_id is None else (g.pai_id if g.pai_id in grupos_raiz_ids else None)
        if raiz_id is not None:
            itens_por_grupo.setdefault(raiz_id, []).append(item)

    resultado = []
    for grupo in sorted(grupos_raiz, key=lambda g: g.ordem):
        itens_grupo = itens_por_grupo.get(grupo.id, [])
        if not itens_grupo:
            continue

        total_grupo = sum(float(i.total) for i in itens_grupo)

        # planejado_pct: média ponderada pelo total do item
        planejado_num = 0.0
        planejado_den = 0.0
        for item in itens_grupo:
            peso = float(item.total)
            if item.cronograma_linha and peso > 0:
                dist = item.cronograma_linha.distribuicao_json or {}
                pct = sum(v for k, v in dist.items() if k <= mes_atual)
                planejado_num += pct * peso
                planejado_den += peso
        planejado_pct = planejado_num / planejado_den if planejado_den > 0 else 0.0

        # realizado_pct: média ponderada pelo total do item
        realizado_num = 0.0
        realizado_den = 0.0
        for item in itens_grupo:
            peso = float(item.total)
            pct = float(linhas_json.get(str(item.id), 0))
            if peso > 0:
                realizado_num += pct * peso
                realizado_den += peso
        realizado_pct = realizado_num / realizado_den if realizado_den > 0 else 0.0

        valor_medido = Decimal(str(round(sum(
            float(i.total) * float(linhas_json.get(str(i.id), 0)) / 100
            for i in itens_grupo
        ), 2)))

        resultado.append(RelatorioMedicaoGrupo(
            grupo_id=grupo.id,
            grupo_nome=grupo.nome,
            planejado_pct=round(planejado_pct, 2),
            realizado_pct=round(realizado_pct, 2),
            desvio_pct=round(realizado_pct - planejado_pct, 2),
            valor_medido=valor_medido,
            valor_total=Decimal(str(round(total_grupo, 2))),
        ))

    return RelatorioMedicaoOut(
        versao_id=versao_id,
        ultima_medicao_id=ultima_medicao.id if ultima_medicao else None,
        periodo_fim=ultima_medicao.periodo_fim if ultima_medicao else None,
        grupos=resultado,
    )


@router.get("/obras/{obra_id}/comparar", response_model=ComparativoOut)
async def comparar_versoes(
    obra_id: int,
    v1: int = Query(...),
    v2: int = Query(...),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verificar que a obra pertence à empresa
    obra_r = await db.execute(
        select(Obra).where(Obra.id == obra_id, Obra.empresa_id == current_user.empresa_id)
    )
    obra = obra_r.scalar_one_or_none()
    if obra is None:
        raise HTTPException(status_code=404, detail="Obra não encontrada")

    # Carregar as duas versões — ambas devem pertencer à obra
    versao1_r = await db.execute(
        select(Versao).where(Versao.id == v1, Versao.obra_id == obra_id)
    )
    versao1 = versao1_r.scalar_one_or_none()
    versao2_r = await db.execute(
        select(Versao).where(Versao.id == v2, Versao.obra_id == obra_id)
    )
    versao2 = versao2_r.scalar_one_or_none()

    if versao1 is None or versao2 is None:
        raise HTTPException(status_code=400, detail="Uma ou ambas as versões não pertencem a esta obra")

    # Carregar itens de cada versão
    async def _get_itens_versao(versao_id: int) -> list[Item]:
        r = await db.execute(
            select(Item)
            .join(Grupo, Item.grupo_id == Grupo.id)
            .where(Grupo.versao_id == versao_id)
            .options(selectinload(Item.grupo), selectinload(Item.composicao))
        )
        return r.scalars().all()

    itens_v1 = await _get_itens_versao(v1)
    itens_v2 = await _get_itens_versao(v2)

    # Indexar por composicao_id
    v1_map: dict[int, Item] = {}
    v1_sem_comp: list[Item] = []
    for item in itens_v1:
        if item.composicao_id is not None:
            v1_map[item.composicao_id] = item
        else:
            v1_sem_comp.append(item)

    v2_map: dict[int, Item] = {}
    v2_sem_comp: list[Item] = []
    for item in itens_v2:
        if item.composicao_id is not None:
            v2_map[item.composicao_id] = item
        else:
            v2_sem_comp.append(item)

    def _descricao(item: Item) -> str:
        if item.composicao:
            return item.composicao.descricao
        return "Item sem composição"

    itens_resultado: list[ComparativoItem] = []

    todas_comp_ids = set(v1_map.keys()) | set(v2_map.keys())
    for comp_id in todas_comp_ids:
        i1 = v1_map.get(comp_id)
        i2 = v2_map.get(comp_id)

        if i1 and i2:
            preco_diff = i1.preco_unitario_sem_bdi != i2.preco_unitario_sem_bdi
            qtd_diff = i1.quantidade != i2.quantidade
            status = "alterado" if (preco_diff or qtd_diff) else "igual"
            t1 = i1.total or Decimal("0")
            t2 = i2.total or Decimal("0")
            itens_resultado.append(ComparativoItem(
                status=status,
                grupo_nome=i2.grupo.nome,
                descricao=_descricao(i2),
                unidade=i2.unidade,
                v1_preco_unit=i1.preco_unitario_sem_bdi,
                v2_preco_unit=i2.preco_unitario_sem_bdi,
                v1_quantidade=i1.quantidade,
                v2_quantidade=i2.quantidade,
                v1_total=t1,
                v2_total=t2,
                delta_total=t2 - t1,
            ))
        elif i1 and not i2:
            t1 = i1.total or Decimal("0")
            itens_resultado.append(ComparativoItem(
                status="removido",
                grupo_nome=i1.grupo.nome,
                descricao=_descricao(i1),
                unidade=i1.unidade,
                v1_preco_unit=i1.preco_unitario_sem_bdi,
                v2_preco_unit=None,
                v1_quantidade=i1.quantidade,
                v2_quantidade=None,
                v1_total=t1,
                v2_total=None,
                delta_total=-t1,
            ))
        else:
            t2 = i2.total or Decimal("0")  # type: ignore[union-attr]
            itens_resultado.append(ComparativoItem(
                status="novo",
                grupo_nome=i2.grupo.nome,  # type: ignore[union-attr]
                descricao=_descricao(i2),  # type: ignore[union-attr]
                unidade=i2.unidade,  # type: ignore[union-attr]
                v1_preco_unit=None,
                v2_preco_unit=i2.preco_unitario_sem_bdi,  # type: ignore[union-attr]
                v1_quantidade=None,
                v2_quantidade=i2.quantidade,  # type: ignore[union-attr]
                v1_total=None,
                v2_total=t2,
                delta_total=t2,
            ))

    # Itens sem composicao_id
    for item in v1_sem_comp:
        t1 = item.total or Decimal("0")
        itens_resultado.append(ComparativoItem(
            status="removido",
            grupo_nome=item.grupo.nome,
            descricao=_descricao(item),
            unidade=item.unidade,
            v1_preco_unit=item.preco_unitario_sem_bdi,
            v2_preco_unit=None,
            v1_quantidade=item.quantidade,
            v2_quantidade=None,
            v1_total=t1,
            v2_total=None,
            delta_total=-t1,
        ))
    for item in v2_sem_comp:
        t2 = item.total or Decimal("0")
        itens_resultado.append(ComparativoItem(
            status="novo",
            grupo_nome=item.grupo.nome,
            descricao=_descricao(item),
            unidade=item.unidade,
            v1_preco_unit=None,
            v2_preco_unit=item.preco_unitario_sem_bdi,
            v1_quantidade=None,
            v2_quantidade=item.quantidade,
            v1_total=None,
            v2_total=t2,
            delta_total=t2,
        ))

    total_v1 = versao1.total_sem_bdi or Decimal("0")
    total_v2 = versao2.total_sem_bdi or Decimal("0")
    delta = total_v2 - total_v1
    delta_pct = float(delta / total_v1 * 100) if total_v1 != 0 else 0.0

    return ComparativoOut(
        obra_id=obra_id,
        v1_id=v1,
        v2_id=v2,
        v1_nome=f"Versão {versao1.numero}" + (f" — {versao1.nome}" if versao1.nome else ""),
        v2_nome=f"Versão {versao2.numero}" + (f" — {versao2.nome}" if versao2.nome else ""),
        v1_total=total_v1,
        v2_total=total_v2,
        delta_total=delta,
        delta_pct=round(delta_pct, 2),
        qtd_novos=sum(1 for i in itens_resultado if i.status == "novo"),
        qtd_removidos=sum(1 for i in itens_resultado if i.status == "removido"),
        qtd_alterados=sum(1 for i in itens_resultado if i.status == "alterado"),
        itens=itens_resultado,
    )
