import pytest
from datetime import date
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_diario_vazio(client: AsyncClient, auth_headers: dict, obra):
    r = await client.get(f"/obras/{obra.id}/diario", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_create_entrada(client: AsyncClient, auth_headers: dict, obra):
    payload = {
        "data": str(date.today()),
        "clima": "ensolarado",
        "efetivo": 10,
        "atividades": "Concretagem pilar P3",
    }
    r = await client.post(f"/obras/{obra.id}/diario", json=payload, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["clima"] == "ensolarado"
    assert data["efetivo"] == 10
    assert data["atividades"] == "Concretagem pilar P3"
    assert data["fotos"] == []


@pytest.mark.asyncio
async def test_create_entrada_data_duplicada(client: AsyncClient, auth_headers: dict, obra):
    payload = {"data": "2026-01-10", "clima": "nublado", "efetivo": 5, "atividades": "Teste"}
    await client.post(f"/obras/{obra.id}/diario", json=payload, headers=auth_headers)
    r = await client.post(f"/obras/{obra.id}/diario", json=payload, headers=auth_headers)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_get_entrada(client: AsyncClient, auth_headers: dict, obra):
    r = await client.post(
        f"/obras/{obra.id}/diario",
        json={"data": "2026-02-01", "clima": "chuvoso", "efetivo": 3, "atividades": "Armação"},
        headers=auth_headers,
    )
    eid = r.json()["id"]
    r2 = await client.get(f"/obras/{obra.id}/diario/{eid}", headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["atividades"] == "Armação"


@pytest.mark.asyncio
async def test_update_entrada(client: AsyncClient, auth_headers: dict, obra):
    r = await client.post(
        f"/obras/{obra.id}/diario",
        json={"data": "2026-03-01", "clima": "ensolarado", "efetivo": 8, "atividades": "Original"},
        headers=auth_headers,
    )
    eid = r.json()["id"]
    r2 = await client.patch(
        f"/obras/{obra.id}/diario/{eid}",
        json={"atividades": "Atualizado", "efetivo": 12},
        headers=auth_headers,
    )
    assert r2.status_code == 200
    assert r2.json()["atividades"] == "Atualizado"
    assert r2.json()["efetivo"] == 12


@pytest.mark.asyncio
async def test_delete_entrada(client: AsyncClient, auth_headers: dict, obra):
    r = await client.post(
        f"/obras/{obra.id}/diario",
        json={"data": "2026-04-01", "clima": "nublado", "efetivo": 4, "atividades": "Temp"},
        headers=auth_headers,
    )
    eid = r.json()["id"]
    r2 = await client.delete(f"/obras/{obra.id}/diario/{eid}", headers=auth_headers)
    assert r2.status_code == 204


@pytest.mark.asyncio
async def test_lista_ordenada_desc(client: AsyncClient, auth_headers: dict, obra):
    for d in ["2026-05-01", "2026-05-03", "2026-05-02"]:
        await client.post(
            f"/obras/{obra.id}/diario",
            json={"data": d, "clima": "ensolarado", "efetivo": 1, "atividades": d},
            headers=auth_headers,
        )
    r = await client.get(f"/obras/{obra.id}/diario", headers=auth_headers)
    datas = [e["data"] for e in r.json()]
    assert datas == sorted(datas, reverse=True)


@pytest.mark.asyncio
async def test_tenant_isolation(client: AsyncClient, auth_headers: dict, obra, db_session):
    from app.models.empresa import Empresa
    from app.models.usuario import Usuario
    from app.services.auth_service import hash_password, create_access_token

    empresa_b = Empresa(nome="Empresa B", cnpj="99.999.999/0001-99")
    db_session.add(empresa_b)
    await db_session.flush()
    user_b = Usuario(
        empresa_id=empresa_b.id, nome="B", email="b@b.com",
        senha_hash=hash_password("x"), papel="admin",
    )
    db_session.add(user_b)
    await db_session.flush()
    token_b = create_access_token({"sub": str(user_b.id), "papel": "admin", "empresa_id": empresa_b.id})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    r = await client.get(f"/obras/{obra.id}/diario", headers=headers_b)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_upload_foto(client: AsyncClient, auth_headers: dict, obra):
    r = await client.post(
        f"/obras/{obra.id}/diario",
        json={"data": "2026-06-01", "clima": "ensolarado", "efetivo": 1, "atividades": "Teste foto"},
        headers=auth_headers,
    )
    eid = r.json()["id"]
    import io
    fake_img = io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 100)
    r2 = await client.post(
        f"/obras/{obra.id}/diario/{eid}/fotos",
        files={"file": ("foto.jpg", fake_img, "image/jpeg")},
        headers=auth_headers,
    )
    assert r2.status_code == 201
    assert r2.json()["nome_original"] == "foto.jpg"


@pytest.mark.asyncio
async def test_upload_foto_limite_5(client: AsyncClient, auth_headers: dict, obra):
    r = await client.post(
        f"/obras/{obra.id}/diario",
        json={"data": "2026-06-10", "clima": "nublado", "efetivo": 1, "atividades": "Limite"},
        headers=auth_headers,
    )
    eid = r.json()["id"]
    import io
    for i in range(5):
        fake_img = io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 10)
        await client.post(
            f"/obras/{obra.id}/diario/{eid}/fotos",
            files={"file": (f"foto{i}.jpg", fake_img, "image/jpeg")},
            headers=auth_headers,
        )
    extra = io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 10)
    r2 = await client.post(
        f"/obras/{obra.id}/diario/{eid}/fotos",
        files={"file": ("extra.jpg", extra, "image/jpeg")},
        headers=auth_headers,
    )
    assert r2.status_code == 422


@pytest.mark.asyncio
async def test_delete_foto(client: AsyncClient, auth_headers: dict, obra):
    r = await client.post(
        f"/obras/{obra.id}/diario",
        json={"data": "2026-06-15", "clima": "ensolarado", "efetivo": 1, "atividades": "Del foto"},
        headers=auth_headers,
    )
    eid = r.json()["id"]
    import io
    fake_img = io.BytesIO(b"\xff\xd8\xff" + b"\x00" * 10)
    r2 = await client.post(
        f"/obras/{obra.id}/diario/{eid}/fotos",
        files={"file": ("del.jpg", fake_img, "image/jpeg")},
        headers=auth_headers,
    )
    fid = r2.json()["id"]
    r3 = await client.delete(f"/obras/{obra.id}/diario/{eid}/fotos/{fid}", headers=auth_headers)
    assert r3.status_code == 204
