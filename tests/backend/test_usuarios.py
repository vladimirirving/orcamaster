import pytest


@pytest.mark.asyncio
async def test_list_usuarios_requires_auth(client):
    resp = await client.get("/usuarios")
    assert resp.status_code == 403  # no bearer token


@pytest.mark.asyncio
async def test_admin_can_create_usuario(client, admin_user, empresa):
    from app.services.auth_service import create_access_token
    token = create_access_token({"sub": str(admin_user.id), "papel": "admin", "empresa_id": empresa.id})

    resp = await client.post(
        "/usuarios",
        json={"nome": "João Silva", "email": "joao@teste.com", "senha": "abc123", "papel": "orcamentista"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "joao@teste.com"
    assert "senha_hash" not in data


@pytest.mark.asyncio
async def test_orcamentista_cannot_create_usuario(client, admin_user, empresa, db_session):
    from app.services.auth_service import create_access_token, hash_password
    from app.models.usuario import Usuario
    orc = Usuario(empresa_id=empresa.id, nome="Orc", email="orc@teste.com",
                  senha_hash=hash_password("x"), papel="orcamentista")
    db_session.add(orc)
    await db_session.flush()
    token = create_access_token({"sub": str(orc.id), "papel": "orcamentista", "empresa_id": empresa.id})
    resp = await client.post("/usuarios", json={"nome": "X", "email": "x@x.com", "senha": "y", "papel": "admin"},
                             headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
