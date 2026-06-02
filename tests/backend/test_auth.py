import pytest


@pytest.mark.asyncio
async def test_login_success(client, admin_user):
    resp = await client.post("/auth/login", json={"email": "admin@teste.com", "senha": "senha123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert resp.cookies.get("refresh_token") is not None


@pytest.mark.asyncio
async def test_login_wrong_password(client, admin_user):
    resp = await client.post("/auth/login", json={"email": "admin@teste.com", "senha": "errada"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client, admin_user):
    login = await client.post("/auth/login", json={"email": "admin@teste.com", "senha": "senha123"})
    refresh_token = login.cookies["refresh_token"]
    resp = await client.post("/auth/refresh", cookies={"refresh_token": refresh_token})
    assert resp.status_code == 200
    assert "access_token" in resp.json()
