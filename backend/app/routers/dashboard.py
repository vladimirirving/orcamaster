from datetime import date
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
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
from app.schemas.dashboard import CurvaSPonto, DashboardResumoItem, ObraDashboardData, GrupoDistribuicao, DistribuicaoGruposOut

router = APIRouter(tags=["dashboard"])


def _get_meses(inicio: str, fim: str) -> list[str]:
    meses = []
    y, m = int(inicio[:4]), int(inicio[5:7])
    ey, em = int(fim[:4]), int(fim[5:7])
    while (y, m) <= (ey, em):
        meses.append(f"{y}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return meses


def _calc(versao: Versao, itens: list, medicoes: list) -> Optional[dict]:
    """Returns dict with keys planejado_pct_hoje, realizado_pct, desvio, status, curva_s.
    Returns None when data is insufficient (sem_dados)."""
    if versao.total_sem_bdi is None:
        return None
    total_versao = float(versao.total_sem_bdi)
    if total_versao == 0 or not versao.cronograma_inicio or not versao.cronograma_fim:
        return None

    meses = _get_meses(versao.cronograma_inicio, versao.cronograma_fim)
    total_item = {item.id: float(item.total) for item in itens}
    dist = {
        item.id: (dict(item.cronograma_linha.distribuicao_json) if item.cronograma_linha else {})
        for item in itens
    }

    # Cumulative planned % per month
    planejado: dict[str, float] = {}
    acum = 0.0
    for mes in meses:
        for item_id, d in dist.items():
            acum += d.get(mes, 0) / 100 * total_item.get(item_id, 0)
        planejado[mes] = round(acum / total_versao * 100, 2)

    # Realizado % for months with a medicao
    realizado: dict[str, float] = {}
    for medicao in medicoes:
        mes = medicao.periodo_inicio.strftime("%Y-%m")
        if mes not in planejado:
            continue
        real_val = sum(
            medicao.linhas_json.get(str(item_id), 0) / 100 * total_item.get(item_id, 0)
            for item_id in total_item
        )
        realizado[mes] = round(real_val / total_versao * 100, 2)

    if not realizado:
        return None

    # planejado_pct_hoje
    mes_hoje = date.today().strftime("%Y-%m")
    if mes_hoje < meses[0]:
        planejado_pct_hoje = 0.0
    elif mes_hoje > meses[-1]:
        planejado_pct_hoje = planejado[meses[-1]]
    else:
        meses_ate_hoje = [m for m in meses if m <= mes_hoje]
        planejado_pct_hoje = planejado[meses_ate_hoje[-1]]

    # realizado_pct from latest medicao
    medicoes_sorted = sorted(medicoes, key=lambda m: m.periodo_inicio)
    mes_ultima = medicoes_sorted[-1].periodo_inicio.strftime("%Y-%m")
    realizado_pct = realizado.get(mes_ultima)
    if realizado_pct is None:
        return None

    desvio = round(realizado_pct - planejado_pct_hoje, 2)
    status = "adiantado" if desvio > 3 else "atrasado" if desvio < -3 else "no_prazo"

    curva_s = [
        CurvaSPonto(mes=mes, planejado_acum=planejado[mes], realizado_acum=realizado.get(mes))
        for mes in meses
    ]

    return {
        "planejado_pct_hoje": round(planejado_pct_hoje, 2),
        "realizado_pct": realizado_pct,
        "desvio": desvio,
        "status": status,
        "curva_s": curva_s,
    }


async def _get_versao_ativa_da_obra(obra_id: int, db: AsyncSession) -> Optional[Versao]:
    result = await db.execute(
        select(Versao).where(
            Versao.obra_id == obra_id,
            Versao.bloqueada == False,
            Versao.deletada_em.is_(None),
        ).order_by(Versao.id.desc()).limit(1)
    )
    return result.scalars().first()


async def _get_itens(versao_id: int, db: AsyncSession) -> list:
    result = await db.execute(
        select(Item)
        .join(Grupo, Item.grupo_id == Grupo.id)
        .where(Grupo.versao_id == versao_id)
        .options(selectinload(Item.cronograma_linha))
    )
    return result.scalars().all()


async def _get_medicoes(versao_id: int, db: AsyncSession) -> list:
    result = await db.execute(select(Medicao).where(Medicao.versao_id == versao_id))
    return result.scalars().all()


@router.get("/dashboard", response_model=list[DashboardResumoItem])
async def get_dashboard(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    obras_result = await db.execute(
        select(Obra)
        .where(Obra.empresa_id == current_user.empresa_id)
        .order_by(Obra.nome)
    )
    obras = obras_result.scalars().all()

    resultado = []
    for obra in obras:
        versao = await _get_versao_ativa_da_obra(obra.id, db)
        if versao is None:
            resultado.append(DashboardResumoItem(
                obra_id=obra.id, obra_nome=obra.nome,
                versao_id=None, total_sem_bdi=None, total_com_bdi=None,
                estado=obra.estado, tem_alertas=False,
                planejado_pct_hoje=None, realizado_pct=None,
                desvio=None, status="sem_dados",
            ))
            continue
        itens = await _get_itens(versao.id, db)
        medicoes = await _get_medicoes(versao.id, db)
        calc = _calc(versao, itens, medicoes)
        tem_alertas = any(i.requer_revisao for i in itens)
        if calc is None:
            resultado.append(DashboardResumoItem(
                obra_id=obra.id, obra_nome=obra.nome,
                versao_id=versao.id, total_sem_bdi=str(versao.total_sem_bdi),
                total_com_bdi=str(versao.total_com_bdi),
                estado=obra.estado, tem_alertas=tem_alertas,
                planejado_pct_hoje=None, realizado_pct=None,
                desvio=None, status="sem_dados",
            ))
        else:
            resultado.append(DashboardResumoItem(
                obra_id=obra.id, obra_nome=obra.nome,
                versao_id=versao.id, total_sem_bdi=str(versao.total_sem_bdi),
                total_com_bdi=str(versao.total_com_bdi),
                estado=obra.estado, tem_alertas=tem_alertas,
                planejado_pct_hoje=calc["planejado_pct_hoje"],
                realizado_pct=calc["realizado_pct"],
                desvio=calc["desvio"],
                status=calc["status"],
            ))
    return resultado


@router.get("/obras/{obra_id}/dashboard", response_model=ObraDashboardData)
async def get_obra_dashboard(
    obra_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    obra_result = await db.execute(
        select(Obra).where(Obra.id == obra_id, Obra.empresa_id == current_user.empresa_id)
    )
    if obra_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Obra não encontrada")

    versao = await _get_versao_ativa_da_obra(obra_id, db)
    if versao is None:
        return ObraDashboardData(
            versao_id=None, total_sem_bdi=None, total_com_bdi=None,
            planejado_pct_hoje=None, realizado_pct=None,
            desvio=None, status="sem_dados", curva_s=[],
        )

    itens = await _get_itens(versao.id, db)
    medicoes = await _get_medicoes(versao.id, db)
    calc = _calc(versao, itens, medicoes)

    if calc is None:
        return ObraDashboardData(
            versao_id=versao.id, total_sem_bdi=str(versao.total_sem_bdi),
            total_com_bdi=str(versao.total_com_bdi),
            planejado_pct_hoje=None, realizado_pct=None,
            desvio=None, status="sem_dados", curva_s=[],
        )

    return ObraDashboardData(
        versao_id=versao.id,
        total_sem_bdi=str(versao.total_sem_bdi),
        total_com_bdi=str(versao.total_com_bdi),
        planejado_pct_hoje=calc["planejado_pct_hoje"],
        realizado_pct=calc["realizado_pct"],
        desvio=calc["desvio"],
        status=calc["status"],
        curva_s=calc["curva_s"],
    )


@router.get("/obras/{obra_id}/distribuicao-grupos", response_model=DistribuicaoGruposOut)
async def get_distribuicao_grupos(
    obra_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    obra_result = await db.execute(
        select(Obra).where(Obra.id == obra_id, Obra.empresa_id == current_user.empresa_id)
    )
    if obra_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Obra não encontrada")

    versao = await _get_versao_ativa_da_obra(obra_id, db)
    if versao is None or versao.total_sem_bdi == 0:
        versao_id_out = versao.id if versao else 0
        return DistribuicaoGruposOut(
            versao_id=versao_id_out,
            total_versao=Decimal("0"),
            grupos=[],
        )

    # Grupos raiz e todos os grupos da versão
    grupos_r = await db.execute(
        select(Grupo).where(Grupo.versao_id == versao.id, Grupo.pai_id.is_(None))
    )
    grupos_raiz = grupos_r.scalars().all()
    grupos_raiz_ids = {g.id for g in grupos_raiz}

    todos_grupos_r = await db.execute(
        select(Grupo).where(Grupo.versao_id == versao.id)
    )
    todos_grupos = {g.id: g for g in todos_grupos_r.scalars().all()}

    # Todos os itens da versão
    todos_itens_r = await db.execute(
        select(Item)
        .join(Grupo, Item.grupo_id == Grupo.id)
        .where(Grupo.versao_id == versao.id)
    )
    todos_itens = todos_itens_r.scalars().all()

    # Agregar total por grupo raiz
    totais: dict[int, Decimal] = {g.id: Decimal("0") for g in grupos_raiz}
    for item in todos_itens:
        g = todos_grupos.get(item.grupo_id)
        if g is None:
            continue
        raiz_id = g.id if g.pai_id is None else (g.pai_id if g.pai_id in grupos_raiz_ids else None)
        if raiz_id is not None:
            totais[raiz_id] = totais.get(raiz_id, Decimal("0")) + (item.total or Decimal("0"))

    total_versao = versao.total_sem_bdi
    resultado = []
    for grupo in sorted(grupos_raiz, key=lambda g: totais.get(g.id, Decimal("0")), reverse=True):
        grupo_total = totais.get(grupo.id, Decimal("0"))
        pct = float(grupo_total / total_versao * 100) if total_versao else 0.0
        resultado.append(GrupoDistribuicao(
            grupo_id=grupo.id,
            grupo_nome=grupo.nome,
            total=grupo_total,
            participacao_pct=round(pct, 2),
        ))

    return DistribuicaoGruposOut(
        versao_id=versao.id,
        total_versao=total_versao,
        grupos=resultado,
    )
