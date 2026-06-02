import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.versao import Versao
from app.models.grupo import Grupo
from app.models.item import Item


async def _seed_grupos_itens(db: AsyncSession, versao_id: int) -> tuple:
    """Seeds one root grupo with one item. Returns (grupo_id, item_id)."""
    g = Grupo(versao_id=versao_id, nome="Terraplenagem", ordem=0)
    db.add(g)
    await db.flush()
    i = Item(
        grupo_id=g.id, ordem=0, quantidade=Decimal("100"),
        unidade="m3", preco_unitario_sem_bdi=Decimal("10.000000"),
        preco_unitario_com_bdi=Decimal("12.000000"),
        etiqueta_revisao=True, requer_revisao=True,
    )
    db.add(i)
    await db.flush()
    return g.id, i.id


@pytest.mark.asyncio
async def test_create_versao_clones_grupos_e_itens(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, obra, versao_ativa
):
    await _seed_grupos_itens(db_session, versao_ativa.id)
    await db_session.commit()

    resp = await client.post(f"/obras/{obra.id}/versoes", headers=auth_headers)
    assert resp.status_code == 201
    nova_id = resp.json()["id"]
    assert nova_id != versao_ativa.id
    assert resp.json()["numero"] == 2

    await db_session.refresh(versao_ativa)
    assert versao_ativa.bloqueada is True

    r = await db_session.execute(select(Grupo).where(Grupo.versao_id == nova_id))
    grupos = r.scalars().all()
    assert len(grupos) == 1
    assert grupos[0].nome == "Terraplenagem"

    r2 = await db_session.execute(select(Item).where(Item.grupo_id == grupos[0].id))
    itens = r2.scalars().all()
    assert len(itens) == 1
    assert itens[0].etiqueta_revisao is True   # copiado verbatim
    assert itens[0].requer_revisao is False     # resetado


@pytest.mark.asyncio
async def test_create_versao_sem_versao_ativa_retorna_409(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, obra, versao_ativa
):
    versao_ativa.bloqueada = True
    await db_session.commit()

    resp = await client.post(f"/obras/{obra.id}/versoes", headers=auth_headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_clone_preserva_subgrupos(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, obra, versao_ativa
):
    g_root = Grupo(versao_id=versao_ativa.id, nome="Pavimentação", ordem=0)
    db_session.add(g_root)
    await db_session.flush()
    g_sub = Grupo(versao_id=versao_ativa.id, pai_id=g_root.id, nome="CBUQ", ordem=0)
    db_session.add(g_sub)
    await db_session.commit()

    resp = await client.post(f"/obras/{obra.id}/versoes", headers=auth_headers)
    assert resp.status_code == 201
    nova_id = resp.json()["id"]

    r = await db_session.execute(select(Grupo).where(Grupo.versao_id == nova_id))
    grupos = r.scalars().all()
    assert len(grupos) == 2
    roots = [g for g in grupos if g.pai_id is None]
    subs = [g for g in grupos if g.pai_id is not None]
    assert len(roots) == 1
    assert len(subs) == 1
    assert subs[0].pai_id == roots[0].id  # correct parent mapping


@pytest.mark.asyncio
async def test_soft_delete_versao(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, obra, versao_ativa
):
    resp = await client.delete(f"/versoes/{versao_ativa.id}", headers=auth_headers)
    assert resp.status_code == 204

    await db_session.refresh(versao_ativa)
    assert versao_ativa.deletada_em is not None


@pytest.mark.asyncio
async def test_soft_delete_versao_not_found(
    client: AsyncClient, auth_headers: dict
):
    resp = await client.delete("/versoes/99999", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_restore_versao(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, obra, versao_ativa
):
    from datetime import datetime
    versao_ativa.deletada_em = datetime.utcnow()
    versao_ativa.bloqueada = True
    await db_session.commit()

    resp = await client.post(f"/versoes/{versao_ativa.id}/restore", headers=auth_headers)
    assert resp.status_code == 200

    await db_session.refresh(versao_ativa)
    assert versao_ativa.deletada_em is None


@pytest.mark.asyncio
async def test_restore_recusado_se_ja_existe_versao_ativa(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, obra, versao_ativa
):
    from datetime import datetime
    v2 = Versao(obra_id=obra.id, numero=2, bloqueada=True,
                deletada_em=datetime.utcnow())
    db_session.add(v2)
    await db_session.commit()

    # versao_ativa is still active — restoring v2 would create two active versões
    resp = await client.post(f"/versoes/{v2.id}/restore", headers=auth_headers)
    assert resp.status_code == 409
