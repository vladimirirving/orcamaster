import pytest
from datetime import date, timedelta
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.contrato import Contrato, Aditivo
from app.models.item import Item
from app.models.grupo import Grupo
from app.models.medicao import Medicao
from app.models.versao import Versao


@pytest.mark.asyncio
async def test_alertas_lista_vazia(client: AsyncClient, auth_headers: dict, obra):
    resp = await client.get("/alertas", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_contrato_vencido_gera_alerta_alta(
    client: AsyncClient, auth_headers: dict, obra, db_session: AsyncSession
):
    ontem = date.today() - timedelta(days=3)
    contrato = Contrato(
        obra_id=obra.id, objeto="Obras viárias",
        valor_original=Decimal("100000"), data_fim=ontem,
    )
    db_session.add(contrato)
    await db_session.commit()

    resp = await client.get("/alertas", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["tipo"] == "contrato_vencido"
    assert data[0]["severidade"] == "alta"
    assert "3 dias" in data[0]["titulo"]
    assert data[0]["obra_id"] == obra.id


@pytest.mark.asyncio
async def test_contrato_vencendo_gera_alerta_media(
    client: AsyncClient, auth_headers: dict, obra, db_session: AsyncSession
):
    em_15_dias = date.today() + timedelta(days=15)
    contrato = Contrato(
        obra_id=obra.id, objeto="Pavimentação",
        valor_original=Decimal("50000"), data_fim=em_15_dias,
    )
    db_session.add(contrato)
    await db_session.commit()

    resp = await client.get("/alertas", headers=auth_headers)
    data = resp.json()
    assert len(data) == 1
    assert data[0]["tipo"] == "contrato_vencendo"
    assert data[0]["severidade"] == "media"
    assert "15 dias" in data[0]["titulo"]


@pytest.mark.asyncio
async def test_contrato_sem_data_fim_nao_gera_alerta(
    client: AsyncClient, auth_headers: dict, obra, db_session: AsyncSession
):
    contrato = Contrato(
        obra_id=obra.id, objeto="Saneamento",
        valor_original=Decimal("80000"), data_fim=None,
    )
    db_session.add(contrato)
    await db_session.commit()

    resp = await client.get("/alertas", headers=auth_headers)
    assert resp.json() == []


@pytest.mark.asyncio
async def test_contrato_alem_de_30_dias_nao_gera_alerta(
    client: AsyncClient, auth_headers: dict, obra, db_session: AsyncSession
):
    em_60_dias = date.today() + timedelta(days=60)
    contrato = Contrato(
        obra_id=obra.id, objeto="Rodovia",
        valor_original=Decimal("200000"), data_fim=em_60_dias,
    )
    db_session.add(contrato)
    await db_session.commit()

    resp = await client.get("/alertas", headers=auth_headers)
    assert resp.json() == []


@pytest.mark.asyncio
async def test_obra_concluida_nao_gera_alerta(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, empresa, admin_user
):
    from app.models.obra import Obra as ObraModel
    obra_concluida = ObraModel(
        empresa_id=empresa.id, nome="Obra Concluída",
        tipo_obra="ponte", estado="concluido",
        data_criacao=date.today(),
    )
    db_session.add(obra_concluida)
    await db_session.flush()
    ontem = date.today() - timedelta(days=1)
    contrato = Contrato(
        obra_id=obra_concluida.id, objeto="Objeto",
        valor_original=Decimal("10000"), data_fim=ontem,
    )
    db_session.add(contrato)
    await db_session.commit()

    resp = await client.get("/alertas", headers=auth_headers)
    assert resp.json() == []


@pytest.mark.asyncio
async def test_item_revisao_gera_alerta_baixa(
    client: AsyncClient, auth_headers: dict, obra, db_session: AsyncSession,
    versao_ativa,
):
    grupo = Grupo(versao_id=versao_ativa.id, nome="Grupo 1", codigo=None, ordem=1)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, ordem=1, quantidade=Decimal("1"),
        unidade="un", requer_revisao=True,
    )
    db_session.add(item)
    await db_session.commit()

    resp = await client.get("/alertas", headers=auth_headers)
    data = resp.json()
    tipos = [a["tipo"] for a in data]
    assert "item_revisao" in tipos
    alerta = next(a for a in data if a["tipo"] == "item_revisao")
    assert alerta["severidade"] == "baixa"
    assert "1 item" in alerta["titulo"]


@pytest.mark.asyncio
async def test_aditivo_data_fim_atual_usada_para_alerta(
    client: AsyncClient, auth_headers: dict, obra, db_session: AsyncSession
):
    em_60_dias = date.today() + timedelta(days=60)
    em_5_dias = date.today() + timedelta(days=5)
    contrato = Contrato(
        obra_id=obra.id, objeto="Terraplanagem",
        valor_original=Decimal("30000"), data_fim=em_60_dias,
    )
    db_session.add(contrato)
    await db_session.flush()
    aditivo = Aditivo(
        contrato_id=contrato.id, tipo="prazo",
        nova_data_fim=em_5_dias,
    )
    db_session.add(aditivo)
    await db_session.commit()

    resp = await client.get("/alertas", headers=auth_headers)
    data = resp.json()
    assert len(data) == 1
    assert data[0]["tipo"] == "contrato_vencendo"
    assert "5 dias" in data[0]["titulo"]


@pytest.mark.asyncio
async def test_alertas_ordenados_severidade_alta_primeiro(
    client: AsyncClient, auth_headers: dict, obra, db_session: AsyncSession, versao_ativa
):
    ontem = date.today() - timedelta(days=1)
    contrato = Contrato(
        obra_id=obra.id, objeto="Obra",
        valor_original=Decimal("10000"), data_fim=ontem,
    )
    db_session.add(contrato)
    grupo = Grupo(versao_id=versao_ativa.id, nome="G", codigo=None, ordem=1)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(grupo_id=grupo.id, ordem=1, quantidade=Decimal("1"), unidade="un", requer_revisao=True)
    db_session.add(item)
    await db_session.commit()

    resp = await client.get("/alertas", headers=auth_headers)
    data = resp.json()
    assert len(data) >= 2
    assert data[0]["severidade"] == "alta"
    assert data[-1]["severidade"] == "baixa"
