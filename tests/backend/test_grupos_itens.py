import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.grupo import Grupo
from app.models.item import Item


@pytest.mark.asyncio
async def test_create_grupo_raiz(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    resp = await client.post(
        f"/versoes/{versao_ativa.id}/grupos",
        json={"nome": "Terraplenagem", "ordem": 0},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["nome"] == "Terraplenagem"
    assert data["pai_id"] is None
    assert data["filhos"] == []


@pytest.mark.asyncio
async def test_create_subgrupo(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    r1 = await client.post(
        f"/versoes/{versao_ativa.id}/grupos",
        json={"nome": "Pavimentação", "ordem": 0},
        headers=auth_headers,
    )
    grupo_id = r1.json()["id"]

    resp = await client.post(
        f"/grupos/{grupo_id}/subgrupos",
        json={"nome": "CBUQ", "ordem": 0},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["pai_id"] == grupo_id


@pytest.mark.asyncio
async def test_create_subgrupo_de_subgrupo_retorna_422(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    r1 = await client.post(
        f"/versoes/{versao_ativa.id}/grupos",
        json={"nome": "Grupo A", "ordem": 0},
        headers=auth_headers,
    )
    g1_id = r1.json()["id"]

    r2 = await client.post(
        f"/grupos/{g1_id}/subgrupos",
        json={"nome": "Subgrupo B", "ordem": 0},
        headers=auth_headers,
    )
    sg_id = r2.json()["id"]

    resp = await client.post(
        f"/grupos/{sg_id}/subgrupos",
        json={"nome": "Nível 3 inválido", "ordem": 0},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_grupos_includes_filhos(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    root = Grupo(versao_id=versao_ativa.id, nome="Root", ordem=0)
    db_session.add(root)
    await db_session.flush()
    child = Grupo(versao_id=versao_ativa.id, pai_id=root.id, nome="Child", ordem=0)
    db_session.add(child)
    await db_session.commit()

    resp = await client.get(f"/versoes/{versao_ativa.id}/grupos", headers=auth_headers)
    assert resp.status_code == 200
    grupos = resp.json()
    assert len(grupos) == 1
    assert grupos[0]["nome"] == "Root"
    assert len(grupos[0]["filhos"]) == 1
    assert grupos[0]["filhos"][0]["nome"] == "Child"


@pytest.mark.asyncio
async def test_update_grupo(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    g = Grupo(versao_id=versao_ativa.id, nome="Old Name", ordem=0)
    db_session.add(g)
    await db_session.commit()

    resp = await client.patch(f"/grupos/{g.id}", json={"nome": "New Name"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["nome"] == "New Name"


@pytest.mark.asyncio
async def test_delete_grupo(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    g = Grupo(versao_id=versao_ativa.id, nome="To Delete", ordem=0)
    db_session.add(g)
    await db_session.commit()

    resp = await client.delete(f"/grupos/{g.id}", headers=auth_headers)
    assert resp.status_code == 204

    r = await db_session.execute(select(Grupo).where(Grupo.id == g.id))
    assert r.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_create_grupo_em_versao_bloqueada_retorna_409(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    versao_ativa.bloqueada = True
    await db_session.commit()

    resp = await client.post(
        f"/versoes/{versao_ativa.id}/grupos",
        json={"nome": "Grupo X", "ordem": 0},
        headers=auth_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_item_recalcula_totais(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, obra, versao_ativa
):
    r_g = await client.post(
        f"/versoes/{versao_ativa.id}/grupos",
        json={"nome": "Drenagem", "ordem": 0},
        headers=auth_headers,
    )
    grupo_id = r_g.json()["id"]

    resp = await client.post(
        f"/grupos/{grupo_id}/itens",
        json={"quantidade": "100.000000", "unidade": "m"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    item = resp.json()
    assert item["quantidade"] == "100.000000"
    assert item["unidade"] == "m"
    assert item["preco_unitario_sem_bdi"] is None


@pytest.mark.asyncio
async def test_update_item_quantidade_recalcula_totais(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, obra, versao_ativa
):
    g = Grupo(versao_id=versao_ativa.id, nome="OAC", ordem=0)
    db_session.add(g)
    await db_session.flush()
    i = Item(
        grupo_id=g.id, ordem=0, quantidade=Decimal("50"),
        unidade="m3", preco_unitario_sem_bdi=Decimal("10.000000"),
        preco_unitario_com_bdi=Decimal("12.000000"),
    )
    db_session.add(i)
    await db_session.commit()

    resp = await client.patch(
        f"/itens/{i.id}",
        json={"quantidade": "200.000000"},
        headers=auth_headers,
    )
    assert resp.status_code == 200

    r_v = await client.get(f"/obras/{obra.id}/versoes", headers=auth_headers)
    versao = next(v for v in r_v.json() if v["id"] == versao_ativa.id)
    assert Decimal(versao["total_sem_bdi"]) == Decimal("2000.00")


@pytest.mark.asyncio
async def test_delete_item_recalcula_totais(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, obra, versao_ativa
):
    g = Grupo(versao_id=versao_ativa.id, nome="Sinalização", ordem=0)
    db_session.add(g)
    await db_session.flush()
    i = Item(
        grupo_id=g.id, ordem=0, quantidade=Decimal("10"),
        unidade="m2", preco_unitario_sem_bdi=Decimal("100.000000"),
    )
    db_session.add(i)
    await db_session.commit()

    resp = await client.delete(f"/itens/{i.id}", headers=auth_headers)
    assert resp.status_code == 204

    r_v = await client.get(f"/obras/{obra.id}/versoes", headers=auth_headers)
    versao = next(v for v in r_v.json() if v["id"] == versao_ativa.id)
    assert Decimal(versao["total_sem_bdi"]) == Decimal("0.00")


@pytest.mark.asyncio
async def test_update_etiqueta_revisao(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    g = Grupo(versao_id=versao_ativa.id, nome="G", ordem=0)
    db_session.add(g)
    await db_session.flush()
    i = Item(grupo_id=g.id, ordem=0, quantidade=Decimal("1"), unidade="un")
    db_session.add(i)
    await db_session.commit()

    resp = await client.patch(
        f"/itens/{i.id}",
        json={"etiqueta_revisao": True},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["etiqueta_revisao"] is True
