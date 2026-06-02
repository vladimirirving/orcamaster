# Cronograma Físico-Financeiro Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a Cronograma tab to PlanilhaPage where the orçamentista distributes execution percentages per month per item, with automatic monthly totals and accumulated % footer.

**Architecture:** Backend adds two nullable columns to `versao` (cronograma_inicio/fim) and a new router under `/versoes/{id}/cronograma` with 3 endpoints (GET all, PATCH config, PATCH linha). Frontend adds a tab to PlanilhaPage that renders either a config form (first access) or an inline-editable grid with a fixed footer showing monthly totals and accumulated %.

**Tech Stack:** FastAPI + SQLAlchemy async + Alembic (backend); React 19 + TypeScript + Tailwind (frontend); Vitest (frontend tests); pytest-asyncio (backend tests).

---

## Context for implementers

**Repo root:** `/Users/vladimirirving/Desktop/OrçaAVML`

**Run backend tests:**
```bash
docker compose exec backend pytest tests/backend/test_cronograma.py -v
```

**Run frontend tests:**
```bash
cd frontend && npm test -- --reporter=verbose
```

**Run Alembic migration:**
```bash
docker compose exec backend alembic upgrade head
```

**Key existing patterns to follow:**
- Router isolation check: see `backend/app/routers/bdi.py` — `_get_versao_ativa` (raises 409 if blocked/not found) and `_get_versao_acesso` (raises 404 if not found)
- Test fixtures: see `tests/backend/conftest.py` — `versao_ativa`, `empresa`, `admin_user`, `auth_headers`
- Isolation test pattern: see `tests/backend/test_composicoes.py:432-470`
- Frontend API pattern: see `frontend/src/api/bdi.ts`
- Frontend component pattern: see `frontend/src/components/planilha/BDIModal.tsx`

**Existing data model:**
- `CronogramaLinha` already exists: `item_id` (unique FK → item, CASCADE), `distribuicao_json` (JSONB, `{"2025-01": 40.0}`)
- `Item` has `composicao_id` FK but no `composicao` relationship yet
- `Versao` has no `cronograma_inicio`/`cronograma_fim` columns yet

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `backend/alembic/versions/0002_cronograma_config.py` | Create | Add cronograma_inicio/fim to versao |
| `backend/app/models/versao.py` | Modify | Add cronograma_inicio, cronograma_fim fields |
| `backend/app/models/item.py` | Modify | Add composicao relationship |
| `backend/app/schemas/cronograma.py` | Create | Pydantic schemas for cronograma endpoints |
| `backend/app/routers/cronograma.py` | Create | GET, PATCH config, PATCH linha |
| `backend/app/main.py` | Modify | Register cronograma router |
| `tests/backend/test_cronograma.py` | Create | 8 backend tests |
| `frontend/src/types.ts` | Modify | Add cronograma fields to Versao, new interfaces |
| `frontend/src/api/cronograma.ts` | Create | 3 API calls |
| `frontend/src/components/planilha/CronogramaConfigForm.tsx` | Create | Month range picker form |
| `frontend/src/components/planilha/CronogramaTab.tsx` | Create | Tab orchestrator |
| `frontend/src/components/planilha/CronogramaGrade.tsx` | Create | Editable grid + footer |
| `frontend/src/pages/PlanilhaPage.tsx` | Modify | Add tab state + render CronogramaTab |

---

## Task 1: Backend migration + model updates

**Files:**
- Create: `backend/alembic/versions/0002_cronograma_config.py`
- Modify: `backend/app/models/versao.py`
- Modify: `backend/app/models/item.py`

- [ ] **Step 1: Write the migration file**

```python
# backend/alembic/versions/0002_cronograma_config.py
"""add cronograma_inicio e fim to versao

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-02
"""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('versao', sa.Column('cronograma_inicio', sa.String(7), nullable=True))
    op.add_column('versao', sa.Column('cronograma_fim', sa.String(7), nullable=True))


def downgrade() -> None:
    op.drop_column('versao', 'cronograma_fim')
    op.drop_column('versao', 'cronograma_inicio')
```

- [ ] **Step 2: Update Versao model**

Open `backend/app/models/versao.py`. The current file ends with the `bdi` relationship. Add the two new columns after `deletada_em`:

```python
# Full file after change:
from datetime import datetime
from decimal import Decimal
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, Boolean, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Versao(Base):
    __tablename__ = "versao"

    id: Mapped[int] = mapped_column(primary_key=True)
    obra_id: Mapped[int] = mapped_column(ForeignKey("obra.id"))
    numero: Mapped[int] = mapped_column(Integer)
    nome: Mapped[Optional[str]] = mapped_column(String(200))
    criada_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    criada_por: Mapped[Optional[int]] = mapped_column(ForeignKey("usuario.id"))
    bloqueada: Mapped[bool] = mapped_column(Boolean, default=False)
    total_sem_bdi: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    total_com_bdi: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"))
    deletada_em: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    cronograma_inicio: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)
    cronograma_fim: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)

    obra: Mapped["Obra"] = relationship(back_populates="versoes")
    grupos: Mapped[list["Grupo"]] = relationship(back_populates="versao")
    bdi: Mapped[Optional["BDI"]] = relationship(back_populates="versao", uselist=False)
    medicoes: Mapped[list["Medicao"]] = relationship(back_populates="versao")
    pacote_jobs: Mapped[list["PacoteJob"]] = relationship(back_populates="versao")
```

- [ ] **Step 3: Add composicao relationship to Item model**

Open `backend/app/models/item.py`. Add the `composicao` relationship after the existing `cronograma_linha` relationship:

```python
# Full file after change:
from decimal import Decimal
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, Boolean, Numeric, Computed
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class Item(Base):
    __tablename__ = "item"

    id: Mapped[int] = mapped_column(primary_key=True)
    grupo_id: Mapped[int] = mapped_column(ForeignKey("grupo.id"))
    ordem: Mapped[int] = mapped_column(Integer, default=0)
    composicao_id: Mapped[Optional[int]] = mapped_column(ForeignKey("composicao.id"), nullable=True)
    quantidade: Mapped[Decimal] = mapped_column(Numeric(15, 6))
    unidade: Mapped[str] = mapped_column(String(20))
    preco_unitario_sem_bdi: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 6), nullable=True)
    preco_unitario_com_bdi: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 6), nullable=True)
    total: Mapped[Decimal] = mapped_column(
        Numeric(15, 6),
        Computed("quantidade * COALESCE(preco_unitario_sem_bdi, 0)", persisted=True),
    )
    etiqueta_revisao: Mapped[bool] = mapped_column(Boolean, default=False)
    requer_revisao: Mapped[bool] = mapped_column(Boolean, default=False)

    grupo: Mapped["Grupo"] = relationship(back_populates="itens")
    cronograma_linha: Mapped[Optional["CronogramaLinha"]] = relationship(
        back_populates="item", uselist=False, cascade="all, delete-orphan"
    )
    composicao: Mapped[Optional["Composicao"]] = relationship(
        "Composicao", foreign_keys=[composicao_id]
    )
```

- [ ] **Step 4: Run migration**

```bash
docker compose exec backend alembic upgrade head
```

Expected output ends with: `Running upgrade 0001 -> 0002, add cronograma_inicio e fim to versao`

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/versions/0002_cronograma_config.py \
        backend/app/models/versao.py \
        backend/app/models/item.py
git commit -m "feat: migration add cronograma_inicio/fim to versao, composicao relationship on Item"
```

---

## Task 2: Backend cronograma schemas + router + tests

**Files:**
- Create: `backend/app/schemas/cronograma.py`
- Create: `backend/app/routers/cronograma.py`
- Modify: `backend/app/main.py`
- Create: `tests/backend/test_cronograma.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/backend/test_cronograma.py
import pytest
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.cronograma_linha import CronogramaLinha
from app.models.composicao import Composicao


async def _setup_versao_com_itens(db_session, versao_ativa, empresa):
    """Helper: creates grupo + 2 itens, one with composicao, one without."""
    comp = Composicao(
        empresa_id=None, origem="sinapi", codigo="99999",
        descricao="TERRAPLANAGEM MECANIZADA", unidade="M3",
        preco_unitario=Decimal("45.000000"), requer_revisao=False,
    )
    db_session.add(comp)
    await db_session.flush()

    grupo = Grupo(versao_id=versao_ativa.id, nome="Terraplenagem", ordem=0)
    db_session.add(grupo)
    await db_session.flush()

    item1 = Item(
        grupo_id=grupo.id, ordem=0,
        composicao_id=comp.id,
        quantidade=Decimal("500.000000"), unidade="M3",
        preco_unitario_sem_bdi=Decimal("45.000000"),
    )
    item2 = Item(
        grupo_id=grupo.id, ordem=1,
        composicao_id=None,
        quantidade=Decimal("1.000000"), unidade="UN",
    )
    db_session.add_all([item1, item2])
    await db_session.commit()
    return item1, item2


@pytest.mark.asyncio
async def test_get_cronograma_retorna_config_e_linhas_vazias(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa, empresa
):
    item1, item2 = await _setup_versao_com_itens(db_session, versao_ativa, empresa)

    resp = await client.get(
        f"/versoes/{versao_ativa.id}/cronograma", headers=auth_headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["cronograma_inicio"] is None
    assert data["cronograma_fim"] is None
    assert len(data["linhas"]) == 2
    # Item with composicao has descricao
    linha1 = next(l for l in data["linhas"] if l["item_id"] == item1.id)
    assert linha1["descricao"] == "TERRAPLANAGEM MECANIZADA"
    assert linha1["distribuicao_json"] == {}
    # Item without composicao has empty descricao
    linha2 = next(l for l in data["linhas"] if l["item_id"] == item2.id)
    assert linha2["descricao"] == ""
    assert linha2["distribuicao_json"] == {}


@pytest.mark.asyncio
async def test_patch_config_persiste_datas(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    resp = await client.patch(
        f"/versoes/{versao_ativa.id}/cronograma/config",
        json={"cronograma_inicio": "2025-01", "cronograma_fim": "2026-06"},
        headers=auth_headers,
    )
    assert resp.status_code == 204

    await db_session.refresh(versao_ativa)
    assert versao_ativa.cronograma_inicio == "2025-01"
    assert versao_ativa.cronograma_fim == "2026-06"


@pytest.mark.asyncio
async def test_patch_linha_cria_cronograma_linha(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa, empresa
):
    item1, _ = await _setup_versao_com_itens(db_session, versao_ativa, empresa)

    resp = await client.patch(
        f"/versoes/{versao_ativa.id}/cronograma/linhas/{item1.id}",
        json={"distribuicao_json": {"2025-01": 40.0, "2025-02": 60.0}},
        headers=auth_headers,
    )
    assert resp.status_code == 204

    r = await db_session.execute(
        select(CronogramaLinha).where(CronogramaLinha.item_id == item1.id)
    )
    cl = r.scalar_one_or_none()
    assert cl is not None
    assert cl.distribuicao_json == {"2025-01": 40.0, "2025-02": 60.0}


@pytest.mark.asyncio
async def test_patch_linha_atualiza_linha_existente(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa, empresa
):
    item1, _ = await _setup_versao_com_itens(db_session, versao_ativa, empresa)
    cl = CronogramaLinha(item_id=item1.id, distribuicao_json={"2025-01": 100.0})
    db_session.add(cl)
    await db_session.commit()

    resp = await client.patch(
        f"/versoes/{versao_ativa.id}/cronograma/linhas/{item1.id}",
        json={"distribuicao_json": {"2025-01": 50.0, "2025-02": 50.0}},
        headers=auth_headers,
    )
    assert resp.status_code == 204

    await db_session.refresh(cl)
    assert cl.distribuicao_json == {"2025-01": 50.0, "2025-02": 50.0}


@pytest.mark.asyncio
async def test_patch_linha_remove_zeros_do_json(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa, empresa
):
    item1, _ = await _setup_versao_com_itens(db_session, versao_ativa, empresa)

    resp = await client.patch(
        f"/versoes/{versao_ativa.id}/cronograma/linhas/{item1.id}",
        json={"distribuicao_json": {"2025-01": 0.0, "2025-02": 60.0, "2025-03": 0.0}},
        headers=auth_headers,
    )
    assert resp.status_code == 204

    r = await db_session.execute(
        select(CronogramaLinha).where(CronogramaLinha.item_id == item1.id)
    )
    cl = r.scalar_one_or_none()
    assert cl.distribuicao_json == {"2025-02": 60.0}


@pytest.mark.asyncio
async def test_patch_config_em_versao_bloqueada_retorna_409(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    versao_ativa.bloqueada = True
    await db_session.commit()

    resp = await client.patch(
        f"/versoes/{versao_ativa.id}/cronograma/config",
        json={"cronograma_inicio": "2025-01", "cronograma_fim": "2025-12"},
        headers=auth_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_patch_linha_em_versao_bloqueada_retorna_409(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa, empresa
):
    item1, _ = await _setup_versao_com_itens(db_session, versao_ativa, empresa)
    versao_ativa.bloqueada = True
    await db_session.commit()

    resp = await client.patch(
        f"/versoes/{versao_ativa.id}/cronograma/linhas/{item1.id}",
        json={"distribuicao_json": {"2025-01": 100.0}},
        headers=auth_headers,
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_isolamento_empresa_b_nao_acessa_cronograma_empresa_a(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa
):
    from app.models.empresa import Empresa
    from app.models.usuario import Usuario
    from app.services.auth_service import hash_password, create_access_token

    empresa_b = Empresa(nome="Empresa B", cnpj="11.111.111/0001-11")
    db_session.add(empresa_b)
    await db_session.flush()
    user_b = Usuario(
        empresa_id=empresa_b.id, nome="User B", email="userb@teste.com",
        senha_hash=hash_password("senha123"), papel="admin",
    )
    db_session.add(user_b)
    await db_session.commit()

    token_b = create_access_token({
        "sub": str(user_b.id), "papel": user_b.papel, "empresa_id": user_b.empresa_id,
    })
    headers_b = {"Authorization": f"Bearer {token_b}"}

    resp = await client.get(
        f"/versoes/{versao_ativa.id}/cronograma", headers=headers_b
    )
    assert resp.status_code == 404
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
docker compose exec backend pytest tests/backend/test_cronograma.py -v
```

Expected: all 8 tests fail with import errors or 404/422 (router doesn't exist yet).

- [ ] **Step 3: Create schemas**

```python
# backend/app/schemas/cronograma.py
from typing import Optional
from pydantic import BaseModel


class CronogramaLinhaOut(BaseModel):
    item_id: int
    descricao: str
    unidade: str
    quantidade: str
    total_sem_bdi: str
    distribuicao_json: dict[str, float]


class CronogramaOut(BaseModel):
    cronograma_inicio: Optional[str]
    cronograma_fim: Optional[str]
    linhas: list[CronogramaLinhaOut]


class CronogramaConfigIn(BaseModel):
    cronograma_inicio: str
    cronograma_fim: str


class CronogramaLinhaIn(BaseModel):
    distribuicao_json: dict[str, float]
```

- [ ] **Step 4: Create router**

```python
# backend/app/routers/cronograma.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.dependencies import get_current_user
from app.models.cronograma_linha import CronogramaLinha
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.schemas.cronograma import (
    CronogramaConfigIn, CronogramaLinhaIn, CronogramaLinhaOut, CronogramaOut,
)

router = APIRouter(tags=["cronograma"])


async def _get_versao_ativa(versao_id: int, current_user: Usuario, db: AsyncSession) -> Versao:
    result = await db.execute(
        select(Versao)
        .join(Obra, Versao.obra_id == Obra.id)
        .where(
            Versao.id == versao_id,
            Obra.empresa_id == current_user.empresa_id,
            Versao.bloqueada == False,
            Versao.deletada_em.is_(None),
        )
    )
    v = result.scalar_one_or_none()
    if v is None:
        raise HTTPException(status_code=409, detail="Versão não encontrada ou não está ativa")
    return v


async def _get_versao_acesso(versao_id: int, current_user: Usuario, db: AsyncSession) -> Versao:
    result = await db.execute(
        select(Versao)
        .join(Obra, Versao.obra_id == Obra.id)
        .where(Versao.id == versao_id, Obra.empresa_id == current_user.empresa_id)
    )
    v = result.scalar_one_or_none()
    if v is None:
        raise HTTPException(status_code=404, detail="Versão não encontrada")
    return v


@router.get("/versoes/{versao_id}/cronograma", response_model=CronogramaOut)
async def get_cronograma(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    versao = await _get_versao_acesso(versao_id, current_user, db)

    stmt = (
        select(Item)
        .join(Grupo, Item.grupo_id == Grupo.id)
        .where(Grupo.versao_id == versao_id)
        .order_by(Grupo.ordem, Item.ordem)
        .options(
            selectinload(Item.cronograma_linha),
            selectinload(Item.composicao),
        )
    )
    itens = (await db.execute(stmt)).scalars().all()

    linhas = []
    for item in itens:
        cl = item.cronograma_linha
        linhas.append(CronogramaLinhaOut(
            item_id=item.id,
            descricao=item.composicao.descricao if item.composicao else "",
            unidade=item.unidade,
            quantidade=str(item.quantidade),
            total_sem_bdi=str(item.total),
            distribuicao_json=dict(cl.distribuicao_json) if cl else {},
        ))

    return CronogramaOut(
        cronograma_inicio=versao.cronograma_inicio,
        cronograma_fim=versao.cronograma_fim,
        linhas=linhas,
    )


@router.patch("/versoes/{versao_id}/cronograma/config", status_code=status.HTTP_204_NO_CONTENT)
async def patch_cronograma_config(
    versao_id: int,
    body: CronogramaConfigIn,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    versao = await _get_versao_ativa(versao_id, current_user, db)
    versao.cronograma_inicio = body.cronograma_inicio
    versao.cronograma_fim = body.cronograma_fim
    await db.commit()


@router.patch(
    "/versoes/{versao_id}/cronograma/linhas/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def patch_cronograma_linha(
    versao_id: int,
    item_id: int,
    body: CronogramaLinhaIn,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao_ativa(versao_id, current_user, db)

    # Verify item belongs to this versao
    r = await db.execute(
        select(Item)
        .join(Grupo, Item.grupo_id == Grupo.id)
        .where(Item.id == item_id, Grupo.versao_id == versao_id)
    )
    item = r.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=404, detail="Item não encontrado nesta versão")

    cleaned = {k: v for k, v in body.distribuicao_json.items() if v != 0}

    r2 = await db.execute(select(CronogramaLinha).where(CronogramaLinha.item_id == item_id))
    cl = r2.scalar_one_or_none()
    if cl is None:
        cl = CronogramaLinha(item_id=item_id, distribuicao_json=cleaned)
        db.add(cl)
    else:
        cl.distribuicao_json = cleaned
    await db.commit()
```

- [ ] **Step 5: Register router in main.py**

Open `backend/app/main.py`. Add import and include_router:

```python
# Full file after change:
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, usuarios, obras, versoes, grupos, composicoes, bdi
from app.routers import cronograma
from app.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="OrçaAVML API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(obras.router)
app.include_router(versoes.router)
app.include_router(grupos.router)
app.include_router(composicoes.router)
app.include_router(bdi.router)
app.include_router(cronograma.router)
```

- [ ] **Step 6: Run tests — verify they pass**

```bash
docker compose exec backend pytest tests/backend/test_cronograma.py -v
```

Expected: 8 passed.

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/cronograma.py \
        backend/app/routers/cronograma.py \
        backend/app/main.py \
        tests/backend/test_cronograma.py
git commit -m "feat: cronograma router — GET, PATCH config, PATCH linha with empresa isolation"
```

---

## Task 3: Frontend types + API

**Files:**
- Modify: `frontend/src/types.ts`
- Create: `frontend/src/api/cronograma.ts`

- [ ] **Step 1: Update types.ts**

Open `frontend/src/types.ts`. Add `cronograma_inicio` and `cronograma_fim` to `Versao`, and append the two new interfaces at the end:

```typescript
// Full file after change:
export interface Obra {
  id: number
  nome: string
  tipo_obra: string
  estado: string
  data_criacao: string
  cliente: string | null
  municipio: string | null
  uf: string | null
}

export interface Versao {
  id: number
  obra_id: number
  numero: number
  nome: string | null
  bloqueada: boolean
  deletada_em: string | null
  total_sem_bdi: string
  total_com_bdi: string
  cronograma_inicio: string | null
  cronograma_fim: string | null
}

export interface Grupo {
  id: number
  versao_id: number
  pai_id: number | null
  nome: string
  codigo: string | null
  ordem: number
  filhos: Grupo[]
}

export interface Item {
  id: number
  grupo_id: number
  ordem: number
  composicao_id: number | null
  quantidade: string
  unidade: string | null
  preco_unitario_sem_bdi: string | null
  preco_unitario_com_bdi: string | null
  total: string
  requer_revisao: boolean
  etiqueta_revisao: string | null
}

export interface BDI {
  id: number
  versao_id: number
  ac: string; sg: string; r: string; df: string; lucro: string
  iss: string; pis: string; cofins: string
  bdi_composto: string
}

export interface Composicao {
  id: number
  origem: string
  codigo: string
  descricao: string
  unidade: string
  preco_unitario: string
}

export interface CronogramaLinhaData {
  item_id: number
  descricao: string
  unidade: string
  quantidade: string
  total_sem_bdi: string
  distribuicao_json: Record<string, number>
}

export interface CronogramaData {
  cronograma_inicio: string | null
  cronograma_fim: string | null
  linhas: CronogramaLinhaData[]
}
```

- [ ] **Step 2: Create API module**

```typescript
// frontend/src/api/cronograma.ts
import { api } from '@/api/client'
import type { CronogramaData } from '@/types'

export const getCronograma = (versaoId: number) =>
  api.get<CronogramaData>(`/versoes/${versaoId}/cronograma`).then(r => r.data)

export const patchCronogramaConfig = (
  versaoId: number,
  data: { cronograma_inicio: string; cronograma_fim: string }
) => api.patch(`/versoes/${versaoId}/cronograma/config`, data)

export const patchCronogramaLinha = (
  versaoId: number,
  itemId: number,
  distribuicao_json: Record<string, number>
) => api.patch(`/versoes/${versaoId}/cronograma/linhas/${itemId}`, { distribuicao_json })
```

- [ ] **Step 3: Run TypeScript check**

```bash
cd /Users/vladimirirving/Desktop/OrçaAVML/frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types.ts frontend/src/api/cronograma.ts
git commit -m "feat: frontend cronograma types and API module"
```

---

## Task 4: CronogramaConfigForm + CronogramaTab

**Files:**
- Create: `frontend/src/components/planilha/CronogramaConfigForm.tsx`
- Create: `frontend/src/components/planilha/CronogramaTab.tsx`

- [ ] **Step 1: Create CronogramaConfigForm**

```tsx
// frontend/src/components/planilha/CronogramaConfigForm.tsx
import { useState } from 'react'
import { patchCronogramaConfig } from '@/api/cronograma'
import { toast } from '@/hooks/useToast'

interface Props {
  versaoId: number
  initialInicio: string
  initialFim: string
  onSaved: (inicio: string, fim: string) => void
}

export default function CronogramaConfigForm({ versaoId, initialInicio, initialFim, onSaved }: Props) {
  const [inicio, setInicio] = useState(initialInicio)
  const [fim, setFim] = useState(initialFim)
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (fim < inicio) {
      toast('A data de fim deve ser igual ou posterior ao início', 'error')
      return
    }
    setSaving(true)
    try {
      await patchCronogramaConfig(versaoId, { cronograma_inicio: inicio, cronograma_fim: fim })
      onSaved(inicio, fim)
    } catch {
      toast('Erro ao salvar período', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex flex-col items-center justify-center flex-1 gap-6">
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 w-full max-w-md">
        <h2 className="text-base font-semibold text-gray-900 mb-1">Definir período do cronograma</h2>
        <p className="text-sm text-gray-500 mb-5">Escolha o mês de início e fim da obra.</p>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Mês de início</label>
            <input
              required
              type="month"
              value={inicio}
              onChange={e => setInicio(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Mês de fim</label>
            <input
              required
              type="month"
              value={fim}
              onChange={e => setFim(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            type="submit"
            disabled={saving}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Salvando...' : 'Definir período'}
          </button>
        </form>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Create CronogramaTab**

```tsx
// frontend/src/components/planilha/CronogramaTab.tsx
import { useState, useEffect } from 'react'
import { getCronograma } from '@/api/cronograma'
import type { CronogramaData } from '@/types'
import { useOrcamento } from '@/stores/orcamento'
import CronogramaConfigForm from './CronogramaConfigForm'
import CronogramaGrade from './CronogramaGrade'

interface Props {
  versaoId: number
  isReadOnly: boolean
}

export default function CronogramaTab({ versaoId, isReadOnly }: Props) {
  const { versao } = useOrcamento()
  const [data, setData] = useState<CronogramaData | null>(null)
  const [loading, setLoading] = useState(true)
  const [showConfig, setShowConfig] = useState(false)

  useEffect(() => {
    getCronograma(versaoId)
      .then(setData)
      .finally(() => setLoading(false))
  }, [versaoId])

  function handleConfigSaved(inicio: string, fim: string) {
    setData(prev => prev ? { ...prev, cronograma_inicio: inicio, cronograma_fim: fim } : null)
    setShowConfig(false)
  }

  function handleLinhaUpdated(itemId: number, distribuicao_json: Record<string, number>) {
    setData(prev => {
      if (!prev) return prev
      return {
        ...prev,
        linhas: prev.linhas.map(l =>
          l.item_id === itemId ? { ...l, distribuicao_json } : l
        ),
      }
    })
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
        Carregando cronograma...
      </div>
    )
  }

  const configured = !!(data?.cronograma_inicio && data?.cronograma_fim)

  if (!configured || showConfig) {
    return (
      <CronogramaConfigForm
        versaoId={versaoId}
        initialInicio={data?.cronograma_inicio ?? ''}
        initialFim={data?.cronograma_fim ?? ''}
        onSaved={handleConfigSaved}
      />
    )
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {!isReadOnly && (
        <div className="flex items-center justify-end px-4 py-2 border-b border-gray-100 bg-white shrink-0">
          <button
            onClick={() => setShowConfig(true)}
            className="text-xs text-gray-500 hover:text-blue-600 border border-gray-200 px-3 py-1 rounded-lg"
          >
            Alterar período ({data!.cronograma_inicio} → {data!.cronograma_fim})
          </button>
        </div>
      )}
      <CronogramaGrade
        versaoId={versaoId}
        data={data!}
        totalSemBdi={parseFloat(versao?.total_sem_bdi ?? '0')}
        isReadOnly={isReadOnly}
        onLinhaUpdated={handleLinhaUpdated}
      />
    </div>
  )
}
```

- [ ] **Step 3: Run TypeScript check**

```bash
cd /Users/vladimirirving/Desktop/OrçaAVML/frontend && npx tsc --noEmit
```

Expected: no errors (CronogramaGrade will be a missing module error until Task 5 — that's acceptable at this stage; alternatively create an empty stub first).

If tsc fails only on missing `CronogramaGrade`, create a stub:

```tsx
// frontend/src/components/planilha/CronogramaGrade.tsx (stub — replaced in Task 5)
export default function CronogramaGrade(_props: any) { return null }
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/planilha/CronogramaConfigForm.tsx \
        frontend/src/components/planilha/CronogramaTab.tsx
git commit -m "feat: CronogramaConfigForm and CronogramaTab — period config and tab orchestration"
```

---

## Task 5: CronogramaGrade

**Files:**
- Create: `frontend/src/components/planilha/CronogramaGrade.tsx`

- [ ] **Step 1: Create CronogramaGrade**

```tsx
// frontend/src/components/planilha/CronogramaGrade.tsx
import { useState, useRef } from 'react'
import { CheckCircle, AlertTriangle } from 'lucide-react'
import { patchCronogramaLinha } from '@/api/cronograma'
import { fmtBRL } from '@/lib/utils'
import { toast } from '@/hooks/useToast'
import type { CronogramaData, CronogramaLinhaData } from '@/types'

interface Props {
  versaoId: number
  data: CronogramaData
  totalSemBdi: number
  isReadOnly: boolean
  onLinhaUpdated: (itemId: number, distribuicao_json: Record<string, number>) => void
}

function getMeses(inicio: string, fim: string): string[] {
  const meses: string[] = []
  const [sy, sm] = inicio.split('-').map(Number)
  const [ey, em] = fim.split('-').map(Number)
  let y = sy, m = sm
  while (y < ey || (y === ey && m <= em)) {
    meses.push(`${y}-${String(m).padStart(2, '0')}`)
    m++
    if (m > 12) { m = 1; y++ }
  }
  return meses
}

function fmtMesLabel(mes: string): string {
  const [y, m] = mes.split('-')
  const labels = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
  return `${labels[parseInt(m) - 1]}/${y.slice(2)}`
}

function somaPercentual(dist: Record<string, number>): number {
  return Object.values(dist).reduce((a, b) => a + b, 0)
}

export default function CronogramaGrade({ versaoId, data, totalSemBdi, isReadOnly, onLinhaUpdated }: Props) {
  const meses = getMeses(data.cronograma_inicio!, data.cronograma_fim!)

  const [localDist, setLocalDist] = useState<Record<number, Record<string, number>>>(
    () => Object.fromEntries(data.linhas.map(l => [l.item_id, { ...l.distribuicao_json }]))
  )
  const localDistRef = useRef(localDist)
  localDistRef.current = localDist

  const [saving, setSaving] = useState<Record<number, boolean>>({})
  const saveTimers = useRef<Record<number, ReturnType<typeof setTimeout>>>({})

  function scheduleSave(itemId: number) {
    if (saveTimers.current[itemId]) clearTimeout(saveTimers.current[itemId])
    saveTimers.current[itemId] = setTimeout(async () => {
      const dist = localDistRef.current[itemId]
      setSaving(s => ({ ...s, [itemId]: true }))
      try {
        await patchCronogramaLinha(versaoId, itemId, dist)
        onLinhaUpdated(itemId, dist)
      } catch {
        toast('Erro ao salvar linha do cronograma', 'error')
      } finally {
        setSaving(s => ({ ...s, [itemId]: false }))
      }
    }, 300)
  }

  function handleChange(itemId: number, mes: string, value: string) {
    const num = parseFloat(value) || 0
    setLocalDist(prev => ({
      ...prev,
      [itemId]: { ...prev[itemId], [mes]: num },
    }))
  }

  function handleBlur(itemId: number) {
    scheduleSave(itemId)
  }

  function handleKeyDown(
    e: React.KeyboardEvent<HTMLInputElement>,
    rowIdx: number,
    colIdx: number
  ) {
    if (e.key === 'Tab') {
      e.preventDefault()
      const nextCol = colIdx + (e.shiftKey ? -1 : 1)
      if (nextCol >= 0 && nextCol < meses.length) {
        document.querySelector<HTMLInputElement>(
          `[data-row="${rowIdx}"][data-col="${nextCol}"]`
        )?.focus()
      }
    }
    if (e.key === 'Enter') {
      e.preventDefault()
      const nextRow = rowIdx + (e.shiftKey ? -1 : 1)
      if (nextRow >= 0 && nextRow < data.linhas.length) {
        document.querySelector<HTMLInputElement>(
          `[data-row="${nextRow}"][data-col="${colIdx}"]`
        )?.focus()
      }
    }
  }

  // Footer calculations
  const totalMensal: Record<string, number> = {}
  for (const mes of meses) {
    totalMensal[mes] = data.linhas.reduce((sum, linha) => {
      const pct = localDist[linha.item_id]?.[mes] ?? 0
      return sum + parseFloat(linha.total_sem_bdi) * pct / 100
    }, 0)
  }

  let acumulado = 0
  const acumuladoR$: Record<string, number> = {}
  const acumuladoPct: Record<string, number> = {}
  for (const mes of meses) {
    acumulado += totalMensal[mes]
    acumuladoR$[mes] = acumulado
    acumuladoPct[mes] = totalSemBdi > 0 ? (acumulado / totalSemBdi) * 100 : 0
  }

  const incompletos = data.linhas.filter(l => {
    const soma = somaPercentual(localDist[l.item_id] ?? {})
    return Math.abs(soma - 100) > 0.01
  }).length

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {incompletos > 0 && (
        <div className="mx-4 mt-3 px-3 py-2 bg-yellow-50 border border-yellow-200 rounded-lg text-xs text-yellow-700 shrink-0">
          {incompletos} {incompletos === 1 ? 'item sem' : 'itens sem'} distribuição completa (soma ≠ 100%)
        </div>
      )}

      <div className="flex-1 overflow-auto mt-2">
        <table className="border-collapse text-xs" style={{ minWidth: 'max-content' }}>
          <thead>
            <tr className="bg-gray-50 sticky top-0 z-10">
              <th className="text-left px-3 py-2 font-medium text-gray-600 border-b border-gray-200 sticky left-0 bg-gray-50 min-w-64">
                Serviço
              </th>
              <th className="text-right px-3 py-2 font-medium text-gray-600 border-b border-gray-200 sticky left-64 bg-gray-50 min-w-28">
                Total S/BDI
              </th>
              {meses.map(mes => (
                <th key={mes} className="text-center px-2 py-2 font-medium text-gray-600 border-b border-gray-200 min-w-16">
                  {fmtMesLabel(mes)}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {data.linhas.map((linha, rowIdx) => {
              const dist = localDist[linha.item_id] ?? {}
              const soma = somaPercentual(dist)
              const valida = Math.abs(soma - 100) <= 0.01
              const isSaving = saving[linha.item_id]

              return (
                <tr key={linha.item_id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-3 py-1.5 sticky left-0 bg-white hover:bg-gray-50 min-w-64 max-w-64">
                    <div className="flex items-center gap-1.5">
                      {valida
                        ? <CheckCircle size={12} className="text-green-500 shrink-0" />
                        : <AlertTriangle size={12} className="text-red-400 shrink-0" />
                      }
                      <span className="truncate text-gray-800">
                        {linha.descricao || <span className="text-gray-400">—</span>}
                      </span>
                      {isSaving && <span className="text-gray-300 text-xs ml-1">●</span>}
                    </div>
                  </td>
                  <td className="px-3 py-1.5 text-right text-gray-600 sticky left-64 bg-white hover:bg-gray-50 min-w-28">
                    {fmtBRL(linha.total_sem_bdi)}
                  </td>
                  {meses.map((mes, colIdx) => {
                    const val = dist[mes] ?? 0
                    return (
                      <td
                        key={mes}
                        className={`px-1 py-0.5 text-center min-w-16 ${val > 0 ? 'bg-blue-50' : ''}`}
                      >
                        {isReadOnly ? (
                          <span className="text-gray-700">{val > 0 ? `${val}%` : ''}</span>
                        ) : (
                          <input
                            type="number"
                            min={0}
                            max={100}
                            step={0.01}
                            value={val || ''}
                            disabled={isSaving}
                            data-row={rowIdx}
                            data-col={colIdx}
                            onChange={e => handleChange(linha.item_id, mes, e.target.value)}
                            onBlur={() => handleBlur(linha.item_id)}
                            onKeyDown={e => handleKeyDown(e, rowIdx, colIdx)}
                            placeholder="—"
                            className="w-full text-center bg-transparent text-gray-800 placeholder-gray-300 focus:outline-none focus:bg-white focus:ring-1 focus:ring-blue-400 rounded px-1 py-0.5 disabled:opacity-40"
                          />
                        )}
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>

          <tfoot className="sticky bottom-0">
            <tr className="bg-slate-800 text-slate-200">
              <td colSpan={2} className="px-3 py-1.5 font-medium text-xs sticky left-0 bg-slate-800">
                Total R$
              </td>
              {meses.map(mes => (
                <td key={mes} className="px-2 py-1.5 text-center text-xs">
                  {totalMensal[mes] > 0 ? fmtBRL(String(totalMensal[mes].toFixed(2))) : '—'}
                </td>
              ))}
            </tr>
            <tr className="bg-slate-700 text-slate-200">
              <td colSpan={2} className="px-3 py-1.5 font-medium text-xs sticky left-0 bg-slate-700">
                Acumulado R$
              </td>
              {meses.map(mes => (
                <td key={mes} className="px-2 py-1.5 text-center text-xs">
                  {acumuladoR$[mes] > 0 ? fmtBRL(String(acumuladoR$[mes].toFixed(2))) : '—'}
                </td>
              ))}
            </tr>
            <tr className="bg-slate-900 text-blue-300 font-semibold">
              <td colSpan={2} className="px-3 py-1.5 text-xs sticky left-0 bg-slate-900">
                Acumulado %
              </td>
              {meses.map(mes => (
                <td key={mes} className="px-2 py-1.5 text-center text-xs">
                  {acumuladoPct[mes] > 0 ? `${acumuladoPct[mes].toFixed(1)}%` : '—'}
                </td>
              ))}
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Run TypeScript check**

```bash
cd /Users/vladimirirving/Desktop/OrçaAVML/frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/planilha/CronogramaGrade.tsx
git commit -m "feat: CronogramaGrade — inline editable grid with footer totals and accumulated %"
```

---

## Task 6: PlanilhaPage tab integration

**Files:**
- Modify: `frontend/src/pages/PlanilhaPage.tsx`

- [ ] **Step 1: Update PlanilhaPage**

Replace the full file content:

```tsx
// frontend/src/pages/PlanilhaPage.tsx
import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getVersoes } from '@/api/obras'
import { getGrupos } from '@/api/grupos'
import { getBdi } from '@/api/bdi'
import { useOrcamento } from '@/stores/orcamento'
import { fmtBRL, fmtPct } from '@/lib/utils'
import PlanilhaTabela from '@/components/planilha/PlanilhaTabela'
import PainelLateral from '@/components/planilha/PainelLateral'
import BDIModal from '@/components/planilha/BDIModal'
import CronogramaTab from '@/components/planilha/CronogramaTab'

type Tab = 'planilha' | 'cronograma'

export default function PlanilhaPage() {
  const { obraId, versaoId } = useParams<{ obraId: string; versaoId: string }>()
  const numObraId = Number(obraId)
  const numVersaoId = Number(versaoId)
  const { versao, bdi, setVersao, setBdi, setGrupos } = useOrcamento()
  const [bdiModalOpen, setBdiModalOpen] = useState(false)
  const [tab, setTab] = useState<Tab>('planilha')

  useEffect(() => {
    async function load() {
      const [versoes, grupos] = await Promise.all([
        getVersoes(numObraId),
        getGrupos(numVersaoId),
      ])
      const v = versoes.find(x => x.id === numVersaoId)
      if (v) setVersao(v)
      setGrupos(grupos)
      getBdi(numVersaoId).then(setBdi).catch(() => setBdi(null))
    }
    load()
    return () => {
      useOrcamento.setState({ versao: null, bdi: null, grupos: [], itens: {}, gruposAbertos: new Set(), painel: null })
    }
  }, [numVersaoId])

  const isReadOnly = versao?.bloqueada ?? false

  return (
    <div className="flex flex-col h-[calc(100vh-48px)]">
      {/* Toolbar */}
      <div className="flex items-center gap-4 px-4 py-2 bg-white border-b border-gray-200 shrink-0">
        <nav className="text-sm text-gray-500">
          <Link to="/obras" className="hover:text-blue-600">Obras</Link>
          <span className="mx-1">›</span>
          <Link to={`/obras/${obraId}`} className="hover:text-blue-600">Obra</Link>
          <span className="mx-1">›</span>
          <span className="text-gray-900 font-medium">Versão {versao?.numero}</span>
        </nav>

        {isReadOnly && (
          <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full">Somente leitura</span>
        )}

        <div className="ml-auto flex items-center gap-3">
          <button
            onClick={() => setBdiModalOpen(true)}
            className="text-sm text-gray-600 hover:text-blue-600 border border-gray-200 px-3 py-1 rounded-lg"
          >
            BDI: {bdi ? fmtPct(bdi.bdi_composto) : 'Configurar BDI'}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 bg-white shrink-0 px-4">
        <button
          onClick={() => setTab('planilha')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === 'planilha'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-800'
          }`}
        >
          Planilha
        </button>
        <button
          onClick={() => setTab('cronograma')}
          className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
            tab === 'cronograma'
              ? 'border-blue-600 text-blue-600'
              : 'border-transparent text-gray-500 hover:text-gray-800'
          }`}
        >
          Cronograma
        </button>
      </div>

      {/* Body */}
      {tab === 'planilha' && (
        <div className="flex flex-1 overflow-hidden p-4 gap-4">
          <PlanilhaTabela versaoId={numVersaoId} isReadOnly={isReadOnly} />
          <PainelLateral isReadOnly={isReadOnly} />
        </div>
      )}
      {tab === 'cronograma' && (
        <div className="flex flex-1 overflow-hidden">
          <CronogramaTab versaoId={numVersaoId} isReadOnly={isReadOnly} />
        </div>
      )}

      {/* Footer totals */}
      <div className="flex items-center justify-end gap-6 px-6 py-2 bg-white border-t border-gray-200 text-sm shrink-0">
        <span className="text-gray-500">Total S/BDI: <span className="font-semibold text-gray-900">{fmtBRL(versao?.total_sem_bdi)}</span></span>
        <span className="text-gray-500">Total C/BDI: <span className="font-semibold text-blue-700">{fmtBRL(versao?.total_com_bdi)}</span></span>
      </div>

      <BDIModal
        open={bdiModalOpen}
        onOpenChange={setBdiModalOpen}
        versaoId={numVersaoId}
        obraId={numObraId}
      />
    </div>
  )
}
```

- [ ] **Step 2: Run TypeScript check**

```bash
cd /Users/vladimirirving/Desktop/OrçaAVML/frontend && npx tsc --noEmit
```

Expected: no errors.

- [ ] **Step 3: Run all frontend tests**

```bash
cd /Users/vladimirirving/Desktop/OrçaAVML/frontend && npm test -- --reporter=verbose
```

Expected: 4 passed (existing bdi utility tests — no new frontend tests for this module since the logic is in pure UI interactions and backend-tested endpoints).

- [ ] **Step 4: Run all backend tests**

```bash
docker compose exec backend pytest tests/backend/ -v
```

Expected: all tests pass (including the 8 new cronograma tests).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/PlanilhaPage.tsx
git commit -m "feat: PlanilhaPage adds Planilha/Cronograma tabs — Módulo 5 complete"
```
