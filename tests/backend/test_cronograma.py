import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.cronograma_linha import CronogramaLinha
from app.models.composicao import Composicao


async def _setup_versao_com_itens(db_session, versao_ativa, empresa):
    """Helper: creates grupo + 2 itens, one with composicao, one without."""
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

    item1 = Item(
        grupo_id=grupo.id, ordem=0,
        composicao_id=comp.id,
        quantidade=Decimal("500.000000"), unidade="M3",
        preco_unitario_sem_bdi=Decimal("45.000000"),
    )
    item2 = Item(
        grupo_id=grupo.id, ordem=1,
        composicao_id=None,
        quantidade=Decimal("1.000000"), unidade="UN",
    )
    db_session.add_all([item1, item2])
    await db_session.commit()
    return item1, item2


@pytest.mark.asyncio
async def test_get_cronograma_retorna_config_e_linhas_vazias(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa, empresa
):
    item1, item2 = await _setup_versao_com_itens(db_session, versao_ativa, empresa)

    resp = await client.get(
        f"/versoes/{versao_ativa.id}/cronograma", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["cronograma_inicio"] is None
    assert data["cronograma_fim"] is None
    assert len(data["linhas"]) == 2
    linha1 = next(l for l in data["linhas"] if l["item_id"] == item1.id)
    assert linha1["descricao"] == "TERRAPLANAGEM MECANIZADA"
    assert linha1["distribuicao_json"] == {}
    linha2 = next(l for l in data["linhas"] if l["item_id"] == item2.id)
    assert linha2["descricao"] == ""
    assert linha2["distribuicao_json"] == {}


@pytest.mark.asyncio
async def test_patch_config_persiste_datas(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    resp = await client.patch(
        f"/versoes/{versao_ativa.id}/cronograma/config",
        json={"cronograma_inicio": "2025-01", "cronograma_fim": "2026-06"},
        headers=auth_headers,
    )
    assert resp.status_code == 204

    await db_session.refresh(versao_ativa)
    assert versao_ativa.cronograma_inicio == "2025-01"
    assert versao_ativa.cronograma_fim == "2026-06"


@pytest.mark.asyncio
async def test_patch_linha_cria_cronograma_linha(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa, empresa
):
    item1, _ = await _setup_versao_com_itens(db_session, versao_ativa, empresa)

    resp = await client.patch(
        f"/versoes/{versao_ativa.id}/cronograma/linhas/{item1.id}",
        json={"distribuicao_json": {"2025-01": 40.0, "2025-02": 60.0}},
        headers=auth_headers,
    )
    assert resp.status_code == 204

    r = await db_session.execute(
        select(CronogramaLinha).where(CronogramaLinha.item_id == item1.id)
    )
    cl = r.scalar_one_or_none()
    assert cl is not None
    assert cl.distribuicao_json == {"2025-01": 40.0, "2025-02": 60.0}


@pytest.mark.asyncio
async def test_patch_linha_atualiza_linha_existente(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa, empresa
):
    item1, _ = await _setup_versao_com_itens(db_session, versao_ativa, empresa)
    cl = CronogramaLinha(item_id=item1.id, distribuicao_json={"2025-01": 100.0})
    db_session.add(cl)
    await db_session.commit()

    resp = await client.patch(
        f"/versoes/{versao_ativa.id}/cronograma/linhas/{item1.id}",
        json={"distribuicao_json": {"2025-01": 50.0, "2025-02": 50.0}},
        headers=auth_headers,
    )
    assert resp.status_code == 204

    await db_session.refresh(cl)
    assert cl.distribuicao_json == {"2025-01": 50.0, "2025-02": 50.0}


@pytest.mark.asyncio
async def test_patch_linha_remove_zeros_do_json(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa, empresa
):
    item1, _ = await _setup_versao_com_itens(db_session, versao_ativa, empresa)

    resp = await client.patch(
        f"/versoes/{versao_ativa.id}/cronograma/linhas/{item1.id}",
        json={"distribuicao_json": {"2025-01": 0.0, "2025-02": 60.0, "2025-03": 0.0}},
        headers=auth_headers,
    )
    assert resp.status_code == 204

    r = await db_session.execute(
        select(CronogramaLinha).where(CronogramaLinha.item_id == item1.id)
    )
    cl = r.scalar_one_or_none()
    assert cl.distribuicao_json == {"2025-02": 60.0}


@pytest.mark.asyncio
async def test_patch_config_em_versao_bloqueada_retorna_409(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    versao_ativa.bloqueada = True
    await db_session.commit()

    resp = await client.patch(
        f"/versoes/{versao_ativa.id}/cronograma/config",
        json={"cronograma_inicio": "2025-01", "cronograma_fim": "2025-12"},
        headers=auth_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_patch_linha_em_versao_bloqueada_retorna_409(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa, empresa
):
    item1, _ = await _setup_versao_com_itens(db_session, versao_ativa, empresa)
    versao_ativa.bloqueada = True
    await db_session.commit()

    resp = await client.patch(
        f"/versoes/{versao_ativa.id}/cronograma/linhas/{item1.id}",
        json={"distribuicao_json": {"2025-01": 100.0}},
        headers=auth_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_isolamento_empresa_b_nao_acessa_cronograma_empresa_a(
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

    resp = await client.get(
        f"/versoes/{versao_ativa.id}/cronograma", headers=headers_b
    )
    assert resp.status_code == 404
