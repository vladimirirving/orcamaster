import io
import pytest
from decimal import Decimal
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.contrato import Contrato, Aditivo


@pytest.mark.asyncio
async def test_list_contratos_vazio(client: AsyncClient, auth_headers: dict, obra):
    resp = await client.get(f"/obras/{obra.id}/contratos", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_create_contrato(client: AsyncClient, auth_headers: dict, obra):
    resp = await client.post(
        f"/obras/{obra.id}/contratos",
        json={"objeto": "Execução de pavimentação", "valor_original": "500000.00"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["objeto"] == "Execução de pavimentação"
    assert Decimal(data["valor_original"]) == Decimal("500000.00")
    assert Decimal(data["valor_atual"]) == Decimal("500000.00")
    assert data["data_fim_atual"] is None
    assert data["aditivos"] == []


@pytest.mark.asyncio
async def test_create_contrato_campos_opcionais(client: AsyncClient, auth_headers: dict, obra):
    resp = await client.post(
        f"/obras/{obra.id}/contratos",
        json={
            "objeto": "Reforma de ponte",
            "valor_original": "200000.00",
            "numero": "CT-2024-001",
            "data_assinatura": "2024-01-15",
            "data_fim": "2024-12-31",
            "contratante_nome": "DNIT",
            "contratado_nome": "Construtora ABC Ltda",
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["numero"] == "CT-2024-001"
    assert data["data_assinatura"] == "2024-01-15"
    assert data["data_fim"] == "2024-12-31"
    assert data["data_fim_atual"] == "2024-12-31"


@pytest.mark.asyncio
async def test_update_contrato(client: AsyncClient, auth_headers: dict, obra):
    create = await client.post(
        f"/obras/{obra.id}/contratos",
        json={"objeto": "Saneamento básico", "valor_original": "300000.00"},
        headers=auth_headers,
    )
    cid = create.json()["id"]
    resp = await client.patch(
        f"/contratos/{cid}",
        json={"numero": "CT-2024-002", "contratante_cnpj": "00.000.000/0001-00"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["numero"] == "CT-2024-002"


@pytest.mark.asyncio
async def test_delete_contrato(client: AsyncClient, auth_headers: dict, obra):
    create = await client.post(
        f"/obras/{obra.id}/contratos",
        json={"objeto": "Rede elétrica", "valor_original": "150000.00"},
        headers=auth_headers,
    )
    cid = create.json()["id"]
    resp = await client.delete(f"/contratos/{cid}", headers=auth_headers)
    assert resp.status_code == 204
    lista = await client.get(f"/obras/{obra.id}/contratos", headers=auth_headers)
    assert lista.json() == []


@pytest.mark.asyncio
async def test_contrato_404(client: AsyncClient, auth_headers: dict):
    resp = await client.get("/contratos/99999/download", headers=auth_headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_create_aditivo_valor(client: AsyncClient, auth_headers: dict, obra):
    create = await client.post(
        f"/obras/{obra.id}/contratos",
        json={"objeto": "Obras diversas", "valor_original": "100000.00"},
        headers=auth_headers,
    )
    cid = create.json()["id"]
    resp = await client.post(
        f"/contratos/{cid}/aditivos",
        json={"tipo": "valor", "delta_valor": "20000.00", "justificativa": "Serviço adicional"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["tipo"] == "valor"
    assert Decimal(resp.json()["delta_valor"]) == Decimal("20000.00")


@pytest.mark.asyncio
async def test_valor_atual_soma_aditivos(client: AsyncClient, auth_headers: dict, obra):
    create = await client.post(
        f"/obras/{obra.id}/contratos",
        json={"objeto": "Pavimentação", "valor_original": "100000.00"},
        headers=auth_headers,
    )
    cid = create.json()["id"]
    await client.post(f"/contratos/{cid}/aditivos",
        json={"tipo": "valor", "delta_valor": "20000.00"}, headers=auth_headers)
    await client.post(f"/contratos/{cid}/aditivos",
        json={"tipo": "valor", "delta_valor": "-5000.00"}, headers=auth_headers)
    lista = await client.get(f"/obras/{obra.id}/contratos", headers=auth_headers)
    c = lista.json()[0]
    assert Decimal(c["valor_atual"]) == Decimal("115000.00")


@pytest.mark.asyncio
async def test_data_fim_atual_usa_aditivo_mais_recente(client: AsyncClient, auth_headers: dict, obra):
    create = await client.post(
        f"/obras/{obra.id}/contratos",
        json={"objeto": "Dragagem", "valor_original": "80000.00", "data_fim": "2024-06-30"},
        headers=auth_headers,
    )
    cid = create.json()["id"]
    await client.post(f"/contratos/{cid}/aditivos",
        json={"tipo": "prazo", "nova_data_fim": "2024-09-30"}, headers=auth_headers)
    await client.post(f"/contratos/{cid}/aditivos",
        json={"tipo": "prazo", "nova_data_fim": "2024-12-31"}, headers=auth_headers)
    lista = await client.get(f"/obras/{obra.id}/contratos", headers=auth_headers)
    assert lista.json()[0]["data_fim_atual"] == "2024-12-31"


@pytest.mark.asyncio
async def test_aditivo_valor_prazo(client: AsyncClient, auth_headers: dict, obra):
    create = await client.post(
        f"/obras/{obra.id}/contratos",
        json={"objeto": "Aterro", "valor_original": "60000.00", "data_fim": "2024-03-31"},
        headers=auth_headers,
    )
    cid = create.json()["id"]
    resp = await client.post(
        f"/contratos/{cid}/aditivos",
        json={"tipo": "valor_prazo", "delta_valor": "10000.00", "nova_data_fim": "2024-06-30"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    lista = await client.get(f"/obras/{obra.id}/contratos", headers=auth_headers)
    c = lista.json()[0]
    assert Decimal(c["valor_atual"]) == Decimal("70000.00")
    assert c["data_fim_atual"] == "2024-06-30"


@pytest.mark.asyncio
async def test_update_aditivo(client: AsyncClient, auth_headers: dict, obra):
    create = await client.post(
        f"/obras/{obra.id}/contratos",
        json={"objeto": "Galeria", "valor_original": "40000.00"},
        headers=auth_headers,
    )
    cid = create.json()["id"]
    ad = await client.post(f"/contratos/{cid}/aditivos",
        json={"tipo": "valor", "delta_valor": "5000.00"}, headers=auth_headers)
    aid = ad.json()["id"]
    resp = await client.patch(f"/aditivos/{aid}",
        json={"numero": "1º Aditivo"}, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["numero"] == "1º Aditivo"


@pytest.mark.asyncio
async def test_delete_aditivo(client: AsyncClient, auth_headers: dict, obra):
    create = await client.post(
        f"/obras/{obra.id}/contratos",
        json={"objeto": "Bueiro", "valor_original": "25000.00"},
        headers=auth_headers,
    )
    cid = create.json()["id"]
    ad = await client.post(f"/contratos/{cid}/aditivos",
        json={"tipo": "valor", "delta_valor": "3000.00"}, headers=auth_headers)
    aid = ad.json()["id"]
    del_resp = await client.delete(f"/aditivos/{aid}", headers=auth_headers)
    assert del_resp.status_code == 204
    lista = await client.get(f"/obras/{obra.id}/contratos", headers=auth_headers)
    assert lista.json()[0]["aditivos"] == []


@pytest.mark.asyncio
async def test_upload_pdf_contrato(client: AsyncClient, auth_headers: dict, obra, tmp_path):
    create = await client.post(
        f"/obras/{obra.id}/contratos",
        json={"objeto": "Terraplanagem", "valor_original": "90000.00"},
        headers=auth_headers,
    )
    cid = create.json()["id"]
    pdf_bytes = b"%PDF-1.4 fake pdf content"
    resp = await client.post(
        f"/contratos/{cid}/upload",
        files={"file": ("contrato.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["arquivo_path"] is not None


@pytest.mark.asyncio
async def test_upload_pdf_tipo_invalido(client: AsyncClient, auth_headers: dict, obra):
    create = await client.post(
        f"/obras/{obra.id}/contratos",
        json={"objeto": "Obras gerais", "valor_original": "10000.00"},
        headers=auth_headers,
    )
    cid = create.json()["id"]
    resp = await client.post(
        f"/contratos/{cid}/upload",
        files={"file": ("doc.docx", io.BytesIO(b"fake"), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
        headers=auth_headers,
    )
    assert resp.status_code == 422
