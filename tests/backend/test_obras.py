import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.versao import Versao


@pytest.mark.asyncio
async def test_create_obra_creates_versao_1(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, empresa
):
    resp = await client.post("/obras", json={
        "nome": "Ponte Rio Verde",
        "tipo_obra": "ponte",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["nome"] == "Ponte Rio Verde"
    assert data["estado"] == "em_elaboracao"
    assert data["empresa_id"] == empresa.id

    r = await db_session.execute(select(Versao).where(Versao.obra_id == data["id"]))
    versoes = r.scalars().all()
    assert len(versoes) == 1
    assert versoes[0].numero == 1
    assert versoes[0].bloqueada is False


@pytest.mark.asyncio
async def test_list_obras_scoped_to_empresa(
    client: AsyncClient, auth_headers: dict, obra
):
    resp = await client.get("/obras", headers=auth_headers)
    assert resp.status_code == 200
    ids = [o["id"] for o in resp.json()]
    assert obra.id in ids


@pytest.mark.asyncio
async def test_get_obra(client: AsyncClient, auth_headers: dict, obra):
    resp = await client.get(f"/obras/{obra.id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == obra.id


@pytest.mark.asyncio
async def test_get_obra_not_found(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/obras/99999", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_update_obra(client: AsyncClient, auth_headers: dict, obra):
    resp = await client.patch(
        f"/obras/{obra.id}",
        json={"estado": "concluido"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["estado"] == "concluido"


@pytest.mark.asyncio
async def test_list_versoes(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa
):
    resp = await client.get(f"/obras/{obra.id}/versoes", headers=auth_headers)
    assert resp.status_code == 200
    versoes = resp.json()
    assert len(versoes) == 1
    assert versoes[0]["id"] == versao_ativa.id
    assert versoes[0]["numero"] == 1
