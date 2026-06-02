import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.bdi import BDI
from app.models.grupo import Grupo
from app.models.item import Item


BDI_BASE = {
    "ac": "0.0500",
    "sg": "0.0000",
    "r": "0.0000",
    "df": "0.0000",
    "lucro": "0.0000",
    "iss": "0.0000",
    "pis": "0.0000",
    "cofins": "0.0000",
}
# bdi_composto = ((1 + 0.05) / (1 - 0)) - 1 = 0.05


@pytest.mark.asyncio
async def test_put_bdi_cria_e_calcula_bdi_composto(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    resp = await client.put(
        f"/versoes/{versao_ativa.id}/bdi",
        json=BDI_BASE,
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert Decimal(data["bdi_composto"]) == Decimal("0.050000")
    assert data["versao_id"] == versao_ativa.id


@pytest.mark.asyncio
async def test_put_bdi_aplica_preco_com_bdi_nos_itens(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    grupo = Grupo(versao_id=versao_ativa.id, nome="G", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, ordem=0,
        quantidade=Decimal("1.000000"), unidade="m3",
        preco_unitario_sem_bdi=Decimal("100.000000"),
    )
    db_session.add(item)
    await db_session.commit()

    await client.put(
        f"/versoes/{versao_ativa.id}/bdi",
        json=BDI_BASE,
        headers=auth_headers,
    )

    await db_session.refresh(item)
    assert item.preco_unitario_com_bdi == Decimal("105.000000")


@pytest.mark.asyncio
async def test_put_bdi_atualiza_total_com_bdi_versao(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, obra, versao_ativa
):
    grupo = Grupo(versao_id=versao_ativa.id, nome="G", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, ordem=0,
        quantidade=Decimal("10.000000"), unidade="m3",
        preco_unitario_sem_bdi=Decimal("200.000000"),
    )
    db_session.add(item)
    await db_session.commit()

    await client.put(
        f"/versoes/{versao_ativa.id}/bdi",
        json=BDI_BASE,
        headers=auth_headers,
    )

    r_v = await client.get(f"/obras/{obra.id}/versoes", headers=auth_headers)
    versao_data = next(v for v in r_v.json() if v["id"] == versao_ativa.id)
    # total_com_bdi = 10 * 200 * 1.05 = 2100.00
    assert Decimal(versao_data["total_com_bdi"]) == Decimal("2100.00")


@pytest.mark.asyncio
async def test_get_bdi_retorna_404_quando_nao_existe(
    client: AsyncClient, auth_headers: dict, versao_ativa
):
    resp = await client.get(f"/versoes/{versao_ativa.id}/bdi", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_bdi_retorna_bdi_existente(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    await client.put(
        f"/versoes/{versao_ativa.id}/bdi",
        json=BDI_BASE,
        headers=auth_headers,
    )
    resp = await client.get(f"/versoes/{versao_ativa.id}/bdi", headers=auth_headers)
    assert resp.status_code == 200
    assert Decimal(resp.json()["ac"]) == Decimal("0.0500")


@pytest.mark.asyncio
async def test_put_bdi_atualiza_bdi_existente(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    grupo = Grupo(versao_id=versao_ativa.id, nome="G", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, ordem=0,
        quantidade=Decimal("1.000000"), unidade="m",
        preco_unitario_sem_bdi=Decimal("100.000000"),
    )
    db_session.add(item)
    await db_session.commit()

    await client.put(f"/versoes/{versao_ativa.id}/bdi", json=BDI_BASE, headers=auth_headers)

    bdi_updated = {**BDI_BASE, "ac": "0.1000"}
    resp = await client.put(
        f"/versoes/{versao_ativa.id}/bdi",
        json=bdi_updated,
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert Decimal(resp.json()["bdi_composto"]) == Decimal("0.100000")

    await db_session.refresh(item)
    assert item.preco_unitario_com_bdi == Decimal("110.000000")


@pytest.mark.asyncio
async def test_delete_bdi_zera_preco_com_bdi_nos_itens(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, obra, versao_ativa
):
    grupo = Grupo(versao_id=versao_ativa.id, nome="G", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, ordem=0,
        quantidade=Decimal("1.000000"), unidade="m",
        preco_unitario_sem_bdi=Decimal("100.000000"),
    )
    db_session.add(item)
    await db_session.commit()

    await client.put(f"/versoes/{versao_ativa.id}/bdi", json=BDI_BASE, headers=auth_headers)
    resp = await client.delete(f"/versoes/{versao_ativa.id}/bdi", headers=auth_headers)
    assert resp.status_code == 204

    await db_session.refresh(item)
    assert item.preco_unitario_com_bdi is None

    r_v = await client.get(f"/obras/{obra.id}/versoes", headers=auth_headers)
    versao_data = next(v for v in r_v.json() if v["id"] == versao_ativa.id)
    assert Decimal(versao_data["total_com_bdi"]) == Decimal("0.00")


@pytest.mark.asyncio
async def test_put_bdi_em_versao_bloqueada_retorna_409(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    versao_ativa.bloqueada = True
    await db_session.commit()

    resp = await client.put(
        f"/versoes/{versao_ativa.id}/bdi",
        json=BDI_BASE,
        headers=auth_headers,
    )
    assert resp.status_code == 409
