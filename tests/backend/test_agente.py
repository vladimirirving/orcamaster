import json
import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from unittest.mock import patch

from app.models.composicao import Composicao
from app.models.empresa import Empresa
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.services.agente_service import (
    buscar_composicao_tool,
    listar_grupos_tipicos_tool,
    obter_composicao_tool,
)
from app.services.auth_service import create_access_token, hash_password


@pytest.mark.asyncio
async def test_buscar_composicao_tool_por_descricao(db_session: AsyncSession, empresa: Empresa):
    c = Composicao(
        empresa_id=None, origem="sinapi", codigo="94966",
        descricao="ESCAVACAO MECANIZADA DE VALA",
        unidade="M3", preco_unitario=Decimal("45.23"), requer_revisao=False,
    )
    db_session.add(c)
    await db_session.commit()

    results = await buscar_composicao_tool("escavacao", None, empresa.id, db_session)
    assert len(results) >= 1
    assert any(r["codigo"] == "94966" for r in results)


@pytest.mark.asyncio
async def test_buscar_composicao_tool_filtro_origem(db_session: AsyncSession, empresa: Empresa):
    db_session.add(Composicao(
        empresa_id=None, origem="sinapi", codigo="S001", descricao="Servico Sinapi",
        unidade="UN", preco_unitario=Decimal("10"), requer_revisao=False,
    ))
    db_session.add(Composicao(
        empresa_id=None, origem="sicro", codigo="X001", descricao="Servico Sicro",
        unidade="UN", preco_unitario=Decimal("20"), requer_revisao=False,
    ))
    await db_session.commit()

    results = await buscar_composicao_tool("Servico", "sinapi", empresa.id, db_session)
    assert len(results) >= 1
    assert all(r["origem"] == "sinapi" for r in results)


def test_listar_grupos_tipicos_rodovia():
    grupos = listar_grupos_tipicos_tool("rodovia")
    assert "Terraplenagem" in grupos
    assert "Drenagem Superficial" in grupos


def test_listar_grupos_tipicos_tipo_desconhecido():
    grupos = listar_grupos_tipicos_tool("xyz_desconhecido")
    assert len(grupos) > 0


@pytest.mark.asyncio
async def test_obter_composicao_tool(db_session: AsyncSession, empresa: Empresa):
    c = Composicao(
        empresa_id=None, origem="sinapi", codigo="94966",
        descricao="ESCAVACAO MECANIZADA", unidade="M3",
        preco_unitario=Decimal("45.23"), requer_revisao=False,
    )
    db_session.add(c)
    await db_session.commit()

    result = await obter_composicao_tool(c.id, empresa.id, db_session)
    assert result is not None
    assert result["codigo"] == "94966"


@pytest.mark.asyncio
async def test_obter_composicao_tool_nao_encontrada(db_session: AsyncSession, empresa: Empresa):
    result = await obter_composicao_tool(99999, empresa.id, db_session)
    assert result is None


@pytest.mark.asyncio
async def test_importar_grupos_ok(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, empresa: Empresa, versao_ativa: Versao,
):
    c1 = Composicao(empresa_id=None, origem="sinapi", codigo="C001",
                    descricao="Composicao 1", unidade="M3",
                    preco_unitario=Decimal("50"), requer_revisao=False)
    c2 = Composicao(empresa_id=None, origem="sinapi", codigo="C002",
                    descricao="Composicao 2", unidade="UN",
                    preco_unitario=Decimal("30"), requer_revisao=False)
    db_session.add_all([c1, c2])
    await db_session.commit()

    payload = {
        "grupos": [
            {
                "nome": "Terraplenagem",
                "itens": [
                    {"composicao_id": c1.id, "descricao": c1.descricao, "codigo": c1.codigo,
                     "unidade": "M3", "quantidade": 100.0},
                    {"composicao_id": c2.id, "descricao": c2.descricao, "codigo": c2.codigo,
                     "unidade": "UN", "quantidade": 5.0},
                ],
            },
            {
                "nome": "Drenagem",
                "itens": [
                    {"composicao_id": c1.id, "descricao": c1.descricao, "codigo": c1.codigo,
                     "unidade": "M3", "quantidade": 200.0},
                ],
            },
        ]
    }
    resp = await client.post(
        f"/versoes/{versao_ativa.id}/agente/importar",
        json=payload, headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["grupos_criados"] == 2
    assert data["itens_criados"] == 3

    grupos = (await db_session.execute(
        select(Grupo).where(Grupo.versao_id == versao_ativa.id).order_by(Grupo.ordem)
    )).scalars().all()
    assert len(grupos) == 2
    assert grupos[0].nome == "Terraplenagem"
    assert grupos[1].nome == "Drenagem"

    await db_session.refresh(versao_ativa)
    assert versao_ativa.total_sem_bdi > 0


@pytest.mark.asyncio
async def test_importar_composicao_invalida(
    client: AsyncClient, auth_headers: dict, versao_ativa: Versao,
):
    payload = {
        "grupos": [{
            "nome": "Grupo",
            "itens": [{"composicao_id": 99999, "descricao": "X", "codigo": "X",
                       "unidade": "UN", "quantidade": 1.0}],
        }]
    }
    resp = await client.post(
        f"/versoes/{versao_ativa.id}/agente/importar",
        json=payload, headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_importar_versao_bloqueada(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, obra: Obra,
):
    versao_bloqueada = Versao(obra_id=obra.id, numero=99, bloqueada=True)
    db_session.add(versao_bloqueada)
    await db_session.commit()

    resp = await client.post(
        f"/versoes/{versao_bloqueada.id}/agente/importar",
        json={"grupos": []}, headers=auth_headers,
    )
    assert resp.status_code == 409


# ── Streaming endpoint tests ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_gerar_proposta_stream(
    client: AsyncClient, auth_headers: dict, versao_ativa: Versao,
):
    proposta_data = {"grupos": [{"nome": "Terraplenagem", "itens": []}]}

    async def fake_stream(descricao, versao_id, empresa_id, db):
        yield 'data: {"type": "progress", "msg": "Analisando..."}\n\n'
        yield f'data: {{"type": "proposta", "data": {json.dumps(proposta_data)}}}\n\n'

    with patch("app.routers.agente.gerar_proposta_stream", new=fake_stream):
        resp = await client.post(
            f"/versoes/{versao_ativa.id}/agente/gerar",
            json={"descricao": "Rodovia de 10km"},
            headers=auth_headers,
        )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers["content-type"]
    assert '"type": "progress"' in resp.text
    assert '"type": "proposta"' in resp.text


@pytest.mark.asyncio
async def test_gerar_proposta_versao_nao_encontrada(
    client: AsyncClient,
    db_session: AsyncSession, empresa: Empresa, versao_ativa: Versao,
):
    empresa_b = Empresa(nome="Empresa B", cnpj="11.111.111/0001-11")
    db_session.add(empresa_b)
    await db_session.flush()
    usuario_b = Usuario(
        empresa_id=empresa_b.id, nome="User B", email="b_ag@test.com",
        senha_hash=hash_password("x"), papel="admin",
    )
    db_session.add(usuario_b)
    await db_session.flush()
    token_b = create_access_token({
        "sub": str(usuario_b.id), "papel": "admin", "empresa_id": empresa_b.id,
    })
    headers_b = {"Authorization": f"Bearer {token_b}"}

    resp = await client.post(
        f"/versoes/{versao_ativa.id}/agente/gerar",
        json={"descricao": "Rodovia"},
        headers=headers_b,
    )
    assert resp.status_code == 404
