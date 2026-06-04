import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.composicao import Composicao
from app.models.insumo import Insumo
from app.models.item import Item
from app.models.grupo import Grupo


# ── Composição CRUD ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_composicoes_inclui_sinapi_e_proprias(
    client: AsyncClient, auth_headers: dict,
    composicao_sinapi, composicao_propria
):
    resp = await client.get("/composicoes", headers=auth_headers)
    assert resp.status_code == 200
    ids = [c["id"] for c in resp.json()]
    assert composicao_sinapi.id in ids
    assert composicao_propria.id in ids


@pytest.mark.asyncio
async def test_search_composicoes_por_descricao(
    client: AsyncClient, auth_headers: dict, composicao_sinapi
):
    resp = await client.get("/composicoes?q=ESCAVACAO", headers=auth_headers)
    assert resp.status_code == 200
    assert any(c["codigo"] == "94966" for c in resp.json())


@pytest.mark.asyncio
async def test_filter_composicoes_por_origem(
    client: AsyncClient, auth_headers: dict,
    composicao_sinapi, composicao_propria
):
    resp = await client.get("/composicoes?origem=sinapi", headers=auth_headers)
    assert resp.status_code == 200
    origens = {c["origem"] for c in resp.json()}
    assert origens == {"sinapi"}


@pytest.mark.asyncio
async def test_create_composicao_propria(
    client: AsyncClient, auth_headers: dict, empresa
):
    resp = await client.post("/composicoes", json={
        "codigo": "P-099",
        "descricao": "Servico Teste",
        "unidade": "M",
        "preco_unitario": "55.500000",
    }, headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["origem"] == "propria"
    assert data["empresa_id"] == empresa.id
    assert data["insumos"] == []


@pytest.mark.asyncio
async def test_get_composicao_with_insumos(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, composicao_propria
):
    db_session.add(Insumo(
        composicao_id=composicao_propria.id,
        tipo="material", descricao="Areia", unidade="m3",
        coeficiente=Decimal("1.0"), preco_unitario=Decimal("30.0"),
    ))
    await db_session.commit()

    resp = await client.get(f"/composicoes/{composicao_propria.id}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["codigo"] == "P-001"
    assert len(data["insumos"]) == 1


@pytest.mark.asyncio
async def test_update_composicao_propria(
    client: AsyncClient, auth_headers: dict, composicao_propria
):
    resp = await client.patch(
        f"/composicoes/{composicao_propria.id}",
        json={"descricao": "Servico Atualizado"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["descricao"] == "Servico Atualizado"


@pytest.mark.asyncio
async def test_update_composicao_sinapi_retorna_403(
    client: AsyncClient, auth_headers: dict, composicao_sinapi
):
    resp = await client.patch(
        f"/composicoes/{composicao_sinapi.id}",
        json={"descricao": "Tentativa"},
        headers=auth_headers,
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_delete_composicao_propria(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, composicao_propria
):
    resp = await client.delete(f"/composicoes/{composicao_propria.id}", headers=auth_headers)
    assert resp.status_code == 204
    r = await db_session.execute(
        select(Composicao).where(Composicao.id == composicao_propria.id)
    )
    assert r.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_delete_composicao_sinapi_retorna_403(
    client: AsyncClient, auth_headers: dict, composicao_sinapi
):
    resp = await client.delete(f"/composicoes/{composicao_sinapi.id}", headers=auth_headers)
    assert resp.status_code == 403


# ── Insumo price recalc ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_insumo_recalcula_preco_composicao(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, composicao_propria
):
    resp = await client.post(
        f"/composicoes/{composicao_propria.id}/insumos",
        json={
            "tipo": "material",
            "descricao": "Cimento CP-II",
            "unidade": "kg",
            "coeficiente": "5.000000",
            "preco_unitario": "3.500000",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["tipo"] == "material"

    await db_session.refresh(composicao_propria)
    assert composicao_propria.preco_unitario == Decimal("17.500000")


@pytest.mark.asyncio
async def test_update_insumo_recalcula_preco_composicao(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, composicao_propria
):
    insumo = Insumo(
        composicao_id=composicao_propria.id, tipo="mao_obra",
        descricao="Pedreiro", unidade="h",
        coeficiente=Decimal("2.000000"), preco_unitario=Decimal("10.000000"),
    )
    db_session.add(insumo)
    await db_session.commit()

    resp = await client.patch(
        f"/composicoes/{composicao_propria.id}/insumos/{insumo.id}",
        json={"preco_unitario": "15.000000"},
        headers=auth_headers,
    )
    assert resp.status_code == 200

    await db_session.refresh(composicao_propria)
    assert composicao_propria.preco_unitario == Decimal("30.000000")


@pytest.mark.asyncio
async def test_delete_insumo_recalcula_preco_composicao(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, composicao_propria
):
    i1 = Insumo(
        composicao_id=composicao_propria.id, tipo="material",
        descricao="Areia", unidade="m3",
        coeficiente=Decimal("1.000000"), preco_unitario=Decimal("50.000000"),
    )
    i2 = Insumo(
        composicao_id=composicao_propria.id, tipo="mao_obra",
        descricao="Servente", unidade="h",
        coeficiente=Decimal("2.000000"), preco_unitario=Decimal("10.000000"),
    )
    db_session.add_all([i1, i2])
    await db_session.commit()

    resp = await client.delete(
        f"/composicoes/{composicao_propria.id}/insumos/{i1.id}",
        headers=auth_headers,
    )
    assert resp.status_code == 204

    await db_session.refresh(composicao_propria)
    assert composicao_propria.preco_unitario == Decimal("20.000000")


@pytest.mark.asyncio
async def test_create_insumo_em_sinapi_retorna_403(
    client: AsyncClient, auth_headers: dict, composicao_sinapi
):
    resp = await client.post(
        f"/composicoes/{composicao_sinapi.id}/insumos",
        json={
            "tipo": "material", "descricao": "X", "unidade": "un",
            "coeficiente": "1.0", "preco_unitario": "1.0",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 403


# ── Import CSV ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_import_sinapi_csv_cria_composicoes(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    csv_content = (
        "codigo,descricao,unidade,preco_unitario\n"
        "94966,ESCAVACAO MECANIZADA DE VALA,M3,45.23\n"
        "97645,REATERRO MECANIZADO,M3,8.50\n"
    )
    resp = await client.post(
        "/composicoes/importar",
        data={"origem": "sinapi"},
        files={"file": ("sinapi.csv", csv_content.encode(), "text/csv")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["criadas"] == 2
    assert data["atualizadas"] == 0
    assert data["itens_marcados"] == 0

    r = await db_session.execute(
        select(Composicao).where(Composicao.codigo == "94966", Composicao.origem == "sinapi")
    )
    comp = r.scalar_one_or_none()
    assert comp is not None
    assert comp.preco_unitario == Decimal("45.230000")


@pytest.mark.asyncio
async def test_import_sinapi_atualiza_preco_e_marca_requer_revisao(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa, composicao_sinapi
):
    grupo = Grupo(versao_id=versao_ativa.id, nome="Terra", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, ordem=0,
        quantidade=Decimal("10.000000"), unidade="M3",
        composicao_id=composicao_sinapi.id,
        preco_unitario_sem_bdi=Decimal("45.230000"),
        requer_revisao=False,
    )
    db_session.add(item)
    await db_session.commit()

    csv_content = (
        "codigo,descricao,unidade,preco_unitario\n"
        "94966,ESCAVACAO MECANIZADA DE VALA,M3,50.00\n"
    )
    resp = await client.post(
        "/composicoes/importar",
        data={"origem": "sinapi"},
        files={"file": ("sinapi.csv", csv_content.encode(), "text/csv")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["criadas"] == 0
    assert data["atualizadas"] == 1
    assert data["itens_marcados"] == 1

    await db_session.refresh(item)
    assert item.requer_revisao is True
    await db_session.refresh(composicao_sinapi)
    assert composicao_sinapi.preco_unitario == Decimal("50.000000")


@pytest.mark.asyncio
async def test_import_sem_mudanca_de_preco_nao_marca_requer_revisao(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa, composicao_sinapi
):
    grupo = Grupo(versao_id=versao_ativa.id, nome="G", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, ordem=0,
        quantidade=Decimal("10.000000"), unidade="M3",
        composicao_id=composicao_sinapi.id,
        preco_unitario_sem_bdi=Decimal("45.230000"),
        requer_revisao=False,
    )
    db_session.add(item)
    await db_session.commit()

    csv_content = (
        "codigo,descricao,unidade,preco_unitario\n"
        "94966,ESCAVACAO MECANIZADA DE VALA,M3,45.23\n"
    )
    resp = await client.post(
        "/composicoes/importar",
        data={"origem": "sinapi"},
        files={"file": ("sinapi.csv", csv_content.encode(), "text/csv")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["itens_marcados"] == 0

    await db_session.refresh(item)
    assert item.requer_revisao is False


# ── Vincular composição ao item ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_vincular_composicao_snapshots_preco(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, obra, versao_ativa, composicao_sinapi
):
    grupo = Grupo(versao_id=versao_ativa.id, nome="Terra", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, ordem=0,
        quantidade=Decimal("10.000000"), unidade="M3",
    )
    db_session.add(item)
    await db_session.commit()

    resp = await client.patch(
        f"/itens/{item.id}/composicao",
        json={"composicao_id": composicao_sinapi.id},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["composicao_id"] == composicao_sinapi.id
    assert Decimal(data["preco_unitario_sem_bdi"]) == composicao_sinapi.preco_unitario
    assert data["requer_revisao"] is False


@pytest.mark.asyncio
async def test_vincular_composicao_recalcula_totais_versao(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, obra, versao_ativa, composicao_sinapi
):
    grupo = Grupo(versao_id=versao_ativa.id, nome="Drenagem", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, ordem=0,
        quantidade=Decimal("100.000000"), unidade="M3",
    )
    db_session.add(item)
    await db_session.commit()

    await client.patch(
        f"/itens/{item.id}/composicao",
        json={"composicao_id": composicao_sinapi.id},
        headers=auth_headers,
    )

    r_v = await client.get(f"/obras/{obra.id}/versoes", headers=auth_headers)
    versao_data = next(v for v in r_v.json() if v["id"] == versao_ativa.id)
    # total_sem_bdi = 100 * 45.23 = 4523.00
    assert Decimal(versao_data["total_sem_bdi"]) == Decimal("4523.00")


# ── Atualizar preço ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_atualizar_preco_limpa_requer_revisao_e_atualiza_snapshot(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, obra, versao_ativa, composicao_sinapi
):
    grupo = Grupo(versao_id=versao_ativa.id, nome="G", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, ordem=0,
        quantidade=Decimal("5.000000"), unidade="M3",
        composicao_id=composicao_sinapi.id,
        preco_unitario_sem_bdi=Decimal("40.000000"),  # stale snapshot
        requer_revisao=True,
    )
    db_session.add(item)
    await db_session.commit()

    resp = await client.post(f"/itens/{item.id}/atualizar-preco", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert Decimal(data["preco_unitario_sem_bdi"]) == composicao_sinapi.preco_unitario
    assert data["requer_revisao"] is False


@pytest.mark.asyncio
async def test_atualizar_preco_sem_composicao_retorna_422(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    grupo = Grupo(versao_id=versao_ativa.id, nome="G", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, ordem=0,
        quantidade=Decimal("1.000000"), unidade="UN",
        composicao_id=None,
    )
    db_session.add(item)
    await db_session.commit()

    resp = await client.post(f"/itens/{item.id}/atualizar-preco", headers=auth_headers)
    assert resp.status_code == 422


# ── Isolamento cross-empresa ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_empresa_b_nao_ve_composicao_propria_de_empresa_a(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, composicao_propria
):
    from app.models.empresa import Empresa
    from app.models.usuario import Usuario
    from app.services.auth_service import hash_password, create_access_token

    empresa_b = Empresa(nome="Empresa B", cnpj="11.111.111/0001-11")
    db_session.add(empresa_b)
    await db_session.flush()

    user_b = Usuario(
        empresa_id=empresa_b.id,
        nome="User B",
        email="userb@teste.com",
        senha_hash=hash_password("senha123"),
        papel="admin",
    )
    db_session.add(user_b)
    await db_session.commit()

    token_b = create_access_token({
        "sub": str(user_b.id),
        "papel": user_b.papel,
        "empresa_id": user_b.empresa_id,
    })
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # composicao_propria belongs to empresa A — empresa B should get 403 on direct access
    resp = await client.get(
        f"/composicoes/{composicao_propria.id}", headers=headers_b
    )
    assert resp.status_code == 403

    # empresa B's list should NOT include empresa A's propria composicao
    resp_list = await client.get("/composicoes", headers=headers_b)
    assert resp_list.status_code == 200
    ids = [c["id"] for c in resp_list.json()]
    assert composicao_propria.id not in ids


@pytest.mark.asyncio
async def test_import_sinapi_xlsx(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    from io import BytesIO
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["codigo", "descricao", "unidade", "preco_unitario"])
    ws.append(["X001", "SERVICO XLSX TESTE", "UN", 99.50])
    ws.append(["X002", "OUTRO SERVICO XLSX", "M3", 12.00])
    buf = BytesIO()
    wb.save(buf)

    resp = await client.post(
        "/composicoes/importar",
        data={"origem": "sinapi"},
        files={"file": (
            "sinapi.xlsx",
            buf.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["criadas"] == 2
    assert data["atualizadas"] == 0
    assert data["itens_marcados"] == 0

    result = await db_session.execute(
        select(Composicao).where(Composicao.codigo == "X001", Composicao.origem == "sinapi")
    )
    comp = result.scalar_one_or_none()
    assert comp is not None
    assert comp.descricao == "SERVICO XLSX TESTE"
