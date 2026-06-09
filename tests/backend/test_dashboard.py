import pytest
from decimal import Decimal
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.cronograma_linha import CronogramaLinha
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.medicao import Medicao


async def _setup(db: AsyncSession, versao_ativa, cronograma_inicio: str, cronograma_fim: str,
                 dist1: dict, dist2: dict, medicoes: list[tuple[date, float]]):
    """
    Cria 2 itens (total=1000 cada), linhas de cronograma, e medições.
    dist1/dist2: distribuicao_json para item1 e item2 respectivamente.
    medicoes: lista de (periodo_inicio_date, pct_ambos_itens).
    Seta versao_ativa.total_sem_bdi=2000 e cronograma_inicio/fim.
    """
    grupo = Grupo(versao_id=versao_ativa.id, nome="G1", ordem=0)
    db.add(grupo)
    await db.flush()

    item1 = Item(
        grupo_id=grupo.id, ordem=0, unidade="m³",
        quantidade=Decimal("10"), preco_unitario_sem_bdi=Decimal("100"),
    )
    item2 = Item(
        grupo_id=grupo.id, ordem=1, unidade="m³",
        quantidade=Decimal("10"), preco_unitario_sem_bdi=Decimal("100"),
    )
    db.add_all([item1, item2])
    await db.flush()
    await db.refresh(item1)
    await db.refresh(item2)

    cl1 = CronogramaLinha(item_id=item1.id, distribuicao_json=dist1)
    cl2 = CronogramaLinha(item_id=item2.id, distribuicao_json=dist2)
    db.add_all([cl1, cl2])

    versao_ativa.cronograma_inicio = cronograma_inicio
    versao_ativa.cronograma_fim = cronograma_fim
    versao_ativa.total_sem_bdi = Decimal("2000")

    for inicio, pct in medicoes:
        from calendar import monthrange
        ultimo = monthrange(inicio.year, inicio.month)[1]
        m = Medicao(
            versao_id=versao_ativa.id,
            periodo_inicio=inicio,
            periodo_fim=date(inicio.year, inicio.month, ultimo),
            linhas_json={str(item1.id): pct, str(item2.id): pct},
        )
        db.add(m)

    await db.commit()


@pytest.mark.asyncio
async def test_portfolio_retorna_obra_com_dados(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # cronograma 2020-01 a 2020-02 (passado) → planejado_pct_hoje = 100%
    # medição Jan/2020 com 30% → realizado=30%, desvio=-70 → atrasado
    await _setup(
        db_session, versao_ativa,
        "2020-01", "2020-02",
        {"2020-01": 40, "2020-02": 60}, {"2020-01": 40, "2020-02": 60},
        [(date(2020, 1, 1), 30.0)],
    )
    resp = await client.get("/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    obra = next(d for d in data if d["versao_id"] == versao_ativa.id)
    assert obra["status"] == "atrasado"
    assert obra["realizado_pct"] == pytest.approx(30.0, abs=0.1)


@pytest.mark.asyncio
async def test_portfolio_obra_sem_versao_ativa(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Bloquear a versão → sem versão ativa
    versao_ativa.bloqueada = True
    await db_session.commit()

    resp = await client.get("/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    obra = next((d for d in resp.json() if d["obra_id"] == versao_ativa.obra_id), None)
    assert obra is not None
    assert obra["status"] == "sem_dados"
    assert obra["versao_id"] is None


@pytest.mark.asyncio
async def test_portfolio_obra_sem_cronograma(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Versão ativa sem cronograma_inicio configurado (padrão None)
    resp = await client.get("/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    obra = next(d for d in resp.json() if d["versao_id"] == versao_ativa.id)
    assert obra["status"] == "sem_dados"


@pytest.mark.asyncio
async def test_portfolio_obra_sem_medicao(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Cronograma configurado mas sem medições
    await _setup(
        db_session, versao_ativa,
        "2020-01", "2020-02",
        {"2020-01": 40, "2020-02": 60}, {"2020-01": 40, "2020-02": 60},
        [],  # sem medições
    )
    resp = await client.get("/dashboard", headers=auth_headers)
    obra = next(d for d in resp.json() if d["versao_id"] == versao_ativa.id)
    assert obra["status"] == "sem_dados"


@pytest.mark.asyncio
async def test_curva_s_calcula_planejado(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Distribui 40% Jan e 60% Fev para cada item (total=1000 cada, versao=2000)
    # Jan planejado_acum = (40/100*1000 + 40/100*1000)/2000*100 = 40%
    # Fev planejado_acum = 40% + 60% = 100%
    await _setup(
        db_session, versao_ativa,
        "2020-01", "2020-02",
        {"2020-01": 40, "2020-02": 60}, {"2020-01": 40, "2020-02": 60},
        [(date(2020, 1, 1), 30.0)],
    )
    resp = await client.get(f"/obras/{versao_ativa.obra_id}/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    jan = next(p for p in data["curva_s"] if p["mes"] == "2020-01")
    fev = next(p for p in data["curva_s"] if p["mes"] == "2020-02")
    assert jan["planejado_acum"] == pytest.approx(40.0, abs=0.1)
    assert fev["planejado_acum"] == pytest.approx(100.0, abs=0.1)


@pytest.mark.asyncio
async def test_curva_s_calcula_realizado(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Medição Jan com 30% para cada item → realizado_acum Jan = 30%
    await _setup(
        db_session, versao_ativa,
        "2020-01", "2020-02",
        {"2020-01": 40, "2020-02": 60}, {"2020-01": 40, "2020-02": 60},
        [(date(2020, 1, 1), 30.0)],
    )
    resp = await client.get(f"/obras/{versao_ativa.obra_id}/dashboard", headers=auth_headers)
    data = resp.json()
    jan = next(p for p in data["curva_s"] if p["mes"] == "2020-01")
    fev = next(p for p in data["curva_s"] if p["mes"] == "2020-02")
    assert jan["realizado_acum"] == pytest.approx(30.0, abs=0.1)
    assert fev["realizado_acum"] is None


@pytest.mark.asyncio
async def test_status_atrasado(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Cronograma passado (2020) → planejado_hoje=100%, realizado=30% → desvio=-70 → atrasado
    await _setup(
        db_session, versao_ativa,
        "2020-01", "2020-02",
        {"2020-01": 40, "2020-02": 60}, {"2020-01": 40, "2020-02": 60},
        [(date(2020, 1, 1), 30.0)],
    )
    resp = await client.get(f"/obras/{versao_ativa.obra_id}/dashboard", headers=auth_headers)
    assert resp.json()["status"] == "atrasado"
    assert resp.json()["desvio"] < -3


@pytest.mark.asyncio
async def test_status_adiantado(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Cronograma futuro (2099) → planejado_hoje=0%, realizado=30% → desvio=+30 → adiantado
    await _setup(
        db_session, versao_ativa,
        "2099-01", "2099-02",
        {"2099-01": 40, "2099-02": 60}, {"2099-01": 40, "2099-02": 60},
        [(date(2099, 1, 1), 30.0)],
    )
    resp = await client.get(f"/obras/{versao_ativa.obra_id}/dashboard", headers=auth_headers)
    assert resp.json()["status"] == "adiantado"
    assert resp.json()["desvio"] > 3


@pytest.mark.asyncio
async def test_status_no_prazo(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Cronograma passado → planejado_hoje=100%, realizado=99% → desvio=-1 → no_prazo
    await _setup(
        db_session, versao_ativa,
        "2020-01", "2020-02",
        {"2020-01": 40, "2020-02": 60}, {"2020-01": 40, "2020-02": 60},
        [(date(2020, 1, 1), 99.0)],
    )
    resp = await client.get(f"/obras/{versao_ativa.obra_id}/dashboard", headers=auth_headers)
    assert resp.json()["status"] == "no_prazo"
    assert -3 <= resp.json()["desvio"] <= 3


@pytest.mark.asyncio
async def test_isolamento_empresa_b(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    from app.models.empresa import Empresa
    from app.models.usuario import Usuario
    from app.services.auth_service import hash_password, create_access_token

    # Setup empresa A data
    await _setup(
        db_session, versao_ativa,
        "2020-01", "2020-01",
        {"2020-01": 100}, {"2020-01": 100},
        [(date(2020, 1, 1), 50.0)],
    )

    # Create empresa B inline
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

    # Empresa B should NOT see empresa A's obras in dashboard
    resp = await client.get("/dashboard", headers=headers_b)
    assert resp.status_code == 200
    ids = [d["obra_id"] for d in resp.json()]
    assert versao_ativa.obra_id not in ids


@pytest.mark.asyncio
async def test_curva_s_sem_medicao_retorna_sem_dados(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Cronograma configurado mas sem medições → endpoint obra retorna sem_dados
    await _setup(
        db_session, versao_ativa,
        "2020-01", "2020-02",
        {"2020-01": 40, "2020-02": 60}, {"2020-01": 40, "2020-02": 60},
        [],  # sem medições
    )
    resp = await client.get(f"/obras/{versao_ativa.obra_id}/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "sem_dados"
    assert resp.json()["curva_s"] == []


@pytest.mark.asyncio
async def test_curva_s_empresa_b_recebe_404(
    client: AsyncClient,
    db_session: AsyncSession, versao_ativa,
):
    from app.models.empresa import Empresa
    from app.models.usuario import Usuario
    from app.services.auth_service import hash_password, create_access_token

    empresa_b = Empresa(nome="Empresa B 2", cnpj="22.222.222/0001-22")
    db_session.add(empresa_b)
    await db_session.flush()
    user_b = Usuario(
        empresa_id=empresa_b.id, nome="User B2", email="userb2@teste.com",
        senha_hash=hash_password("senha123"), papel="admin",
    )
    db_session.add(user_b)
    await db_session.commit()

    token_b = create_access_token({
        "sub": str(user_b.id), "papel": user_b.papel, "empresa_id": user_b.empresa_id,
    })
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Empresa B tries to access empresa A's obra dashboard → 404
    resp = await client.get(f"/obras/{versao_ativa.obra_id}/dashboard", headers=headers_b)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_curva_s_dois_medicoes_sequenciais(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Medicao.linhas_json stores cumulative % per item.
    # Jan medição: 30% accumulated. Feb medição: 55% accumulated.
    # The curva_s should show: Jan=30, Feb=55 (each is the running total at that point).
    grupo = Grupo(versao_id=versao_ativa.id, nome="G2", ordem=0)
    db_session.add(grupo)
    await db_session.flush()

    item1 = Item(
        grupo_id=grupo.id, ordem=0, unidade="m³",
        quantidade=Decimal("10"), preco_unitario_sem_bdi=Decimal("100"),
    )
    db_session.add(item1)
    await db_session.flush()
    await db_session.refresh(item1)

    from app.models.cronograma_linha import CronogramaLinha
    cl1 = CronogramaLinha(item_id=item1.id, distribuicao_json={"2020-01": 40, "2020-02": 60})
    db_session.add(cl1)

    versao_ativa.cronograma_inicio = "2020-01"
    versao_ativa.cronograma_fim = "2020-02"
    versao_ativa.total_sem_bdi = Decimal("1000")

    from calendar import monthrange
    jan_fim = monthrange(2020, 1)[1]
    feb_fim = monthrange(2020, 2)[1]
    med_jan = Medicao(
        versao_id=versao_ativa.id,
        periodo_inicio=date(2020, 1, 1),
        periodo_fim=date(2020, 1, jan_fim),
        linhas_json={str(item1.id): 30.0},
    )
    med_feb = Medicao(
        versao_id=versao_ativa.id,
        periodo_inicio=date(2020, 2, 1),
        periodo_fim=date(2020, 2, feb_fim),
        linhas_json={str(item1.id): 55.0},
    )
    db_session.add_all([med_jan, med_feb])
    await db_session.commit()

    resp = await client.get(f"/obras/{versao_ativa.obra_id}/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    jan = next(p for p in data["curva_s"] if p["mes"] == "2020-01")
    fev = next(p for p in data["curva_s"] if p["mes"] == "2020-02")
    assert jan["realizado_acum"] == pytest.approx(30.0, abs=0.1)
    assert fev["realizado_acum"] == pytest.approx(55.0, abs=0.1)
    # realizado_pct is from latest medição
    assert data["realizado_pct"] == pytest.approx(55.0, abs=0.1)


# --- Novos testes Módulo 21 ---


@pytest.mark.asyncio
async def test_dashboard_inclui_estado(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa, db_session
):
    """Campo estado retornado corretamente."""
    r = await client.get("/dashboard", headers=auth_headers)
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["estado"] == "em_elaboracao"


@pytest.mark.asyncio
async def test_dashboard_inclui_total_com_bdi(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa, db_session
):
    """Campo total_com_bdi presente quando versão ativa existe."""
    from decimal import Decimal
    versao_ativa.total_com_bdi = Decimal("9500.00")
    await db_session.flush()

    r = await client.get("/dashboard", headers=auth_headers)
    assert r.status_code == 200
    items = r.json()
    assert items[0]["total_com_bdi"] is not None
    assert float(items[0]["total_com_bdi"]) == pytest.approx(9500.0)


@pytest.mark.asyncio
async def test_dashboard_tem_alertas_true(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa,
    composicao_sinapi, db_session
):
    """tem_alertas=True quando item tem requer_revisao=True."""
    grupo = Grupo(versao_id=versao_ativa.id, nome="G", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, quantidade=Decimal("10"), unidade="M3",
        preco_unitario_sem_bdi=Decimal("50"), preco_unitario_com_bdi=Decimal("55"),
        requer_revisao=True,
    )
    db_session.add(item)
    await db_session.flush()

    r = await client.get("/dashboard", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()[0]["tem_alertas"] is True


@pytest.mark.asyncio
async def test_dashboard_tem_alertas_false(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa,
    composicao_sinapi, db_session
):
    """tem_alertas=False quando sem itens marcados."""
    grupo = Grupo(versao_id=versao_ativa.id, nome="G", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, quantidade=Decimal("10"), unidade="M3",
        preco_unitario_sem_bdi=Decimal("50"), preco_unitario_com_bdi=Decimal("55"),
        requer_revisao=False,
    )
    db_session.add(item)
    await db_session.flush()

    r = await client.get("/dashboard", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()[0]["tem_alertas"] is False


@pytest.mark.asyncio
async def test_distribuicao_grupos_basico(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa,
    composicao_sinapi, db_session
):
    """Participação % correta, dois grupos."""
    grupo_a = Grupo(versao_id=versao_ativa.id, nome="Pavimentação", ordem=0)
    grupo_b = Grupo(versao_id=versao_ativa.id, nome="Terraplenagem", ordem=1)
    db_session.add_all([grupo_a, grupo_b])
    await db_session.flush()

    # grupo_a: 3 itens de 100 cada = 300; grupo_b: 1 item de 700 = 700; total=1000
    for _ in range(3):
        db_session.add(Item(
            grupo_id=grupo_a.id, quantidade=Decimal("1"), unidade="UN",
            preco_unitario_sem_bdi=Decimal("100"), preco_unitario_com_bdi=Decimal("110"),
        ))
    db_session.add(Item(
        grupo_id=grupo_b.id, quantidade=Decimal("1"), unidade="UN",
        preco_unitario_sem_bdi=Decimal("700"), preco_unitario_com_bdi=Decimal("770"),
    ))
    await db_session.flush()
    versao_ativa.total_sem_bdi = Decimal("1000")
    await db_session.flush()

    r = await client.get(f"/obras/{obra.id}/distribuicao-grupos", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["versao_id"] == versao_ativa.id
    grupos = {g["grupo_nome"]: g for g in data["grupos"]}
    assert pytest.approx(grupos["Pavimentação"]["participacao_pct"], abs=0.1) == 30.0
    assert pytest.approx(grupos["Terraplenagem"]["participacao_pct"], abs=0.1) == 70.0
    total_pct = sum(g["participacao_pct"] for g in data["grupos"])
    assert pytest.approx(total_pct, abs=0.5) == 100.0


@pytest.mark.asyncio
async def test_distribuicao_grupos_sem_versao_ativa(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa, db_session
):
    """Sem versão ativa: lista vazia."""
    versao_ativa.bloqueada = True
    await db_session.flush()

    r = await client.get(f"/obras/{obra.id}/distribuicao-grupos", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["grupos"] == []


@pytest.mark.asyncio
async def test_distribuicao_grupos_tenant_isolation(
    client: AsyncClient, obra, db_session
):
    """Obra de outra empresa → 404."""
    from app.models.empresa import Empresa
    from app.models.usuario import Usuario
    from app.services.auth_service import hash_password, create_access_token

    emp_b = Empresa(nome="Emp B", cnpj="33.333.333/0001-33")
    db_session.add(emp_b)
    await db_session.flush()
    user_b = Usuario(
        empresa_id=emp_b.id, nome="B", email="d4@b.com",
        senha_hash=hash_password("x"), papel="admin",
    )
    db_session.add(user_b)
    await db_session.flush()
    token_b = create_access_token({"sub": str(user_b.id), "papel": "admin", "empresa_id": emp_b.id})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    r = await client.get(f"/obras/{obra.id}/distribuicao-grupos", headers=headers_b)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_distribuicao_grupos_com_subgrupos(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa, db_session
):
    """Items in subgroups are attributed to their root group."""
    grupo_raiz = Grupo(versao_id=versao_ativa.id, nome="Pavimentação", ordem=0, pai_id=None)
    db_session.add(grupo_raiz)
    await db_session.flush()

    subgrupo = Grupo(versao_id=versao_ativa.id, nome="Sub-pavimentação", ordem=0, pai_id=grupo_raiz.id)
    db_session.add(subgrupo)
    await db_session.flush()

    # Item directly in root group: total = 1 * 300 = 300
    db_session.add(Item(
        grupo_id=grupo_raiz.id, quantidade=Decimal("1"), unidade="T",
        preco_unitario_sem_bdi=Decimal("300"), preco_unitario_com_bdi=Decimal("330"),
    ))
    # Item in subgroup: total = 1 * 700 = 700
    db_session.add(Item(
        grupo_id=subgrupo.id, quantidade=Decimal("1"), unidade="T",
        preco_unitario_sem_bdi=Decimal("700"), preco_unitario_com_bdi=Decimal("770"),
    ))
    await db_session.flush()
    versao_ativa.total_sem_bdi = Decimal("1000")
    await db_session.flush()

    r = await client.get(f"/obras/{obra.id}/distribuicao-grupos", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    # Only root group should appear, with total = 300 + 700 = 1000
    assert len(data["grupos"]) == 1
    assert data["grupos"][0]["grupo_nome"] == "Pavimentação"
    assert pytest.approx(data["grupos"][0]["participacao_pct"], abs=0.1) == 100.0
