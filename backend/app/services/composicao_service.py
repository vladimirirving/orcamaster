import csv
import io
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import Numeric, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.composicao import Composicao
from app.models.insumo import Insumo
from app.models.item import Item

_ZERO = Decimal("0")
_NUM = Numeric(15, 6)


async def recalc_preco_composicao(composicao_id: int, db: AsyncSession) -> None:
    """Recalculate composicao.preco_unitario = SUM(coeficiente * preco_unitario) over its insumos.
    If price changed, bulk-marks items using this composicao with requer_revisao=True.
    Callers must db.flush() before (so in-flight insumo changes are visible).
    Callers must db.commit() after.
    """
    r = await db.execute(
        select(
            func.coalesce(
                func.sum(Insumo.coeficiente * Insumo.preco_unitario), _ZERO
            ).cast(_NUM)
        ).where(Insumo.composicao_id == composicao_id)
    )
    novo_preco = Decimal(str(r.scalar() or _ZERO))

    r2 = await db.execute(
        select(Composicao.preco_unitario).where(Composicao.id == composicao_id)
    )
    preco_atual = Decimal(str(r2.scalar() or _ZERO))

    await db.execute(
        update(Composicao)
        .where(Composicao.id == composicao_id)
        .values(preco_unitario=novo_preco)
        .execution_options(synchronize_session=False)
    )

    if novo_preco != preco_atual:
        await db.execute(
            update(Item)
            .where(Item.composicao_id == composicao_id)
            .values(requer_revisao=True)
            .execution_options(synchronize_session=False)
        )


async def import_composicoes_csv(
    origem: str,
    conteudo: bytes,
    db: AsyncSession,
) -> dict:
    """Upsert composições from CSV by (origem, codigo).
    After upserting, bulk-marks items with requer_revisao=True where preco_unitario changed.
    Returns {"criadas": int, "atualizadas": int, "itens_marcados": int}.

    CSV format (UTF-8, BOM-tolerant):
        codigo,descricao,unidade,preco_unitario[,data_referencia]
    Decimal separator: dot or comma.
    """
    text = conteudo.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    result = await db.execute(
        select(Composicao).where(
            Composicao.origem == origem, Composicao.empresa_id.is_(None)
        )
    )
    existing: dict[str, Composicao] = {c.codigo: c for c in result.scalars().all()}

    criadas = 0
    atualizadas = 0
    changed_ids: list[int] = []

    for row in reader:
        codigo = row.get("codigo", "").strip()
        if not codigo:
            continue
        descricao = row.get("descricao", "").strip()
        unidade = row.get("unidade", "").strip()
        preco_raw = row.get("preco_unitario", "0").strip().replace(",", ".")
        novo_preco = Decimal(preco_raw)
        data_ref: Optional[date] = None
        raw_data = row.get("data_referencia", "").strip()
        if raw_data:
            data_ref = date.fromisoformat(raw_data)

        if codigo in existing:
            comp = existing[codigo]
            if Decimal(str(comp.preco_unitario)) != novo_preco:
                comp.preco_unitario = novo_preco
                changed_ids.append(comp.id)
            comp.descricao = descricao
            comp.unidade = unidade
            if data_ref:
                comp.data_referencia = data_ref
            atualizadas += 1
        else:
            nova = Composicao(
                empresa_id=None,
                origem=origem,
                codigo=codigo,
                descricao=descricao,
                unidade=unidade,
                preco_unitario=novo_preco,
                data_referencia=data_ref,
            )
            db.add(nova)
            existing[codigo] = nova
            criadas += 1

    await db.flush()

    itens_marcados = 0
    if changed_ids:
        r = await db.execute(
            update(Item)
            .where(Item.composicao_id.in_(changed_ids))
            .values(requer_revisao=True)
            .execution_options(synchronize_session=False)
        )
        itens_marcados = r.rowcount

    await db.commit()
    return {"criadas": criadas, "atualizadas": atualizadas, "itens_marcados": itens_marcados}
