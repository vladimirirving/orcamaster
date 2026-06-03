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
