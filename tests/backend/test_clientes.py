import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_clientes_vazio(client: AsyncClient, auth_headers: dict):
    r = await client.get("/clientes", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_create_cliente(client: AsyncClient, auth_headers: dict):
    payload = {"tipo": "pj", "nome": "Construtora ABC", "cpf_cnpj": "12.345.678/0001-99"}
    r = await client.post("/clientes", json=payload, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["nome"] == "Construtora ABC"
    assert data["tipo"] == "pj"
    assert data["id"] > 0


@pytest.mark.asyncio
async def test_create_cliente_cpfcnpj_duplicado(client: AsyncClient, auth_headers: dict):
    payload = {"tipo": "pj", "nome": "ABC", "cpf_cnpj": "11.111.111/0001-11"}
    await client.post("/clientes", json=payload, headers=auth_headers)
    r = await client.post("/clientes", json=payload, headers=auth_headers)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_get_cliente(client: AsyncClient, auth_headers: dict):
    r = await client.post("/clientes", json={"tipo": "pf", "nome": "João Silva"}, headers=auth_headers)
    cid = r.json()["id"]
    r2 = await client.get(f"/clientes/{cid}", headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["nome"] == "João Silva"


@pytest.mark.asyncio
async def test_update_cliente(client: AsyncClient, auth_headers: dict):
    r = await client.post("/clientes", json={"tipo": "pf", "nome": "Antigo"}, headers=auth_headers)
    cid = r.json()["id"]
    r2 = await client.patch(f"/clientes/{cid}", json={"nome": "Novo Nome"}, headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["nome"] == "Novo Nome"


@pytest.mark.asyncio
async def test_delete_cliente(client: AsyncClient, auth_headers: dict):
    r = await client.post("/clientes", json={"tipo": "pf", "nome": "Temporário"}, headers=auth_headers)
    cid = r.json()["id"]
    r2 = await client.delete(f"/clientes/{cid}", headers=auth_headers)
    assert r2.status_code == 204


@pytest.mark.asyncio
async def test_busca_por_nome(client: AsyncClient, auth_headers: dict):
    await client.post("/clientes", json={"tipo": "pj", "nome": "Empresa Alpha"}, headers=auth_headers)
    await client.post("/clientes", json={"tipo": "pj", "nome": "Empresa Beta"}, headers=auth_headers)
    r = await client.get("/clientes?q=alpha", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["nome"] == "Empresa Alpha"
