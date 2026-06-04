import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import Usuario
from app.services.auth_service import verify_password


@pytest.mark.asyncio
async def test_alterar_nome_ok(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    admin_user: Usuario,
):
    resp = await client.patch(
        "/auth/me",
        json={"nome": "Novo Nome Teste"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    await db_session.refresh(admin_user)
    assert admin_user.nome == "Novo Nome Teste"


@pytest.mark.asyncio
async def test_alterar_senha_ok(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    admin_user: Usuario,
):
    resp = await client.post(
        "/auth/alterar-senha",
        json={"senha_atual": "senha123", "nova_senha": "novaSenha456"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    await db_session.refresh(admin_user)
    assert verify_password("novaSenha456", admin_user.senha_hash)


@pytest.mark.asyncio
async def test_alterar_senha_atual_errada(
    client: AsyncClient,
    auth_headers: dict,
):
    resp = await client.post(
        "/auth/alterar-senha",
        json={"senha_atual": "senhaErrada999", "nova_senha": "novaSenha456"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_alterar_senha_muito_curta(
    client: AsyncClient,
    auth_headers: dict,
):
    resp = await client.post(
        "/auth/alterar-senha",
        json={"senha_atual": "senha123", "nova_senha": "curta"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
