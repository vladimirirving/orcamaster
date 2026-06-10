import pytest
from decimal import Decimal
from io import BytesIO
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import openpyxl

from app.models.composicao import Composicao
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.obra import Obra
from app.models.versao import Versao


def _make_xlsx(rows: list[list]) -> bytes:
    """rows[0] = header, rows[1:] = data"""
    wb = openpyxl.Workbook()
    ws = wb.active
    for row in rows:
        ws.append(row)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_importar_planilha_ok(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa: Versao,
):
    c1 = Composicao(empresa_id=None, origem="sinapi", codigo="IMP001",
                    descricao="Servico A", unidade="M3",
                    preco_unitario=Decimal("50"), requer_revisao=False)
    c2 = Composicao(empresa_id=None, origem="sinapi", codigo="IMP002",
                    descricao="Servico B", unidade="UN",
                    preco_unitario=Decimal("30"), requer_revisao=False)
    db_session.add_all([c1, c2])
    await db_session.commit()

    xlsx = _make_xlsx([
        ["grupo", "subgrupo", "codigo_composicao", "descricao", "unidade", "quantidade"],
        ["Terraplenagem", "", "IMP001", "", "M3", 100],
        ["Terraplenagem", "", "IMP002", "", "UN", 5],
        ["Drenagem", "", "IMP001", "", "M3", 200],
    ])

    resp = await client.post(
        f"/versoes/{versao_ativa.id}/planilha/importar",
        files={"file": ("planilha.xlsx", xlsx,
               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["grupos_criados"] == 2
    assert data["itens_criados"] == 3
    assert data["itens_sem_composicao"] == 0

    grupos = (await db_session.execute(
        select(Grupo).where(Grupo.versao_id == versao_ativa.id).order_by(Grupo.ordem)
    )).scalars().all()
    assert len(grupos) == 2
    assert grupos[0].nome == "Terraplenagem"
    assert grupos[1].nome == "Drenagem"

    await db_session.refresh(versao_ativa)
    assert versao_ativa.total_sem_bdi > 0


@pytest.mark.asyncio
async def test_importar_sem_composicao(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa: Versao,
):
    xlsx = _make_xlsx([
        ["grupo", "subgrupo", "codigo_composicao", "descricao", "unidade", "quantidade"],
        ["Grupo A", "", "NAOEXISTE999", "Servico manual", "UN", 10],
    ])

    resp = await client.post(
        f"/versoes/{versao_ativa.id}/planilha/importar",
        files={"file": ("planilha.xlsx", xlsx,
               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["itens_criados"] == 1
    assert data["itens_sem_composicao"] == 1

    item_result = await db_session.execute(
        select(Item)
        .join(Grupo, Item.grupo_id == Grupo.id)
        .where(Grupo.versao_id == versao_ativa.id)
    )
    item = item_result.scalar_one()
    assert item.requer_revisao is True
    assert item.composicao_id is None


@pytest.mark.asyncio
async def test_importar_versao_bloqueada(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, obra: Obra,
):
    versao_bloqueada = Versao(obra_id=obra.id, numero=99, bloqueada=True)
    db_session.add(versao_bloqueada)
    await db_session.commit()

    xlsx = _make_xlsx([
        ["grupo", "subgrupo", "codigo_composicao", "descricao", "unidade", "quantidade"],
        ["G", "", "", "Item", "UN", 1],
    ])
    resp = await client.post(
        f"/versoes/{versao_bloqueada.id}/planilha/importar",
        files={"file": ("p.xlsx", xlsx,
               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert resp.status_code == 409
