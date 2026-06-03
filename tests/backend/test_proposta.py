import pytest
import pytest_asyncio
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.models.obra import Obra
from app.models.versao import Versao
from app.services.auth_service import create_access_token, hash_password


@pytest.mark.asyncio
async def test_empresa_get(client: AsyncClient, auth_headers: dict, empresa: Empresa):
    resp = await client.get("/empresa", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == empresa.id
    assert data["nome"] == empresa.nome
    assert data["cnpj"] == empresa.cnpj
    assert data["representante_nome"] is None
    assert data["declaracoes_padrao"] is None


@pytest.mark.asyncio
async def test_empresa_patch_admin(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession, empresa: Empresa
):
    payload = {
        "representante_nome": "João da Silva",
        "representante_cpf": "123.456.789-00",
        "declaracoes_padrao": "Declaro que aceito os termos.",
    }
    resp = await client.patch("/empresa", headers=auth_headers, json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["representante_nome"] == "João da Silva"
    assert data["representante_cpf"] == "123.456.789-00"
    assert data["declaracoes_padrao"] == "Declaro que aceito os termos."
    await db_session.refresh(empresa)
    assert empresa.representante_nome == "João da Silva"


@pytest.mark.asyncio
async def test_empresa_patch_nao_admin(
    client: AsyncClient, db_session: AsyncSession, empresa: Empresa
):
    orc = Usuario(
        empresa_id=empresa.id,
        nome="Orc Teste",
        email="orc_patch@teste.com",
        senha_hash=hash_password("x"),
        papel="orcamentista",
    )
    db_session.add(orc)
    await db_session.flush()
    token = create_access_token({"sub": str(orc.id), "papel": "orcamentista", "empresa_id": empresa.id})
    orc_headers = {"Authorization": f"Bearer {token}"}

    resp = await client.patch("/empresa", headers=orc_headers, json={"representante_nome": "Hack"})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_proposta_not_found(
    client: AsyncClient, auth_headers: dict, versao_ativa: Versao
):
    resp = await client.get(f"/versoes/{versao_ativa.id}/proposta", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_put_proposta_create(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, empresa: Empresa, versao_ativa: Versao
):
    empresa.declaracoes_padrao = "Declaro que os preços são firmes."
    await db_session.commit()
    await db_session.refresh(empresa)

    payload = {"validade_dias": 60, "data_proposta": "2026-07-01"}
    resp = await client.put(
        f"/versoes/{versao_ativa.id}/proposta", headers=auth_headers, json=payload
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["validade_dias"] == 60
    assert data["data_proposta"] == "2026-07-01"
    assert data["declaracoes"] == "Declaro que os preços são firmes."
    assert data["versao_id"] == versao_ativa.id


@pytest.mark.asyncio
async def test_put_proposta_update(
    client: AsyncClient, auth_headers: dict, versao_ativa: Versao
):
    await client.put(
        f"/versoes/{versao_ativa.id}/proposta",
        headers=auth_headers,
        json={"validade_dias": 30, "data_proposta": "2026-06-01"},
    )
    resp = await client.put(
        f"/versoes/{versao_ativa.id}/proposta",
        headers=auth_headers,
        json={"validade_dias": 90, "data_proposta": "2026-08-01", "declaracoes": "Atualizado"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["validade_dias"] == 90
    assert data["declaracoes"] == "Atualizado"


@pytest.mark.asyncio
async def test_put_proposta_clear_declaracoes(
    client: AsyncClient, auth_headers: dict, versao_ativa: Versao
):
    await client.put(
        f"/versoes/{versao_ativa.id}/proposta",
        headers=auth_headers,
        json={"validade_dias": 60, "data_proposta": "2026-07-01", "declaracoes": "Inicial"},
    )
    resp = await client.put(
        f"/versoes/{versao_ativa.id}/proposta",
        headers=auth_headers,
        json={"validade_dias": 60, "data_proposta": "2026-07-01", "declaracoes": None},
    )
    assert resp.status_code == 200
    assert resp.json()["declaracoes"] is None


@pytest.mark.asyncio
async def test_isolamento_empresa_b(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa: Versao
):
    empresa_b = Empresa(nome="Empresa B Ltda", cnpj="99.999.999/0001-99")
    db_session.add(empresa_b)
    await db_session.flush()
    usuario_b = Usuario(
        empresa_id=empresa_b.id, nome="Admin B", email="admin_b@teste.com",
        senha_hash=hash_password("x"), papel="admin",
    )
    db_session.add(usuario_b)
    await db_session.flush()
    token_b = create_access_token({
        "sub": str(usuario_b.id), "papel": "admin", "empresa_id": empresa_b.id,
    })
    headers_b = {"Authorization": f"Bearer {token_b}"}

    assert (await client.get(f"/versoes/{versao_ativa.id}/proposta", headers=headers_b)).status_code == 404
    assert (await client.put(
        f"/versoes/{versao_ativa.id}/proposta", headers=headers_b,
        json={"validade_dias": 60, "data_proposta": "2026-07-01"},
    )).status_code == 404
