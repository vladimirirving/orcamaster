import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.bdi import BDI
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.versao import Versao


@pytest.mark.asyncio
async def test_duplicar_copia_grupos_subgrupos_itens(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, obra, versao_ativa
):
    raiz = Grupo(versao_id=versao_ativa.id, nome="Terraplenagem", ordem=0)
    db_session.add(raiz)
    await db_session.flush()
    sub = Grupo(versao_id=versao_ativa.id, pai_id=raiz.id, nome="Escavação", ordem=0)
    db_session.add(sub)
    await db_session.flush()
    item = Item(
        grupo_id=sub.id, ordem=0,
        quantidade=Decimal("100.000000"), unidade="m3",
        preco_unitario_sem_bdi=Decimal("50.000000"),
    )
    db_session.add(item)
    await db_session.commit()

    resp = await client.post(
        f"/versoes/{versao_ativa.id}/duplicar",
        headers=auth_headers,
    )
    assert resp.status_code == 201
    nova = resp.json()
    assert nova["id"] != versao_ativa.id
    assert nova["obra_id"] == obra.id
    assert nova["bloqueada"] is False

    r_grupos = await db_session.execute(
        select(func.count()).select_from(Grupo).where(Grupo.versao_id == nova["id"])
    )
    assert r_grupos.scalar() == 2  # raiz + sub

    r_itens = await db_session.execute(
        select(func.count()).select_from(Item)
        .join(Grupo, Item.grupo_id == Grupo.id)
        .where(Grupo.versao_id == nova["id"])
    )
    assert r_itens.scalar() == 1

    r_ids = await db_session.execute(
        select(Grupo.id).where(Grupo.versao_id == nova["id"])
    )
    novos_ids = set(r_ids.scalars().all())
    assert raiz.id not in novos_ids
    assert sub.id not in novos_ids


@pytest.mark.asyncio
async def test_duplicar_numero_incrementado(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    resp = await client.post(
        f"/versoes/{versao_ativa.id}/duplicar",
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["numero"] == versao_ativa.numero + 1


@pytest.mark.asyncio
async def test_duplicar_copia_bdi(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    bdi = BDI(
        versao_id=versao_ativa.id,
        ac=Decimal("0.0500"), sg=Decimal("0"), r=Decimal("0"),
        df=Decimal("0"), lucro=Decimal("0"),
        iss=Decimal("0"), pis=Decimal("0"), cofins=Decimal("0"),
        bdi_composto=Decimal("0.050000"),
    )
    db_session.add(bdi)
    await db_session.commit()

    resp = await client.post(
        f"/versoes/{versao_ativa.id}/duplicar",
        headers=auth_headers,
    )
    assert resp.status_code == 201
    nova_id = resp.json()["id"]

    r = await db_session.execute(select(BDI).where(BDI.versao_id == nova_id))
    nova_bdi = r.scalar_one_or_none()
    assert nova_bdi is not None
    assert nova_bdi.ac == Decimal("0.0500")
    assert nova_bdi.id != bdi.id


@pytest.mark.asyncio
async def test_duplicar_versao_sem_bdi(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    resp = await client.post(
        f"/versoes/{versao_ativa.id}/duplicar",
        headers=auth_headers,
    )
    assert resp.status_code == 201
    nova_id = resp.json()["id"]

    r = await db_session.execute(select(BDI).where(BDI.versao_id == nova_id))
    assert r.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_duplicar_versao_bloqueada_retorna_409(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    versao_ativa.bloqueada = True
    await db_session.commit()

    resp = await client.post(
        f"/versoes/{versao_ativa.id}/duplicar",
        headers=auth_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_duplicar_bdi_independente(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    bdi_orig = BDI(
        versao_id=versao_ativa.id,
        ac=Decimal("0.0500"), sg=Decimal("0"), r=Decimal("0"),
        df=Decimal("0"), lucro=Decimal("0"),
        iss=Decimal("0"), pis=Decimal("0"), cofins=Decimal("0"),
        bdi_composto=Decimal("0.050000"),
    )
    db_session.add(bdi_orig)
    await db_session.commit()

    resp = await client.post(
        f"/versoes/{versao_ativa.id}/duplicar",
        headers=auth_headers,
    )
    nova_id = resp.json()["id"]

    r = await db_session.execute(select(BDI).where(BDI.versao_id == nova_id))
    nova_bdi = r.scalar_one()
    nova_bdi.ac = Decimal("0.1000")
    await db_session.commit()

    await db_session.refresh(bdi_orig)
    assert bdi_orig.ac == Decimal("0.0500")
