import pytest
from datetime import date
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.medicao import Medicao
from app.models.composicao import Composicao


async def _setup_versao_com_itens(db_session, versao_ativa):
    comp = Composicao(
        empresa_id=None, origem="sinapi", codigo="99999",
        descricao="TERRAPLANAGEM MECANIZADA", unidade="M3",
        preco_unitario=Decimal("45.000000"), requer_revisao=False,
    )
    db_session.add(comp)
    await db_session.flush()

    grupo = Grupo(versao_id=versao_ativa.id, nome="Terraplenagem", ordem=0)
    db_session.add(grupo)
    await db_session.flush()

    item = Item(
        grupo_id=grupo.id, ordem=0,
        composicao_id=comp.id,
        quantidade=Decimal("500.000000"), unidade="M3",
        preco_unitario_sem_bdi=Decimal("45.000000"),
    )
    db_session.add(item)
    await db_session.commit()
    return item


@pytest.mark.asyncio
async def test_get_lista_medicoes_ordenadas_desc(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    m1 = Medicao(
        versao_id=versao_ativa.id,
        periodo_inicio=date(2025, 4, 1), periodo_fim=date(2025, 4, 30),
        linhas_json={},
    )
    m2 = Medicao(
        versao_id=versao_ativa.id,
        periodo_inicio=date(2025, 6, 1), periodo_fim=date(2025, 6, 30),
        linhas_json={},
    )
    db_session.add_all([m1, m2])
    await db_session.commit()

    resp = await client.get(f"/versoes/{versao_ativa.id}/medicoes", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["periodo_inicio"] == "2025-06-01"
    assert data[1]["periodo_inicio"] == "2025-04-01"


@pytest.mark.asyncio
async def test_get_lista_vazia(
    client: AsyncClient, auth_headers: dict,
    versao_ativa
):
    resp = await client.get(f"/versoes/{versao_ativa.id}/medicoes", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_post_cria_medicao_com_periodo_correto(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    resp = await client.post(
        f"/versoes/{versao_ativa.id}/medicoes",
        json={"mes": "2025-06"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["periodo_inicio"] == "2025-06-01"
    assert data["periodo_fim"] == "2025-06-30"
    assert data["linhas_json"] == {}

    r = await db_session.execute(
        select(Medicao).where(Medicao.versao_id == versao_ativa.id)
    )
    assert r.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_post_pre_popula_de_medicao_anterior(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    anterior = Medicao(
        versao_id=versao_ativa.id,
        periodo_inicio=date(2025, 5, 1), periodo_fim=date(2025, 5, 31),
        linhas_json={"42": 22.0, "43": 15.0},
    )
    db_session.add(anterior)
    await db_session.commit()

    resp = await client.post(
        f"/versoes/{versao_ativa.id}/medicoes",
        json={"mes": "2025-06"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["linhas_json"] == {"42": 22.0, "43": 15.0}


@pytest.mark.asyncio
async def test_post_mes_duplicado_retorna_422(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    m = Medicao(
        versao_id=versao_ativa.id,
        periodo_inicio=date(2025, 6, 1), periodo_fim=date(2025, 6, 30),
        linhas_json={},
    )
    db_session.add(m)
    await db_session.commit()

    resp = await client.post(
        f"/versoes/{versao_ativa.id}/medicoes",
        json={"mes": "2025-06"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
    assert "Já existe" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_post_versao_bloqueada_retorna_409(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    versao_ativa.bloqueada = True
    await db_session.commit()

    resp = await client.post(
        f"/versoes/{versao_ativa.id}/medicoes",
        json={"mes": "2025-06"},
        headers=auth_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_patch_atualiza_linhas_json(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    m = Medicao(
        versao_id=versao_ativa.id,
        periodo_inicio=date(2025, 6, 1), periodo_fim=date(2025, 6, 30),
        linhas_json={"42": 10.0},
    )
    db_session.add(m)
    await db_session.commit()

    resp = await client.patch(
        f"/versoes/{versao_ativa.id}/medicoes/{m.id}",
        json={"linhas_json": {"42": 35.0, "43": 25.0}},
        headers=auth_headers,
    )
    assert resp.status_code == 204

    await db_session.refresh(m)
    assert m.linhas_json == {"42": 35.0, "43": 25.0}


@pytest.mark.asyncio
async def test_patch_versao_bloqueada_retorna_409(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    m = Medicao(
        versao_id=versao_ativa.id,
        periodo_inicio=date(2025, 6, 1), periodo_fim=date(2025, 6, 30),
        linhas_json={},
    )
    db_session.add(m)
    versao_ativa.bloqueada = True
    await db_session.commit()

    resp = await client.patch(
        f"/versoes/{versao_ativa.id}/medicoes/{m.id}",
        json={"linhas_json": {"42": 35.0}},
        headers=auth_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_isolamento_empresa_b_nao_acessa_medicoes_empresa_a(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    from app.models.empresa import Empresa
    from app.models.usuario import Usuario
    from app.services.auth_service import hash_password, create_access_token

    empresa_b = Empresa(nome="Empresa B", cnpj="11.111.111/0001-11")
    db_session.add(empresa_b)
    await db_session.flush()
    user_b = Usuario(
        empresa_id=empresa_b.id, nome="User B", email="userb@teste.com",
        senha_hash=hash_password("senha123"), papel="admin",
    )
    db_session.add(user_b)
    await db_session.commit()

    token_b = create_access_token({
        "sub": str(user_b.id), "papel": user_b.papel, "empresa_id": user_b.empresa_id,
    })
    headers_b = {"Authorization": f"Bearer {token_b}"}

    resp_get = await client.get(f"/versoes/{versao_ativa.id}/medicoes", headers=headers_b)
    assert resp_get.status_code == 404

    resp_post = await client.post(
        f"/versoes/{versao_ativa.id}/medicoes",
        json={"mes": "2025-06"},
        headers=headers_b,
    )
    assert resp_post.status_code == 409
