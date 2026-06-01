import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.composicao import Composicao
from app.models.insumo import Insumo
from app.models.item import Item
from app.models.grupo import Grupo


# ── Composição CRUD ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_composicoes_inclui_sinapi_e_proprias(
    client: AsyncClient, auth_headers: dict,
    composicao_sinapi, composicao_propria
):
    resp = await client.get("/composicoes", headers=auth_headers)
    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()]
    assert composicao_sinapi.id in ids
    assert composicao_propria.id in ids


@pytest.mark.asyncio
async def test_search_composicoes_por_descricao(
    client: AsyncClient, auth_headers: dict, composicao_sinapi
):
    resp = await client.get("/composicoes?q=ESCAVACAO", headers=auth_headers)
    assert resp.status_code == 200
    assert any(c["codigo"] == "94966" for c in resp.json())


@pytest.mark.asyncio
async def test_filter_composicoes_por_origem(
    client: AsyncClient, auth_headers: dict,
    composicao_sinapi, composicao_propria
):
    resp = await client.get("/composicoes?origem=sinapi", headers=auth_headers)
    assert resp.status_code == 200
    origens = {c["origem"] for c in resp.json()}
    assert origens == {"sinapi"}


@pytest.mark.asyncio
async def test_create_composicao_propria(
    client: AsyncClient, auth_headers: dict, empresa
):
    resp = await client.post("/composicoes", json={
        "codigo": "P-099",
        "descricao": "Servico Teste",
        "unidade": "M",
        "preco_unitario": "55.500000",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["origem"] == "propria"
    assert data["empresa_id"] == empresa.id
    assert data["insumos"] == []


@pytest.mark.asyncio
async def test_get_composicao_with_insumos(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, composicao_propria
):
    db_session.add(Insumo(
        composicao_id=composicao_propria.id,
        tipo="material", descricao="Areia", unidade="m3",
        coeficiente=Decimal("1.0"), preco_unitario=Decimal("30.0"),
    ))
    await db_session.commit()

    resp = await client.get(f"/composicoes/{composicao_propria.id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["codigo"] == "P-001"
    assert len(data["insumos"]) == 1


@pytest.mark.asyncio
async def test_update_composicao_propria(
    client: AsyncClient, auth_headers: dict, composicao_propria
):
    resp = await client.patch(
        f"/composicoes/{composicao_propria.id}",
        json={"descricao": "Servico Atualizado"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["descricao"] == "Servico Atualizado"


@pytest.mark.asyncio
async def test_update_composicao_sinapi_retorna_403(
    client: AsyncClient, auth_headers: dict, composicao_sinapi
):
    resp = await client.patch(
        f"/composicoes/{composicao_sinapi.id}",
        json={"descricao": "Tentativa"},
        headers=auth_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_composicao_propria(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, composicao_propria
):
    resp = await client.delete(f"/composicoes/{composicao_propria.id}", headers=auth_headers)
    assert resp.status_code == 204
    r = await db_session.execute(
        select(Composicao).where(Composicao.id == composicao_propria.id)
    )
    assert r.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_composicao_sinapi_retorna_403(
    client: AsyncClient, auth_headers: dict, composicao_sinapi
):
    resp = await client.delete(f"/composicoes/{composicao_sinapi.id}", headers=auth_headers)
    assert resp.status_code == 403
