import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.empresa import Empresa
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.pacote_job import PacoteJob
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.services.auth_service import create_access_token, hash_password
from app.services.pacote_service import processar_pacote


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


# ---------------------------------------------------------------------------
# Service tests — chamam processar_pacote diretamente com DB de teste
# ---------------------------------------------------------------------------
import os
import zipfile
from decimal import Decimal
from pathlib import Path
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

_TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://orcaavml:orcaavml@localhost:5432/orcaavml_test",
)


async def _setup_dados(db: AsyncSession, versao_ativa: Versao) -> None:
    grupo = Grupo(versao_id=versao_ativa.id, nome="Terraplanagem", ordem=0)
    db.add(grupo)
    await db.flush()
    db.add(Item(
        grupo_id=grupo.id, ordem=0, unidade="m³",
        quantidade=Decimal("100"), preco_unitario_sem_bdi=Decimal("50"),
    ))
    versao_ativa.total_sem_bdi = Decimal("5000")
    versao_ativa.total_com_bdi = Decimal("5000")
    await db.commit()


@pytest.mark.asyncio
async def test_processar_pacote_ok(
    db_session: AsyncSession, empresa: Empresa, versao_ativa: Versao, tmp_path: Path
):
    await _setup_dados(db_session, versao_ativa)
    job = PacoteJob(versao_id=versao_ativa.id, empresa_id=empresa.id, status="pendente")
    db_session.add(job)
    await db_session.commit()

    test_engine = create_async_engine(_TEST_DB_URL)
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    try:
        with patch("app.services.pacote_service.settings") as mock_cfg:
            mock_cfg.pacotes_dir = str(tmp_path)
            await processar_pacote(job.id, versao_ativa.id, _db_factory=factory)
    finally:
        await test_engine.dispose()

    await db_session.refresh(job)
    assert job.status == "pronto"
    assert job.url_download is not None
    zip_path = tmp_path / job.url_download
    assert zip_path.exists()
    with zipfile.ZipFile(zip_path) as zf:
        assert "planilha.xlsx" in zf.namelist()


@pytest.mark.asyncio
async def test_processar_pacote_sem_proposta(
    db_session: AsyncSession, empresa: Empresa, versao_ativa: Versao, tmp_path: Path
):
    """PropostaConfig ausente → proposta.pdf omitida, job fica pronto."""
    await _setup_dados(db_session, versao_ativa)
    job = PacoteJob(versao_id=versao_ativa.id, empresa_id=empresa.id, status="pendente")
    db_session.add(job)
    await db_session.commit()

    test_engine = create_async_engine(_TEST_DB_URL)
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    try:
        with patch("app.services.pacote_service.settings") as mock_cfg:
            mock_cfg.pacotes_dir = str(tmp_path)
            await processar_pacote(job.id, versao_ativa.id, _db_factory=factory)
    finally:
        await test_engine.dispose()

    await db_session.refresh(job)
    assert job.status == "pronto"
    with zipfile.ZipFile(tmp_path / job.url_download) as zf:
        assert "proposta.pdf" not in zf.namelist()
        assert "planilha.xlsx" in zf.namelist()


@pytest.mark.asyncio
async def test_processar_pacote_sem_cronograma(
    db_session: AsyncSession, empresa: Empresa, versao_ativa: Versao, tmp_path: Path
):
    """versao.cronograma_inicio == None → cronograma.xlsx omitido, job fica pronto."""
    await _setup_dados(db_session, versao_ativa)
    job = PacoteJob(versao_id=versao_ativa.id, empresa_id=empresa.id, status="pendente")
    db_session.add(job)
    await db_session.commit()

    test_engine = create_async_engine(_TEST_DB_URL)
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    try:
        with patch("app.services.pacote_service.settings") as mock_cfg:
            mock_cfg.pacotes_dir = str(tmp_path)
            await processar_pacote(job.id, versao_ativa.id, _db_factory=factory)
    finally:
        await test_engine.dispose()

    await db_session.refresh(job)
    assert job.status == "pronto"
    with zipfile.ZipFile(tmp_path / job.url_download) as zf:
        assert "cronograma.xlsx" not in zf.namelist()
        assert "planilha.xlsx" in zf.namelist()


@pytest.mark.asyncio
async def test_processar_pacote_erro(
    db_session: AsyncSession, empresa: Empresa, versao_ativa: Versao, tmp_path: Path
):
    """Erro inesperado em gerar_planilha_bytes → job fica com status 'erro'."""
    job = PacoteJob(versao_id=versao_ativa.id, empresa_id=empresa.id, status="pendente")
    db_session.add(job)
    await db_session.commit()

    test_engine = create_async_engine(_TEST_DB_URL)
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    try:
        with patch(
            "app.services.pacote_service.gerar_planilha_bytes",
            new_callable=AsyncMock,
            side_effect=RuntimeError("disk full"),
        ):
            with patch("app.services.pacote_service.settings") as mock_cfg:
                mock_cfg.pacotes_dir = str(tmp_path)
                await processar_pacote(job.id, versao_ativa.id, _db_factory=factory)
    finally:
        await test_engine.dispose()

    await db_session.refresh(job)
    assert job.status == "erro"
    assert job.erro_mensagem == "Erro interno ao gerar o pacote. Contate o suporte."
