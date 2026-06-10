import csv
import io
from datetime import date
from decimal import Decimal
from typing import Optional

import openpyxl
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


def _parse_csv(conteudo: bytes) -> list[dict]:
    text = conteudo.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return [
        {k.strip().lower(): v.strip() for k, v in row.items()}
        for row in reader
    ]


def _parse_xlsx(conteudo: bytes) -> list[dict]:
    wb = openpyxl.load_workbook(io.BytesIO(conteudo), read_only=True, data_only=True)
    try:
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True)) if ws is not None else []
    finally:
        wb.close()
    if not rows:
        return []
    header = [str(h).strip().lower() if h is not None else "" for h in rows[0]]
    result = []
    for row in rows[1:]:
        d = {key: (str(val).strip() if val is not None else "") for key, val in zip(header, row)}
        if d.get("codigo", ""):
            result.append(d)
    return result


async def import_composicoes(
    origem: str,
    conteudo: bytes,
    filename: str,
    db: AsyncSession,
) -> dict:
    """Upsert composições from CSV or XLSX by (origem, codigo).
    After upserting, bulk-marks items with requer_revisao=True where preco_unitario changed.
    Returns {"criadas": int, "atualizadas": int, "itens_marcados": int}.

    CSV format (UTF-8, BOM-tolerant) or XLSX first sheet:
        codigo, descricao, unidade, preco_unitario[, data_referencia]
    Decimal separator in CSV: dot or comma.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "csv"
    rows = _parse_xlsx(conteudo) if ext in ("xlsx", "xls") else _parse_csv(conteudo)

    result = await db.execute(
        select(Composicao).where(
            Composicao.origem == origem, Composicao.empresa_id.is_(None)
        )
    )
    existing: dict[str, Composicao] = {c.codigo: c for c in result.scalars().all()}

    criadas = 0
    atualizadas = 0
    changed_ids: list[int] = []

    for row in rows:
        codigo = row.get("codigo", "").strip()
        if not codigo:
            continue
        descricao = row.get("descricao", "").strip()
        unidade = row.get("unidade", "").strip()
        preco_raw = row.get("preco_unitario", "0").strip().replace(",", ".")
        try:
            novo_preco = Decimal(preco_raw) if preco_raw else _ZERO
        except Exception:
            novo_preco = _ZERO
        data_ref: Optional[date] = None
        raw_data = row.get("data_referencia", "").strip()
        if raw_data:
            try:
                data_ref = date.fromisoformat(raw_data[:10])
            except ValueError:
                data_ref = None

        if codigo in existing:
            comp = existing[codigo]
            if Decimal(str(comp.preco_unitario)) != novo_preco:
                comp.preco_unitario = novo_preco
                if comp.id is not None:
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
