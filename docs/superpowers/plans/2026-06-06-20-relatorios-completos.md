# Módulo 20 — Relatórios Completos: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expandir `/relatorios` em 3 subtabs funcionais: Curva ABC (visual + downloads), Medições (planejado × realizado por grupo) e Comparativo de Versões (diff item a item entre duas versões).

**Architecture:** Dois novos endpoints backend (`GET /versoes/{id}/relatorio-medicao` e `GET /obras/{id}/comparar`), ambos sem migration. Frontend refatorado com 3 componentes de aba independentes montados em `RelatoriosPage`. TDD obrigatório para os dois novos endpoints.

**Tech Stack:** FastAPI + SQLAlchemy async + PostgreSQL. React + TypeScript + Tailwind. Testes via pytest-asyncio + httpx AsyncClient.

---

## File Map

### Backend — novos
| Arquivo | Responsabilidade |
|---------|-----------------|
| `backend/app/schemas/relatorios.py` | `RelatorioMedicaoOut`, `RelatorioMedicaoGrupo`, `ComparativoOut`, `ComparativoItem` |
| `backend/app/routers/relatorios.py` | `GET /versoes/{id}/relatorio-medicao` + `GET /obras/{id}/comparar` |
| `tests/backend/test_relatorios.py` | 8 testes de integração |

### Backend — modificados
| Arquivo | Alteração |
|---------|-----------|
| `backend/app/main.py` | Registrar `relatorios_router` |

### Frontend — novos
| Arquivo | Responsabilidade |
|---------|-----------------|
| `frontend/src/api/relatorios.ts` | `getRelatorioMedicao`, `getComparativo` |
| `frontend/src/components/relatorios/CurvaAbcTab.tsx` | Tabela ABC com badges + downloads |
| `frontend/src/components/relatorios/MedicoesTab.tsx` | Tabela planejado × realizado |
| `frontend/src/components/relatorios/ComparativoTab.tsx` | Seletores de versão + diff table |

### Frontend — modificados
| Arquivo | Alteração |
|---------|-----------|
| `frontend/src/types.ts` | Adicionar `RelatorioMedicaoOut`, `RelatorioMedicaoGrupo`, `ComparativoOut`, `ComparativoItem` |
| `frontend/src/pages/RelatoriosPage.tsx` | Refatorar: 3 subtabs + seletor de obra compartilhado |

---

## Task 1: Backend Schemas

**Files:**
- Create: `backend/app/schemas/relatorios.py`

- [ ] **Step 1: Criar schemas**

```python
# backend/app/schemas/relatorios.py
from datetime import date
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel


class RelatorioMedicaoGrupo(BaseModel):
    grupo_id: int
    grupo_nome: str
    planejado_pct: float
    realizado_pct: float
    desvio_pct: float
    valor_medido: Decimal
    valor_total: Decimal


class RelatorioMedicaoOut(BaseModel):
    versao_id: int
    ultima_medicao_id: Optional[int]
    periodo_fim: Optional[date]
    grupos: List[RelatorioMedicaoGrupo]


class ComparativoItem(BaseModel):
    status: Literal["novo", "removido", "alterado", "igual"]
    grupo_nome: str
    descricao: str
    unidade: str
    v1_preco_unit: Optional[Decimal]
    v2_preco_unit: Optional[Decimal]
    v1_quantidade: Optional[Decimal]
    v2_quantidade: Optional[Decimal]
    v1_total: Optional[Decimal]
    v2_total: Optional[Decimal]
    delta_total: Decimal


class ComparativoOut(BaseModel):
    obra_id: int
    v1_id: int
    v2_id: int
    v1_nome: str
    v2_nome: str
    v1_total: Decimal
    v2_total: Decimal
    delta_total: Decimal
    delta_pct: float
    qtd_novos: int
    qtd_removidos: int
    qtd_alterados: int
    itens: List[ComparativoItem]
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/schemas/relatorios.py
git commit -m "feat: schemas RelatorioMedicaoOut + ComparativoOut"
```

---

## Task 2: Backend Router — relatorio-medicao + Testes

**Files:**
- Create: `backend/app/routers/relatorios.py`
- Create: `tests/backend/test_relatorios.py`
- Modify: `backend/app/main.py`

- [ ] **Step 1: Escrever testes (TDD)**

```python
# tests/backend/test_relatorios.py
import pytest
from decimal import Decimal as D
from httpx import AsyncClient
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.cronograma_linha import CronogramaLinha
from app.models.medicao import Medicao
from datetime import date


@pytest.mark.asyncio
async def test_relatorio_medicao_sem_medicoes(
    client: AsyncClient, auth_headers: dict, versao_ativa, db_session
):
    """Sem medições: realizado_pct = 0 para todos os grupos."""
    grupo = Grupo(versao_id=versao_ativa.id, nome="Terraplenagem", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, quantidade=D("100"), unidade="M3",
        preco_unitario_sem_bdi=D("50"), preco_unitario_com_bdi=D("55"),
    )
    db_session.add(item)
    await db_session.flush()

    r = await client.get(
        f"/versoes/{versao_ativa.id}/relatorio-medicao",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ultima_medicao_id"] is None
    assert len(data["grupos"]) == 1
    assert data["grupos"][0]["grupo_nome"] == "Terraplenagem"
    assert data["grupos"][0]["realizado_pct"] == 0.0


@pytest.mark.asyncio
async def test_relatorio_medicao_com_medicao(
    client: AsyncClient, auth_headers: dict, versao_ativa, db_session
):
    """Com medição: realizado_pct e valor_medido corretos."""
    grupo = Grupo(versao_id=versao_ativa.id, nome="Pavimentação", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, quantidade=D("200"), unidade="T",
        preco_unitario_sem_bdi=D("300"), preco_unitario_com_bdi=D("330"),
    )
    db_session.add(item)
    await db_session.flush()

    medicao = Medicao(
        versao_id=versao_ativa.id,
        periodo_inicio=date(2026, 5, 1),
        periodo_fim=date(2026, 5, 31),
        linhas_json={str(item.id): 40.0},
    )
    db_session.add(medicao)
    await db_session.flush()

    r = await client.get(
        f"/versoes/{versao_ativa.id}/relatorio-medicao",
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["ultima_medicao_id"] == medicao.id
    g = data["grupos"][0]
    assert g["realizado_pct"] == pytest.approx(40.0)
    # valor_medido = item.total (200*300=60000) * 40/100 = 24000
    assert float(g["valor_medido"]) == pytest.approx(24000.0)


@pytest.mark.asyncio
async def test_relatorio_medicao_tenant_isolation(
    client: AsyncClient, versao_ativa, db_session
):
    """Versão de outra empresa → 404."""
    from app.models.empresa import Empresa
    from app.models.usuario import Usuario
    from app.services.auth_service import hash_password, create_access_token

    empresa_b = Empresa(nome="Outra Empresa", cnpj="11.111.111/0001-11")
    db_session.add(empresa_b)
    await db_session.flush()
    user_b = Usuario(
        empresa_id=empresa_b.id, nome="B", email="b2@b.com",
        senha_hash=hash_password("x"), papel="admin",
    )
    db_session.add(user_b)
    await db_session.flush()
    token_b = create_access_token({"sub": str(user_b.id), "papel": "admin", "empresa_id": empresa_b.id})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    r = await client.get(
        f"/versoes/{versao_ativa.id}/relatorio-medicao",
        headers=headers_b,
    )
    assert r.status_code == 404
```

- [ ] **Step 2: Rodar testes — devem falhar**

```bash
docker exec -w /app -e PYTHONPATH=/app orcaavml-backend-1 \
  python -m pytest tests/backend/test_relatorios.py -v 2>&1 | tail -10
```

Esperado: ImportError ou 404s (router não existe ainda).

- [ ] **Step 3: Criar router com endpoint relatorio-medicao**

```python
# backend/app/routers/relatorios.py
from datetime import datetime
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.dependencies import get_current_user
from app.models.cronograma_linha import CronogramaLinha
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.medicao import Medicao
from app.models.obra import Obra
from app.models.usuario import Usuario
from app.models.versao import Versao
from app.schemas.relatorios import (
    ComparativoItem, ComparativoOut,
    RelatorioMedicaoGrupo, RelatorioMedicaoOut,
)

router = APIRouter(tags=["relatorios"])


async def _get_versao(versao_id: int, current_user: Usuario, db: AsyncSession) -> Versao:
    result = await db.execute(
        select(Versao)
        .join(Obra, Versao.obra_id == Obra.id)
        .where(Versao.id == versao_id, Obra.empresa_id == current_user.empresa_id)
    )
    v = result.scalar_one_or_none()
    if v is None:
        raise HTTPException(status_code=404, detail="Versão não encontrada")
    return v


@router.get("/versoes/{versao_id}/relatorio-medicao", response_model=RelatorioMedicaoOut)
async def get_relatorio_medicao(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao(versao_id, current_user, db)

    # Grupos raiz da versão
    grupos_r = await db.execute(
        select(Grupo).where(Grupo.versao_id == versao_id, Grupo.pai_id.is_(None))
    )
    grupos_raiz = grupos_r.scalars().all()
    grupos_raiz_ids = {g.id for g in grupos_raiz}

    # Todos os grupos da versão (para resolver subgrupo → raiz)
    todos_grupos_r = await db.execute(
        select(Grupo).where(Grupo.versao_id == versao_id)
    )
    todos_grupos = {g.id: g for g in todos_grupos_r.scalars().all()}

    # Todos os itens da versão com grupo e cronograma_linha
    todos_itens_r = await db.execute(
        select(Item)
        .join(Grupo, Item.grupo_id == Grupo.id)
        .where(Grupo.versao_id == versao_id)
        .options(selectinload(Item.grupo), selectinload(Item.cronograma_linha))
    )
    todos_itens = todos_itens_r.scalars().all()

    # Última medição: MAX(periodo_fim), desempate por MAX(id)
    med_r = await db.execute(
        select(Medicao)
        .where(Medicao.versao_id == versao_id)
        .order_by(Medicao.periodo_fim.desc(), Medicao.id.desc())
        .limit(1)
    )
    ultima_medicao = med_r.scalar_one_or_none()
    linhas_json: dict = ultima_medicao.linhas_json if ultima_medicao else {}

    # Mês atual no formato YYYY-MM
    mes_atual = datetime.now().strftime("%Y-%m")

    # Agrupar itens por grupo raiz (subgrupo → pai)
    itens_por_grupo: dict[int, list[Item]] = {g.id: [] for g in grupos_raiz}
    for item in todos_itens:
        g = todos_grupos.get(item.grupo_id)
        if g is None:
            continue
        raiz_id = g.id if g.pai_id is None else (g.pai_id if g.pai_id in grupos_raiz_ids else None)
        if raiz_id is not None:
            itens_por_grupo.setdefault(raiz_id, []).append(item)

    resultado = []
    for grupo in sorted(grupos_raiz, key=lambda g: g.ordem):
        itens_grupo = itens_por_grupo.get(grupo.id, [])
        if not itens_grupo:
            continue

        total_grupo = sum(float(i.total) for i in itens_grupo)

        # planejado_pct: média ponderada pelo total do item
        planejado_num = 0.0
        planejado_den = 0.0
        for item in itens_grupo:
            peso = float(item.total)
            if item.cronograma_linha and peso > 0:
                dist = item.cronograma_linha.distribuicao_json or {}
                pct = sum(v for k, v in dist.items() if k <= mes_atual)
                planejado_num += pct * peso
                planejado_den += peso
        planejado_pct = planejado_num / planejado_den if planejado_den > 0 else 0.0

        # realizado_pct: média ponderada pelo total do item
        realizado_num = 0.0
        realizado_den = 0.0
        for item in itens_grupo:
            peso = float(item.total)
            pct = float(linhas_json.get(str(item.id), 0))
            if peso > 0:
                realizado_num += pct * peso
                realizado_den += peso
        realizado_pct = realizado_num / realizado_den if realizado_den > 0 else 0.0

        valor_medido = Decimal(str(round(sum(
            float(i.total) * float(linhas_json.get(str(i.id), 0)) / 100
            for i in itens_grupo
        ), 2)))

        resultado.append(RelatorioMedicaoGrupo(
            grupo_id=grupo.id,
            grupo_nome=grupo.nome,
            planejado_pct=round(planejado_pct, 2),
            realizado_pct=round(realizado_pct, 2),
            desvio_pct=round(realizado_pct - planejado_pct, 2),
            valor_medido=valor_medido,
            valor_total=Decimal(str(round(total_grupo, 2))),
        ))

    return RelatorioMedicaoOut(
        versao_id=versao_id,
        ultima_medicao_id=ultima_medicao.id if ultima_medicao else None,
        periodo_fim=ultima_medicao.periodo_fim if ultima_medicao else None,
        grupos=resultado,
    )
```

- [ ] **Step 4: Registrar router em `main.py`**

Adicionar ao final dos imports:
```python
from app.routers.relatorios import router as relatorios_router
```

Adicionar ao final dos `app.include_router(...)`:
```python
app.include_router(relatorios_router)
```

- [ ] **Step 5: Rodar testes de relatorio-medicao**

```bash
docker exec -w /app -e PYTHONPATH=/app orcaavml-backend-1 \
  python -m pytest tests/backend/test_relatorios.py::test_relatorio_medicao_sem_medicoes \
                   tests/backend/test_relatorios.py::test_relatorio_medicao_com_medicao \
                   tests/backend/test_relatorios.py::test_relatorio_medicao_tenant_isolation \
                   -v 2>&1 | tail -15
```

Esperado: 3 PASS.

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/relatorios.py backend/app/main.py \
        tests/backend/test_relatorios.py
git commit -m "feat: GET /versoes/{id}/relatorio-medicao + testes"
```

---

## Task 3: Backend Router — Comparativo de Versões + Testes

**Files:**
- Modify: `backend/app/routers/relatorios.py` (adicionar endpoint)
- Modify: `tests/backend/test_relatorios.py` (adicionar testes)

- [ ] **Step 1: Adicionar testes do comparativo**

Adicionar ao final de `tests/backend/test_relatorios.py`:

```python
@pytest.mark.asyncio
async def test_comparativo_item_novo(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa,
    composicao_sinapi, db_session
):
    """Item em V2 sem par em V1 → status 'novo'."""
    from app.models.versao import Versao
    v2 = Versao(obra_id=obra.id, numero=2, bloqueada=False)
    db_session.add(v2)
    await db_session.flush()

    # V1: sem itens com composicao_sinapi
    g1 = Grupo(versao_id=versao_ativa.id, nome="Terraplenagem", ordem=0)
    db_session.add(g1)
    await db_session.flush()

    # V2: com item usando composicao_sinapi
    g2 = Grupo(versao_id=v2.id, nome="Terraplenagem", ordem=0)
    db_session.add(g2)
    await db_session.flush()
    item2 = Item(
        grupo_id=g2.id, composicao_id=composicao_sinapi.id,
        quantidade=D("100"), unidade="M3",
        preco_unitario_sem_bdi=D("45.23"), preco_unitario_com_bdi=D("50"),
    )
    db_session.add(item2)
    await db_session.flush()

    r = await client.get(
        f"/obras/{obra.id}/comparar",
        params={"v1": versao_ativa.id, "v2": v2.id},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["qtd_novos"] == 1
    assert data["qtd_removidos"] == 0
    novos = [i for i in data["itens"] if i["status"] == "novo"]
    assert len(novos) == 1
    assert novos[0]["v1_preco_unit"] is None


@pytest.mark.asyncio
async def test_comparativo_item_removido(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa,
    composicao_sinapi, db_session
):
    """Item em V1 sem par em V2 → status 'removido'."""
    from app.models.versao import Versao
    v2 = Versao(obra_id=obra.id, numero=2, bloqueada=False)
    db_session.add(v2)
    await db_session.flush()

    # V1: com item
    g1 = Grupo(versao_id=versao_ativa.id, nome="Pavimentação", ordem=0)
    db_session.add(g1)
    await db_session.flush()
    item1 = Item(
        grupo_id=g1.id, composicao_id=composicao_sinapi.id,
        quantidade=D("200"), unidade="T",
        preco_unitario_sem_bdi=D("300"), preco_unitario_com_bdi=D("330"),
    )
    db_session.add(item1)
    await db_session.flush()

    # V2: sem itens
    g2 = Grupo(versao_id=v2.id, nome="Pavimentação", ordem=0)
    db_session.add(g2)
    await db_session.flush()

    r = await client.get(
        f"/obras/{obra.id}/comparar",
        params={"v1": versao_ativa.id, "v2": v2.id},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["qtd_removidos"] == 1
    removidos = [i for i in data["itens"] if i["status"] == "removido"]
    assert removidos[0]["v2_preco_unit"] is None


@pytest.mark.asyncio
async def test_comparativo_preco_alterado(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa,
    composicao_sinapi, db_session
):
    """Mesmo composicao_id, preço diferente → status 'alterado'."""
    from app.models.versao import Versao
    v2 = Versao(obra_id=obra.id, numero=2, bloqueada=False)
    db_session.add(v2)
    await db_session.flush()

    g1 = Grupo(versao_id=versao_ativa.id, nome="Drenagem", ordem=0)
    g2 = Grupo(versao_id=v2.id, nome="Drenagem", ordem=0)
    db_session.add_all([g1, g2])
    await db_session.flush()

    item1 = Item(
        grupo_id=g1.id, composicao_id=composicao_sinapi.id,
        quantidade=D("50"), unidade="M3",
        preco_unitario_sem_bdi=D("45.00"), preco_unitario_com_bdi=D("49.50"),
    )
    item2 = Item(
        grupo_id=g2.id, composicao_id=composicao_sinapi.id,
        quantidade=D("50"), unidade="M3",
        preco_unitario_sem_bdi=D("50.00"), preco_unitario_com_bdi=D("55.00"),
    )
    db_session.add_all([item1, item2])
    await db_session.flush()

    r = await client.get(
        f"/obras/{obra.id}/comparar",
        params={"v1": versao_ativa.id, "v2": v2.id},
        headers=auth_headers,
    )
    assert r.status_code == 200
    data = r.json()
    assert data["qtd_alterados"] == 1
    alt = [i for i in data["itens"] if i["status"] == "alterado"][0]
    assert float(alt["v1_preco_unit"]) == pytest.approx(45.0)
    assert float(alt["v2_preco_unit"]) == pytest.approx(50.0)
    # delta_total = (50*50) - (50*45) = 2500 - 2250 = 250
    assert float(alt["delta_total"]) == pytest.approx(250.0)


@pytest.mark.asyncio
async def test_comparativo_versoes_de_obras_diferentes(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa,
    empresa, db_session
):
    """V1 e V2 de obras distintas → 400."""
    outra_obra = Obra(
        empresa_id=empresa.id, nome="Outra Obra", tipo_obra="rodovia",
        estado="em_elaboracao", data_criacao=date.today(),
    )
    db_session.add(outra_obra)
    await db_session.flush()
    from app.models.versao import Versao
    v_outra = Versao(obra_id=outra_obra.id, numero=1, bloqueada=False)
    db_session.add(v_outra)
    await db_session.flush()

    r = await client.get(
        f"/obras/{obra.id}/comparar",
        params={"v1": versao_ativa.id, "v2": v_outra.id},
        headers=auth_headers,
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_comparativo_tenant_isolation(
    client: AsyncClient, obra, versao_ativa, db_session
):
    """Obra de outra empresa → 404."""
    from app.models.empresa import Empresa
    from app.models.usuario import Usuario
    from app.models.versao import Versao
    from app.services.auth_service import hash_password, create_access_token

    empresa_b = Empresa(nome="Empresa C", cnpj="22.222.222/0001-22")
    db_session.add(empresa_b)
    await db_session.flush()
    user_b = Usuario(
        empresa_id=empresa_b.id, nome="C", email="c3@c.com",
        senha_hash=hash_password("x"), papel="admin",
    )
    db_session.add(user_b)
    await db_session.flush()
    token_b = create_access_token({"sub": str(user_b.id), "papel": "admin", "empresa_id": empresa_b.id})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    v2 = Versao(obra_id=obra.id, numero=2, bloqueada=False)
    db_session.add(v2)
    await db_session.flush()

    r = await client.get(
        f"/obras/{obra.id}/comparar",
        params={"v1": versao_ativa.id, "v2": v2.id},
        headers=headers_b,
    )
    assert r.status_code == 404
```

- [ ] **Step 2: Rodar testes do comparativo — devem falhar**

```bash
docker exec -w /app -e PYTHONPATH=/app orcaavml-backend-1 \
  python -m pytest tests/backend/test_relatorios.py::test_comparativo_item_novo -v 2>&1 | tail -5
```

Esperado: 404 (endpoint não existe).

- [ ] **Step 3: Adicionar endpoint `comparar` ao router**

Adicionar ao final de `backend/app/routers/relatorios.py`:

```python
@router.get("/obras/{obra_id}/comparar", response_model=ComparativoOut)
async def comparar_versoes(
    obra_id: int,
    v1: int = Query(...),
    v2: int = Query(...),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Verificar que a obra pertence à empresa
    obra_r = await db.execute(
        select(Obra).where(Obra.id == obra_id, Obra.empresa_id == current_user.empresa_id)
    )
    obra = obra_r.scalar_one_or_none()
    if obra is None:
        raise HTTPException(status_code=404, detail="Obra não encontrada")

    # Carregar as duas versões
    def _load_versao(vid: int):
        return db.execute(
            select(Versao)
            .where(Versao.id == vid, Versao.obra_id == obra_id)
        )

    versao1_r = await _load_versao(v1)
    versao1 = versao1_r.scalar_one_or_none()
    versao2_r = await _load_versao(v2)
    versao2 = versao2_r.scalar_one_or_none()

    if versao1 is None or versao2 is None:
        raise HTTPException(status_code=400, detail="Uma ou ambas as versões não pertencem a esta obra")

    # Carregar itens de cada versão
    async def _get_itens_versao(versao_id: int) -> list[Item]:
        r = await db.execute(
            select(Item)
            .join(Grupo, Item.grupo_id == Grupo.id)
            .where(Grupo.versao_id == versao_id)
            .options(selectinload(Item.grupo), selectinload(Item.composicao))
        )
        return r.scalars().all()

    itens_v1 = await _get_itens_versao(v1)
    itens_v2 = await _get_itens_versao(v2)

    # Indexar por composicao_id
    v1_map: dict[int, Item] = {}
    v1_sem_comp: list[Item] = []
    for item in itens_v1:
        if item.composicao_id is not None:
            v1_map[item.composicao_id] = item
        else:
            v1_sem_comp.append(item)

    v2_map: dict[int, Item] = {}
    v2_sem_comp: list[Item] = []
    for item in itens_v2:
        if item.composicao_id is not None:
            v2_map[item.composicao_id] = item
        else:
            v2_sem_comp.append(item)

    def _descricao(item: Item) -> str:
        if item.composicao:
            return item.composicao.descricao
        return "Item sem composição"

    def _unidade(item: Item) -> str:
        return item.unidade

    itens_resultado: list[ComparativoItem] = []

    # Itens de V1 (comparar com V2)
    todas_comp_ids = set(v1_map.keys()) | set(v2_map.keys())
    for comp_id in todas_comp_ids:
        i1 = v1_map.get(comp_id)
        i2 = v2_map.get(comp_id)

        if i1 and i2:
            # Presente em ambos — alterado ou igual
            preco_diff = i1.preco_unitario_sem_bdi != i2.preco_unitario_sem_bdi
            qtd_diff = i1.quantidade != i2.quantidade
            status = "alterado" if (preco_diff or qtd_diff) else "igual"
            t1 = i1.total or Decimal("0")
            t2 = i2.total or Decimal("0")
            itens_resultado.append(ComparativoItem(
                status=status,
                grupo_nome=i2.grupo.nome,
                descricao=_descricao(i2),
                unidade=_unidade(i2),
                v1_preco_unit=i1.preco_unitario_sem_bdi,
                v2_preco_unit=i2.preco_unitario_sem_bdi,
                v1_quantidade=i1.quantidade,
                v2_quantidade=i2.quantidade,
                v1_total=t1,
                v2_total=t2,
                delta_total=t2 - t1,
            ))
        elif i1 and not i2:
            # Removido
            t1 = i1.total or Decimal("0")
            itens_resultado.append(ComparativoItem(
                status="removido",
                grupo_nome=i1.grupo.nome,
                descricao=_descricao(i1),
                unidade=_unidade(i1),
                v1_preco_unit=i1.preco_unitario_sem_bdi,
                v2_preco_unit=None,
                v1_quantidade=i1.quantidade,
                v2_quantidade=None,
                v1_total=t1,
                v2_total=None,
                delta_total=-t1,
            ))
        elif not i1 and i2:
            # Novo
            t2 = i2.total or Decimal("0")
            itens_resultado.append(ComparativoItem(
                status="novo",
                grupo_nome=i2.grupo.nome,
                descricao=_descricao(i2),
                unidade=_unidade(i2),
                v1_preco_unit=None,
                v2_preco_unit=i2.preco_unitario_sem_bdi,
                v1_quantidade=None,
                v2_quantidade=i2.quantidade,
                v1_total=None,
                v2_total=t2,
                delta_total=t2,
            ))

    # Itens sem composicao_id
    for item in v1_sem_comp:
        t1 = item.total or Decimal("0")
        itens_resultado.append(ComparativoItem(
            status="removido",
            grupo_nome=item.grupo.nome,
            descricao=_descricao(item),
            unidade=_unidade(item),
            v1_preco_unit=item.preco_unitario_sem_bdi,
            v2_preco_unit=None,
            v1_quantidade=item.quantidade,
            v2_quantidade=None,
            v1_total=t1,
            v2_total=None,
            delta_total=-t1,
        ))
    for item in v2_sem_comp:
        t2 = item.total or Decimal("0")
        itens_resultado.append(ComparativoItem(
            status="novo",
            grupo_nome=item.grupo.nome,
            descricao=_descricao(item),
            unidade=_unidade(item),
            v1_preco_unit=None,
            v2_preco_unit=item.preco_unitario_sem_bdi,
            v1_quantidade=None,
            v2_quantidade=item.quantidade,
            v1_total=None,
            v2_total=t2,
            delta_total=t2,
        ))

    total_v1 = versao1.total_sem_bdi or Decimal("0")
    total_v2 = versao2.total_sem_bdi or Decimal("0")
    delta = total_v2 - total_v1
    delta_pct = float(delta / total_v1 * 100) if total_v1 != 0 else 0.0

    return ComparativoOut(
        obra_id=obra_id,
        v1_id=v1,
        v2_id=v2,
        v1_nome=f"Versão {versao1.numero}" + (f" — {versao1.nome}" if versao1.nome else ""),
        v2_nome=f"Versão {versao2.numero}" + (f" — {versao2.nome}" if versao2.nome else ""),
        v1_total=total_v1,
        v2_total=total_v2,
        delta_total=delta,
        delta_pct=round(delta_pct, 2),
        qtd_novos=sum(1 for i in itens_resultado if i.status == "novo"),
        qtd_removidos=sum(1 for i in itens_resultado if i.status == "removido"),
        qtd_alterados=sum(1 for i in itens_resultado if i.status == "alterado"),
        itens=itens_resultado,
    )
```

Também adicionar o import de `Obra` na parte superior do arquivo (já está) e garantir que `Query` está importado:
```python
from fastapi import APIRouter, Depends, HTTPException, Query
```

- [ ] **Step 4: Rodar todos os testes de relatorios**

```bash
docker exec -w /app -e PYTHONPATH=/app orcaavml-backend-1 \
  python -m pytest tests/backend/test_relatorios.py -v 2>&1 | tail -20
```

Esperado: 8 PASS.

- [ ] **Step 5: Rodar suite completa**

```bash
docker exec -w /app -e PYTHONPATH=/app orcaavml-backend-1 \
  python -m pytest tests/backend/ -q 2>&1 | tail -5
```

Esperado: todos PASS (≥ 184 testes).

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/relatorios.py tests/backend/test_relatorios.py
git commit -m "feat: GET /obras/{id}/comparar — diff de versões + testes"
```

---

## Task 4: Frontend — Tipos + API

**Files:**
- Modify: `frontend/src/types.ts`
- Create: `frontend/src/api/relatorios.ts`

- [ ] **Step 1: Adicionar tipos em `types.ts`**

Adicionar ao final de `frontend/src/types.ts`:

```typescript
export interface RelatorioMedicaoGrupo {
  grupo_id: number
  grupo_nome: string
  planejado_pct: number
  realizado_pct: number
  desvio_pct: number
  valor_medido: string
  valor_total: string
}

export interface RelatorioMedicaoOut {
  versao_id: number
  ultima_medicao_id: number | null
  periodo_fim: string | null
  grupos: RelatorioMedicaoGrupo[]
}

export interface ComparativoItem {
  status: 'novo' | 'removido' | 'alterado' | 'igual'
  grupo_nome: string
  descricao: string
  unidade: string
  v1_preco_unit: string | null
  v2_preco_unit: string | null
  v1_quantidade: string | null
  v2_quantidade: string | null
  v1_total: string | null
  v2_total: string | null
  delta_total: string
}

export interface ComparativoOut {
  obra_id: number
  v1_id: number
  v2_id: number
  v1_nome: string
  v2_nome: string
  v1_total: string
  v2_total: string
  delta_total: string
  delta_pct: number
  qtd_novos: number
  qtd_removidos: number
  qtd_alterados: number
  itens: ComparativoItem[]
}
```

- [ ] **Step 2: Criar `api/relatorios.ts`**

```typescript
// frontend/src/api/relatorios.ts
import { api } from '@/api/client'
import type { RelatorioMedicaoOut, ComparativoOut } from '@/types'

export const getRelatorioMedicao = (versaoId: number): Promise<RelatorioMedicaoOut> =>
  api.get<RelatorioMedicaoOut>(`/versoes/${versaoId}/relatorio-medicao`).then(r => r.data)

export const getComparativo = (
  obraId: number,
  v1: number,
  v2: number,
): Promise<ComparativoOut> =>
  api
    .get<ComparativoOut>(`/obras/${obraId}/comparar`, { params: { v1, v2 } })
    .then(r => r.data)
```

- [ ] **Step 3: TypeCheck**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -10
```

Esperado: sem erros.

- [ ] **Step 4: Commit**

```bash
cd /Users/vladimirirving/Desktop/orcaavml && \
git add frontend/src/types.ts frontend/src/api/relatorios.ts && \
git commit -m "feat: tipos RelatorioMedicao/Comparativo + api/relatorios.ts"
```

---

## Task 5: CurvaAbcTab

**Files:**
- Create: `frontend/src/components/relatorios/CurvaAbcTab.tsx`

- [ ] **Step 1: Criar componente**

```tsx
// frontend/src/components/relatorios/CurvaAbcTab.tsx
import { useEffect, useState } from 'react'
import { getCurvaAbc, downloadCurvaAbcExcel } from '@/api/curvaAbc'
import { downloadPropostaPdf } from '@/api/proposta'
import { toast } from '@/hooks/useToast'
import type { CurvaAbcData, Versao } from '@/types'

const FAIXA_COLORS = {
  A: 'bg-green-100 text-green-800',
  B: 'bg-yellow-100 text-yellow-800',
  C: 'bg-red-100 text-red-800',
}

interface Props {
  versao: Versao | null
}

export default function CurvaAbcTab({ versao }: Props) {
  const [data, setData] = useState<CurvaAbcData | null>(null)
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState<'excel' | 'pdf' | null>(null)

  useEffect(() => {
    if (!versao) { setData(null); return }
    setLoading(true)
    getCurvaAbc(versao.id)
      .then(setData)
      .catch(() => toast('Erro ao carregar Curva ABC', 'error'))
      .finally(() => setLoading(false))
  }, [versao?.id])

  if (!versao) {
    return <p className="text-gray-400 text-sm py-8 text-center">Selecione uma obra para ver a Curva ABC.</p>
  }

  if (loading) return <p className="text-gray-400 text-sm py-8 text-center">Carregando…</p>

  if (!data || data.itens.length === 0) {
    return <p className="text-gray-400 text-sm py-8 text-center">Nenhum item com valor na versão ativa.</p>
  }

  const resumo = (['A', 'B', 'C'] as const).map(faixa => ({
    faixa,
    qtd: data.itens.filter(i => i.faixa === faixa).length,
    pct: data.itens.filter(i => i.faixa === faixa).reduce((s, i) => s + i.participacao_pct, 0),
  }))

  async function handleDownloadExcel() {
    if (!versao) return
    setDownloading('excel')
    try { await downloadCurvaAbcExcel(versao.id) }
    catch { toast('Erro ao baixar Excel', 'error') }
    finally { setDownloading(null) }
  }

  async function handleDownloadPdf() {
    if (!versao) return
    setDownloading('pdf')
    try { await downloadPropostaPdf(versao.id) }
    catch (e: any) {
      if (e?.response?.status === 404) toast('Proposta não configurada', 'error')
      else toast('Erro ao baixar PDF', 'error')
    }
    finally { setDownloading(null) }
  }

  return (
    <div className="space-y-4">
      {/* Resumo por faixa */}
      <div className="flex gap-3">
        {resumo.map(({ faixa, qtd, pct }) => (
          <div key={faixa} className={`rounded-lg px-4 py-2 text-sm font-semibold ${FAIXA_COLORS[faixa]}`}>
            {faixa} — {qtd} {qtd === 1 ? 'serviço' : 'serviços'} · {pct.toFixed(1)}%
          </div>
        ))}
      </div>

      {/* Tabela */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-2 font-medium text-gray-600 w-8">#</th>
              <th className="text-left px-4 py-2 font-medium text-gray-600">Grupo</th>
              <th className="text-left px-4 py-2 font-medium text-gray-600">Serviço</th>
              <th className="text-left px-4 py-2 font-medium text-gray-600 w-16">Unid.</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600 w-28">Total</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600 w-20">Part%</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600 w-20">Acum%</th>
              <th className="text-center px-4 py-2 font-medium text-gray-600 w-16">Classe</th>
            </tr>
          </thead>
          <tbody>
            {data.itens.map((item, idx) => (
              <tr key={item.rank} className={`border-t border-gray-100 ${idx % 2 === 1 ? 'bg-gray-50/50' : ''}`}>
                <td className="px-4 py-2 text-gray-400">{item.rank}</td>
                <td className="px-4 py-2 text-gray-600 truncate max-w-[120px]">{item.grupo_nome}</td>
                <td className="px-4 py-2 truncate max-w-[280px]">{item.descricao}</td>
                <td className="px-4 py-2 text-gray-500">{item.unidade}</td>
                <td className="px-4 py-2 text-right font-mono text-xs">
                  R$ {parseFloat(item.total).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </td>
                <td className="px-4 py-2 text-right">{item.participacao_pct.toFixed(2)}%</td>
                <td className="px-4 py-2 text-right">{item.acumulado_pct.toFixed(2)}%</td>
                <td className="px-4 py-2 text-center">
                  <span className={`text-xs font-bold px-2 py-0.5 rounded ${FAIXA_COLORS[item.faixa]}`}>
                    {item.faixa}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Downloads */}
      <div className="flex gap-2">
        <button
          onClick={handleDownloadExcel}
          disabled={downloading === 'excel'}
          className="text-sm px-3 py-1.5 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-40"
        >
          {downloading === 'excel' ? 'Baixando…' : '↓ Excel'}
        </button>
        <button
          onClick={handleDownloadPdf}
          disabled={downloading === 'pdf'}
          className="text-sm px-3 py-1.5 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-40"
        >
          {downloading === 'pdf' ? 'Baixando…' : '↓ Proposta PDF'}
        </button>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: TypeCheck**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -10
```

Esperado: sem erros.

- [ ] **Step 3: Commit**

```bash
cd /Users/vladimirirving/Desktop/orcaavml && \
git add frontend/src/components/relatorios/CurvaAbcTab.tsx && \
git commit -m "feat: CurvaAbcTab — tabela ABC com badges e downloads"
```

---

## Task 6: MedicoesTab

**Files:**
- Create: `frontend/src/components/relatorios/MedicoesTab.tsx`

- [ ] **Step 1: Criar componente**

```tsx
// frontend/src/components/relatorios/MedicoesTab.tsx
import { useEffect, useState } from 'react'
import { getRelatorioMedicao } from '@/api/relatorios'
import { toast } from '@/hooks/useToast'
import { fmtBRL } from '@/lib/utils'
import type { RelatorioMedicaoOut, Versao } from '@/types'

interface Props {
  versao: Versao | null
}

export default function MedicoesTab({ versao }: Props) {
  const [data, setData] = useState<RelatorioMedicaoOut | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!versao) { setData(null); return }
    setLoading(true)
    getRelatorioMedicao(versao.id)
      .then(setData)
      .catch(() => toast('Erro ao carregar relatório de medições', 'error'))
      .finally(() => setLoading(false))
  }, [versao?.id])

  if (!versao) {
    return <p className="text-gray-400 text-sm py-8 text-center">Selecione uma obra para ver as medições.</p>
  }

  if (loading) return <p className="text-gray-400 text-sm py-8 text-center">Carregando…</p>

  if (!data || data.grupos.length === 0) {
    return <p className="text-gray-400 text-sm py-8 text-center">Nenhum grupo com itens na versão ativa.</p>
  }

  return (
    <div className="space-y-4">
      {data.ultima_medicao_id === null && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-700">
          Nenhuma medição registrada — percentuais realizados exibidos como 0%.
        </div>
      )}
      {data.periodo_fim && (
        <p className="text-xs text-gray-500">
          Baseado na medição de{' '}
          <strong>{new Date(data.periodo_fim + 'T12:00:00').toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}</strong>
        </p>
      )}

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-2 font-medium text-gray-600">Grupo</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600 w-28">Planejado %</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600 w-28">Realizado %</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600 w-24">Desvio</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600 w-36">Valor medido</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600 w-36">Total grupo</th>
            </tr>
          </thead>
          <tbody>
            {data.grupos.map((grupo, idx) => {
              const desvio = grupo.desvio_pct
              return (
                <tr key={grupo.grupo_id} className={`border-t border-gray-100 ${idx % 2 === 1 ? 'bg-gray-50/50' : ''}`}>
                  <td className="px-4 py-2 font-medium">{grupo.grupo_nome}</td>
                  <td className="px-4 py-2 text-right text-gray-600">{grupo.planejado_pct.toFixed(1)}%</td>
                  <td className="px-4 py-2 text-right">{grupo.realizado_pct.toFixed(1)}%</td>
                  <td className={`px-4 py-2 text-right font-semibold ${desvio > 0 ? 'text-green-600' : desvio < 0 ? 'text-red-600' : 'text-gray-400'}`}>
                    {desvio > 0 ? '+' : ''}{desvio.toFixed(1)}%
                  </td>
                  <td className="px-4 py-2 text-right font-mono text-xs">{fmtBRL(parseFloat(grupo.valor_medido))}</td>
                  <td className="px-4 py-2 text-right font-mono text-xs text-gray-500">{fmtBRL(parseFloat(grupo.valor_total))}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: TypeCheck**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -10
```

Esperado: sem erros.

- [ ] **Step 3: Commit**

```bash
cd /Users/vladimirirving/Desktop/orcaavml && \
git add frontend/src/components/relatorios/MedicoesTab.tsx && \
git commit -m "feat: MedicoesTab — planejado × realizado por grupo"
```

---

## Task 7: ComparativoTab

**Files:**
- Create: `frontend/src/components/relatorios/ComparativoTab.tsx`

- [ ] **Step 1: Verificar como getVersoes funciona**

```bash
grep -n "getVersoes" /Users/vladimirirving/Desktop/orcaavml/frontend/src/api/obras.ts
```

Esperado: `export const getVersoes = (obraId: number) => api.get<Versao[]>(...)`

- [ ] **Step 2: Criar componente**

```tsx
// frontend/src/components/relatorios/ComparativoTab.tsx
import { useEffect, useState } from 'react'
import { getVersoes } from '@/api/obras'
import { getComparativo } from '@/api/relatorios'
import { toast } from '@/hooks/useToast'
import { fmtBRL } from '@/lib/utils'
import type { ComparativoOut, Obra, Versao } from '@/types'

const STATUS_COLORS: Record<string, string> = {
  novo: 'bg-green-50',
  removido: 'bg-orange-50',
  alterado: '',
  igual: '',
}

const STATUS_BADGES: Record<string, string> = {
  novo: 'bg-green-100 text-green-800',
  removido: 'bg-orange-100 text-orange-800',
  alterado: 'bg-blue-100 text-blue-800',
}

interface Props {
  obra: Obra | null
}

export default function ComparativoTab({ obra }: Props) {
  const [versoes, setVersoes] = useState<Versao[]>([])
  const [v1Id, setV1Id] = useState<number | null>(null)
  const [v2Id, setV2Id] = useState<number | null>(null)
  const [data, setData] = useState<ComparativoOut | null>(null)
  const [loading, setLoading] = useState(false)
  const [mostrarIguais, setMostrarIguais] = useState(false)

  useEffect(() => {
    if (!obra) { setVersoes([]); setV1Id(null); setV2Id(null); setData(null); return }
    getVersoes(obra.id)
      .then(vs => {
        const sorted = [...vs].sort((a, b) => a.numero - b.numero)
        setVersoes(sorted)
        if (sorted.length >= 2) {
          setV1Id(sorted[sorted.length - 2].id)
          setV2Id(sorted[sorted.length - 1].id)
        }
      })
      .catch(() => toast('Erro ao carregar versões', 'error'))
    setData(null)
  }, [obra?.id])

  async function handleComparar() {
    if (!obra || !v1Id || !v2Id || v1Id === v2Id) return
    setLoading(true)
    try {
      const result = await getComparativo(obra.id, v1Id, v2Id)
      setData(result)
    } catch (e: any) {
      toast(e?.response?.data?.detail ?? 'Erro ao comparar versões', 'error')
    } finally {
      setLoading(false)
    }
  }

  if (!obra) {
    return <p className="text-gray-400 text-sm py-8 text-center">Selecione uma obra para comparar versões.</p>
  }

  if (versoes.length < 2) {
    return <p className="text-gray-400 text-sm py-8 text-center">Esta obra precisa de pelo menos 2 versões para comparar.</p>
  }

  const versaoLabel = (v: Versao) =>
    `Versão ${v.numero}${v.nome ? ` — ${v.nome}` : ''}${!v.bloqueada && !v.deletada_em ? ' (ativa)' : v.bloqueada ? ' (bloqueada)' : ''}`

  const itensFiltrados = data
    ? (mostrarIguais ? data.itens : data.itens.filter(i => i.status !== 'igual'))
    : []

  return (
    <div className="space-y-4">
      {/* Seletores */}
      <div className="flex items-center gap-3 flex-wrap">
        <select
          value={v1Id ?? ''}
          onChange={e => { setV1Id(Number(e.target.value)); setData(null) }}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {versoes.map(v => (
            <option key={v.id} value={v.id}>{versaoLabel(v)}</option>
          ))}
        </select>

        <span className="text-gray-500 text-sm font-medium">vs</span>

        <select
          value={v2Id ?? ''}
          onChange={e => { setV2Id(Number(e.target.value)); setData(null) }}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {versoes.map(v => (
            <option key={v.id} value={v.id}>{versaoLabel(v)}</option>
          ))}
        </select>

        <button
          onClick={handleComparar}
          disabled={loading || !v1Id || !v2Id || v1Id === v2Id}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
        >
          {loading ? 'Comparando…' : 'Comparar'}
        </button>
      </div>

      {/* Resultado */}
      {data && (
        <div className="space-y-4">
          {/* Resumo */}
          <div className="flex flex-wrap gap-3 items-center">
            <div className="bg-green-50 border border-green-200 rounded-lg px-3 py-2 text-sm text-green-800">
              <strong>{data.qtd_novos}</strong> adicionado{data.qtd_novos !== 1 ? 's' : ''}
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded-lg px-3 py-2 text-sm text-orange-800">
              <strong>{data.qtd_removidos}</strong> removido{data.qtd_removidos !== 1 ? 's' : ''}
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 text-sm text-blue-800">
              <strong>{data.qtd_alterados}</strong> alterado{data.qtd_alterados !== 1 ? 's' : ''}
            </div>
            <div className="ml-auto text-sm text-gray-600">
              <span className="text-gray-400">{data.v1_nome}:</span> {fmtBRL(parseFloat(data.v1_total))}
              {' → '}
              <span className="text-gray-400">{data.v2_nome}:</span> <strong>{fmtBRL(parseFloat(data.v2_total))}</strong>
              {' '}
              <span className={parseFloat(data.delta_total) >= 0 ? 'text-red-600' : 'text-green-600'}>
                ({parseFloat(data.delta_total) >= 0 ? '+' : ''}{fmtBRL(parseFloat(data.delta_total))}, {data.delta_pct >= 0 ? '+' : ''}{data.delta_pct.toFixed(1)}%)
              </span>
            </div>
          </div>

          {/* Filtro iguais */}
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={mostrarIguais}
              onChange={e => setMostrarIguais(e.target.checked)}
            />
            Mostrar itens iguais
          </label>

          {/* Tabela */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Grupo</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Serviço</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-600 w-24">V1 preço</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-600 w-24">V2 preço</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-600 w-24">Δ total</th>
                  <th className="text-center px-4 py-2 font-medium text-gray-600 w-24">Status</th>
                </tr>
              </thead>
              <tbody>
                {itensFiltrados.map((item, idx) => (
                  <tr
                    key={idx}
                    className={`border-t border-gray-100 ${STATUS_COLORS[item.status]}`}
                  >
                    <td className="px-4 py-2 text-gray-600 text-xs">{item.grupo_nome}</td>
                    <td className="px-4 py-2 truncate max-w-[240px]">{item.descricao}</td>
                    <td className="px-4 py-2 text-right font-mono text-xs text-gray-500">
                      {item.v1_preco_unit ? `R$ ${parseFloat(item.v1_preco_unit).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}` : '—'}
                    </td>
                    <td className="px-4 py-2 text-right font-mono text-xs">
                      {item.v2_preco_unit ? `R$ ${parseFloat(item.v2_preco_unit).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}` : '—'}
                    </td>
                    <td className={`px-4 py-2 text-right font-mono text-xs font-semibold ${parseFloat(item.delta_total) > 0 ? 'text-red-600' : parseFloat(item.delta_total) < 0 ? 'text-green-600' : 'text-gray-400'}`}>
                      {parseFloat(item.delta_total) !== 0
                        ? `${parseFloat(item.delta_total) > 0 ? '+' : ''}${fmtBRL(parseFloat(item.delta_total))}`
                        : '—'}
                    </td>
                    <td className="px-4 py-2 text-center">
                      {item.status !== 'igual' && (
                        <span className={`text-xs px-2 py-0.5 rounded font-medium ${STATUS_BADGES[item.status]}`}>
                          {item.status === 'novo' ? 'NOVO' : item.status === 'removido' ? 'REMOVIDO' : 'ALTERADO'}
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
                {itensFiltrados.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-400 text-sm">
                      Nenhuma diferença encontrada entre as versões.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 3: TypeCheck**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -10
```

Esperado: sem erros.

- [ ] **Step 4: Commit**

```bash
cd /Users/vladimirirving/Desktop/orcaavml && \
git add frontend/src/components/relatorios/ComparativoTab.tsx && \
git commit -m "feat: ComparativoTab — seletores de versão + diff table"
```

---

## Task 8: RelatoriosPage Refatorada

**Files:**
- Modify: `frontend/src/pages/RelatoriosPage.tsx`

- [ ] **Step 1: Ler o arquivo atual**

```bash
cat /Users/vladimirirving/Desktop/orcaavml/frontend/src/pages/RelatoriosPage.tsx
```

Entender estrutura atual — lista de obras com botões de download.

- [ ] **Step 2: Substituir pelo conteúdo refatorado**

```tsx
// frontend/src/pages/RelatoriosPage.tsx
import { useEffect, useState } from 'react'
import { getObras, getVersoes } from '@/api/obras'
import { toast } from '@/hooks/useToast'
import type { Obra, Versao } from '@/types'
import CurvaAbcTab from '@/components/relatorios/CurvaAbcTab'
import MedicoesTab from '@/components/relatorios/MedicoesTab'
import ComparativoTab from '@/components/relatorios/ComparativoTab'

type Tab = 'curva-abc' | 'medicoes' | 'comparativo'

const TABS: { id: Tab; label: string }[] = [
  { id: 'curva-abc', label: 'Curva ABC' },
  { id: 'medicoes', label: 'Medições' },
  { id: 'comparativo', label: 'Comparativo de Versões' },
]

export default function RelatoriosPage() {
  const [tab, setTab] = useState<Tab>('curva-abc')
  const [obras, setObras] = useState<Obra[]>([])
  const [obraId, setObraId] = useState<number | null>(null)
  const [versaoAtiva, setVersaoAtiva] = useState<Versao | null>(null)
  const [loadingObras, setLoadingObras] = useState(true)

  useEffect(() => {
    getObras()
      .then(os => {
        setObras(os)
        if (os.length > 0) setObraId(os[0].id)
      })
      .catch(() => toast('Erro ao carregar obras', 'error'))
      .finally(() => setLoadingObras(false))
  }, [])

  useEffect(() => {
    if (!obraId) { setVersaoAtiva(null); return }
    getVersoes(obraId).then(vs => {
      const ativa = vs.find(v => !v.bloqueada && v.deletada_em === null) ?? null
      setVersaoAtiva(ativa)
    }).catch(() => setVersaoAtiva(null))
  }, [obraId])

  const obraAtual = obras.find(o => o.id === obraId) ?? null

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Relatórios</h1>

        {/* Seletor de obra */}
        {!loadingObras && obras.length > 0 && (
          <select
            value={obraId ?? ''}
            onChange={e => setObraId(Number(e.target.value))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 max-w-xs"
          >
            {obras.map(o => (
              <option key={o.id} value={o.id}>{o.nome}</option>
            ))}
          </select>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t.id
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Conteúdo */}
      {loadingObras ? (
        <p className="text-gray-400 text-sm">Carregando obras…</p>
      ) : obras.length === 0 ? (
        <p className="text-gray-400 text-sm py-8 text-center">Nenhuma obra cadastrada.</p>
      ) : (
        <>
          {tab === 'curva-abc' && <CurvaAbcTab versao={versaoAtiva} />}
          {tab === 'medicoes' && <MedicoesTab versao={versaoAtiva} />}
          {tab === 'comparativo' && <ComparativoTab obra={obraAtual} />}
        </>
      )}
    </div>
  )
}
```

- [ ] **Step 3: TypeCheck**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -10
```

Esperado: sem erros.

- [ ] **Step 4: Commit**

```bash
cd /Users/vladimirirving/Desktop/orcaavml && \
git add frontend/src/pages/RelatoriosPage.tsx && \
git commit -m "feat: RelatoriosPage — 3 subtabs Curva ABC / Medições / Comparativo"
```

---

## Task 9: Verificação Final

- [ ] **Step 1: Rodar todos os testes backend**

```bash
docker exec -w /app -e PYTHONPATH=/app orcaavml-backend-1 \
  python -m pytest tests/backend/ -q 2>&1 | tail -5
```

Esperado: todos PASS (≥ 184 testes).

- [ ] **Step 2: TypeCheck frontend**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -10
```

Esperado: sem erros.

- [ ] **Step 3: Verificar no browser** (Vite dev server rodando em http://localhost:5173)

1. Abrir `/relatorios` → ver 3 abas e seletor de obra no topo
2. Aba **Curva ABC** → selecionar obra → tabela aparece com badges A/B/C coloridos, botões ↓ Excel e ↓ Proposta PDF
3. Aba **Medições** → tabela de grupos com planejado %, realizado %, desvio colorido e valor medido
4. Aba **Comparativo** → aparece com 2 selects de versão → clicar "Comparar" → badges de resumo + tabela diff
5. Checkbox "Mostrar itens iguais" → toggling exibe/oculta itens com `status = 'igual'`
6. Navegar entre abas sem recarregar a obra selecionada

- [ ] **Step 4: Commit final**

```bash
cd /Users/vladimirirving/Desktop/orcaavml && \
git add . && \
git commit -m "feat: Módulo 20 completo — Relatórios Completos (Curva ABC / Medições / Comparativo)"
```
