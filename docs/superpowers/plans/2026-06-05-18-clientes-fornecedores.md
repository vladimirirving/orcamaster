# Módulo 18 — Clientes & Fornecedores: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar cadastro de Clientes e Fornecedores com páginas de detalhe, vínculo de cliente em Obra, e dropdown "Cadastros ▾" na TopBar com ícones SVG.

**Architecture:** Dois novos models SQLAlchemy (`Cliente`, `Fornecedor`) + migration 0005. `Obra` ganha coluna `cliente_id` FK opcional que coexiste com o campo `cliente` (texto livre legado — não remover). CRUD REST padrão. Frontend: 4 novas páginas, 2 modais, TopBar redesenhada com dropdown, card de cliente em ObraDetailPage, select de cliente em ObrasPage.

**Tech Stack:** FastAPI + SQLAlchemy async + PostgreSQL + Pydantic v2. React + TypeScript + Tailwind. Testes via pytest-asyncio + httpx AsyncClient.

---

## File Map

### Backend — novos
| Arquivo | Responsabilidade |
|---|---|
| `backend/app/models/cliente.py` | Model `Cliente` |
| `backend/app/models/fornecedor.py` | Model `Fornecedor` |
| `backend/app/schemas/cliente.py` | `ClienteCreate`, `ClienteUpdate`, `ClienteOut` |
| `backend/app/schemas/fornecedor.py` | `FornecedorCreate`, `FornecedorUpdate`, `FornecedorOut` |
| `backend/app/routers/clientes.py` | CRUD + `/clientes/{id}/obras` |
| `backend/app/routers/fornecedores.py` | CRUD |
| `backend/alembic/versions/0005_clientes_fornecedores.py` | Migration |
| `tests/backend/test_clientes.py` | Testes CRUD de clientes |
| `tests/backend/test_fornecedores.py` | Testes CRUD de fornecedores |

### Backend — modificados
| Arquivo | Alteração |
|---|---|
| `backend/app/models/obra.py` | Adicionar `cliente_id` FK + relationship |
| `backend/app/schemas/obra.py` | Incluir `cliente_id` em `ObraCreate`, `ObraUpdate`, `ObraOut` |
| `backend/app/routers/obras.py` | Passar `cliente_id` no create/update |
| `backend/app/main.py` | Registrar novos routers |
| `backend/app/models/__init__.py` | Importar `Cliente`, `Fornecedor` |

### Frontend — novos
| Arquivo | Responsabilidade |
|---|---|
| `frontend/src/api/clientes.ts` | `listClientes`, `getCliente`, `createCliente`, `updateCliente`, `deleteCliente`, `getClienteObras` |
| `frontend/src/api/fornecedores.ts` | `listFornecedores`, `getFornecedor`, `createFornecedor`, `updateFornecedor`, `deleteFornecedor` |
| `frontend/src/pages/ClientesPage.tsx` | Lista `/clientes` |
| `frontend/src/pages/ClienteDetailPage.tsx` | Detalhe `/clientes/:id` com abas |
| `frontend/src/pages/FornecedoresPage.tsx` | Lista `/fornecedores` |
| `frontend/src/pages/FornecedorDetailPage.tsx` | Detalhe `/fornecedores/:id` com abas |
| `frontend/src/components/clientes/ClienteModal.tsx` | Modal criar/editar |
| `frontend/src/components/fornecedores/FornecedorModal.tsx` | Modal criar/editar |

### Frontend — modificados
| Arquivo | Alteração |
|---|---|
| `frontend/src/types.ts` | Adicionar `Cliente`, `Fornecedor`, atualizar `Obra` |
| `frontend/src/components/layout/TopBar.tsx` | Dropdown "Cadastros ▾" com SVG icons |
| `frontend/src/App.tsx` | 4 novas rotas + proxy bypass |
| `frontend/vite.config.ts` | Proxy bypass para `/clientes`, `/fornecedores` |
| `frontend/src/pages/ObraDetailPage.tsx` | Card de cliente no header |
| `frontend/src/pages/ObrasPage.tsx` | Select de cliente no modal "Nova Obra" |

---

## Task 1: Migration + Models

**Files:**
- Create: `backend/alembic/versions/0005_clientes_fornecedores.py`
- Create: `backend/app/models/cliente.py`
- Create: `backend/app/models/fornecedor.py`
- Modify: `backend/app/models/obra.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Criar model Cliente**

```python
# backend/app/models/cliente.py
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Cliente(Base):
    __tablename__ = "cliente"

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"))
    tipo: Mapped[str] = mapped_column(String(2))  # 'pf' | 'pj'
    nome: Mapped[str] = mapped_column(String(200))
    cpf_cnpj: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    telefone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    endereco: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    cidade: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    estado: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    obras: Mapped[list["Obra"]] = relationship(back_populates="cliente_obj")
```

- [ ] **Step 2: Criar model Fornecedor**

```python
# backend/app/models/fornecedor.py
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base


class Fornecedor(Base):
    __tablename__ = "fornecedor"

    id: Mapped[int] = mapped_column(primary_key=True)
    empresa_id: Mapped[int] = mapped_column(ForeignKey("empresa.id"))
    nome: Mapped[str] = mapped_column(String(200))
    cnpj: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    telefone: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    endereco: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    cidade: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    estado: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    categorias: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    observacoes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
```

- [ ] **Step 3: Adicionar `cliente_id` ao model Obra**

No arquivo `backend/app/models/obra.py`, adicionar após a linha `responsavel_id`:

```python
    cliente_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("cliente.id", ondelete="SET NULL"), nullable=True
    )
    cliente_obj: Mapped[Optional["Cliente"]] = relationship(back_populates="obras")
```

⚠️ O campo `cliente: Mapped[Optional[str]]` existente (linha 15) é texto livre legado — **não remover**.

- [ ] **Step 4: Registrar novos models em `__init__.py`**

Abrir `backend/app/models/__init__.py` e adicionar:
```python
from app.models.cliente import Cliente
from app.models.fornecedor import Fornecedor
```

- [ ] **Step 5: Criar migration 0005**

```python
# backend/alembic/versions/0005_clientes_fornecedores.py
"""add cliente and fornecedor tables, obra.cliente_id FK

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-05
"""
from alembic import op
import sqlalchemy as sa

revision = '0005'
down_revision = '0004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'cliente',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresa.id'), nullable=False),
        sa.Column('tipo', sa.String(2), nullable=False),
        sa.Column('nome', sa.String(200), nullable=False),
        sa.Column('cpf_cnpj', sa.String(20), nullable=True),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('telefone', sa.String(30), nullable=True),
        sa.Column('endereco', sa.String(300), nullable=True),
        sa.Column('cidade', sa.String(100), nullable=True),
        sa.Column('estado', sa.String(2), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_cliente_empresa_id', 'cliente', ['empresa_id'])
    op.execute(
        "CREATE UNIQUE INDEX uq_cliente_empresa_cpfcnpj "
        "ON cliente(empresa_id, cpf_cnpj) WHERE cpf_cnpj IS NOT NULL"
    )

    op.create_table(
        'fornecedor',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('empresa_id', sa.Integer(), sa.ForeignKey('empresa.id'), nullable=False),
        sa.Column('nome', sa.String(200), nullable=False),
        sa.Column('cnpj', sa.String(20), nullable=True),
        sa.Column('email', sa.String(200), nullable=True),
        sa.Column('telefone', sa.String(30), nullable=True),
        sa.Column('endereco', sa.String(300), nullable=True),
        sa.Column('cidade', sa.String(100), nullable=True),
        sa.Column('estado', sa.String(2), nullable=True),
        sa.Column('categorias', sa.String(100), nullable=True),
        sa.Column('observacoes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_fornecedor_empresa_id', 'fornecedor', ['empresa_id'])
    op.execute(
        "CREATE UNIQUE INDEX uq_fornecedor_empresa_cnpj "
        "ON fornecedor(empresa_id, cnpj) WHERE cnpj IS NOT NULL"
    )

    op.add_column('obra', sa.Column(
        'cliente_id', sa.Integer(),
        sa.ForeignKey('cliente.id', ondelete='SET NULL'),
        nullable=True,
    ))


def downgrade() -> None:
    op.drop_column('obra', 'cliente_id')
    op.drop_table('fornecedor')
    op.drop_table('cliente')
```

- [ ] **Step 6: Rodar a migration**

```bash
docker exec -w /app -e PYTHONPATH=/app orcaavml-backend-1 alembic upgrade head
```

Esperado: `Running upgrade 0004 -> 0005, add cliente and fornecedor tables, obra.cliente_id FK`

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/cliente.py backend/app/models/fornecedor.py \
        backend/app/models/obra.py backend/app/models/__init__.py \
        backend/alembic/versions/0005_clientes_fornecedores.py
git commit -m "feat: models Cliente, Fornecedor + migration 0005 + obra.cliente_id"
```

---

## Task 2: Backend Schemas

**Files:**
- Create: `backend/app/schemas/cliente.py`
- Create: `backend/app/schemas/fornecedor.py`
- Modify: `backend/app/schemas/obra.py`

- [ ] **Step 1: Criar schemas de Cliente**

```python
# backend/app/schemas/cliente.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ClienteCreate(BaseModel):
    tipo: str  # 'pf' | 'pj'
    nome: str
    cpf_cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    observacoes: Optional[str] = None


class ClienteUpdate(BaseModel):
    tipo: Optional[str] = None
    nome: Optional[str] = None
    cpf_cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    observacoes: Optional[str] = None


class ClienteOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    empresa_id: int
    tipo: str
    nome: str
    cpf_cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    observacoes: Optional[str] = None
    created_at: datetime
```

- [ ] **Step 2: Criar schemas de Fornecedor**

```python
# backend/app/schemas/fornecedor.py
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FornecedorCreate(BaseModel):
    nome: str
    cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    categorias: Optional[str] = None  # CSV: 'material,mao_obra,equipamento,servico'
    observacoes: Optional[str] = None


class FornecedorUpdate(BaseModel):
    nome: Optional[str] = None
    cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    categorias: Optional[str] = None
    observacoes: Optional[str] = None


class FornecedorOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    empresa_id: int
    nome: str
    cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    categorias: Optional[str] = None
    observacoes: Optional[str] = None
    created_at: datetime
```

- [ ] **Step 3: Atualizar schemas de Obra** — adicionar `cliente_id` e `cliente_nome` em `ObraCreate`, `ObraUpdate`, `ObraOut`

Em `backend/app/schemas/obra.py`, adicionar nas três classes. `cliente_nome` é read-only (só em `ObraOut`) e permite exibir o nome do cliente vinculado sem um segundo request:

```python
class ObraCreate(BaseModel):
    nome: str
    numero_processo: Optional[str] = None
    cliente: Optional[str] = None
    cliente_id: Optional[int] = None   # ← novo
    uf: Optional[str] = None
    municipio: Optional[str] = None
    tipo_obra: str
    responsavel_id: Optional[int] = None
    data_prazo: Optional[date] = None


class ObraUpdate(BaseModel):
    nome: Optional[str] = None
    numero_processo: Optional[str] = None
    cliente: Optional[str] = None
    cliente_id: Optional[int] = None   # ← novo
    uf: Optional[str] = None
    municipio: Optional[str] = None
    tipo_obra: Optional[str] = None
    estado: Optional[str] = None
    responsavel_id: Optional[int] = None
    data_prazo: Optional[date] = None


class ObraOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    empresa_id: int
    nome: str
    numero_processo: Optional[str] = None
    cliente: Optional[str] = None
    cliente_id: Optional[int] = None      # ← novo
    cliente_nome: Optional[str] = None    # ← novo (read-only, carregado no router)
    uf: Optional[str] = None
    municipio: Optional[str] = None
    tipo_obra: str
    estado: str
    responsavel_id: Optional[int] = None
    data_criacao: date
    data_prazo: Optional[date] = None
```

- [ ] **Step 4: Commit**

```bash
git add backend/app/schemas/cliente.py backend/app/schemas/fornecedor.py \
        backend/app/schemas/obra.py
git commit -m "feat: schemas ClienteCreate/Out, FornecedorCreate/Out, obra.cliente_id"
```

---

## Task 3: Router de Clientes + Testes

**Files:**
- Create: `backend/app/routers/clientes.py`
- Create: `tests/backend/test_clientes.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Escrever testes primeiro**

```python
# tests/backend/test_clientes.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_clientes_vazio(client: AsyncClient, auth_headers: dict):
    r = await client.get("/clientes", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_create_cliente(client: AsyncClient, auth_headers: dict):
    payload = {"tipo": "pj", "nome": "Construtora ABC", "cpf_cnpj": "12.345.678/0001-99"}
    r = await client.post("/clientes", json=payload, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["nome"] == "Construtora ABC"
    assert data["tipo"] == "pj"
    assert data["id"] > 0


@pytest.mark.asyncio
async def test_create_cliente_cpfcnpj_duplicado(client: AsyncClient, auth_headers: dict):
    payload = {"tipo": "pj", "nome": "ABC", "cpf_cnpj": "11.111.111/0001-11"}
    await client.post("/clientes", json=payload, headers=auth_headers)
    r = await client.post("/clientes", json=payload, headers=auth_headers)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_get_cliente(client: AsyncClient, auth_headers: dict):
    r = await client.post("/clientes", json={"tipo": "pf", "nome": "João Silva"}, headers=auth_headers)
    cid = r.json()["id"]
    r2 = await client.get(f"/clientes/{cid}", headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["nome"] == "João Silva"


@pytest.mark.asyncio
async def test_update_cliente(client: AsyncClient, auth_headers: dict):
    r = await client.post("/clientes", json={"tipo": "pf", "nome": "Antigo"}, headers=auth_headers)
    cid = r.json()["id"]
    r2 = await client.patch(f"/clientes/{cid}", json={"nome": "Novo Nome"}, headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["nome"] == "Novo Nome"


@pytest.mark.asyncio
async def test_delete_cliente(client: AsyncClient, auth_headers: dict):
    r = await client.post("/clientes", json={"tipo": "pf", "nome": "Temporário"}, headers=auth_headers)
    cid = r.json()["id"]
    r2 = await client.delete(f"/clientes/{cid}", headers=auth_headers)
    assert r2.status_code == 204


@pytest.mark.asyncio
async def test_busca_por_nome(client: AsyncClient, auth_headers: dict):
    await client.post("/clientes", json={"tipo": "pj", "nome": "Empresa Alpha"}, headers=auth_headers)
    await client.post("/clientes", json={"tipo": "pj", "nome": "Empresa Beta"}, headers=auth_headers)
    r = await client.get("/clientes?q=alpha", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["nome"] == "Empresa Alpha"
```

- [ ] **Step 2: Rodar testes — devem falhar**

```bash
docker exec -w /app -e PYTHONPATH=/app orcaavml-backend-1 \
  python -m pytest tests/backend/test_clientes.py -v 2>&1 | tail -20
```

Esperado: erros de import / 404 (router não existe ainda).

- [ ] **Step 3: Criar router de Clientes**

```python
# backend/app/routers/clientes.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.cliente import Cliente
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.schemas.cliente import ClienteCreate, ClienteOut, ClienteUpdate
from app.schemas.obra import ObraOut

router = APIRouter(prefix="/clientes", tags=["clientes"])


async def _get_cliente(cliente_id: int, current_user: Usuario, db: AsyncSession) -> Cliente:
    result = await db.execute(
        select(Cliente).where(
            Cliente.id == cliente_id,
            Cliente.empresa_id == current_user.empresa_id,
        )
    )
    c = result.scalar_one_or_none()
    if c is None:
        raise HTTPException(status_code=404, detail="Cliente não encontrado")
    return c


@router.get("", response_model=List[ClienteOut])
async def list_clientes(
    q: Optional[str] = Query(None),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Cliente).where(Cliente.empresa_id == current_user.empresa_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(Cliente.nome.ilike(like), Cliente.cpf_cnpj.ilike(like))
        )
    stmt = stmt.order_by(Cliente.nome)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=ClienteOut, status_code=status.HTTP_201_CREATED)
async def create_cliente(
    body: ClienteCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.cpf_cnpj:
        dup = await db.execute(
            select(Cliente).where(
                Cliente.empresa_id == current_user.empresa_id,
                Cliente.cpf_cnpj == body.cpf_cnpj,
            )
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="CPF/CNPJ já cadastrado")
    c = Cliente(empresa_id=current_user.empresa_id, **body.model_dump())
    db.add(c)
    await db.commit()
    await db.refresh(c)
    return c


@router.get("/{cliente_id}", response_model=ClienteOut)
async def get_cliente(
    cliente_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_cliente(cliente_id, current_user, db)


@router.patch("/{cliente_id}", response_model=ClienteOut)
async def update_cliente(
    cliente_id: int,
    body: ClienteUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c = await _get_cliente(cliente_id, current_user, db)
    if body.cpf_cnpj and body.cpf_cnpj != c.cpf_cnpj:
        dup = await db.execute(
            select(Cliente).where(
                Cliente.empresa_id == current_user.empresa_id,
                Cliente.cpf_cnpj == body.cpf_cnpj,
            )
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="CPF/CNPJ já cadastrado")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(c, field, value)
    await db.commit()
    await db.refresh(c)
    return c


@router.delete("/{cliente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cliente(
    cliente_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    c = await _get_cliente(cliente_id, current_user, db)
    count_result = await db.execute(
        select(func.count()).select_from(Obra).where(Obra.cliente_id == cliente_id)
    )
    if count_result.scalar() > 0:
        raise HTTPException(
            status_code=409,
            detail="Cliente possui obras vinculadas e não pode ser excluído",
        )
    await db.delete(c)
    await db.commit()


@router.get("/{cliente_id}/obras", response_model=List[ObraOut])
async def get_cliente_obras(
    cliente_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_cliente(cliente_id, current_user, db)
    result = await db.execute(
        select(Obra).where(
            Obra.cliente_id == cliente_id,
            Obra.empresa_id == current_user.empresa_id,
        ).order_by(Obra.data_criacao.desc())
    )
    return result.scalars().all()
```

- [ ] **Step 4: Registrar router em `main.py`**

Abrir `backend/app/main.py` e adicionar:
```python
from app.routers.clientes import router as clientes_router
# ...
app.include_router(clientes_router)
```

- [ ] **Step 5: Rodar testes — devem passar**

```bash
docker exec -w /app -e PYTHONPATH=/app orcaavml-backend-1 \
  python -m pytest tests/backend/test_clientes.py -v 2>&1 | tail -20
```

Esperado: todos os testes PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/clientes.py backend/app/main.py \
        tests/backend/test_clientes.py
git commit -m "feat: router /clientes CRUD + testes"
```

---

## Task 4: Router de Fornecedores + Testes

**Files:**
- Create: `backend/app/routers/fornecedores.py`
- Create: `tests/backend/test_fornecedores.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Escrever testes**

```python
# tests/backend/test_fornecedores.py
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_fornecedores_vazio(client: AsyncClient, auth_headers: dict):
    r = await client.get("/fornecedores", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == []


@pytest.mark.asyncio
async def test_create_fornecedor(client: AsyncClient, auth_headers: dict):
    payload = {"nome": "Aço Brasil Ltda", "cnpj": "99.888.777/0001-55", "categorias": "material"}
    r = await client.post("/fornecedores", json=payload, headers=auth_headers)
    assert r.status_code == 201
    data = r.json()
    assert data["nome"] == "Aço Brasil Ltda"
    assert data["categorias"] == "material"


@pytest.mark.asyncio
async def test_create_fornecedor_cnpj_duplicado(client: AsyncClient, auth_headers: dict):
    payload = {"nome": "F1", "cnpj": "11.222.333/0001-44"}
    await client.post("/fornecedores", json=payload, headers=auth_headers)
    r = await client.post("/fornecedores", json=payload, headers=auth_headers)
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_update_fornecedor(client: AsyncClient, auth_headers: dict):
    r = await client.post("/fornecedores", json={"nome": "Antigo"}, headers=auth_headers)
    fid = r.json()["id"]
    r2 = await client.patch(f"/fornecedores/{fid}", json={"nome": "Novo"}, headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["nome"] == "Novo"


@pytest.mark.asyncio
async def test_delete_fornecedor(client: AsyncClient, auth_headers: dict):
    r = await client.post("/fornecedores", json={"nome": "Temp"}, headers=auth_headers)
    fid = r.json()["id"]
    r2 = await client.delete(f"/fornecedores/{fid}", headers=auth_headers)
    assert r2.status_code == 204


@pytest.mark.asyncio
async def test_filtrar_por_categoria(client: AsyncClient, auth_headers: dict):
    await client.post("/fornecedores", json={"nome": "Mat A", "categorias": "material"}, headers=auth_headers)
    await client.post("/fornecedores", json={"nome": "MO B", "categorias": "mao_obra"}, headers=auth_headers)
    r = await client.get("/fornecedores?categoria=material", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 1
    assert data[0]["nome"] == "Mat A"
```

- [ ] **Step 2: Rodar testes — devem falhar**

```bash
docker exec -w /app -e PYTHONPATH=/app orcaavml-backend-1 \
  python -m pytest tests/backend/test_fornecedores.py -v 2>&1 | tail -10
```

- [ ] **Step 3: Criar router de Fornecedores**

```python
# backend/app/routers/fornecedores.py
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.dependencies import get_current_user
from app.models.fornecedor import Fornecedor
from app.models.usuario import Usuario
from app.schemas.fornecedor import FornecedorCreate, FornecedorOut, FornecedorUpdate

router = APIRouter(prefix="/fornecedores", tags=["fornecedores"])


async def _get_fornecedor(forn_id: int, current_user: Usuario, db: AsyncSession) -> Fornecedor:
    result = await db.execute(
        select(Fornecedor).where(
            Fornecedor.id == forn_id,
            Fornecedor.empresa_id == current_user.empresa_id,
        )
    )
    f = result.scalar_one_or_none()
    if f is None:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado")
    return f


@router.get("", response_model=List[FornecedorOut])
async def list_fornecedores(
    q: Optional[str] = Query(None),
    categoria: Optional[str] = Query(None),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Fornecedor).where(Fornecedor.empresa_id == current_user.empresa_id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(
            or_(Fornecedor.nome.ilike(like), Fornecedor.cnpj.ilike(like))
        )
    if categoria:
        stmt = stmt.where(Fornecedor.categorias.ilike(f"%{categoria}%"))
    stmt = stmt.order_by(Fornecedor.nome)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=FornecedorOut, status_code=status.HTTP_201_CREATED)
async def create_fornecedor(
    body: FornecedorCreate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if body.cnpj:
        dup = await db.execute(
            select(Fornecedor).where(
                Fornecedor.empresa_id == current_user.empresa_id,
                Fornecedor.cnpj == body.cnpj,
            )
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="CNPJ já cadastrado")
    f = Fornecedor(empresa_id=current_user.empresa_id, **body.model_dump())
    db.add(f)
    await db.commit()
    await db.refresh(f)
    return f


@router.get("/{fornecedor_id}", response_model=FornecedorOut)
async def get_fornecedor(
    fornecedor_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_fornecedor(fornecedor_id, current_user, db)


@router.patch("/{fornecedor_id}", response_model=FornecedorOut)
async def update_fornecedor(
    fornecedor_id: int,
    body: FornecedorUpdate,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    f = await _get_fornecedor(fornecedor_id, current_user, db)
    if body.cnpj and body.cnpj != f.cnpj:
        dup = await db.execute(
            select(Fornecedor).where(
                Fornecedor.empresa_id == current_user.empresa_id,
                Fornecedor.cnpj == body.cnpj,
            )
        )
        if dup.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="CNPJ já cadastrado")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(f, field, value)
    await db.commit()
    await db.refresh(f)
    return f


@router.delete("/{fornecedor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_fornecedor(
    fornecedor_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    f = await _get_fornecedor(fornecedor_id, current_user, db)
    await db.delete(f)
    await db.commit()
```

- [ ] **Step 4: Registrar em `main.py`**

```python
from app.routers.fornecedores import router as fornecedores_router
# ...
app.include_router(fornecedores_router)
```

- [ ] **Step 5: Rodar testes**

```bash
docker exec -w /app -e PYTHONPATH=/app orcaavml-backend-1 \
  python -m pytest tests/backend/test_fornecedores.py -v 2>&1 | tail -10
```

Esperado: todos PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/fornecedores.py backend/app/main.py \
        tests/backend/test_fornecedores.py
git commit -m "feat: router /fornecedores CRUD + testes"
```

---

## Task 5: Obra — aceitar cliente_id

**Files:**
- Modify: `backend/app/routers/obras.py`

- [ ] **Step 1: Atualizar `create_obra` para salvar `cliente_id`**

No `create_obra`, adicionar `cliente_id=body.cliente_id` ao construtor de `Obra`:

```python
    obra = Obra(
        empresa_id=current_user.empresa_id,
        nome=body.nome,
        numero_processo=body.numero_processo,
        cliente=body.cliente,
        cliente_id=body.cliente_id,   # ← novo
        uf=body.uf,
        municipio=body.municipio,
        tipo_obra=body.tipo_obra,
        estado="em_elaboracao",
        responsavel_id=body.responsavel_id,
        data_criacao=date.today(),
        data_prazo=body.data_prazo,
    )
```

- [ ] **Step 2: Atualizar `create_obra` e `update_obra` para popular `cliente_nome`**

Após `await db.refresh(obra)`, carregar o nome do cliente vinculado para preencher `ObraOut.cliente_nome`. Adicionar helper no topo do arquivo:

```python
from sqlalchemy.orm.attributes import set_committed_value

async def _set_cliente_nome(obra: Obra, db: AsyncSession) -> None:
    """Popula campo transiente cliente_nome para serialização."""
    if obra.cliente_id:
        from app.models.cliente import Cliente as ClienteModel
        r = await db.execute(select(ClienteModel).where(ClienteModel.id == obra.cliente_id))
        c = r.scalar_one_or_none()
        set_committed_value(obra, "cliente_nome", c.nome if c else None)
    else:
        set_committed_value(obra, "cliente_nome", None)
```

Chamar `await _set_cliente_nome(obra, db)` antes de retornar em `create_obra`, `update_obra`, `get_obra`, e `list_obras`.

**Nota:** `cliente_nome` é um campo calculado — não existe na tabela. O `ObraOut` aceita ele como atributo extra via `from_attributes=True` pois `set_committed_value` o injeta no objeto SQLAlchemy. Adicionar também `cliente_nome: Optional[str] = None` ao model `Obra` como atributo Python puro (sem coluna):

```python
# no final de backend/app/models/obra.py, após os relacionamentos:
cliente_nome: Optional[str] = None  # campo transiente, não persiste
```

- [ ] **Step 3: Atualizar `update_obra` para aceitar `cliente_id`**

No handler `update_obra`, garantir que o loop `for field, value in body.model_dump(exclude_unset=True).items()` já cubra `cliente_id` (se o router usa esse padrão). Verificar o handler e aplicar o mesmo pattern dos outros campos.

- [ ] **Step 3: Verificar que testes existentes passam**

```bash
docker exec -w /app -e PYTHONPATH=/app orcaavml-backend-1 \
  python -m pytest tests/backend/ -v --tb=short 2>&1 | tail -20
```

Esperado: todos PASS.

- [ ] **Step 4: Commit**

```bash
git add backend/app/routers/obras.py
git commit -m "feat: obra.create/update aceita cliente_id"
```

---

## Task 6: Frontend — tipos + API

**Files:**
- Modify: `frontend/src/types.ts`
- Create: `frontend/src/api/clientes.ts`
- Create: `frontend/src/api/fornecedores.ts`

- [ ] **Step 1: Atualizar `api/obras.ts`** — adicionar `cliente_id` em `createObra` e adicionar `updateObra`

```typescript
// substituir a linha createObra e adicionar updateObra em frontend/src/api/obras.ts:
export const createObra = (data: { nome: string; tipo_obra: string; cliente_id?: number }) =>
  api.post<Obra>('/obras', data).then(r => r.data)

export const updateObra = (id: number, data: Partial<{ cliente_id: number | null }>) =>
  api.patch<Obra>(`/obras/${id}`, data).then(r => r.data)
```

- [ ] **Step 2: Adicionar tipos em `types.ts`**

Adicionar ao final de `frontend/src/types.ts`:

```typescript
export interface Cliente {
  id: number
  empresa_id: number
  tipo: 'pf' | 'pj'
  nome: string
  cpf_cnpj: string | null
  email: string | null
  telefone: string | null
  endereco: string | null
  cidade: string | null
  estado: string | null
  observacoes: string | null
  created_at: string
}

export interface Fornecedor {
  id: number
  empresa_id: number
  nome: string
  cnpj: string | null
  email: string | null
  telefone: string | null
  endereco: string | null
  cidade: string | null
  estado: string | null
  categorias: string | null
  observacoes: string | null
  created_at: string
}
```

Atualizar interface `Obra` — adicionar `cliente_id: number | null`:

```typescript
export interface Obra {
  id: number
  nome: string
  tipo_obra: string
  estado: string
  data_criacao: string
  cliente: string | null
  cliente_id: number | null    // ← novo
  cliente_nome: string | null  // ← novo (nome do cliente vinculado, preenchido pelo backend)
  municipio: string | null
  uf: string | null
}
```

- [ ] **Step 2: Criar `api/clientes.ts`**

```typescript
// frontend/src/api/clientes.ts
import { api } from '@/api/client'
import type { Cliente, Obra } from '@/types'

export const listClientes = (q?: string): Promise<Cliente[]> =>
  api.get<Cliente[]>('/clientes', { params: q ? { q } : {} }).then(r => r.data)

export const getCliente = (id: number): Promise<Cliente> =>
  api.get<Cliente>(`/clientes/${id}`).then(r => r.data)

export const createCliente = (data: {
  tipo: string
  nome: string
  cpf_cnpj?: string
  email?: string
  telefone?: string
  endereco?: string
  cidade?: string
  estado?: string
  observacoes?: string
}): Promise<Cliente> =>
  api.post<Cliente>('/clientes', data).then(r => r.data)

export const updateCliente = (
  id: number,
  data: Partial<{
    tipo: string
    nome: string
    cpf_cnpj: string
    email: string
    telefone: string
    endereco: string
    cidade: string
    estado: string
    observacoes: string
  }>,
): Promise<Cliente> =>
  api.patch<Cliente>(`/clientes/${id}`, data).then(r => r.data)

export const deleteCliente = (id: number): Promise<void> =>
  api.delete(`/clientes/${id}`)

export const getClienteObras = (id: number): Promise<Obra[]> =>
  api.get<Obra[]>(`/clientes/${id}/obras`).then(r => r.data)
```

- [ ] **Step 3: Criar `api/fornecedores.ts`**

```typescript
// frontend/src/api/fornecedores.ts
import { api } from '@/api/client'
import type { Fornecedor } from '@/types'

export const listFornecedores = (params?: { q?: string; categoria?: string }): Promise<Fornecedor[]> =>
  api.get<Fornecedor[]>('/fornecedores', { params }).then(r => r.data)

export const getFornecedor = (id: number): Promise<Fornecedor> =>
  api.get<Fornecedor>(`/fornecedores/${id}`).then(r => r.data)

export const createFornecedor = (data: {
  nome: string
  cnpj?: string
  email?: string
  telefone?: string
  endereco?: string
  cidade?: string
  estado?: string
  categorias?: string
  observacoes?: string
}): Promise<Fornecedor> =>
  api.post<Fornecedor>('/fornecedores', data).then(r => r.data)

export const updateFornecedor = (
  id: number,
  data: Partial<{
    nome: string
    cnpj: string
    email: string
    telefone: string
    endereco: string
    cidade: string
    estado: string
    categorias: string
    observacoes: string
  }>,
): Promise<Fornecedor> =>
  api.patch<Fornecedor>(`/fornecedores/${id}`, data).then(r => r.data)

export const deleteFornecedor = (id: number): Promise<void> =>
  api.delete(`/fornecedores/${id}`)
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types.ts frontend/src/api/clientes.ts \
        frontend/src/api/fornecedores.ts
git commit -m "feat: tipos Cliente/Fornecedor + api/clientes + api/fornecedores"
```

---

## Task 7: ClienteModal

**Files:**
- Create: `frontend/src/components/clientes/ClienteModal.tsx`

- [ ] **Step 1: Criar o modal**

```tsx
// frontend/src/components/clientes/ClienteModal.tsx
import { useState } from 'react'
import { createCliente, updateCliente } from '@/api/clientes'
import { toast } from '@/hooks/useToast'
import type { Cliente } from '@/types'

const UFS = ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']

interface Props {
  cliente?: Cliente
  onClose: () => void
  onSuccess: (c: Cliente) => void
}

export default function ClienteModal({ cliente, onClose, onSuccess }: Props) {
  const isEdit = !!cliente
  const [tipo, setTipo] = useState(cliente?.tipo ?? 'pj')
  const [nome, setNome] = useState(cliente?.nome ?? '')
  const [cpfCnpj, setCpfCnpj] = useState(cliente?.cpf_cnpj ?? '')
  const [email, setEmail] = useState(cliente?.email ?? '')
  const [telefone, setTelefone] = useState(cliente?.telefone ?? '')
  const [endereco, setEndereco] = useState(cliente?.endereco ?? '')
  const [cidade, setCidade] = useState(cliente?.cidade ?? '')
  const [estado, setEstado] = useState(cliente?.estado ?? '')
  const [observacoes, setObservacoes] = useState(cliente?.observacoes ?? '')
  const [saving, setSaving] = useState(false)
  const [cpfError, setCpfError] = useState('')

  const isValid = nome.trim().length > 0

  async function handleSubmit() {
    if (!isValid) return
    setSaving(true)
    setCpfError('')
    const data = {
      tipo,
      nome: nome.trim(),
      cpf_cnpj: cpfCnpj.trim() || undefined,
      email: email.trim() || undefined,
      telefone: telefone.trim() || undefined,
      endereco: endereco.trim() || undefined,
      cidade: cidade.trim() || undefined,
      estado: estado || undefined,
      observacoes: observacoes.trim() || undefined,
    }
    try {
      const result = isEdit && cliente
        ? await updateCliente(cliente.id, data)
        : await createCliente(data)
      onSuccess(result)
    } catch (e: any) {
      if (e?.response?.status === 409) {
        setCpfError('CPF/CNPJ já cadastrado.')
      } else {
        toast('Erro ao salvar cliente', 'error')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 p-6 space-y-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">
            {isEdit ? 'Editar cliente' : 'Novo cliente'}
          </h2>
          <button onClick={onClose} aria-label="Fechar" className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Tipo</label>
            <div className="flex gap-3">
              {(['pj', 'pf'] as const).map(t => (
                <label key={t} className="flex items-center gap-1.5 text-sm cursor-pointer">
                  <input type="radio" name="tipo" value={t} checked={tipo === t} onChange={() => setTipo(t)} />
                  {t === 'pj' ? 'Pessoa Jurídica' : 'Pessoa Física'}
                </label>
              ))}
            </div>
          </div>

          <div>
            <label htmlFor="cliente-nome" className="block text-xs font-medium text-gray-700 mb-1">
              {tipo === 'pj' ? 'Razão Social' : 'Nome'} *
            </label>
            <input
              id="cliente-nome"
              type="text"
              value={nome}
              onChange={e => setNome(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="cliente-cpfcnpj" className="block text-xs font-medium text-gray-700 mb-1">
              {tipo === 'pj' ? 'CNPJ' : 'CPF'}
            </label>
            <input
              id="cliente-cpfcnpj"
              type="text"
              value={cpfCnpj}
              onChange={e => { setCpfCnpj(e.target.value); setCpfError('') }}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${cpfError ? 'border-red-400' : 'border-gray-300'}`}
            />
            {cpfError && <p role="alert" className="text-xs text-red-500 mt-1">{cpfError}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="cliente-email" className="block text-xs font-medium text-gray-700 mb-1">Email</label>
              <input id="cliente-email" type="email" value={email} onChange={e => setEmail(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label htmlFor="cliente-tel" className="block text-xs font-medium text-gray-700 mb-1">Telefone</label>
              <input id="cliente-tel" type="tel" value={telefone} onChange={e => setTelefone(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>

          <div>
            <label htmlFor="cliente-end" className="block text-xs font-medium text-gray-700 mb-1">Endereço</label>
            <input id="cliente-end" type="text" value={endereco} onChange={e => setEndereco(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="cliente-cidade" className="block text-xs font-medium text-gray-700 mb-1">Cidade</label>
              <input id="cliente-cidade" type="text" value={cidade} onChange={e => setCidade(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label htmlFor="cliente-uf" className="block text-xs font-medium text-gray-700 mb-1">UF</label>
              <select id="cliente-uf" value={estado} onChange={e => setEstado(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">—</option>
                {UFS.map(uf => <option key={uf} value={uf}>{uf}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label htmlFor="cliente-obs" className="block text-xs font-medium text-gray-700 mb-1">Observações</label>
            <textarea id="cliente-obs" value={observacoes} onChange={e => setObservacoes(e.target.value)} rows={2}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none" />
          </div>
        </div>

        <div className="flex gap-2 justify-end pt-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancelar</button>
          <button
            onClick={handleSubmit}
            disabled={!isValid || saving}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
          >
            {saving ? 'Salvando…' : isEdit ? 'Salvar' : 'Criar'}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/clientes/ClienteModal.tsx
git commit -m "feat: ClienteModal — criar/editar cliente"
```

---

## Task 8: ClientesPage

**Files:**
- Create: `frontend/src/pages/ClientesPage.tsx`

- [ ] **Step 1: Criar a página**

```tsx
// frontend/src/pages/ClientesPage.tsx
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { UserPlus } from 'lucide-react'
import { listClientes, deleteCliente } from '@/api/clientes'
import { toast } from '@/hooks/useToast'
import type { Cliente } from '@/types'
import ClienteModal from '@/components/clientes/ClienteModal'

export default function ClientesPage() {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null)
  const navigate = useNavigate()

  async function reload(query = q) {
    const data = await listClientes(query || undefined)
    setClientes(data)
  }

  useEffect(() => {
    reload().finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    const t = setTimeout(() => reload(q), 300)
    return () => clearTimeout(t)
  }, [q])

  async function handleDelete(id: number) {
    try {
      await deleteCliente(id)
      setClientes(prev => prev.filter(c => c.id !== id))
      setConfirmDelete(null)
      toast('Cliente excluído')
    } catch (e: any) {
      if (e?.response?.status === 409) {
        toast('Cliente possui obras vinculadas e não pode ser excluído', 'error')
      } else {
        toast('Erro ao excluir cliente', 'error')
      }
      setConfirmDelete(null)
    }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Clientes</h1>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium"
        >
          <UserPlus size={16} /> Novo Cliente
        </button>
      </div>

      <input
        type="text"
        value={q}
        onChange={e => setQ(e.target.value)}
        placeholder="Buscar por nome ou CPF/CNPJ…"
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />

      {loading && <p className="text-gray-500 text-sm">Carregando…</p>}

      {!loading && clientes.length === 0 && (
        <p className="text-gray-400 text-sm text-center py-12">Nenhum cliente cadastrado.</p>
      )}

      {!loading && clientes.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
              <tr>
                <th className="text-left px-4 py-3">Nome</th>
                <th className="text-left px-4 py-3">CPF/CNPJ</th>
                <th className="text-left px-4 py-3">Email</th>
                <th className="text-left px-4 py-3">Telefone</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {clientes.map(c => (
                <tr
                  key={c.id}
                  className="border-t border-gray-100 hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/clientes/${c.id}`)}
                >
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {c.nome}
                    <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full ${c.tipo === 'pj' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}`}>
                      {c.tipo === 'pj' ? 'PJ' : 'PF'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{c.cpf_cnpj ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-500">{c.email ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-500">{c.telefone ?? '—'}</td>
                  <td className="px-4 py-3 text-right" onClick={e => e.stopPropagation()}>
                    {confirmDelete === c.id ? (
                      <span className="flex items-center gap-2 justify-end">
                        <button onClick={() => handleDelete(c.id)} className="text-xs bg-red-600 text-white px-2 py-1 rounded">Confirmar</button>
                        <button onClick={() => setConfirmDelete(null)} className="text-xs text-gray-500">Cancelar</button>
                      </span>
                    ) : (
                      <button
                        onClick={() => setConfirmDelete(c.id)}
                        className="text-gray-400 hover:text-red-500 text-xs"
                        aria-label={`Excluir ${c.nome}`}
                      >
                        🗑
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <ClienteModal
          onClose={() => setShowModal(false)}
          onSuccess={c => {
            setClientes(prev => [c, ...prev])
            setShowModal(false)
            toast('Cliente criado')
          }}
        />
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/ClientesPage.tsx
git commit -m "feat: ClientesPage — lista com busca, criação, exclusão"
```

---

## Task 9: ClienteDetailPage

**Files:**
- Create: `frontend/src/pages/ClienteDetailPage.tsx`

- [ ] **Step 1: Criar a página**

```tsx
// frontend/src/pages/ClienteDetailPage.tsx
import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Pencil } from 'lucide-react'
import { getCliente, getClienteObras } from '@/api/clientes'
import { toast } from '@/hooks/useToast'
import type { Cliente, Obra } from '@/types'
import ClienteModal from '@/components/clientes/ClienteModal'

type Tab = 'dados' | 'obras' | 'propostas'

export default function ClienteDetailPage() {
  const { id } = useParams<{ id: string }>()
  const clienteId = Number(id)
  const navigate = useNavigate()
  const [cliente, setCliente] = useState<Cliente | null>(null)
  const [obras, setObras] = useState<Obra[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<Tab>('dados')
  const [editOpen, setEditOpen] = useState(false)

  async function reload() {
    const [c, os] = await Promise.all([getCliente(clienteId), getClienteObras(clienteId)])
    setCliente(c)
    setObras(os)
  }

  useEffect(() => {
    reload().finally(() => setLoading(false))
  }, [clienteId])

  if (loading) return <div className="p-6 text-gray-500">Carregando…</div>
  if (!cliente) return <div className="p-6 text-red-500">Cliente não encontrado</div>

  const field = (label: string, value: string | null | undefined) => (
    <div key={label}>
      <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">{label}</p>
      <p className="text-sm text-gray-900">{value || '—'}</p>
    </div>
  )

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <nav className="text-sm text-gray-500 mb-4 flex items-center gap-1">
        <Link to="/clientes" className="hover:text-blue-600 flex items-center gap-1">
          <ArrowLeft size={14} /> Clientes
        </Link>
        <span>›</span>
        <span className="text-gray-900 font-medium">{cliente.nome}</span>
      </nav>

      <div className="flex items-start justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{cliente.nome}</h1>
          <span className={`text-xs px-2 py-0.5 rounded-full mt-1 inline-block ${cliente.tipo === 'pj' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}`}>
            {cliente.tipo === 'pj' ? 'Pessoa Jurídica' : 'Pessoa Física'}
          </span>
        </div>
        <button
          onClick={() => setEditOpen(true)}
          className="flex items-center gap-2 border border-gray-300 px-3 py-2 rounded-lg text-sm hover:bg-gray-50"
        >
          <Pencil size={14} /> Editar
        </button>
      </div>

      <div className="flex gap-0 border-b border-gray-200 mb-6">
        {(['dados', 'obras', 'propostas'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t === 'dados' ? 'Dados' : t === 'obras' ? `Obras (${obras.length})` : 'Propostas'}
          </button>
        ))}
      </div>

      {tab === 'dados' && (
        <div className="grid grid-cols-2 gap-x-8 gap-y-4">
          {field(cliente.tipo === 'pj' ? 'CNPJ' : 'CPF', cliente.cpf_cnpj)}
          {field('Email', cliente.email)}
          {field('Telefone', cliente.telefone)}
          {field('Endereço', cliente.endereco)}
          {field('Cidade', cliente.cidade)}
          {field('UF', cliente.estado)}
          {cliente.observacoes && (
            <div className="col-span-2">
              {field('Observações', cliente.observacoes)}
            </div>
          )}
        </div>
      )}

      {tab === 'obras' && (
        <>
          {obras.length === 0 ? (
            <p className="text-gray-400 text-sm text-center py-12">Nenhuma obra vinculada.</p>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
                  <tr>
                    <th className="text-left px-4 py-3">Obra</th>
                    <th className="text-left px-4 py-3">Tipo</th>
                    <th className="text-left px-4 py-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {obras.map(o => (
                    <tr
                      key={o.id}
                      className="border-t border-gray-100 hover:bg-gray-50 cursor-pointer"
                      onClick={() => navigate(`/obras/${o.id}`)}
                    >
                      <td className="px-4 py-3 font-medium text-gray-900">{o.nome}</td>
                      <td className="px-4 py-3 text-gray-500 capitalize">{o.tipo_obra.replace(/_/g, ' ')}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          o.estado === 'em_elaboracao' ? 'bg-blue-100 text-blue-700' :
                          o.estado === 'concluido' ? 'bg-green-100 text-green-700' :
                          'bg-gray-100 text-gray-600'
                        }`}>
                          {o.estado.replace(/_/g, ' ')}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {tab === 'propostas' && (
        <div className="text-center py-12 text-gray-400">
          <p className="text-sm">Propostas comerciais disponíveis em breve.</p>
        </div>
      )}

      {editOpen && (
        <ClienteModal
          cliente={cliente}
          onClose={() => setEditOpen(false)}
          onSuccess={updated => {
            setCliente(updated)
            setEditOpen(false)
            toast('Cliente atualizado')
          }}
        />
      )}
    </div>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/ClienteDetailPage.tsx
git commit -m "feat: ClienteDetailPage — abas Dados / Obras / Propostas"
```

---

## Task 10: FornecedorModal + FornecedoresPage + FornecedorDetailPage

**Files:**
- Create: `frontend/src/components/fornecedores/FornecedorModal.tsx`
- Create: `frontend/src/pages/FornecedoresPage.tsx`
- Create: `frontend/src/pages/FornecedorDetailPage.tsx`

- [ ] **Step 1: Criar FornecedorModal**

```tsx
// frontend/src/components/fornecedores/FornecedorModal.tsx
import { useState } from 'react'
import { createFornecedor, updateFornecedor } from '@/api/fornecedores'
import { toast } from '@/hooks/useToast'
import type { Fornecedor } from '@/types'

const UFS = ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']
const CATEGORIAS = [
  { value: 'material', label: 'Material' },
  { value: 'mao_obra', label: 'Mão de obra' },
  { value: 'equipamento', label: 'Equipamento' },
  { value: 'servico', label: 'Serviço' },
]

interface Props {
  fornecedor?: Fornecedor
  onClose: () => void
  onSuccess: (f: Fornecedor) => void
}

export default function FornecedorModal({ fornecedor, onClose, onSuccess }: Props) {
  const isEdit = !!fornecedor
  const [nome, setNome] = useState(fornecedor?.nome ?? '')
  const [cnpj, setCnpj] = useState(fornecedor?.cnpj ?? '')
  const [email, setEmail] = useState(fornecedor?.email ?? '')
  const [telefone, setTelefone] = useState(fornecedor?.telefone ?? '')
  const [endereco, setEndereco] = useState(fornecedor?.endereco ?? '')
  const [cidade, setCidade] = useState(fornecedor?.cidade ?? '')
  const [estado, setEstado] = useState(fornecedor?.estado ?? '')
  const [cats, setCats] = useState<string[]>(
    fornecedor?.categorias ? fornecedor.categorias.split(',') : []
  )
  const [observacoes, setObservacoes] = useState(fornecedor?.observacoes ?? '')
  const [saving, setSaving] = useState(false)
  const [cnpjError, setCnpjError] = useState('')

  const toggleCat = (v: string) =>
    setCats(prev => prev.includes(v) ? prev.filter(x => x !== v) : [...prev, v])

  const isValid = nome.trim().length > 0

  async function handleSubmit() {
    if (!isValid) return
    setSaving(true)
    setCnpjError('')
    const data = {
      nome: nome.trim(),
      cnpj: cnpj.trim() || undefined,
      email: email.trim() || undefined,
      telefone: telefone.trim() || undefined,
      endereco: endereco.trim() || undefined,
      cidade: cidade.trim() || undefined,
      estado: estado || undefined,
      categorias: cats.length ? cats.join(',') : undefined,
      observacoes: observacoes.trim() || undefined,
    }
    try {
      const result = isEdit && fornecedor
        ? await updateFornecedor(fornecedor.id, data)
        : await createFornecedor(data)
      onSuccess(result)
    } catch (e: any) {
      if (e?.response?.status === 409) {
        setCnpjError('CNPJ já cadastrado.')
      } else {
        toast('Erro ao salvar fornecedor', 'error')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 p-6 space-y-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">
            {isEdit ? 'Editar fornecedor' : 'Novo fornecedor'}
          </h2>
          <button onClick={onClose} aria-label="Fechar" className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>

        <div className="space-y-3">
          <div>
            <label htmlFor="forn-nome" className="block text-xs font-medium text-gray-700 mb-1">Nome / Razão Social *</label>
            <input id="forn-nome" type="text" value={nome} onChange={e => setNome(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label htmlFor="forn-cnpj" className="block text-xs font-medium text-gray-700 mb-1">CNPJ</label>
            <input id="forn-cnpj" type="text" value={cnpj} onChange={e => { setCnpj(e.target.value); setCnpjError('') }}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${cnpjError ? 'border-red-400' : 'border-gray-300'}`} />
            {cnpjError && <p role="alert" className="text-xs text-red-500 mt-1">{cnpjError}</p>}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="forn-email" className="block text-xs font-medium text-gray-700 mb-1">Email</label>
              <input id="forn-email" type="email" value={email} onChange={e => setEmail(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label htmlFor="forn-tel" className="block text-xs font-medium text-gray-700 mb-1">Telefone</label>
              <input id="forn-tel" type="tel" value={telefone} onChange={e => setTelefone(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div>
            <label htmlFor="forn-end" className="block text-xs font-medium text-gray-700 mb-1">Endereço</label>
            <input id="forn-end" type="text" value={endereco} onChange={e => setEndereco(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="forn-cidade" className="block text-xs font-medium text-gray-700 mb-1">Cidade</label>
              <input id="forn-cidade" type="text" value={cidade} onChange={e => setCidade(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label htmlFor="forn-uf" className="block text-xs font-medium text-gray-700 mb-1">UF</label>
              <select id="forn-uf" value={estado} onChange={e => setEstado(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">—</option>
                {UFS.map(uf => <option key={uf} value={uf}>{uf}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Categorias</label>
            <div className="flex flex-wrap gap-2">
              {CATEGORIAS.map(cat => (
                <label key={cat.value} className="flex items-center gap-1.5 text-sm cursor-pointer">
                  <input type="checkbox" checked={cats.includes(cat.value)} onChange={() => toggleCat(cat.value)} />
                  {cat.label}
                </label>
              ))}
            </div>
          </div>
          <div>
            <label htmlFor="forn-obs" className="block text-xs font-medium text-gray-700 mb-1">Observações</label>
            <textarea id="forn-obs" value={observacoes} onChange={e => setObservacoes(e.target.value)} rows={2}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none" />
          </div>
        </div>

        <div className="flex gap-2 justify-end pt-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancelar</button>
          <button
            onClick={handleSubmit}
            disabled={!isValid || saving}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
          >
            {saving ? 'Salvando…' : isEdit ? 'Salvar' : 'Criar'}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Criar FornecedoresPage**

```tsx
// frontend/src/pages/FornecedoresPage.tsx
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Building2 } from 'lucide-react'
import { listFornecedores, deleteFornecedor } from '@/api/fornecedores'
import { toast } from '@/hooks/useToast'
import type { Fornecedor } from '@/types'
import FornecedorModal from '@/components/fornecedores/FornecedorModal'

const CAT_LABELS: Record<string, string> = {
  material: 'Material', mao_obra: 'Mão de obra',
  equipamento: 'Equipamento', servico: 'Serviço',
}

export default function FornecedoresPage() {
  const [fornecedores, setFornecedores] = useState<Fornecedor[]>([])
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null)
  const navigate = useNavigate()

  async function reload(query = q) {
    const data = await listFornecedores(query ? { q: query } : {})
    setFornecedores(data)
  }

  useEffect(() => { reload().finally(() => setLoading(false)) }, [])
  useEffect(() => {
    const t = setTimeout(() => reload(q), 300)
    return () => clearTimeout(t)
  }, [q])

  async function handleDelete(id: number) {
    try {
      await deleteFornecedor(id)
      setFornecedores(prev => prev.filter(f => f.id !== id))
      setConfirmDelete(null)
      toast('Fornecedor excluído')
    } catch {
      toast('Erro ao excluir fornecedor', 'error')
      setConfirmDelete(null)
    }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Fornecedores</h1>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium"
        >
          <Building2 size={16} /> Novo Fornecedor
        </button>
      </div>

      <input
        type="text"
        value={q}
        onChange={e => setQ(e.target.value)}
        placeholder="Buscar por nome ou CNPJ…"
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />

      {loading && <p className="text-gray-500 text-sm">Carregando…</p>}
      {!loading && fornecedores.length === 0 && (
        <p className="text-gray-400 text-sm text-center py-12">Nenhum fornecedor cadastrado.</p>
      )}
      {!loading && fornecedores.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
              <tr>
                <th className="text-left px-4 py-3">Nome</th>
                <th className="text-left px-4 py-3">CNPJ</th>
                <th className="text-left px-4 py-3">Telefone</th>
                <th className="text-left px-4 py-3">Categorias</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {fornecedores.map(f => (
                <tr key={f.id} className="border-t border-gray-100 hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/fornecedores/${f.id}`)}>
                  <td className="px-4 py-3 font-medium text-gray-900">{f.nome}</td>
                  <td className="px-4 py-3 text-gray-500">{f.cnpj ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-500">{f.telefone ?? '—'}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {f.categorias ? f.categorias.split(',').map(c => (
                        <span key={c} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                          {CAT_LABELS[c] ?? c}
                        </span>
                      )) : '—'}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right" onClick={e => e.stopPropagation()}>
                    {confirmDelete === f.id ? (
                      <span className="flex items-center gap-2 justify-end">
                        <button onClick={() => handleDelete(f.id)} className="text-xs bg-red-600 text-white px-2 py-1 rounded">Confirmar</button>
                        <button onClick={() => setConfirmDelete(null)} className="text-xs text-gray-500">Cancelar</button>
                      </span>
                    ) : (
                      <button onClick={() => setConfirmDelete(f.id)}
                        className="text-gray-400 hover:text-red-500 text-xs"
                        aria-label={`Excluir ${f.nome}`}>🗑</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <FornecedorModal
          onClose={() => setShowModal(false)}
          onSuccess={f => {
            setFornecedores(prev => [f, ...prev])
            setShowModal(false)
            toast('Fornecedor criado')
          }}
        />
      )}
    </div>
  )
}
```

- [ ] **Step 3: Criar FornecedorDetailPage**

```tsx
// frontend/src/pages/FornecedorDetailPage.tsx
import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Pencil } from 'lucide-react'
import { getFornecedor } from '@/api/fornecedores'
import { toast } from '@/hooks/useToast'
import type { Fornecedor } from '@/types'
import FornecedorModal from '@/components/fornecedores/FornecedorModal'

const CAT_LABELS: Record<string, string> = {
  material: 'Material', mao_obra: 'Mão de obra',
  equipamento: 'Equipamento', servico: 'Serviço',
}

type Tab = 'dados' | 'compras'

export default function FornecedorDetailPage() {
  const { id } = useParams<{ id: string }>()
  const fornecedorId = Number(id)
  const [fornecedor, setFornecedor] = useState<Fornecedor | null>(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<Tab>('dados')
  const [editOpen, setEditOpen] = useState(false)

  useEffect(() => {
    getFornecedor(fornecedorId).then(setFornecedor).finally(() => setLoading(false))
  }, [fornecedorId])

  if (loading) return <div className="p-6 text-gray-500">Carregando…</div>
  if (!fornecedor) return <div className="p-6 text-red-500">Fornecedor não encontrado</div>

  const field = (label: string, value: string | null | undefined) => (
    <div key={label}>
      <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">{label}</p>
      <p className="text-sm text-gray-900">{value || '—'}</p>
    </div>
  )

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <nav className="text-sm text-gray-500 mb-4 flex items-center gap-1">
        <Link to="/fornecedores" className="hover:text-blue-600 flex items-center gap-1">
          <ArrowLeft size={14} /> Fornecedores
        </Link>
        <span>›</span>
        <span className="text-gray-900 font-medium">{fornecedor.nome}</span>
      </nav>

      <div className="flex items-start justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">{fornecedor.nome}</h1>
        <button
          onClick={() => setEditOpen(true)}
          className="flex items-center gap-2 border border-gray-300 px-3 py-2 rounded-lg text-sm hover:bg-gray-50"
        >
          <Pencil size={14} /> Editar
        </button>
      </div>

      <div className="flex gap-0 border-b border-gray-200 mb-6">
        {(['dados', 'compras'] as Tab[]).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}>
            {t === 'dados' ? 'Dados' : 'Compras'}
          </button>
        ))}
      </div>

      {tab === 'dados' && (
        <div className="grid grid-cols-2 gap-x-8 gap-y-4">
          {field('CNPJ', fornecedor.cnpj)}
          {field('Email', fornecedor.email)}
          {field('Telefone', fornecedor.telefone)}
          {field('Endereço', fornecedor.endereco)}
          {field('Cidade', fornecedor.cidade)}
          {field('UF', fornecedor.estado)}
          {fornecedor.categorias && (
            <div className="col-span-2">
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Categorias</p>
              <div className="flex flex-wrap gap-1">
                {fornecedor.categorias.split(',').map(c => (
                  <span key={c} className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                    {CAT_LABELS[c] ?? c}
                  </span>
                ))}
              </div>
            </div>
          )}
          {fornecedor.observacoes && (
            <div className="col-span-2">{field('Observações', fornecedor.observacoes)}</div>
          )}
        </div>
      )}

      {tab === 'compras' && (
        <div className="text-center py-12 text-gray-400">
          <p className="text-sm">Disponível no Módulo 20 — Compras.</p>
        </div>
      )}

      {editOpen && (
        <FornecedorModal
          fornecedor={fornecedor}
          onClose={() => setEditOpen(false)}
          onSuccess={updated => {
            setFornecedor(updated)
            setEditOpen(false)
            toast('Fornecedor atualizado')
          }}
        />
      )}
    </div>
  )
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/fornecedores/FornecedorModal.tsx \
        frontend/src/pages/FornecedoresPage.tsx \
        frontend/src/pages/FornecedorDetailPage.tsx
git commit -m "feat: FornecedorModal + FornecedoresPage + FornecedorDetailPage"
```

---

## Task 11: TopBar — Dropdown "Cadastros ▾"

**Files:**
- Modify: `frontend/src/components/layout/TopBar.tsx`

- [ ] **Step 1: Substituir TopBar com dropdown de Cadastros**

O arquivo atual usa `Link` simples. Vamos adicionar o dropdown "Cadastros ▾" seguindo o mesmo padrão do dropdown "Admin ▾" já existente.

Substituir o conteúdo de `frontend/src/components/layout/TopBar.tsx` por:

```tsx
import { useState, useRef, useEffect } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import PerfilModal from '@/components/layout/PerfilModal'

const CADASTROS_ITEMS = [
  {
    label: 'Clientes',
    to: '/clientes',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
        <circle cx="12" cy="7" r="4"/>
      </svg>
    ),
  },
  {
    label: 'Fornecedores',
    to: '/fornecedores',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="7" width="20" height="14" rx="2"/>
        <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>
      </svg>
    ),
  },
  {
    label: 'Insumos',
    to: '/insumos',
    icon: (
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="3"/>
        <path d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"/>
      </svg>
    ),
  },
]

export default function TopBar() {
  const { logout, papel, nome } = useAuth()
  const navigate = useNavigate()
  const [userDropdown, setUserDropdown] = useState(false)
  const [cadastrosDropdown, setCadastrosDropdown] = useState(false)
  const [perfilOpen, setPerfilOpen] = useState(false)
  const userRef = useRef<HTMLDivElement>(null)
  const cadastrosRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (userRef.current && !userRef.current.contains(e.target as Node)) setUserDropdown(false)
      if (cadastrosRef.current && !cadastrosRef.current.contains(e.target as Node)) setCadastrosDropdown(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  async function handleLogout() {
    setUserDropdown(false)
    try { await logout() } finally { navigate('/login') }
  }

  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `hover:text-blue-300 transition-colors text-sm ${isActive ? 'text-blue-400 font-medium' : ''}`

  return (
    <header className="bg-gray-900 text-white px-4 h-12 flex items-center gap-6 shrink-0">
      <span className="font-bold text-blue-400">AVML</span>
      <nav className="flex gap-4 text-sm items-center">
        <NavLink to="/" end className={navLinkClass}>Dashboard</NavLink>
        <NavLink to="/obras" className={navLinkClass}>Obras</NavLink>

        {/* Dropdown Cadastros */}
        <div className="relative" ref={cadastrosRef}>
          <button
            onClick={() => setCadastrosDropdown(v => !v)}
            className="flex items-center gap-1 text-sm hover:text-blue-300 transition-colors"
          >
            Cadastros
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" className="text-gray-500 mt-0.5">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </button>
          {cadastrosDropdown && (
            <div className="absolute top-8 left-0 bg-white text-gray-800 rounded-lg shadow-lg py-1 min-w-44 z-50 border border-gray-100">
              {CADASTROS_ITEMS.map(item => (
                <Link
                  key={item.to}
                  to={item.to}
                  onClick={() => setCadastrosDropdown(false)}
                  className="flex items-center gap-2.5 px-4 py-2 text-sm hover:bg-gray-50 text-gray-700"
                >
                  <span className="text-gray-400">{item.icon}</span>
                  {item.label}
                </Link>
              ))}
            </div>
          )}
        </div>

        <NavLink to="/composicoes" className={navLinkClass}>Base de Comp.</NavLink>
        <NavLink to="/relatorios" className={navLinkClass}>Relatórios</NavLink>
      </nav>

      <div className="ml-auto flex items-center gap-3 text-sm">
        {papel === 'admin' && (
          <Link to="/configuracoes" className="text-gray-400 hover:text-white transition-colors text-sm">
            Configurações
          </Link>
        )}
        <div className="relative" ref={userRef}>
          <button
            onClick={() => setUserDropdown(v => !v)}
            className="text-gray-300 hover:text-white transition-colors flex items-center gap-1"
          >
            {nome ?? papel}
            <span className="text-gray-500 text-xs">▾</span>
          </button>
          {userDropdown && (
            <div className="absolute right-0 top-8 bg-white text-gray-800 rounded-lg shadow-lg py-1 min-w-36 z-50">
              <button
                onClick={() => { setUserDropdown(false); setPerfilOpen(true) }}
                className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50"
              >
                Meu Perfil
              </button>
              <hr className="border-gray-100 my-1" />
              <button
                onClick={handleLogout}
                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                Sair
              </button>
            </div>
          )}
        </div>
      </div>
      {perfilOpen && <PerfilModal onClose={() => setPerfilOpen(false)} />}
    </header>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/layout/TopBar.tsx
git commit -m "feat: TopBar — dropdown Cadastros com SVG icons, NavLink active state"
```

---

## Task 12: App.tsx + Vite Proxy + Rotas

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/vite.config.ts`

- [ ] **Step 1: Adicionar rotas em `App.tsx`**

Adicionar imports e rotas no arquivo existente:

```tsx
// imports a adicionar:
import ClientesPage from '@/pages/ClientesPage'
import ClienteDetailPage from '@/pages/ClienteDetailPage'
import FornecedoresPage from '@/pages/FornecedoresPage'
import FornecedorDetailPage from '@/pages/FornecedorDetailPage'

// rotas a adicionar dentro do <Routes>:
<Route path="/clientes" element={<ClientesPage />} />
<Route path="/clientes/:id" element={<ClienteDetailPage />} />
<Route path="/fornecedores" element={<FornecedoresPage />} />
<Route path="/fornecedores/:id" element={<FornecedorDetailPage />} />
<Route path="/insumos" element={
  <div className="p-10 text-center text-gray-400 text-sm">Módulo Insumos — em breve.</div>
} />
```

- [ ] **Step 2: Adicionar proxy bypass em `vite.config.ts`**

No array de paths do `Object.fromEntries(...)`, adicionar `'/clientes'` e `'/fornecedores'`:

```typescript
['/auth', '/usuarios', '/obras', '/versoes', '/grupos', '/itens', '/bdi',
 '/composicoes', '/dashboard', '/agente', '/clientes', '/fornecedores']
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/App.tsx frontend/vite.config.ts
git commit -m "feat: rotas /clientes, /fornecedores, /insumos (em breve) + proxy bypass"
```

---

## Task 13: ObraDetailPage — Card de Cliente

**Files:**
- Modify: `frontend/src/pages/ObraDetailPage.tsx`

- [ ] **Step 1: Adicionar card de cliente ao header**

No `ObraDetailPage`, após a seção do `<h1>` com o nome da obra e antes das tabs, adicionar o card de cliente. Também adicionar state para o select modal.

Adicionar imports no topo:
```tsx
import { Link } from 'react-router-dom'  // já existe, confirmar
import { listClientes } from '@/api/clientes'
import { updateObra } from '@/api/obras'   // verificar se existe; se não, adicionar
import type { Cliente } from '@/types'
```

Verificar `api/obras.ts` — se `updateObra` não existir, adicionar:
```typescript
export const updateObra = (id: number, data: Partial<{ cliente_id: number | null }>) =>
  api.patch<Obra>(`/obras/${id}`, data).then(r => r.data)
```

No componente `ObraDetailPage`, adicionar state:
```tsx
const [clientes, setClientes] = useState<Cliente[]>([])
const [clienteSelectOpen, setClienteSelectOpen] = useState(false)
const [clienteSearch, setClienteSearch] = useState('')
```

Adicionar `useEffect` para carregar clientes quando o select abrir:
```tsx
useEffect(() => {
  if (clienteSelectOpen) {
    listClientes().then(setClientes)
  }
}, [clienteSelectOpen])
```

Adicionar função para vincular cliente:
```tsx
async function handleVincularCliente(clienteId: number | null) {
  try {
    const updated = await updateObra(obraId, { cliente_id: clienteId })
    setObra(updated)
    setClienteSelectOpen(false)
    setClienteSearch('')
    toast(clienteId ? 'Cliente vinculado' : 'Cliente desvinculado')
  } catch {
    toast('Erro ao vincular cliente', 'error')
  }
}
```

Adicionar o card após `</div>` do header (antes das tabs), usando `UserCircle` da `lucide-react`:

```tsx
{/* Card de cliente */}
<div className="mt-3 flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6b7280" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
    <circle cx="12" cy="7" r="4"/>
  </svg>
  <div className="flex-1">
    <p className="text-xs text-gray-500 uppercase tracking-wide leading-none mb-0.5">Cliente</p>
    {obra.cliente_id ? (
      <Link
        to={`/clientes/${obra.cliente_id}`}
        className="text-sm font-medium text-blue-600 hover:underline"
        onClick={e => e.stopPropagation()}
      >
        {obra.cliente_nome ?? obra.cliente ?? `Cliente #${obra.cliente_id}`} →
      </Link>
    ) : (
      <span className="text-sm text-gray-400">Nenhum cliente vinculado</span>
    )}
  </div>
  <button
    onClick={() => setClienteSelectOpen(true)}
    className="text-xs border border-gray-300 px-2 py-1 rounded hover:bg-white transition-colors text-gray-600"
  >
    {obra.cliente_id ? 'Alterar' : 'Vincular'}
  </button>
</div>

{/* Modal de seleção de cliente */}
{clienteSelectOpen && (
  <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
    <div className="bg-white rounded-xl shadow-xl w-full max-w-sm mx-4 p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-gray-900">Vincular cliente</h3>
        <button onClick={() => setClienteSelectOpen(false)} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
      </div>
      <input
        type="text"
        value={clienteSearch}
        onChange={e => setClienteSearch(e.target.value)}
        placeholder="Buscar cliente…"
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
        autoFocus
      />
      <div className="max-h-48 overflow-y-auto space-y-1">
        {obra.cliente_id && (
          <button
            onClick={() => handleVincularCliente(null)}
            className="w-full text-left px-3 py-2 rounded-lg text-sm text-red-600 hover:bg-red-50"
          >
            Remover vínculo
          </button>
        )}
        {clientes
          .filter(c => !clienteSearch || c.nome.toLowerCase().includes(clienteSearch.toLowerCase()))
          .map(c => (
            <button
              key={c.id}
              onClick={() => handleVincularCliente(c.id)}
              className={`w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-blue-50 ${obra.cliente_id === c.id ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'}`}
            >
              {c.nome}
              {c.cpf_cnpj && <span className="ml-2 text-gray-400 text-xs">{c.cpf_cnpj}</span>}
            </button>
          ))
        }
      </div>
    </div>
  </div>
)}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/ObraDetailPage.tsx frontend/src/api/obras.ts
git commit -m "feat: ObraDetailPage — card de cliente com vincular/alterar"
```

---

## Task 14: ObrasPage — Select de Cliente em "Nova Obra"

**Files:**
- Modify: `frontend/src/pages/ObrasPage.tsx`

- [ ] **Step 1: Adicionar campo Cliente no modal "Nova Obra"**

No `ObrasPage.tsx`, adicionar:

1. Imports:
```tsx
import { listClientes } from '@/api/clientes'
import type { Cliente } from '@/types'
```

2. State:
```tsx
const [clienteId, setClienteId] = useState<number | ''>('')
const [clientes, setClientes] = useState<Cliente[]>([])
```

3. `useEffect` para carregar clientes quando o dialog abre:
```tsx
useEffect(() => {
  if (open) listClientes().then(setClientes)
}, [open])
```

4. No `handleCreate`, passar `cliente_id`:
```tsx
const obra = await createObra({
  nome,
  tipo_obra: tipo,
  cliente_id: clienteId !== '' ? clienteId : undefined,
})
```

5. Reset no close/success:
```tsx
setClienteId('')
```

6. Campo no formulário, antes dos botões Cancelar/Criar:
```tsx
<div>
  <label className="block text-sm font-medium text-gray-700 mb-1">
    Cliente <span className="text-gray-400 font-normal">(opcional)</span>
  </label>
  <select
    value={clienteId}
    onChange={e => setClienteId(e.target.value ? Number(e.target.value) : '')}
    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
  >
    <option value="">Sem cliente</option>
    {clientes.map(c => (
      <option key={c.id} value={c.id}>{c.nome}{c.cpf_cnpj ? ` — ${c.cpf_cnpj}` : ''}</option>
    ))}
  </select>
</div>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/ObrasPage.tsx
git commit -m "feat: ObrasPage — campo cliente opcional em Nova Obra"
```

---

## Task 15: Verificação Final

- [ ] **Step 1: Rodar todos os testes backend**

```bash
docker exec -w /app -e PYTHONPATH=/app orcaavml-backend-1 \
  python -m pytest tests/backend/ -v --tb=short 2>&1 | tail -30
```

Esperado: todos os testes PASS (incluindo testes anteriores de obras, composições, etc.).

- [ ] **Step 2: TypeCheck frontend**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Esperado: sem erros de tipo.

- [ ] **Step 3: Verificar no browser**

Com o Vite dev server rodando (`npm run dev` em `frontend/`):

1. `/clientes` — abre e mostra lista vazia
2. Criar cliente PJ com CNPJ → aparece na lista
3. Tentar criar com mesmo CNPJ → "CPF/CNPJ já cadastrado."
4. Clicar no cliente → página de detalhe com abas Dados / Obras / Propostas
5. `/fornecedores` — funciona igual
6. `/obras` → "Nova Obra" tem campo Cliente
7. ObraDetailPage → card de cliente aparece no header, "Vincular" abre select
8. Dropdown "Cadastros ▾" na TopBar → lista Clientes, Fornecedores, Insumos (em breve)
9. `/insumos` → mostra "em breve"
10. Navegar diretamente a `/clientes` no browser (reload) → funciona sem retornar JSON

- [ ] **Step 4: Commit final**

```bash
git add .
git commit -m "feat: Módulo 18 completo — Clientes, Fornecedores, TopBar Cadastros"
```
