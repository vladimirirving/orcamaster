# Módulo 9 — Gerador de Proposta para Pregão: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Gerar PDF de proposta para pregão eletrônico a partir de dados persistidos por versão, com formulário no frontend e endpoint de exportação via WeasyPrint.

**Architecture:** Extensão do modelo Empresa com campos de representante legal + nova tabela `proposta_config` por Versão. Router `proposta.py` expõe GET/PUT para CRUD e GET /export para streaming PDF. Serviço `proposta_pdf.py` renderiza template Jinja2 + WeasyPrint e é a interface reutilizável pelo Módulo 10. Frontend adiciona aba "Proposta" em ObraDetailPage e página `/configuracoes` para admins.

**Tech Stack:** FastAPI · SQLAlchemy async · PostgreSQL · Alembic · Jinja2 · WeasyPrint 62.3 (já em pyproject.toml) · React 19 · TypeScript · Tailwind CSS

---

### Task 1: Migração Alembic + dependência Jinja2 + Dockerfile

**Files:**
- Create: `backend/alembic/versions/0003_proposta_config.py`
- Modify: `backend/pyproject.toml`
- Modify: `backend/Dockerfile`

- [ ] **Step 1: Adicionar jinja2 em pyproject.toml**

Em `backend/pyproject.toml`, inserir após a linha `"openpyxl==3.1.5",`:

```toml
    "jinja2>=3.1",
```

- [ ] **Step 2: Atualizar Dockerfile com fontes para WeasyPrint**

Substituir o bloco `apt-get` em `backend/Dockerfile`:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*
```

- [ ] **Step 3: Criar a migration 0003**

Criar `backend/alembic/versions/0003_proposta_config.py`:

```python
"""add proposta_config table and empresa representante fields

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-03
"""
from alembic import op
import sqlalchemy as sa

revision = '0003'
down_revision = '0002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('empresa', sa.Column('representante_nome', sa.String(200), nullable=True))
    op.add_column('empresa', sa.Column('representante_cpf', sa.String(14), nullable=True))
    op.add_column('empresa', sa.Column('declaracoes_padrao', sa.Text(), nullable=True))

    op.create_table(
        'proposta_config',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('versao_id', sa.Integer(),
                  sa.ForeignKey('versao.id', ondelete='CASCADE'), nullable=False),
        sa.Column('validade_dias', sa.Integer(), nullable=False, server_default='60'),
        sa.Column('data_proposta', sa.Date(), nullable=False),
        sa.Column('declaracoes', sa.Text(), nullable=True),
        sa.Column('criado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('atualizado_em', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('versao_id'),
    )


def downgrade() -> None:
    op.drop_table('proposta_config')
    op.drop_column('empresa', 'declaracoes_padrao')
    op.drop_column('empresa', 'representante_cpf')
    op.drop_column('empresa', 'representante_nome')
```

- [ ] **Step 4: Aplicar a migration**

```bash
docker compose exec backend alembic upgrade head
```

Expected: `Running upgrade 0002 -> 0003, add proposta_config table and empresa representante fields`

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/versions/0003_proposta_config.py backend/pyproject.toml backend/Dockerfile
git commit -m "feat: migration 0003 — proposta_config table + empresa representante fields"
```

---

### Task 2: Modelos Python

**Files:**
- Create: `backend/app/models/proposta_config.py`
- Modify: `backend/app/models/empresa.py`
- Modify: `backend/app/models/versao.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Criar app/models/proposta_config.py**

```python
from datetime import date, datetime
from typing import Optional
from sqlalchemy import ForeignKey, Integer, Date, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class PropostaConfig(Base):
    __tablename__ = "proposta_config"
    __table_args__ = (UniqueConstraint("versao_id"),)

    id:            Mapped[int]           = mapped_column(primary_key=True)
    versao_id:     Mapped[int]           = mapped_column(ForeignKey("versao.id", ondelete="CASCADE"))
    validade_dias: Mapped[int]           = mapped_column(Integer, default=60)
    data_proposta: Mapped[date]          = mapped_column(Date)
    declaracoes:   Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criado_em:     Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow,
                                                          onupdate=datetime.utcnow)

    versao: Mapped["Versao"] = relationship(back_populates="proposta_config")
```

- [ ] **Step 2: Estender app/models/empresa.py**

Substituir o conteúdo completo de `backend/app/models/empresa.py`:

```python
from typing import Optional
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Empresa(Base):
    __tablename__ = "empresa"

    id:   Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(200))
    cnpj: Mapped[str] = mapped_column(String(18), unique=True)
    representante_nome: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    representante_cpf:  Mapped[Optional[str]] = mapped_column(String(14),  nullable=True)
    declaracoes_padrao: Mapped[Optional[str]] = mapped_column(Text,         nullable=True)

    usuarios: Mapped[list["Usuario"]] = relationship(back_populates="empresa")
    obras:    Mapped[list["Obra"]]    = relationship(back_populates="empresa")
```

- [ ] **Step 3: Adicionar relacionamento proposta_config em Versao**

Em `backend/app/models/versao.py`, adicionar ao final dos relacionamentos existentes:

```python
    proposta_config: Mapped[Optional["PropostaConfig"]] = relationship(
        back_populates="versao", uselist=False
    )
```

(A tipagem `Optional` já é importada no arquivo; `PropostaConfig` é resolvida via forward reference.)

- [ ] **Step 4: Registrar PropostaConfig em app/models/__init__.py**

Adicionar no final de `backend/app/models/__init__.py`:

```python
from app.models.proposta_config import PropostaConfig  # noqa: F401
```

- [ ] **Step 5: Verificar import**

```bash
docker compose exec backend python -c "from app.models import PropostaConfig; print('OK')"
```

Expected: `OK`

- [ ] **Step 6: Commit**

```bash
git add backend/app/models/proposta_config.py backend/app/models/empresa.py \
        backend/app/models/versao.py backend/app/models/__init__.py
git commit -m "feat: PropostaConfig model + Empresa representante fields"
```

---

### Task 3: Schemas + router de empresa + testes de empresa

**Files:**
- Create: `backend/app/schemas/proposta.py`
- Create: `backend/app/routers/empresa.py`
- Create: `tests/backend/test_proposta.py` (seção empresa)
- Modify: `backend/app/main.py`

- [ ] **Step 1: Escrever os testes de empresa**

Criar `tests/backend/test_proposta.py`:

```python
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
```

- [ ] **Step 2: Confirmar que os testes falham (endpoint não existe)**

```bash
docker compose exec backend pytest tests/backend/test_proposta.py -v
```

Expected: FAIL com "404 Not Found"

- [ ] **Step 3: Criar app/schemas/proposta.py**

```python
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel


class PropostaConfigIn(BaseModel):
    validade_dias: int = 60
    data_proposta: date
    declaracoes: Optional[str] = None


class PropostaConfigOut(PropostaConfigIn):
    id: int
    versao_id: int
    criado_em: datetime
    atualizado_em: datetime
    model_config = {"from_attributes": True}


class EmpresaConfigIn(BaseModel):
    representante_nome: Optional[str] = None
    representante_cpf:  Optional[str] = None
    declaracoes_padrao: Optional[str] = None


class EmpresaConfigOut(EmpresaConfigIn):
    id: int
    nome: str
    cnpj: str
    model_config = {"from_attributes": True}
```

- [ ] **Step 4: Criar app/routers/empresa.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user, require_admin
from app.models.empresa import Empresa
from app.models.usuario import Usuario
from app.schemas.proposta import EmpresaConfigIn, EmpresaConfigOut

router = APIRouter(tags=["empresa"])


@router.get("/empresa", response_model=EmpresaConfigOut)
async def get_empresa(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Empresa).where(Empresa.id == current_user.empresa_id))
    return result.scalar_one()


@router.patch("/empresa", response_model=EmpresaConfigOut)
async def update_empresa(
    body: EmpresaConfigIn,
    admin: Usuario = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Empresa).where(Empresa.id == admin.empresa_id))
    empresa = result.scalar_one()
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(empresa, field, value)
    await db.commit()
    await db.refresh(empresa)
    return empresa
```

- [ ] **Step 5: Registrar empresa.router em app/main.py**

Adicionar o import:
```python
from app.routers import empresa
```
E logo após `app.include_router(curva_abc.router)`:
```python
app.include_router(empresa.router)
```

- [ ] **Step 6: Confirmar que os testes passam**

```bash
docker compose exec backend pytest tests/backend/test_proposta.py -v
```

Expected: 3 PASSED

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/proposta.py backend/app/routers/empresa.py \
        backend/app/main.py tests/backend/test_proposta.py
git commit -m "feat: empresa config endpoint + schemas"
```

---

### Task 4: Router de proposta (GET/PUT) + testes CRUD

**Files:**
- Create: `backend/app/routers/proposta.py`
- Modify: `tests/backend/test_proposta.py` (adicionar testes CRUD)
- Modify: `backend/app/main.py`

- [ ] **Step 1: Adicionar testes CRUD de proposta ao test_proposta.py**

Acrescentar ao final de `tests/backend/test_proposta.py`:

```python
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
```

- [ ] **Step 2: Confirmar que os 5 novos testes falham**

```bash
docker compose exec backend pytest tests/backend/test_proposta.py -k "proposta" -v
```

Expected: 5 FAIL

- [ ] **Step 3: Criar app/routers/proposta.py**

```python
import io
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.empresa import Empresa
from app.models.obra import Obra
from app.models.proposta_config import PropostaConfig
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.schemas.proposta import PropostaConfigIn, PropostaConfigOut

router = APIRouter(tags=["proposta"])


async def _get_versao(versao_id: int, current_user: Usuario, db: AsyncSession) -> Versao:
    result = await db.execute(
        select(Versao)
        .join(Obra, Versao.obra_id == Obra.id)
        .where(Versao.id == versao_id, Obra.empresa_id == current_user.empresa_id)
    )
    versao = result.scalar_one_or_none()
    if versao is None:
        raise HTTPException(status_code=404, detail="Versão não encontrada")
    return versao


@router.get("/versoes/{versao_id}/proposta", response_model=PropostaConfigOut)
async def get_proposta(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao(versao_id, current_user, db)
    result = await db.execute(
        select(PropostaConfig).where(PropostaConfig.versao_id == versao_id)
    )
    pc = result.scalar_one_or_none()
    if pc is None:
        raise HTTPException(status_code=404, detail="Proposta não configurada")
    return pc


@router.put("/versoes/{versao_id}/proposta", response_model=PropostaConfigOut)
async def upsert_proposta(
    versao_id: int,
    body: PropostaConfigIn,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao(versao_id, current_user, db)
    result = await db.execute(
        select(PropostaConfig).where(PropostaConfig.versao_id == versao_id)
    )
    pc = result.scalar_one_or_none()

    if pc is None:
        empresa_result = await db.execute(
            select(Empresa).where(Empresa.id == current_user.empresa_id)
        )
        empresa = empresa_result.scalar_one()
        pc = PropostaConfig(
            versao_id=versao_id,
            validade_dias=body.validade_dias,
            data_proposta=body.data_proposta,
            declaracoes=body.declaracoes if body.declaracoes is not None else empresa.declaracoes_padrao,
        )
        db.add(pc)
    else:
        pc.validade_dias = body.validade_dias
        pc.data_proposta = body.data_proposta
        pc.declaracoes = body.declaracoes

    await db.commit()
    await db.refresh(pc)
    return pc
```

- [ ] **Step 4: Registrar proposta.router em app/main.py**

Adicionar:
```python
from app.routers import proposta
```
E:
```python
app.include_router(proposta.router)
```

- [ ] **Step 5: Confirmar que todos os testes passam**

```bash
docker compose exec backend pytest tests/backend/test_proposta.py -v
```

Expected: 8 PASSED

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/proposta.py backend/app/main.py tests/backend/test_proposta.py
git commit -m "feat: proposta CRUD endpoints — GET/PUT /versoes/{id}/proposta"
```

---

### Task 5: Serviço PDF + template Jinja2 + endpoint export

**Files:**
- Create: `backend/app/templates/proposta.html.j2`
- Create: `backend/app/services/proposta_pdf.py`
- Modify: `backend/app/routers/proposta.py` (adicionar endpoint export)
- Modify: `tests/backend/test_proposta.py` (adicionar testes de export)

- [ ] **Step 1: Adicionar testes de export ao test_proposta.py**

Acrescentar ao final de `tests/backend/test_proposta.py`:

```python
from app.models.grupo import Grupo
from app.models.item import Item
from decimal import Decimal


async def _setup_proposta_dados(
    db: AsyncSession, empresa: Empresa, versao_ativa: Versao
) -> None:
    empresa.representante_nome = "João da Silva"
    empresa.representante_cpf = "123.456.789-00"
    grupo = Grupo(versao_id=versao_ativa.id, nome="Terraplanagem", ordem=0)
    db.add(grupo)
    await db.flush()
    item = Item(
        grupo_id=grupo.id, ordem=0, unidade="m³",
        quantidade=Decimal("100"), preco_unitario_sem_bdi=Decimal("50"),
    )
    db.add(item)
    versao_ativa.total_sem_bdi = Decimal("5000")
    versao_ativa.total_com_bdi = Decimal("5750")
    await db.commit()


@pytest.mark.asyncio
async def test_export_pdf_not_configured(
    client: AsyncClient, auth_headers: dict, versao_ativa: Versao
):
    resp = await client.get(
        f"/versoes/{versao_ativa.id}/proposta/export", headers=auth_headers
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_export_pdf_ok(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, empresa: Empresa, versao_ativa: Versao
):
    await _setup_proposta_dados(db_session, empresa, versao_ativa)

    await client.put(
        f"/versoes/{versao_ativa.id}/proposta",
        headers=auth_headers,
        json={"validade_dias": 60, "data_proposta": "2026-07-01", "declaracoes": "Declaro."},
    )

    resp = await client.get(
        f"/versoes/{versao_ativa.id}/proposta/export", headers=auth_headers
    )
    assert resp.status_code == 200
    assert "application/pdf" in resp.headers["content-type"]
    assert len(resp.content) > 0
```

- [ ] **Step 2: Confirmar que os 2 novos testes falham**

```bash
docker compose exec backend pytest tests/backend/test_proposta.py::test_export_pdf_not_configured tests/backend/test_proposta.py::test_export_pdf_ok -v
```

Expected: FAIL (endpoint não existe)

- [ ] **Step 3: Criar diretório de templates**

```bash
mkdir -p backend/app/templates
```

- [ ] **Step 4: Criar backend/app/templates/proposta.html.j2**

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<style>
  @page { size: A4; margin: 2cm; }
  body { font-family: Liberation Sans, Arial, sans-serif; font-size: 10pt; color: #111; }
  h1 { font-size: 13pt; margin: 0 0 2pt; }
  h2 { font-size: 11pt; margin: 14pt 0 4pt; border-bottom: 1px solid #ccc; padding-bottom: 2pt; }
  .header { text-align: center; margin-bottom: 16pt; }
  .header .cnpj { font-size: 9pt; color: #555; }
  .meta { display: flex; gap: 40pt; margin-bottom: 10pt; }
  .meta div { flex: 1; }
  .label { font-size: 8pt; color: #777; text-transform: uppercase; letter-spacing: 0.5pt; }
  .value { font-size: 10pt; }
  table { width: 100%; border-collapse: collapse; font-size: 9pt; margin-bottom: 10pt; }
  th { background: #f0f0f0; text-align: left; padding: 4pt 6pt; border: 0.5pt solid #bbb; font-weight: bold; }
  td { padding: 3pt 6pt; border: 0.5pt solid #ccc; vertical-align: top; }
  .group-row td { background: #f8f8f8; font-weight: bold; }
  .total-row td { background: #e8e8e8; font-weight: bold; }
  .num { text-align: right; }
  .validity { margin-bottom: 10pt; font-style: italic; }
  .declarations { white-space: pre-wrap; font-size: 9pt; color: #333;
                  border: 0.5pt solid #ddd; padding: 8pt; margin-bottom: 16pt; }
  .signature { margin-top: 30pt; border-top: 0.5pt dotted #888;
               padding-top: 8pt; font-size: 9pt; text-align: center; }
</style>
</head>
<body>

<div class="header">
  <h1>{{ empresa.nome }}</h1>
  <div class="cnpj">CNPJ: {{ empresa.cnpj }}</div>
</div>

<h2>Dados da Proposta</h2>
<div class="meta">
  <div>
    <div class="label">Representante Legal</div>
    <div class="value">{{ empresa.representante_nome or '—' }}</div>
    <div class="value" style="font-size:9pt;color:#555;">
      CPF: {{ empresa.representante_cpf or '—' }}
    </div>
  </div>
  <div>
    <div class="label">Data da Proposta</div>
    <div class="value">{{ proposta.data_proposta.strftime('%d/%m/%Y') }}</div>
  </div>
</div>

<h2>Dados da Obra</h2>
<div class="meta">
  <div>
    <div class="label">Obra</div>
    <div class="value">{{ obra.nome }}</div>
  </div>
  <div>
    <div class="label">Processo</div>
    <div class="value">{{ obra.numero_processo or '—' }}</div>
  </div>
</div>
<div class="meta">
  <div>
    <div class="label">Cliente / Contratante</div>
    <div class="value">{{ obra.cliente or '—' }}</div>
  </div>
  <div>
    <div class="label">Local</div>
    <div class="value">
      {% if obra.municipio %}{{ obra.municipio }}/{{ obra.uf or '' }}{% else %}—{% endif %}
    </div>
  </div>
</div>

<div class="validity">
  Esta proposta é válida por <strong>{{ proposta.validade_dias }} dias</strong>
  a partir de {{ proposta.data_proposta.strftime('%d/%m/%Y') }}.
</div>

<h2>Planilha de Preços</h2>
<table>
  <thead>
    <tr>
      <th style="width:38%">Descrição</th>
      <th style="width:8%">Un</th>
      <th class="num" style="width:12%">Qtd</th>
      <th class="num" style="width:16%">Preço Unit. (R$)</th>
      <th class="num" style="width:16%">Total (R$)</th>
    </tr>
  </thead>
  <tbody>
    {% for grupo in grupos %}
    <tr class="group-row">
      <td colspan="5">{{ grupo.nome }}</td>
    </tr>
    {% for item in grupo.itens %}
    <tr>
      <td>{{ item.composicao.descricao if item.composicao else '—' }}</td>
      <td>{{ item.unidade }}</td>
      <td class="num">{{ '%.2f'|format(item.quantidade|float) }}</td>
      <td class="num">
        {% if item.preco_unitario_sem_bdi %}
          {{ '%,.2f'|format(item.preco_unitario_sem_bdi|float) }}
        {% else %}—{% endif %}
      </td>
      <td class="num">{{ '%,.2f'|format(item.total|float) }}</td>
    </tr>
    {% endfor %}
    {% endfor %}
    <tr class="total-row">
      <td colspan="4" style="text-align:right">Subtotal sem BDI</td>
      <td class="num">{{ '%,.2f'|format(versao.total_sem_bdi|float) }}</td>
    </tr>
    {% if bdi %}
    <tr>
      <td colspan="4" style="text-align:right">
        BDI ({{ '%.2f'|format(bdi.bdi_composto|float * 100) }}%)
      </td>
      <td class="num">
        {{ '%,.2f'|format(versao.total_com_bdi|float - versao.total_sem_bdi|float) }}
      </td>
    </tr>
    {% endif %}
    <tr class="total-row">
      <td colspan="4" style="text-align:right"><strong>TOTAL GERAL</strong></td>
      <td class="num"><strong>{{ '%,.2f'|format(versao.total_com_bdi|float) }}</strong></td>
    </tr>
  </tbody>
</table>

{% if proposta.declaracoes %}
<h2>Declarações</h2>
<div class="declarations">{{ proposta.declaracoes }}</div>
{% endif %}

<div class="signature">
  <p>{{ obra.municipio or '___________' }},
     {{ proposta.data_proposta.strftime('%d de %B de %Y') }}</p>
  <br><br>
  <p>__________________________________________________</p>
  <p><strong>{{ empresa.representante_nome or '______________________________' }}</strong></p>
  {% if empresa.representante_cpf %}<p>CPF: {{ empresa.representante_cpf }}</p>{% endif %}
  <p>Responsável Legal</p>
</div>

</body>
</html>
```

- [ ] **Step 5: Criar backend/app/services/proposta_pdf.py**

```python
from pathlib import Path
from typing import Optional
import jinja2
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from weasyprint import HTML
from app.models.bdi import BDI
from app.models.empresa import Empresa
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.obra import Obra
from app.models.proposta_config import PropostaConfig
from app.models.versao import Versao

_template_dir = Path(__file__).resolve().parent.parent / "templates"
_jinja_env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(str(_template_dir)),
    autoescape=False,
)


async def gerar_pdf_bytes(versao_id: int, db: AsyncSession) -> bytes:
    """Carrega todos os dados e retorna o PDF em bytes. Levanta 404 se PropostaConfig não existe."""
    pc_result = await db.execute(
        select(PropostaConfig).where(PropostaConfig.versao_id == versao_id)
    )
    pc = pc_result.scalar_one_or_none()
    if pc is None:
        raise HTTPException(status_code=404, detail="Proposta não configurada")

    versao_result = await db.execute(
        select(Versao).options(selectinload(Versao.obra)).where(Versao.id == versao_id)
    )
    versao = versao_result.scalar_one()
    obra: Obra = versao.obra

    empresa_result = await db.execute(select(Empresa).where(Empresa.id == obra.empresa_id))
    empresa = empresa_result.scalar_one()

    bdi_result = await db.execute(select(BDI).where(BDI.versao_id == versao_id))
    bdi: Optional[BDI] = bdi_result.scalar_one_or_none()

    grupos_result = await db.execute(
        select(Grupo)
        .where(Grupo.versao_id == versao_id)
        .options(selectinload(Grupo.itens).selectinload(Item.composicao))
        .order_by(Grupo.ordem)
    )
    grupos = grupos_result.scalars().all()

    html_str = _jinja_env.get_template("proposta.html.j2").render(
        empresa=empresa,
        obra=obra,
        versao=versao,
        proposta=pc,
        bdi=bdi,
        grupos=grupos,
    )
    return HTML(string=html_str).write_pdf()
```

- [ ] **Step 6: Adicionar endpoint export ao app/routers/proposta.py**

Adicionar no bloco de imports no topo:
```python
from app.services.proposta_pdf import gerar_pdf_bytes
```

Adicionar o endpoint após `upsert_proposta`:

```python
@router.get("/versoes/{versao_id}/proposta/export")
async def export_proposta(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao(versao_id, current_user, db)
    pdf_bytes = await gerar_pdf_bytes(versao_id, db)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="proposta-v{versao_id}.pdf"'},
    )
```

- [ ] **Step 7: Rodar todos os testes de proposta**

```bash
docker compose exec backend pytest tests/backend/test_proposta.py -v
```

Expected: 10 PASSED

- [ ] **Step 8: Rodar a suíte completa para verificar regressões**

```bash
docker compose exec backend pytest tests/backend/ -v
```

Expected: todos passam

- [ ] **Step 9: Commit**

```bash
git add backend/app/templates/proposta.html.j2 backend/app/services/proposta_pdf.py \
        backend/app/routers/proposta.py tests/backend/test_proposta.py
git commit -m "feat: PDF service + Jinja2 template + export endpoint — backend Módulo 9 completo"
```

---

### Task 6: Frontend — tipos + módulo de API

**Files:**
- Modify: `frontend/src/types.ts`
- Create: `frontend/src/api/proposta.ts`

- [ ] **Step 1: Adicionar tipos em frontend/src/types.ts**

Acrescentar ao final do arquivo:

```ts
export interface PropostaConfig {
  id: number
  versao_id: number
  validade_dias: number
  data_proposta: string   // YYYY-MM-DD
  declaracoes: string | null
  criado_em: string
  atualizado_em: string
}

export interface EmpresaConfig {
  id: number
  nome: string
  cnpj: string
  representante_nome: string | null
  representante_cpf: string | null
  declaracoes_padrao: string | null
}
```

- [ ] **Step 2: Criar frontend/src/api/proposta.ts**

```ts
import { api } from '@/api/client'
import type { PropostaConfig, EmpresaConfig } from '@/types'

export const getPropostaConfig = (versaoId: number): Promise<PropostaConfig> =>
  api.get<PropostaConfig>(`/versoes/${versaoId}/proposta`).then(r => r.data)

export const savePropostaConfig = (
  versaoId: number,
  body: { validade_dias: number; data_proposta: string; declaracoes: string | null }
): Promise<PropostaConfig> =>
  api.put<PropostaConfig>(`/versoes/${versaoId}/proposta`, body).then(r => r.data)

export async function downloadPropostaPdf(versaoId: number): Promise<void> {
  const resp = await api.get<Blob>(`/versoes/${versaoId}/proposta/export`, {
    responseType: 'blob',
  })
  const url = URL.createObjectURL(resp.data)
  const a = document.createElement('a')
  a.href = url
  a.download = `proposta-v${versaoId}.pdf`
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 100)
}

export const getEmpresaConfig = (): Promise<EmpresaConfig> =>
  api.get<EmpresaConfig>('/empresa').then(r => r.data)

export const updateEmpresaConfig = (
  body: Partial<Pick<EmpresaConfig, 'representante_nome' | 'representante_cpf' | 'declaracoes_padrao'>>
): Promise<EmpresaConfig> =>
  api.patch<EmpresaConfig>('/empresa', body).then(r => r.data)
```

- [ ] **Step 3: Confirmar que TypeScript compila**

```bash
cd frontend && npx tsc --noEmit
```

Expected: sem erros

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types.ts frontend/src/api/proposta.ts
git commit -m "feat: proposta types and API module"
```

---

### Task 7: PropostaTab + ObraDetailPage

**Files:**
- Create: `frontend/src/components/obra/PropostaTab.tsx`
- Modify: `frontend/src/pages/ObraDetailPage.tsx`

- [ ] **Step 1: Criar frontend/src/components/obra/PropostaTab.tsx**

```tsx
import { useState, useEffect } from 'react'
import { getPropostaConfig, savePropostaConfig, downloadPropostaPdf } from '@/api/proposta'
import { toast } from '@/hooks/useToast'
import type { PropostaConfig } from '@/types'

interface Props {
  versaoId: number
}

const TODAY = new Date().toISOString().slice(0, 10)

export default function PropostaTab({ versaoId }: Props) {
  const [config, setConfig] = useState<PropostaConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [dirty, setDirty] = useState(false)

  const [validade, setValidade] = useState(60)
  const [dataProposta, setDataProposta] = useState(TODAY)
  const [declaracoes, setDeclaracoes] = useState('')

  useEffect(() => {
    setLoading(true)
    getPropostaConfig(versaoId)
      .then(pc => {
        setConfig(pc)
        setValidade(pc.validade_dias)
        setDataProposta(pc.data_proposta)
        setDeclaracoes(pc.declaracoes ?? '')
      })
      .catch(e => {
        if (e?.response?.status !== 404) {
          toast('Erro ao carregar proposta', 'error')
        }
      })
      .finally(() => setLoading(false))
  }, [versaoId])

  async function handleSave() {
    setSaving(true)
    try {
      const pc = await savePropostaConfig(versaoId, {
        validade_dias: validade,
        data_proposta: dataProposta,
        declaracoes: declaracoes || null,
      })
      setConfig(pc)
      setDirty(false)
      toast('Proposta salva')
    } catch {
      toast('Erro ao salvar proposta', 'error')
    } finally {
      setSaving(false)
    }
  }

  async function handleExport() {
    if (config === null) {
      toast('Salve a proposta antes de gerar o PDF', 'error')
      return
    }
    setExporting(true)
    try {
      await downloadPropostaPdf(versaoId)
    } catch {
      toast('Erro ao gerar PDF', 'error')
    } finally {
      setExporting(false)
    }
  }

  if (loading) return <div className="p-6 text-gray-400 text-sm">Carregando...</div>

  return (
    <div className="p-6 max-w-2xl space-y-5">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Validade da proposta
          </label>
          <select
            value={validade}
            onChange={e => { setValidade(Number(e.target.value)); setDirty(true) }}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={30}>30 dias</option>
            <option value={60}>60 dias</option>
            <option value={90}>90 dias</option>
            <option value={180}>180 dias</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Data da proposta
          </label>
          <input
            type="date"
            value={dataProposta}
            onChange={e => { setDataProposta(e.target.value); setDirty(true) }}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">Declarações</label>
        <textarea
          rows={8}
          value={declaracoes}
          onChange={e => { setDeclaracoes(e.target.value); setDirty(true) }}
          placeholder="Texto das declarações que aparecerá no documento..."
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
        />
      </div>

      <div className="flex gap-3">
        <button
          onClick={handleSave}
          disabled={!dirty || saving}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
        >
          {saving ? 'Salvando...' : 'Salvar'}
        </button>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-40"
        >
          {exporting ? 'Gerando...' : 'Baixar PDF'}
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Atualizar ObraDetailPage.tsx**

**2a.** Adicionar import:
```ts
import PropostaTab from '@/components/obra/PropostaTab'
```

**2b.** Alterar o tipo do estado `tab` (linha 20):
```ts
const [tab, setTab] = useState<'versoes' | 'dashboard' | 'curva-abc' | 'proposta'>('versoes')
```

**2c.** Atualizar o array de tabs (linha 100):
```tsx
{(['versoes', 'dashboard', 'curva-abc', 'proposta'] as const).map(t => (
```

**2d.** Atualizar o mapeamento de labels (linha 110):
```tsx
{t === 'versoes' ? 'Versões' : t === 'dashboard' ? 'Dashboard' : t === 'curva-abc' ? 'Curva ABC' : 'Proposta'}
```

**2e.** Adicionar o painel após o bloco `{tab === 'curva-abc' && ...}`:
```tsx
{tab === 'proposta' && (
  versaoAtiva
    ? <PropostaTab versaoId={versaoAtiva.id} />
    : <div className="p-6 text-center text-gray-400 text-sm py-12">Nenhuma versão ativa para esta obra</div>
)}
```

- [ ] **Step 3: Confirmar que TypeScript compila**

```bash
cd frontend && npx tsc --noEmit
```

Expected: sem erros

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/obra/PropostaTab.tsx frontend/src/pages/ObraDetailPage.tsx
git commit -m "feat: PropostaTab component + aba Proposta em ObraDetailPage"
```

---

### Task 8: EmpresaSettingsPage + routing + TopBar

**Files:**
- Create: `frontend/src/pages/EmpresaSettingsPage.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/components/layout/TopBar.tsx`

- [ ] **Step 1: Criar frontend/src/pages/EmpresaSettingsPage.tsx**

```tsx
import { useState, useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { getEmpresaConfig, updateEmpresaConfig } from '@/api/proposta'
import { toast } from '@/hooks/useToast'
import type { EmpresaConfig } from '@/types'

export default function EmpresaSettingsPage() {
  const { papel } = useAuth()
  if (papel !== 'admin') return <Navigate to="/obras" replace />

  const [empresa, setEmpresa] = useState<EmpresaConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [representanteNome, setRepresentanteNome] = useState('')
  const [representanteCpf, setRepresentanteCpf] = useState('')
  const [declaracoesPadrao, setDeclaracoesPadrao] = useState('')

  useEffect(() => {
    getEmpresaConfig()
      .then(e => {
        setEmpresa(e)
        setRepresentanteNome(e.representante_nome ?? '')
        setRepresentanteCpf(e.representante_cpf ?? '')
        setDeclaracoesPadrao(e.declaracoes_padrao ?? '')
      })
      .catch(() => toast('Erro ao carregar configurações', 'error'))
      .finally(() => setLoading(false))
  }, [])

  async function handleSave() {
    setSaving(true)
    try {
      const updated = await updateEmpresaConfig({
        representante_nome: representanteNome || null,
        representante_cpf: representanteCpf || null,
        declaracoes_padrao: declaracoesPadrao || null,
      })
      setEmpresa(updated)
      toast('Configurações salvas')
    } catch {
      toast('Erro ao salvar', 'error')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="p-6 text-gray-400">Carregando...</div>

  return (
    <div className="p-6 max-w-xl mx-auto">
      <h1 className="text-xl font-bold text-gray-900 mb-1">Configurações da Empresa</h1>
      {empresa && (
        <p className="text-sm text-gray-500 mb-6">
          {empresa.nome} · CNPJ: {empresa.cnpj}
        </p>
      )}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Representante Legal
          </label>
          <input
            type="text"
            value={representanteNome}
            onChange={e => setRepresentanteNome(e.target.value)}
            placeholder="Nome completo"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            CPF do Representante
          </label>
          <input
            type="text"
            value={representanteCpf}
            onChange={e => setRepresentanteCpf(e.target.value)}
            placeholder="000.000.000-00"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Declarações Padrão
          </label>
          <textarea
            rows={6}
            value={declaracoesPadrao}
            onChange={e => setDeclaracoesPadrao(e.target.value)}
            placeholder="Texto pré-preenchido em novas propostas..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
          />
        </div>
        <button
          onClick={handleSave}
          disabled={saving}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
        >
          {saving ? 'Salvando...' : 'Salvar'}
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Adicionar rota /configuracoes em App.tsx**

Adicionar o import:
```ts
import EmpresaSettingsPage from '@/pages/EmpresaSettingsPage'
```

Dentro do `<Routes>` interno (dentro de `AppLayout`), adicionar:
```tsx
<Route path="/configuracoes" element={<EmpresaSettingsPage />} />
```

- [ ] **Step 3: Adicionar link "Configurações" na TopBar**

Em `frontend/src/components/layout/TopBar.tsx`, dentro do `<div className="ml-auto ...">`,
adicionar antes do `<span className="text-gray-400 capitalize">`:

```tsx
        {papel === 'admin' && (
          <Link to="/configuracoes" className="text-gray-400 hover:text-white transition-colors">
            Configurações
          </Link>
        )}
```

- [ ] **Step 4: Confirmar que TypeScript compila**

```bash
cd frontend && npx tsc --noEmit
```

Expected: sem erros

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/EmpresaSettingsPage.tsx frontend/src/App.tsx \
        frontend/src/components/layout/TopBar.tsx
git commit -m "feat: EmpresaSettingsPage + /configuracoes route + TopBar admin link — Módulo 9 completo"
```
