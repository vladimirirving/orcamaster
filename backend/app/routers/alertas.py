from datetime import date
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.contrato import Aditivo, Contrato
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.medicao import Medicao
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.routers.dashboard import _calc, _get_itens, _get_medicoes
from app.schemas.alerta import AlertaOut

router = APIRouter(tags=["alertas"])

_SEV_ORDER = {"alta": 0, "media": 1, "baixa": 2}


def _data_fim_atual_contrato(contrato: Contrato, aditivos: list[Aditivo]) -> date | None:
    data = contrato.data_fim
    for a in sorted(aditivos, key=lambda x: x.id):
        if a.nova_data_fim is not None:
            data = a.nova_data_fim
    return data


@router.get("/alertas", response_model=List[AlertaOut])
async def list_alertas(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    hoje = date.today()
    alertas: list[AlertaOut] = []

    # Only obras em_elaboracao
    obras_r = await db.execute(
        select(Obra).where(
            Obra.empresa_id == current_user.empresa_id,
            Obra.estado == "em_elaboracao",
        ).order_by(Obra.nome)
    )
    obras = obras_r.scalars().all()

    for obra in obras:
        # ── 1 & 2: contratos vencendo / vencidos ─────────────────────────
        contratos_r = await db.execute(
            select(Contrato).where(Contrato.obra_id == obra.id)
        )
        for contrato in contratos_r.scalars().all():
            ads_r = await db.execute(
                select(Aditivo).where(Aditivo.contrato_id == contrato.id).order_by(Aditivo.id)
            )
            data_fim = _data_fim_atual_contrato(contrato, list(ads_r.scalars().all()))
            if data_fim is None:
                continue
            num = f" {contrato.numero}" if contrato.numero else ""
            detalhe = f"Prazo: {data_fim.isoformat()}"
            link = f"/obras/{obra.id}?tab=contratos"
            if data_fim < hoje:
                dias = (hoje - data_fim).days
                s = "s" if dias != 1 else ""
                alertas.append(AlertaOut(
                    tipo="contrato_vencido", severidade="alta",
                    obra_id=obra.id, obra_nome=obra.nome,
                    titulo=f"Contrato{num} venceu há {dias} dia{s}",
                    detalhe=detalhe, link=link,
                ))
            elif (data_fim - hoje).days <= 30:
                dias = (data_fim - hoje).days
                s = "s" if dias != 1 else ""
                alertas.append(AlertaOut(
                    tipo="contrato_vencendo", severidade="media",
                    obra_id=obra.id, obra_nome=obra.nome,
                    titulo=f"Contrato{num} vence em {dias} dia{s}",
                    detalhe=detalhe, link=link,
                ))

        # ── versão ativa necessária para os próximos alertas ─────────────
        versao_r = await db.execute(
            select(Versao).where(
                Versao.obra_id == obra.id,
                Versao.bloqueada == False,
                Versao.deletada_em.is_(None),
            ).order_by(Versao.id.desc()).limit(1)
        )
        versao = versao_r.scalars().first()
        if versao is None:
            continue

        # ── 3: desvio de orçamento ────────────────────────────────────────
        if versao.cronograma_inicio and versao.cronograma_fim:
            itens = await _get_itens(versao.id, db)
            medicoes = await _get_medicoes(versao.id, db)
            calc = _calc(versao, itens, medicoes)
            if (
                calc is not None
                and calc.get("realizado_pct") is not None
                and calc.get("planejado_pct_hoje") is not None
            ):
                r = calc["realizado_pct"]
                p = calc["planejado_pct_hoje"]
                if r - p > 10:
                    alertas.append(AlertaOut(
                        tipo="desvio_orcamento", severidade="media",
                        obra_id=obra.id, obra_nome=obra.nome,
                        titulo=f"Desvio de orçamento: +{r - p:.0f}%",
                        detalhe=f"Realizado {r:.0f}% · Planejado {p:.0f}%",
                        link=f"/obras/{obra.id}?tab=dashboard",
                    ))

        # ── 4: medição atrasada ───────────────────────────────────────────
        if versao.cronograma_inicio and versao.cronograma_fim:
            mes_inicio = date(hoje.year, hoje.month, 1)
            if hoje.month == 12:
                mes_fim = date(hoje.year + 1, 1, 1)
            else:
                mes_fim = date(hoje.year, hoje.month + 1, 1)
            med_count_r = await db.execute(
                select(func.count()).select_from(Medicao).where(
                    Medicao.versao_id == versao.id,
                    Medicao.periodo_inicio >= mes_inicio,
                    Medicao.periodo_inicio < mes_fim,
                )
            )
            if (med_count_r.scalar() or 0) == 0:
                mes_label = hoje.strftime("%b/%Y").capitalize()
                alertas.append(AlertaOut(
                    tipo="medicao_atrasada", severidade="media",
                    obra_id=obra.id, obra_nome=obra.nome,
                    titulo=f"Medição de {mes_label} não lançada",
                    detalhe=None,
                    link=f"/obras/{obra.id}/versoes/{versao.id}",
                ))

        # ── 5: itens para revisar ─────────────────────────────────────────
        count_r = await db.execute(
            select(func.count()).select_from(Item)
            .join(Grupo, Grupo.id == Item.grupo_id)
            .where(Grupo.versao_id == versao.id, Item.requer_revisao == True)
        )
        count = count_r.scalar() or 0
        if count > 0:
            s = "item" if count == 1 else "itens"
            alertas.append(AlertaOut(
                tipo="item_revisao", severidade="baixa",
                obra_id=obra.id, obra_nome=obra.nome,
                titulo=f"{count} {s} aguardando revisão",
                detalhe=None,
                link=f"/obras/{obra.id}/versoes/{versao.id}",
            ))

    alertas.sort(key=lambda a: (_SEV_ORDER[a.severidade], a.obra_nome))
    return alertas
