# Dashboard / Curva S Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preencher o DashboardPage (`/`) com portfólio de obras e adicionar aba Dashboard na ObraDetailPage com a Curva S (planejado × realizado em %) da versão ativa.

**Architecture:** Backend expõe dois endpoints calculados (`GET /dashboard` e `GET /obras/{id}/dashboard`) que derivam planejado/realizado de dados já existentes (CronogramaLinha + Medicao). Frontend usa Recharts (já instalado) para o gráfico e tabela simples para o portfólio. ObraDetailPage ganha tabs Versões | Dashboard; fmtMesLabel é extraída para utils.ts para ser compartilhada.

**Tech Stack:** FastAPI + SQLAlchemy async (backend), React 19 + TypeScript + Recharts + Tailwind (frontend)

---

## Mapa de arquivos

| Arquivo | Ação |
|---|---|
| `backend/app/schemas/dashboard.py` | Criar — 3 schemas Pydantic |
| `backend/app/routers/dashboard.py` | Criar — 2 endpoints + helper `_calc` |
| `backend/app/main.py` | Modificar — incluir router dashboard |
| `tests/backend/test_dashboard.py` | Criar — 9 testes |
| `frontend/src/types.ts` | Modificar — 3 tipos novos |
| `frontend/src/lib/utils.ts` | Modificar — exportar `fmtMesLabel` |
| `frontend/src/components/planilha/CronogramaGrade.tsx` | Modificar — importar `fmtMesLabel` de utils |
| `frontend/src/api/dashboard.ts` | Criar — 2 funções de API |
| `frontend/src/pages/DashboardPage.tsx` | Reescrever — tabela portfólio |
| `frontend/src/pages/ObraDetailPage.tsx` | Modificar — abas Versões \| Dashboard |
| `frontend/src/components/obra/ObraDashboard.tsx` | Criar — Curva S + KPI cards |

---

## Task 1: Backend schemas + router + testes

**Context:** `Item.total` é coluna computed (`quantidade * COALESCE(preco_unitario_sem_bdi, 0)`). `Versao.total_sem_bdi` é campo armazenado. `Versao.cronograma_inicio/fim` é `String(7)` como `"2025-06"`. Siga o padrão de `backend/app/routers/cronograma.py` — imports, `_get_versao_acesso`, etc.

Leia antes de começar:
- `backend/app/routers/cronograma.py` — padrão de router
- `backend/app/models/item.py` — campo `total`
- `backend/app/models/versao.py` — campos cronograma e total_sem_bdi
- `tests/backend/conftest.py` — fixtures disponíveis

**Files:**
- Create: `backend/app/schemas/dashboard.py`
- Create: `backend/app/routers/dashboard.py`
- Modify: `backend/app/main.py`
- Create: `tests/backend/test_dashboard.py`

---

- [ ] **Step 1: Criar schemas**

```python
# backend/app/schemas/dashboard.py
from typing import Optional
from pydantic import BaseModel


class DashboardResumoItem(BaseModel):
    obra_id: int
    obra_nome: str
    versao_id: Optional[int]
    total_sem_bdi: Optional[str]
    planejado_pct_hoje: Optional[float]
    realizado_pct: Optional[float]
    desvio: Optional[float]
    status: str  # "adiantado" | "no_prazo" | "atrasado" | "sem_dados"


class CurvaSPonto(BaseModel):
    mes: str            # "2025-01"
    planejado_acum: float
    realizado_acum: Optional[float]


class ObraDashboardData(BaseModel):
    versao_id: Optional[int]
    total_sem_bdi: Optional[str]
    planejado_pct_hoje: Optional[float]
    realizado_pct: Optional[float]
    desvio: Optional[float]
    status: str
    curva_s: list[CurvaSPonto]
```

- [ ] **Step 2: Escrever testes que falham**

```python
# tests/backend/test_dashboard.py
import pytest
from decimal import Decimal
from datetime import date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.cronograma_linha import CronogramaLinha
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.medicao import Medicao


async def _setup(db: AsyncSession, versao_ativa, cronograma_inicio: str, cronograma_fim: str,
                 dist1: dict, dist2: dict, medicoes: list[tuple[date, float]]):
    """
    Cria 2 itens (total=1000 cada), linhas de cronograma, e medições.
    dist1/dist2: distribuicao_json para item1 e item2 respectivamente.
    medicoes: lista de (periodo_inicio_date, pct_ambos_itens).
    Seta versao_ativa.total_sem_bdi=2000 e cronograma_inicio/fim.
    """
    grupo = Grupo(versao_id=versao_ativa.id, nome="G1", ordem=0)
    db.add(grupo)
    await db.flush()

    item1 = Item(
        grupo_id=grupo.id, ordem=0, unidade="m³",
        quantidade=Decimal("10"), preco_unitario_sem_bdi=Decimal("100"),
    )
    item2 = Item(
        grupo_id=grupo.id, ordem=1, unidade="m³",
        quantidade=Decimal("10"), preco_unitario_sem_bdi=Decimal("100"),
    )
    db.add_all([item1, item2])
    await db.flush()
    await db.refresh(item1)
    await db.refresh(item2)

    cl1 = CronogramaLinha(item_id=item1.id, distribuicao_json=dist1)
    cl2 = CronogramaLinha(item_id=item2.id, distribuicao_json=dist2)
    db.add_all([cl1, cl2])

    versao_ativa.cronograma_inicio = cronograma_inicio
    versao_ativa.cronograma_fim = cronograma_fim
    versao_ativa.total_sem_bdi = Decimal("2000")

    for inicio, pct in medicoes:
        from calendar import monthrange
        ultimo = monthrange(inicio.year, inicio.month)[1]
        m = Medicao(
            versao_id=versao_ativa.id,
            periodo_inicio=inicio,
            periodo_fim=date(inicio.year, inicio.month, ultimo),
            linhas_json={str(item1.id): pct, str(item2.id): pct},
        )
        db.add(m)

    await db.commit()


@pytest.mark.asyncio
async def test_portfolio_retorna_obra_com_dados(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # cronograma 2020-01 a 2020-02 (passado) → planejado_pct_hoje = 100%
    # medição Jan/2020 com 30% → realizado=30%, desvio=-70 → atrasado
    await _setup(
        db_session, versao_ativa,
        "2020-01", "2020-02",
        {"2020-01": 40, "2020-02": 60}, {"2020-01": 40, "2020-02": 60},
        [(date(2020, 1, 1), 30.0)],
    )
    resp = await client.get("/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    obra = next(d for d in data if d["versao_id"] == versao_ativa.id)
    assert obra["status"] == "atrasado"
    assert obra["realizado_pct"] == pytest.approx(30.0, abs=0.1)


@pytest.mark.asyncio
async def test_portfolio_obra_sem_versao_ativa(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Bloquear a versão → sem versão ativa
    versao_ativa.bloqueada = True
    await db_session.commit()

    resp = await client.get("/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    obra = next((d for d in resp.json() if d["obra_id"] == versao_ativa.obra_id), None)
    assert obra is not None
    assert obra["status"] == "sem_dados"
    assert obra["versao_id"] is None


@pytest.mark.asyncio
async def test_portfolio_obra_sem_cronograma(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Versão ativa sem cronograma_inicio configurado (padrão None)
    resp = await client.get("/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    obra = next(d for d in resp.json() if d["versao_id"] == versao_ativa.id)
    assert obra["status"] == "sem_dados"


@pytest.mark.asyncio
async def test_portfolio_obra_sem_medicao(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Cronograma configurado mas sem medições
    await _setup(
        db_session, versao_ativa,
        "2020-01", "2020-02",
        {"2020-01": 40, "2020-02": 60}, {"2020-01": 40, "2020-02": 60},
        [],  # sem medições
    )
    resp = await client.get("/dashboard", headers=auth_headers)
    obra = next(d for d in resp.json() if d["versao_id"] == versao_ativa.id)
    assert obra["status"] == "sem_dados"


@pytest.mark.asyncio
async def test_curva_s_calcula_planejado(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Distribui 40% Jan e 60% Fev para cada item (total=1000 cada, versao=2000)
    # Jan planejado_acum = (40/100*1000 + 40/100*1000)/2000*100 = 40%
    # Fev planejado_acum = 40% + 60% = 100%
    await _setup(
        db_session, versao_ativa,
        "2020-01", "2020-02",
        {"2020-01": 40, "2020-02": 60}, {"2020-01": 40, "2020-02": 60},
        [(date(2020, 1, 1), 30.0)],
    )
    resp = await client.get(f"/obras/{versao_ativa.obra_id}/dashboard", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    jan = next(p for p in data["curva_s"] if p["mes"] == "2020-01")
    fev = next(p for p in data["curva_s"] if p["mes"] == "2020-02")
    assert jan["planejado_acum"] == pytest.approx(40.0, abs=0.1)
    assert fev["planejado_acum"] == pytest.approx(100.0, abs=0.1)


@pytest.mark.asyncio
async def test_curva_s_calcula_realizado(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Medição Jan com 30% para cada item → realizado_acum Jan = 30%
    await _setup(
        db_session, versao_ativa,
        "2020-01", "2020-02",
        {"2020-01": 40, "2020-02": 60}, {"2020-01": 40, "2020-02": 60},
        [(date(2020, 1, 1), 30.0)],
    )
    resp = await client.get(f"/obras/{versao_ativa.obra_id}/dashboard", headers=auth_headers)
    data = resp.json()
    jan = next(p for p in data["curva_s"] if p["mes"] == "2020-01")
    fev = next(p for p in data["curva_s"] if p["mes"] == "2020-02")
    assert jan["realizado_acum"] == pytest.approx(30.0, abs=0.1)
    assert fev["realizado_acum"] is None


@pytest.mark.asyncio
async def test_status_atrasado(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Cronograma passado (2020) → planejado_hoje=100%, realizado=30% → desvio=-70 → atrasado
    await _setup(
        db_session, versao_ativa,
        "2020-01", "2020-02",
        {"2020-01": 40, "2020-02": 60}, {"2020-01": 40, "2020-02": 60},
        [(date(2020, 1, 1), 30.0)],
    )
    resp = await client.get(f"/obras/{versao_ativa.obra_id}/dashboard", headers=auth_headers)
    assert resp.json()["status"] == "atrasado"
    assert resp.json()["desvio"] < -3


@pytest.mark.asyncio
async def test_status_adiantado(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Cronograma futuro (2099) → planejado_hoje=0%, realizado=30% → desvio=+30 → adiantado
    await _setup(
        db_session, versao_ativa,
        "2099-01", "2099-02",
        {"2099-01": 40, "2099-02": 60}, {"2099-01": 40, "2099-02": 60},
        [(date(2099, 1, 1), 30.0)],
    )
    resp = await client.get(f"/obras/{versao_ativa.obra_id}/dashboard", headers=auth_headers)
    assert resp.json()["status"] == "adiantado"
    assert resp.json()["desvio"] > 3


@pytest.mark.asyncio
async def test_status_no_prazo(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
):
    # Cronograma passado → planejado_hoje=100%, realizado=99% → desvio=-1 → no_prazo
    await _setup(
        db_session, versao_ativa,
        "2020-01", "2020-02",
        {"2020-01": 40, "2020-02": 60}, {"2020-01": 40, "2020-02": 60},
        [(date(2020, 1, 1), 99.0)],
    )
    resp = await client.get(f"/obras/{versao_ativa.obra_id}/dashboard", headers=auth_headers)
    assert resp.json()["status"] == "no_prazo"
    assert -3 <= resp.json()["desvio"] <= 3


@pytest.mark.asyncio
async def test_isolamento_empresa_b(
    client: AsyncClient, auth_headers: dict,
    db_session: AsyncSession, versao_ativa,
    other_client: AsyncClient, other_auth_headers: dict,
):
    # Empresa B não vê dados de empresa A no portfolio
    await _setup(
        db_session, versao_ativa,
        "2020-01", "2020-01",
        {"2020-01": 100}, {"2020-01": 100},
        [(date(2020, 1, 1), 50.0)],
    )
    resp = await other_client.get("/dashboard", headers=other_auth_headers)
    assert resp.status_code == 200
    ids = [d["obra_id"] for d in resp.json()]
    assert versao_ativa.obra_id not in ids
```

- [ ] **Step 3: Rodar testes — confirmar que falham**

```bash
docker compose exec backend pytest tests/backend/test_dashboard.py -v 2>&1 | head -30
```

Esperado: FAILED com `404` ou `ImportError` — endpoints ainda não existem.

- [ ] **Step 4: Criar router**

```python
# backend/app/routers/dashboard.py
from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
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
from app.schemas.dashboard import CurvaSPonto, DashboardResumoItem, ObraDashboardData

router = APIRouter(tags=["dashboard"])


def _get_meses(inicio: str, fim: str) -> list[str]:
    meses = []
    y, m = int(inicio[:4]), int(inicio[5:7])
    ey, em = int(fim[:4]), int(fim[5:7])
    while (y, m) <= (ey, em):
        meses.append(f"{y}-{m:02d}")
        m += 1
        if m > 12:
            m = 1
            y += 1
    return meses


def _calc(versao: Versao, itens: list, medicoes: list) -> Optional[dict]:
    """Returns dict with keys planejado_pct_hoje, realizado_pct, desvio, status, curva_s.
    Returns None when data is insufficient (sem_dados)."""
    total_versao = float(versao.total_sem_bdi)
    if total_versao == 0 or not versao.cronograma_inicio or not versao.cronograma_fim:
        return None

    meses = _get_meses(versao.cronograma_inicio, versao.cronograma_fim)
    total_item = {item.id: float(item.total) for item in itens}
    dist = {
        item.id: (dict(item.cronograma_linha.distribuicao_json) if item.cronograma_linha else {})
        for item in itens
    }

    # Cumulative planned % per month
    planejado: dict[str, float] = {}
    acum = 0.0
    for mes in meses:
        for item_id, d in dist.items():
            acum += d.get(mes, 0) / 100 * total_item.get(item_id, 0)
        planejado[mes] = round(acum / total_versao * 100, 2)

    # Realizado % for months with a medicao
    realizado: dict[str, float] = {}
    for medicao in medicoes:
        mes = medicao.periodo_inicio.strftime("%Y-%m")
        if mes not in planejado:
            continue
        real_val = sum(
            medicao.linhas_json.get(str(item_id), 0) / 100 * total_item.get(item_id, 0)
            for item_id in total_item
        )
        realizado[mes] = round(real_val / total_versao * 100, 2)

    if not realizado:
        return None

    # planejado_pct_hoje
    mes_hoje = date.today().strftime("%Y-%m")
    if mes_hoje < meses[0]:
        planejado_pct_hoje = 0.0
    elif mes_hoje > meses[-1]:
        planejado_pct_hoje = planejado[meses[-1]]
    else:
        meses_ate_hoje = [m for m in meses if m <= mes_hoje]
        planejado_pct_hoje = planejado[meses_ate_hoje[-1]]

    # realizado_pct from latest medicao
    medicoes_sorted = sorted(medicoes, key=lambda m: m.periodo_inicio)
    mes_ultima = medicoes_sorted[-1].periodo_inicio.strftime("%Y-%m")
    realizado_pct = realizado.get(mes_ultima)
    if realizado_pct is None:
        return None

    desvio = round(realizado_pct - planejado_pct_hoje, 2)
    status = "adiantado" if desvio > 3 else "atrasado" if desvio < -3 else "no_prazo"

    curva_s = [
        CurvaSPonto(mes=mes, planejado_acum=planejado[mes], realizado_acum=realizado.get(mes))
        for mes in meses
    ]

    return {
        "planejado_pct_hoje": round(planejado_pct_hoje, 2),
        "realizado_pct": realizado_pct,
        "desvio": desvio,
        "status": status,
        "curva_s": curva_s,
    }


async def _get_versao_ativa_da_obra(obra_id: int, db: AsyncSession) -> Optional[Versao]:
    result = await db.execute(
        select(Versao).where(
            Versao.obra_id == obra_id,
            Versao.bloqueada == False,
            Versao.deletada_em.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def _get_itens(versao_id: int, db: AsyncSession) -> list:
    result = await db.execute(
        select(Item)
        .join(Grupo, Item.grupo_id == Grupo.id)
        .where(Grupo.versao_id == versao_id)
        .options(selectinload(Item.cronograma_linha))
    )
    return result.scalars().all()


async def _get_medicoes(versao_id: int, db: AsyncSession) -> list:
    result = await db.execute(select(Medicao).where(Medicao.versao_id == versao_id))
    return result.scalars().all()


@router.get("/dashboard", response_model=list[DashboardResumoItem])
async def get_dashboard(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    obras_result = await db.execute(
        select(Obra)
        .where(Obra.empresa_id == current_user.empresa_id)
        .order_by(Obra.nome)
    )
    obras = obras_result.scalars().all()

    resultado = []
    for obra in obras:
        versao = await _get_versao_ativa_da_obra(obra.id, db)
        if versao is None:
            resultado.append(DashboardResumoItem(
                obra_id=obra.id, obra_nome=obra.nome,
                versao_id=None, total_sem_bdi=None,
                planejado_pct_hoje=None, realizado_pct=None,
                desvio=None, status="sem_dados",
            ))
            continue
        itens = await _get_itens(versao.id, db)
        medicoes = await _get_medicoes(versao.id, db)
        calc = _calc(versao, itens, medicoes)
        if calc is None:
            resultado.append(DashboardResumoItem(
                obra_id=obra.id, obra_nome=obra.nome,
                versao_id=versao.id, total_sem_bdi=str(versao.total_sem_bdi),
                planejado_pct_hoje=None, realizado_pct=None,
                desvio=None, status="sem_dados",
            ))
        else:
            resultado.append(DashboardResumoItem(
                obra_id=obra.id, obra_nome=obra.nome,
                versao_id=versao.id, total_sem_bdi=str(versao.total_sem_bdi),
                planejado_pct_hoje=calc["planejado_pct_hoje"],
                realizado_pct=calc["realizado_pct"],
                desvio=calc["desvio"],
                status=calc["status"],
            ))
    return resultado


@router.get("/obras/{obra_id}/dashboard", response_model=ObraDashboardData)
async def get_obra_dashboard(
    obra_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    obra_result = await db.execute(
        select(Obra).where(Obra.id == obra_id, Obra.empresa_id == current_user.empresa_id)
    )
    if obra_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="Obra não encontrada")

    versao = await _get_versao_ativa_da_obra(obra_id, db)
    if versao is None:
        return ObraDashboardData(
            versao_id=None, total_sem_bdi=None,
            planejado_pct_hoje=None, realizado_pct=None,
            desvio=None, status="sem_dados", curva_s=[],
        )

    itens = await _get_itens(versao.id, db)
    medicoes = await _get_medicoes(versao.id, db)
    calc = _calc(versao, itens, medicoes)

    if calc is None:
        return ObraDashboardData(
            versao_id=versao.id, total_sem_bdi=str(versao.total_sem_bdi),
            planejado_pct_hoje=None, realizado_pct=None,
            desvio=None, status="sem_dados", curva_s=[],
        )

    return ObraDashboardData(
        versao_id=versao.id,
        total_sem_bdi=str(versao.total_sem_bdi),
        planejado_pct_hoje=calc["planejado_pct_hoje"],
        realizado_pct=calc["realizado_pct"],
        desvio=calc["desvio"],
        status=calc["status"],
        curva_s=calc["curva_s"],
    )
```

- [ ] **Step 5: Registrar router em main.py**

Abra `backend/app/main.py`. Após a linha `from app.routers import medicoes`, adicione:

```python
from app.routers import dashboard
```

Após `app.include_router(medicoes.router)`, adicione:

```python
app.include_router(dashboard.router)
```

- [ ] **Step 6: Rodar testes — confirmar que passam**

```bash
docker compose exec backend pytest tests/backend/test_dashboard.py -v
```

Esperado: todos os 9 testes PASSED.

Se algum test de isolamento falhar por fixture `other_client`/`other_auth_headers` não existir, verifique `tests/backend/conftest.py` e ajuste o nome da fixture de acordo com o padrão do projeto.

- [ ] **Step 7: Rodar suite completa — confirmar sem regressões**

```bash
docker compose exec backend pytest tests/backend/ -v
```

Esperado: todos PASSED.

- [ ] **Step 8: Commit**

```bash
git add backend/app/schemas/dashboard.py backend/app/routers/dashboard.py backend/app/main.py tests/backend/test_dashboard.py
git commit -m "feat: dashboard router — portfolio e curva s endpoints"
```

---

## Task 2: Frontend — tipos, API e fmtMesLabel compartilhada

**Context:** `fmtMesLabel` está definida localmente em `CronogramaGrade.tsx` (linha ~29). Precisa ser movida para `src/lib/utils.ts` e re-importada em CronogramaGrade. Depois, reutilizada em ObraDashboard. `frontend/src/lib/utils.ts` já exporta `cn`, `fmtBRL` e `fmtPct`.

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/lib/utils.ts`
- Modify: `frontend/src/components/planilha/CronogramaGrade.tsx`
- Create: `frontend/src/api/dashboard.ts`

---

- [ ] **Step 1: Adicionar tipos em types.ts**

Abra `frontend/src/types.ts`. Ao final do arquivo, adicione:

```ts
export interface DashboardResumoItem {
  obra_id: number
  obra_nome: string
  versao_id: number | null
  total_sem_bdi: string | null
  planejado_pct_hoje: number | null
  realizado_pct: number | null
  desvio: number | null
  status: 'adiantado' | 'no_prazo' | 'atrasado' | 'sem_dados'
}

export interface CurvaSPonto {
  mes: string
  planejado_acum: number
  realizado_acum: number | null
}

export interface ObraDashboardData {
  versao_id: number | null
  total_sem_bdi: string | null
  planejado_pct_hoje: number | null
  realizado_pct: number | null
  desvio: number | null
  status: string
  curva_s: CurvaSPonto[]
}
```

- [ ] **Step 2: Exportar fmtMesLabel de utils.ts**

Abra `frontend/src/lib/utils.ts`. Adicione ao final:

```ts
export function fmtMesLabel(mes: string): string {
  const [y, m] = mes.split('-')
  const labels = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
  return `${labels[parseInt(m) - 1]}/${y.slice(2)}`
}
```

- [ ] **Step 3: Atualizar CronogramaGrade para importar de utils**

Abra `frontend/src/components/planilha/CronogramaGrade.tsx`.

Remova a definição local de `fmtMesLabel` (está em torno da linha 29–33):

```ts
// REMOVER este bloco:
function fmtMesLabel(mes: string): string {
  const [y, m] = mes.split('-')
  const labels = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
  return `${labels[parseInt(m) - 1]}/${y.slice(2)}`
}
```

Na linha de import de utils, adicione `fmtMesLabel`:

```ts
import { fmtBRL, fmtMesLabel } from '@/lib/utils'
```

- [ ] **Step 4: Criar api/dashboard.ts**

```ts
// frontend/src/api/dashboard.ts
import { api } from '@/api/client'
import type { DashboardResumoItem, ObraDashboardData } from '@/types'

export const getDashboard = (): Promise<DashboardResumoItem[]> =>
  api.get<DashboardResumoItem[]>('/dashboard').then(r => r.data)

export const getObraDashboard = (obraId: number): Promise<ObraDashboardData> =>
  api.get<ObraDashboardData>(`/obras/${obraId}/dashboard`).then(r => r.data)
```

- [ ] **Step 5: TypeScript check**

```bash
cd frontend && ./node_modules/.bin/tsc --noEmit
```

Esperado: zero erros.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/types.ts frontend/src/lib/utils.ts frontend/src/components/planilha/CronogramaGrade.tsx frontend/src/api/dashboard.ts
git commit -m "feat: dashboard types, api module, extract fmtMesLabel to utils"
```

---

## Task 3: DashboardPage — tabela portfólio

**Context:** `frontend/src/pages/DashboardPage.tsx` é atualmente um placeholder de 8 linhas. Reescrever completamente. O arquivo usa `useNavigate` do react-router-dom e `fmtBRL` de utils. Não há teste unitário para esta página — testar manualmente no browser após o Task 4.

**Files:**
- Modify: `frontend/src/pages/DashboardPage.tsx`

---

- [ ] **Step 1: Reescrever DashboardPage.tsx**

```tsx
// frontend/src/pages/DashboardPage.tsx
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getDashboard } from '@/api/dashboard'
import { fmtBRL } from '@/lib/utils'
import type { DashboardResumoItem } from '@/types'

const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string }> = {
  adiantado: { label: 'Adiantado', bg: 'bg-green-100', text: 'text-green-700' },
  no_prazo:  { label: 'No prazo',  bg: 'bg-blue-100',  text: 'text-blue-700'  },
  atrasado:  { label: 'Atrasado',  bg: 'bg-yellow-100', text: 'text-yellow-700' },
  sem_dados: { label: 'Sem dados', bg: 'bg-gray-100',  text: 'text-gray-400'  },
}

export default function DashboardPage() {
  const [items, setItems] = useState<DashboardResumoItem[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    getDashboard()
      .then(setItems)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="p-8 text-gray-400 text-sm">Carregando...</div>
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {items.length === 0 && (
        <p className="text-gray-400 text-center py-12">Nenhuma obra cadastrada</p>
      )}

      {items.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-5 py-3 font-medium text-gray-600">Obra</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600 w-32">Planejado %</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600 w-32">Realizado %</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600 w-28">Desvio</th>
                <th className="text-center px-4 py-3 font-medium text-gray-600 w-28">Status</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, idx) => {
                const cfg = STATUS_CONFIG[item.status] ?? STATUS_CONFIG.sem_dados
                const semDados = item.status === 'sem_dados'
                return (
                  <tr
                    key={item.obra_id}
                    onClick={() => navigate(`/obras/${item.obra_id}`)}
                    className={`cursor-pointer hover:bg-gray-50 transition-colors ${
                      idx < items.length - 1 ? 'border-b border-gray-100' : ''
                    }`}
                  >
                    <td className="px-5 py-3">
                      <div className="font-medium text-gray-900">{item.obra_nome}</div>
                      {item.total_sem_bdi && (
                        <div className="text-xs text-gray-400 mt-0.5">
                          {fmtBRL(item.total_sem_bdi)}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-500">
                      {semDados ? '—' : `${item.planejado_pct_hoje?.toFixed(1)}%`}
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-blue-600">
                      {semDados ? '—' : `${item.realizado_pct?.toFixed(1)}%`}
                    </td>
                    <td className={`px-4 py-3 text-right font-medium ${
                      semDados ? 'text-gray-400'
                      : (item.desvio ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {semDados
                        ? '—'
                        : `${(item.desvio ?? 0) >= 0 ? '+' : ''}${item.desvio?.toFixed(1)}pp`
                      }
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${cfg.bg} ${cfg.text}`}>
                        {cfg.label}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: TypeScript check**

```bash
cd frontend && ./node_modules/.bin/tsc --noEmit
```

Esperado: zero erros.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/pages/DashboardPage.tsx
git commit -m "feat: DashboardPage — portfolio table with status badges"
```

---

## Task 4: ObraDashboard + ObraDetailPage tabs

**Context:** `ObraDetailPage` (`frontend/src/pages/ObraDetailPage.tsx`) não tem abas — toda a lógica de versões está diretamente no JSX. Adicionar `type Tab = 'versoes' | 'dashboard'`, barra de abas, e condicional para renderizar ObraDashboard. O botão "Nova Versão" só aparece na aba Versões. `obraId` já é `Number(id)` do `useParams`.

Leia o arquivo completo antes de editar: `frontend/src/pages/ObraDetailPage.tsx`.

**Files:**
- Create: `frontend/src/components/obra/ObraDashboard.tsx`
- Modify: `frontend/src/pages/ObraDetailPage.tsx`

---

- [ ] **Step 1: Criar ObraDashboard.tsx**

```tsx
// frontend/src/components/obra/ObraDashboard.tsx
import { useState, useEffect } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ReferenceLine, ResponsiveContainer,
} from 'recharts'
import { getObraDashboard } from '@/api/dashboard'
import { fmtMesLabel } from '@/lib/utils'
import { toast } from '@/hooks/useToast'
import type { ObraDashboardData } from '@/types'

interface Props {
  obraId: number
}

export default function ObraDashboard({ obraId }: Props) {
  const [data, setData] = useState<ObraDashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getObraDashboard(obraId)
      .then(setData)
      .catch(() => toast('Erro ao carregar dashboard', 'error'))
      .finally(() => setLoading(false))
  }, [obraId])

  if (loading) {
    return <div className="p-6 text-gray-400 text-sm">Carregando...</div>
  }

  if (!data || data.status === 'sem_dados') {
    return (
      <div className="p-6 text-center text-gray-400 text-sm py-12">
        Versão ativa sem cronograma configurado ou sem medições registradas
      </div>
    )
  }

  const mesAtual = new Date().toISOString().slice(0, 7)
  const temHoje = data.curva_s.some(p => p.mes === mesAtual)

  return (
    <div className="p-6 space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-xl p-4 text-center">
          <div className="text-xs text-gray-500 mb-1">Planejado hoje</div>
          <div className="text-3xl font-bold text-blue-600">
            {data.planejado_pct_hoje?.toFixed(1)}%
          </div>
        </div>
        <div className="bg-green-50 rounded-xl p-4 text-center">
          <div className="text-xs text-gray-500 mb-1">Realizado</div>
          <div className="text-3xl font-bold text-green-600">
            {data.realizado_pct?.toFixed(1)}%
          </div>
        </div>
        <div className={`rounded-xl p-4 text-center ${(data.desvio ?? 0) >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
          <div className="text-xs text-gray-500 mb-1">Desvio</div>
          <div className={`text-3xl font-bold ${(data.desvio ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {(data.desvio ?? 0) >= 0 ? '+' : ''}{data.desvio?.toFixed(1)}pp
          </div>
        </div>
      </div>

      {/* Curva S */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="text-sm font-medium text-gray-700 mb-4">Curva S — Planejado × Realizado</div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data.curva_s} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="mes"
              tickFormatter={fmtMesLabel}
              tick={{ fontSize: 11, fill: '#64748b' }}
            />
            <YAxis
              domain={[0, 100]}
              tickFormatter={(v: number) => `${v}%`}
              tick={{ fontSize: 11, fill: '#64748b' }}
              width={42}
            />
            <Tooltip
              formatter={(value: number | null, name: string) => [
                value != null ? `${value.toFixed(1)}%` : '—',
                name === 'planejado_acum' ? 'Planejado' : 'Realizado',
              ]}
              labelFormatter={(label: string) => fmtMesLabel(label)}
            />
            <Legend
              formatter={(name: string) =>
                name === 'planejado_acum' ? 'Planejado' : 'Realizado'
              }
            />
            {temHoje && (
              <ReferenceLine
                x={mesAtual}
                stroke="#94a3b8"
                strokeDasharray="3 3"
                label={{ value: 'hoje', position: 'top', fontSize: 10, fill: '#94a3b8' }}
              />
            )}
            <Line
              type="monotone"
              dataKey="planejado_acum"
              name="planejado_acum"
              stroke="#3b82f6"
              strokeDasharray="5 3"
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="realizado_acum"
              name="realizado_acum"
              stroke="#10b981"
              dot={{ r: 3, fill: '#10b981' }}
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Adicionar tabs em ObraDetailPage.tsx**

Leia o arquivo completo (`frontend/src/pages/ObraDetailPage.tsx`) e aplique as seguintes mudanças:

**2a.** Adicione o import do ObraDashboard no topo (junto com os outros imports):

```tsx
import ObraDashboard from '@/components/obra/ObraDashboard'
```

**2b.** Após `const [confirmDelete, setConfirmDelete] = useState<number | null>(null)`, adicione:

```tsx
const [tab, setTab] = useState<'versoes' | 'dashboard'>('versoes')
```

**2c.** No JSX, após o bloco `<div className="flex items-center justify-between mb-6">` que contém o `<h1>` e o botão "Nova Versão", substitua esse bloco por:

```tsx
      <div className="flex items-center justify-between mb-0">
        <h1 className="text-2xl font-bold text-gray-900">{obra.nome}</h1>
        {tab === 'versoes' && (
          <button
            onClick={handleNovaVersao}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium"
          >
            <Plus size={16} /> Nova Versão
          </button>
        )}
      </div>

      <div className="flex gap-0 border-b border-gray-200 mb-6 mt-4">
        {(['versoes', 'dashboard'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t === 'versoes' ? 'Versões' : 'Dashboard'}
          </button>
        ))}
      </div>
```

**2d.** Envolva o bloco de versões (desde `{versoes.length === 0 && ...}` até o fechamento do `<div className="bg-white rounded-xl...">`) em:

```tsx
      {tab === 'versoes' && (
        <>
          {/* conteúdo de versões existente aqui, sem modificação */}
        </>
      )}

      {tab === 'dashboard' && <ObraDashboard obraId={obraId} />}
```

- [ ] **Step 3: TypeScript check**

```bash
cd frontend && ./node_modules/.bin/tsc --noEmit
```

Esperado: zero erros.

- [ ] **Step 4: Testar no browser**

```bash
cd frontend && npm run dev
```

Verificar:
1. Dashboard `/` — tabela de obras aparece; obras sem cronograma/medição mostram "Sem dados"; clicar em uma linha navega para `/obras/:id`
2. ObraDetailPage — abas "Versões" e "Dashboard" aparecem; botão "Nova Versão" só visível na aba Versões
3. Aba Dashboard — KPI cards (Planejado · Realizado · Desvio) e gráfico Curva S renderizam; sem medições mostra mensagem vazia
4. CronogramaGrade ainda funciona (fmtMesLabel foi apenas re-importada, não removida)

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/obra/ObraDashboard.tsx frontend/src/pages/ObraDetailPage.tsx
git commit -m "feat: ObraDashboard curva S e abas em ObraDetailPage — Módulo 7 completo"
```
