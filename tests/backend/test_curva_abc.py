import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.empresa import Empresa
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.usuario import Usuario


async def _setup(db: AsyncSession, versao_ativa, itens_config: list[tuple[str, str, float]]):
    """
    Cria grupos e itens para o teste.
    itens_config: lista de (grupo_nome, unidade, preco_unitario_sem_bdi).
    Cada item tem quantidade=1.0, portanto total == preco_unitario_sem_bdi.
    Seta versao_ativa.total_sem_bdi = soma dos preços.
    """
    total = Decimal("0")
    for nome_grupo, unidade, preco in itens_config:
        grupo = Grupo(versao_id=versao_ativa.id, nome=nome_grupo, ordem=0)
        db.add(grupo)
        await db.flush()
        preco_dec = Decimal(str(preco))
        item = Item(
            grupo_id=grupo.id,
            ordem=0,
            unidade=unidade,
            quantidade=Decimal("1"),
            preco_unitario_sem_bdi=preco_dec,
        )
        db.add(item)
        total += preco_dec

    versao_ativa.total_sem_bdi = total
    await db.commit()


@pytest.mark.asyncio
async def test_curva_abc_ordenada_por_total(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    await _setup(db_session, versao_ativa, [
        ("Pavimentação", "m²", 800.0),
        ("Sinalização", "m", 50.0),
        ("Terraplenagem", "m³", 150.0),
    ])
    resp = await client.get(f"/versoes/{versao_ativa.id}/curva-abc", headers=auth_headers)
    assert resp.status_code == 200
    itens = resp.json()["itens"]
    assert len(itens) == 3
    assert itens[0]["total"] == "800.00"
    assert itens[1]["total"] == "150.00"
    assert itens[2]["total"] == "50.00"
    assert itens[0]["rank"] == 1
    assert itens[1]["rank"] == 2
    assert itens[2]["rank"] == 3


@pytest.mark.asyncio
async def test_curva_abc_calcula_participacao(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    await _setup(db_session, versao_ativa, [
        ("G1", "un", 800.0),
        ("G2", "un", 150.0),
        ("G3", "un", 50.0),
    ])
    resp = await client.get(f"/versoes/{versao_ativa.id}/curva-abc", headers=auth_headers)
    itens = resp.json()["itens"]
    assert itens[0]["participacao_pct"] == pytest.approx(80.0, abs=0.1)
    assert itens[0]["acumulado_pct"] == pytest.approx(80.0, abs=0.1)
    assert itens[1]["participacao_pct"] == pytest.approx(15.0, abs=0.1)
    assert itens[1]["acumulado_pct"] == pytest.approx(95.0, abs=0.1)
    assert itens[2]["participacao_pct"] == pytest.approx(5.0, abs=0.1)
    assert itens[2]["acumulado_pct"] == pytest.approx(100.0, abs=0.1)


@pytest.mark.asyncio
async def test_curva_abc_faixas_corretas(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # item800 acumulado=80% → A (≤80); item150 acumulado=95% → B (≤95); item50 acumulado=100% → C
    await _setup(db_session, versao_ativa, [
        ("G1", "un", 800.0),
        ("G2", "un", 150.0),
        ("G3", "un", 50.0),
    ])
    resp = await client.get(f"/versoes/{versao_ativa.id}/curva-abc", headers=auth_headers)
    itens = resp.json()["itens"]
    assert itens[0]["faixa"] == "A"
    assert itens[1]["faixa"] == "B"
    assert itens[2]["faixa"] == "C"


@pytest.mark.asyncio
async def test_curva_abc_exclui_total_zero(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    await _setup(db_session, versao_ativa, [
        ("G1", "un", 500.0),
        ("G2", "un", 0.0),
    ])
    versao_ativa.total_sem_bdi = Decimal("500")
    await db_session.commit()

    resp = await client.get(f"/versoes/{versao_ativa.id}/curva-abc", headers=auth_headers)
    assert resp.status_code == 200
    itens = resp.json()["itens"]
    assert len(itens) == 1
    assert itens[0]["total"] == "500.00"


@pytest.mark.asyncio
async def test_curva_abc_vazio(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    resp = await client.get(f"/versoes/{versao_ativa.id}/curva-abc", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["itens"] == []


@pytest.mark.asyncio
async def test_curva_abc_export_xlsx(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    await _setup(db_session, versao_ativa, [
        ("G1", "un", 800.0),
        ("G2", "un", 200.0),
    ])
    resp = await client.get(
        f"/versoes/{versao_ativa.id}/curva-abc/export",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert "spreadsheetml" in resp.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_isolamento_empresa_b(
    client: AsyncClient,
    db_session: AsyncSession, versao_ativa,
):
    from app.services.auth_service import hash_password, create_access_token

    empresa_b = Empresa(nome="Empresa B", cnpj="99.999.999/0001-99")
    db_session.add(empresa_b)
    await db_session.flush()
    user_b = Usuario(
        empresa_id=empresa_b.id, nome="User B", email="userb_abc@teste.com",
        senha_hash=hash_password("senha123"), papel="admin",
    )
    db_session.add(user_b)
    await db_session.commit()

    token_b = create_access_token({
        "sub": str(user_b.id), "papel": user_b.papel, "empresa_id": user_b.empresa_id,
    })
    headers_b = {"Authorization": f"Bearer {token_b}"}

    resp = await client.get(f"/versoes/{versao_ativa.id}/curva-abc", headers=headers_b)
    assert resp.status_code == 404
