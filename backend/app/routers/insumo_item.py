# backend/app/routers/insumo_item.py
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.insumo_item import InsumoItem
from app.models.usuario import Usuario
from app.schemas.insumo_item import InsumoItemListOut, InsumoItemOut

router = APIRouter(prefix="/insumos", tags=["insumos"])

PAGE_SIZE = 50

_ORDER_COLS = {
    "codigo": InsumoItem.codigo,
    "descricao": InsumoItem.descricao,
    "preco_nao_desonerado": InsumoItem.preco_nao_desonerado,
    "preco_desonerado": InsumoItem.preco_desonerado,
}


@router.get("", response_model=InsumoItemListOut)
async def list_insumos(
    q: Optional[str] = Query(None),
    banco: Optional[str] = Query(None),
    estado: Optional[str] = Query(None),
    tipo: Optional[str] = Query(None),
    data_ref: Optional[str] = Query(None),   # formato YYYY-MM
    order_by: str = Query("descricao"),
    page: int = Query(1, ge=1),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(InsumoItem).where(
        (InsumoItem.empresa_id == None) |  # noqa: E711 — SINAPI/SICRO global
        (InsumoItem.empresa_id == current_user.empresa_id)
    )
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(InsumoItem.codigo.ilike(like), InsumoItem.descricao.ilike(like))
        )
    if banco:
        stmt = stmt.where(InsumoItem.banco == banco)
    if estado:
        stmt = stmt.where(InsumoItem.estado == estado)
    if tipo:
        stmt = stmt.where(InsumoItem.tipo == tipo)
    if data_ref:
        try:
            year, month = data_ref.split("-")
            ref_date = date(int(year), int(month), 1)
            stmt = stmt.where(InsumoItem.data_referencia == ref_date)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=422,
                detail="data_ref deve estar no formato YYYY-MM (ex: 2024-01)"
            )

    order_col = _ORDER_COLS.get(order_by, InsumoItem.descricao)
    stmt = stmt.order_by(order_col)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar_one()

    stmt = stmt.offset((page - 1) * PAGE_SIZE).limit(PAGE_SIZE)
    items = (await db.execute(stmt)).scalars().all()

    return {"items": items, "total": total}
