import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_fornecedores_vazio(client: AsyncClient, auth_headers: dict):
    r = await client.get("/fornecedores", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_create_fornecedor(client: AsyncClient, auth_headers: dict):
    payload = {"nome": "Aço Brasil Ltda", "cnpj": "99.888.777/0001-55", "categorias": "material"}
    r = await client.post("/fornecedores", json=payload, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["nome"] == "Aço Brasil Ltda"
    assert data["categorias"] == "material"


@pytest.mark.asyncio
async def test_create_fornecedor_cnpj_duplicado(client: AsyncClient, auth_headers: dict):
    payload = {"nome": "F1", "cnpj": "11.222.333/0001-44"}
    await client.post("/fornecedores", json=payload, headers=auth_headers)
    r = await client.post("/fornecedores", json=payload, headers=auth_headers)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_update_fornecedor(client: AsyncClient, auth_headers: dict):
    r = await client.post("/fornecedores", json={"nome": "Antigo"}, headers=auth_headers)
    fid = r.json()["id"]
    r2 = await client.patch(f"/fornecedores/{fid}", json={"nome": "Novo"}, headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["nome"] == "Novo"


@pytest.mark.asyncio
async def test_delete_fornecedor(client: AsyncClient, auth_headers: dict):
    r = await client.post("/fornecedores", json={"nome": "Temp"}, headers=auth_headers)
    fid = r.json()["id"]
    r2 = await client.delete(f"/fornecedores/{fid}", headers=auth_headers)
    assert r2.status_code == 204


@pytest.mark.asyncio
async def test_filtrar_por_categoria(client: AsyncClient, auth_headers: dict):
    await client.post("/fornecedores", json={"nome": "Mat A", "categorias": "material"}, headers=auth_headers)
    await client.post("/fornecedores", json={"nome": "MO B", "categorias": "mao_obra"}, headers=auth_headers)
    r = await client.get("/fornecedores?categoria=material", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["nome"] == "Mat A"
