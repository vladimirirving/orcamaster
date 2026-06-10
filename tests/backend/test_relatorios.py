import pytest
from decimal import Decimal as D
from httpx import AsyncClient
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.cronograma_linha import CronogramaLinha
from app.models.medicao import Medicao
from app.models.obra import Obra
from datetime import date


@pytest.mark.asyncio
async def test_relatorio_medicao_sem_medicoes(
    client: AsyncClient, auth_headers: dict, versao_ativa, db_session
):
    """Sem medições: realizado_pct = 0 para todos os grupos."""
    grupo = Grupo(versao_id=versao_ativa.id, nome="Terraplenagem", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, quantidade=D("100"), unidade="M3",
        preco_unitario_sem_bdi=D("50"), preco_unitario_com_bdi=D("55"),
    )
    db_session.add(item)
    await db_session.flush()

    r = await client.get(
        f"/versoes/{versao_ativa.id}/relatorio-medicao",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ultima_medicao_id"] is None
    assert len(data["grupos"]) == 1
    assert data["grupos"][0]["grupo_nome"] == "Terraplenagem"
    assert data["grupos"][0]["realizado_pct"] == 0.0


@pytest.mark.asyncio
async def test_relatorio_medicao_com_medicao(
    client: AsyncClient, auth_headers: dict, versao_ativa, db_session
):
    """Com medição: realizado_pct e valor_medido corretos."""
    grupo = Grupo(versao_id=versao_ativa.id, nome="Pavimentação", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, quantidade=D("200"), unidade="T",
        preco_unitario_sem_bdi=D("300"), preco_unitario_com_bdi=D("330"),
    )
    db_session.add(item)
    await db_session.flush()

    medicao = Medicao(
        versao_id=versao_ativa.id,
        periodo_inicio=date(2026, 5, 1),
        periodo_fim=date(2026, 5, 31),
        linhas_json={str(item.id): 40.0},
    )
    db_session.add(medicao)
    await db_session.flush()

    r = await client.get(
        f"/versoes/{versao_ativa.id}/relatorio-medicao",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ultima_medicao_id"] == medicao.id
    g = data["grupos"][0]
    assert g["realizado_pct"] == pytest.approx(40.0)
    # valor_medido = item.total (200*300=60000) * 40/100 = 24000
    assert float(g["valor_medido"]) == pytest.approx(24000.0)


@pytest.mark.asyncio
async def test_relatorio_medicao_tenant_isolation(
    client: AsyncClient, versao_ativa, db_session
):
    """Versão de outra empresa → 404."""
    from app.models.empresa import Empresa
    from app.models.usuario import Usuario
    from app.services.auth_service import hash_password, create_access_token

    empresa_b = Empresa(nome="Outra Empresa", cnpj="11.111.111/0001-11")
    db_session.add(empresa_b)
    await db_session.flush()
    user_b = Usuario(
        empresa_id=empresa_b.id, nome="B", email="b2@b.com",
        senha_hash=hash_password("x"), papel="admin",
    )
    db_session.add(user_b)
    await db_session.flush()
    token_b = create_access_token({"sub": str(user_b.id), "papel": "admin", "empresa_id": empresa_b.id})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    r = await client.get(
        f"/versoes/{versao_ativa.id}/relatorio-medicao",
        headers=headers_b,
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_comparativo_item_novo(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa,
    composicao_sinapi, db_session
):
    """Item em V2 sem par em V1 → status 'novo'."""
    from app.models.versao import Versao
    v2 = Versao(obra_id=obra.id, numero=2, bloqueada=False)
    db_session.add(v2)
    await db_session.flush()

    g1 = Grupo(versao_id=versao_ativa.id, nome="Terraplenagem", ordem=0)
    db_session.add(g1)
    await db_session.flush()

    g2 = Grupo(versao_id=v2.id, nome="Terraplenagem", ordem=0)
    db_session.add(g2)
    await db_session.flush()
    item2 = Item(
        grupo_id=g2.id, composicao_id=composicao_sinapi.id,
        quantidade=D("100"), unidade="M3",
        preco_unitario_sem_bdi=D("45.23"), preco_unitario_com_bdi=D("50"),
    )
    db_session.add(item2)
    await db_session.flush()

    r = await client.get(
        f"/obras/{obra.id}/comparar",
        params={"v1": versao_ativa.id, "v2": v2.id},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["qtd_novos"] == 1
    assert data["qtd_removidos"] == 0
    novos = [i for i in data["itens"] if i["status"] == "novo"]
    assert len(novos) == 1
    assert novos[0]["v1_preco_unit"] is None


@pytest.mark.asyncio
async def test_comparativo_item_removido(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa,
    composicao_sinapi, db_session
):
    """Item em V1 sem par em V2 → status 'removido'."""
    from app.models.versao import Versao
    v2 = Versao(obra_id=obra.id, numero=2, bloqueada=False)
    db_session.add(v2)
    await db_session.flush()

    g1 = Grupo(versao_id=versao_ativa.id, nome="Pavimentação", ordem=0)
    db_session.add(g1)
    await db_session.flush()
    item1 = Item(
        grupo_id=g1.id, composicao_id=composicao_sinapi.id,
        quantidade=D("200"), unidade="T",
        preco_unitario_sem_bdi=D("300"), preco_unitario_com_bdi=D("330"),
    )
    db_session.add(item1)
    await db_session.flush()

    g2 = Grupo(versao_id=v2.id, nome="Pavimentação", ordem=0)
    db_session.add(g2)
    await db_session.flush()

    r = await client.get(
        f"/obras/{obra.id}/comparar",
        params={"v1": versao_ativa.id, "v2": v2.id},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["qtd_removidos"] == 1
    removidos = [i for i in data["itens"] if i["status"] == "removido"]
    assert removidos[0]["v2_preco_unit"] is None


@pytest.mark.asyncio
async def test_comparativo_preco_alterado(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa,
    composicao_sinapi, db_session
):
    """Mesmo composicao_id, preço diferente → status 'alterado'."""
    from app.models.versao import Versao
    v2 = Versao(obra_id=obra.id, numero=2, bloqueada=False)
    db_session.add(v2)
    await db_session.flush()

    g1 = Grupo(versao_id=versao_ativa.id, nome="Drenagem", ordem=0)
    g2 = Grupo(versao_id=v2.id, nome="Drenagem", ordem=0)
    db_session.add_all([g1, g2])
    await db_session.flush()

    item1 = Item(
        grupo_id=g1.id, composicao_id=composicao_sinapi.id,
        quantidade=D("50"), unidade="M3",
        preco_unitario_sem_bdi=D("45.00"), preco_unitario_com_bdi=D("49.50"),
    )
    item2 = Item(
        grupo_id=g2.id, composicao_id=composicao_sinapi.id,
        quantidade=D("50"), unidade="M3",
        preco_unitario_sem_bdi=D("50.00"), preco_unitario_com_bdi=D("55.00"),
    )
    db_session.add_all([item1, item2])
    await db_session.flush()

    r = await client.get(
        f"/obras/{obra.id}/comparar",
        params={"v1": versao_ativa.id, "v2": v2.id},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["qtd_alterados"] == 1
    alt = [i for i in data["itens"] if i["status"] == "alterado"][0]
    assert float(alt["v1_preco_unit"]) == pytest.approx(45.0)
    assert float(alt["v2_preco_unit"]) == pytest.approx(50.0)
    # delta_total = (50*50) - (50*45) = 2500 - 2250 = 250
    assert float(alt["delta_total"]) == pytest.approx(250.0)


@pytest.mark.asyncio
async def test_comparativo_versoes_de_obras_diferentes(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa,
    empresa, db_session
):
    """V1 e V2 de obras distintas → 400."""
    outra_obra = Obra(
        empresa_id=empresa.id, nome="Outra Obra", tipo_obra="rodovia",
        estado="em_elaboracao", data_criacao=date.today(),
    )
    db_session.add(outra_obra)
    await db_session.flush()
    from app.models.versao import Versao
    v_outra = Versao(obra_id=outra_obra.id, numero=1, bloqueada=False)
    db_session.add(v_outra)
    await db_session.flush()

    r = await client.get(
        f"/obras/{obra.id}/comparar",
        params={"v1": versao_ativa.id, "v2": v_outra.id},
        headers=auth_headers,
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_comparativo_tenant_isolation(
    client: AsyncClient, obra, versao_ativa, db_session
):
    """Obra de outra empresa → 404."""
    from app.models.empresa import Empresa
    from app.models.usuario import Usuario
    from app.models.versao import Versao
    from app.services.auth_service import hash_password, create_access_token

    empresa_b = Empresa(nome="Empresa C", cnpj="22.222.222/0001-22")
    db_session.add(empresa_b)
    await db_session.flush()
    user_b = Usuario(
        empresa_id=empresa_b.id, nome="C", email="c3@c.com",
        senha_hash=hash_password("x"), papel="admin",
    )
    db_session.add(user_b)
    await db_session.flush()
    token_b = create_access_token({"sub": str(user_b.id), "papel": "admin", "empresa_id": empresa_b.id})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    v2 = Versao(obra_id=obra.id, numero=2, bloqueada=False)
    db_session.add(v2)
    await db_session.flush()

    r = await client.get(
        f"/obras/{obra.id}/comparar",
        params={"v1": versao_ativa.id, "v2": v2.id},
        headers=headers_b,
    )
    assert r.status_code == 404
