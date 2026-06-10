import pytest
import pytest_asyncio
from datetime import date
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.insumo_item import InsumoItem
from app.models.usuario import Usuario
from app.services.auth_service import hash_password, create_access_token


@pytest_asyncio.fixture
async def sinapi_sp(db_session: AsyncSession) -> InsumoItem:
    item = InsumoItem(
        banco="sinapi", codigo="73829",
        descricao="CONCRETO FCK=25MPA, TRACO",
        unidade="M3", tipo="material",
        preco_nao_desonerado=Decimal("420.000000"),
        preco_desonerado=Decimal("395.000000"),
        estado="SP", data_referencia=date(2019, 8, 1),
        empresa_id=None,
    )
    db_session.add(item)
    await db_session.flush()
    return item


@pytest_asyncio.fixture
async def propria_item(db_session: AsyncSession, empresa) -> InsumoItem:
    item = InsumoItem(
        banco="propria", codigo="PRO-001",
        descricao="ARGAMASSA ESPECIAL",
        unidade="KG", tipo="material",
        preco_nao_desonerado=Decimal("8.500000"),
        preco_desonerado=Decimal("8.500000"),
        estado=None, data_referencia=date(2024, 1, 1),
        empresa_id=empresa.id,
    )
    db_session.add(item)
    await db_session.flush()
    return item


@pytest_asyncio.fixture
async def user_headers(db_session: AsyncSession, empresa) -> dict:
    u = Usuario(
        empresa_id=empresa.id, nome="Usuário Comum",
        email="comum@teste.com",
        senha_hash=hash_password("senha123"),
        papel="membro",
    )
    db_session.add(u)
    await db_session.flush()
    token = create_access_token({
        "sub": str(u.id), "papel": u.papel,
        "empresa_id": u.empresa_id,
    })
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_listar_retorna_items_e_total(
    client: AsyncClient, auth_headers: dict, sinapi_sp, propria_item
):
    resp = await client.get("/insumos", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data and "total" in data
    assert data["total"] == 2
    assert len(data["items"]) == 2


@pytest.mark.asyncio
async def test_filtrar_por_banco_sinapi(
    client: AsyncClient, auth_headers: dict, sinapi_sp, propria_item
):
    resp = await client.get("/insumos?banco=sinapi", headers=auth_headers)
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["banco"] == "sinapi"


@pytest.mark.asyncio
async def test_filtrar_por_estado_sp(
    client: AsyncClient, auth_headers: dict, sinapi_sp, propria_item
):
    resp = await client.get("/insumos?estado=SP", headers=auth_headers)
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["estado"] == "SP"


@pytest.mark.asyncio
async def test_filtrar_por_tipo_material(
    client: AsyncClient, auth_headers: dict, sinapi_sp, propria_item
):
    resp = await client.get("/insumos?tipo=material", headers=auth_headers)
    data = resp.json()
    assert data["total"] == 2


@pytest.mark.asyncio
async def test_filtrar_por_data_ref(
    client: AsyncClient, auth_headers: dict, sinapi_sp, propria_item
):
    resp = await client.get("/insumos?data_ref=2019-08", headers=auth_headers)
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["codigo"] == "73829"


@pytest.mark.asyncio
async def test_busca_por_codigo(
    client: AsyncClient, auth_headers: dict, sinapi_sp, propria_item
):
    resp = await client.get("/insumos?q=73829", headers=auth_headers)
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["codigo"] == "73829"


@pytest.mark.asyncio
async def test_busca_por_descricao(
    client: AsyncClient, auth_headers: dict, sinapi_sp, propria_item
):
    resp = await client.get("/insumos?q=argamassa", headers=auth_headers)
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["codigo"] == "PRO-001"


@pytest.mark.asyncio
async def test_ordenar_por_preco_nao_desonerado(
    client: AsyncClient, auth_headers: dict, sinapi_sp, propria_item
):
    resp = await client.get("/insumos?order_by=preco_nao_desonerado", headers=auth_headers)
    data = resp.json()
    precos = [float(i["preco_nao_desonerado"]) for i in data["items"]]
    assert precos == sorted(precos)


@pytest.mark.asyncio
async def test_paginacao_page1_retorna_50(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    for i in range(60):
        db_session.add(InsumoItem(
            banco="sinapi", codigo=f"COD-{i:03d}",
            descricao=f"Insumo {i}", unidade="UN",
            tipo="material",
            preco_nao_desonerado=Decimal("10"),
            preco_desonerado=Decimal("10"),
            estado="SP", data_referencia=date(2024, 1, 1),
            empresa_id=None,
        ))
    await db_session.flush()
    resp = await client.get("/insumos?page=1", headers=auth_headers)
    data = resp.json()
    assert data["total"] == 60
    assert len(data["items"]) == 50


@pytest.mark.asyncio
async def test_paginacao_page2_retorna_restantes(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    for i in range(60):
        db_session.add(InsumoItem(
            banco="sinapi", codigo=f"PAG-{i:03d}",
            descricao=f"Item {i}", unidade="UN",
            tipo="material",
            preco_nao_desonerado=Decimal("10"),
            preco_desonerado=Decimal("10"),
            estado="RJ", data_referencia=date(2024, 2, 1),
            empresa_id=None,
        ))
    await db_session.flush()
    resp = await client.get("/insumos?page=2", headers=auth_headers)
    data = resp.json()
    assert data["total"] == 60
    assert len(data["items"]) == 10


@pytest.mark.asyncio
async def test_admin_cria_insumo_proprio(
    client: AsyncClient, auth_headers: dict
):
    payload = {
        "codigo": "PRO-NEW", "descricao": "Insumo novo",
        "unidade": "UN", "tipo": "material",
        "preco_nao_desonerado": "15.5", "preco_desonerado": "15.0",
        "estado": None, "data_referencia": "2024-01-01",
    }
    resp = await client.post("/insumos", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["banco"] == "propria"
    assert data["codigo"] == "PRO-NEW"


@pytest.mark.asyncio
async def test_admin_edita_insumo_proprio(
    client: AsyncClient, auth_headers: dict, propria_item
):
    resp = await client.patch(
        f"/insumos/{propria_item.id}",
        json={"descricao": "Atualizado"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["descricao"] == "Atualizado"


@pytest.mark.asyncio
async def test_admin_deleta_insumo_proprio(
    client: AsyncClient, auth_headers: dict, propria_item
):
    resp = await client.delete(f"/insumos/{propria_item.id}", headers=auth_headers)
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_admin_nao_pode_editar_sinapi(
    client: AsyncClient, auth_headers: dict, sinapi_sp
):
    resp = await client.patch(
        f"/insumos/{sinapi_sp.id}",
        json={"descricao": "Hack"},
        headers=auth_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_usuario_comum_nao_pode_criar(
    client: AsyncClient, user_headers: dict
):
    payload = {
        "codigo": "X-001", "descricao": "Teste",
        "unidade": "UN", "tipo": "material",
        "preco_nao_desonerado": "10", "preco_desonerado": "10",
        "data_referencia": "2024-01-01",
    }
    resp = await client.post("/insumos", json=payload, headers=user_headers)
    assert resp.status_code == 403
