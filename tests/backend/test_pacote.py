import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.empresa import Empresa
from app.models.pacote_job import PacoteJob
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.services.auth_service import create_access_token, hash_password


@pytest.mark.asyncio
async def test_post_pacote_cria_job(
    client: AsyncClient, auth_headers: dict, versao_ativa: Versao
):
    with patch("app.routers.pacote.processar_pacote", new_callable=AsyncMock):
        resp = await client.post(f"/versoes/{versao_ativa.id}/pacote", headers=auth_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["versao_id"] == versao_ativa.id
    assert data["status"] == "pendente"


@pytest.mark.asyncio
async def test_post_pacote_conflito(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, empresa: Empresa, versao_ativa: Versao
):
    db_session.add(PacoteJob(versao_id=versao_ativa.id, empresa_id=empresa.id, status="processando"))
    await db_session.commit()

    with patch("app.routers.pacote.processar_pacote", new_callable=AsyncMock):
        resp = await client.post(f"/versoes/{versao_ativa.id}/pacote", headers=auth_headers)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_get_pacote_not_found(
    client: AsyncClient, auth_headers: dict, versao_ativa: Versao
):
    resp = await client.get(f"/versoes/{versao_ativa.id}/pacote", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_pacote_status(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, empresa: Empresa, versao_ativa: Versao
):
    job = PacoteJob(versao_id=versao_ativa.id, empresa_id=empresa.id, status="pronto")
    db_session.add(job)
    await db_session.commit()

    resp = await client.get(f"/versoes/{versao_ativa.id}/pacote", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "pronto"


@pytest.mark.asyncio
async def test_download_not_ready(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, empresa: Empresa, versao_ativa: Versao
):
    db_session.add(PacoteJob(versao_id=versao_ativa.id, empresa_id=empresa.id, status="pendente"))
    await db_session.commit()

    resp = await client.get(f"/versoes/{versao_ativa.id}/pacote/download", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_isolamento_empresa_b(
    client: AsyncClient,
    db_session: AsyncSession, empresa: Empresa, versao_ativa: Versao
):
    empresa_b = Empresa(nome="Empresa B Ltda", cnpj="88.888.888/0001-88")
    db_session.add(empresa_b)
    await db_session.flush()
    usuario_b = Usuario(
        empresa_id=empresa_b.id, nome="Admin B", email="admin_b_pac@teste.com",
        senha_hash=hash_password("x"), papel="admin",
    )
    db_session.add(usuario_b)
    await db_session.flush()
    token_b = create_access_token({
        "sub": str(usuario_b.id), "papel": "admin", "empresa_id": empresa_b.id,
    })
    headers_b = {"Authorization": f"Bearer {token_b}"}

    with patch("app.routers.pacote.processar_pacote", new_callable=AsyncMock):
        r = await client.post(f"/versoes/{versao_ativa.id}/pacote", headers=headers_b)
    assert r.status_code == 404
    assert (await client.get(f"/versoes/{versao_ativa.id}/pacote", headers=headers_b)).status_code == 404
