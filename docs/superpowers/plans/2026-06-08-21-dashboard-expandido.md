# Módulo 21 — Dashboard Expandido: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expandir o dashboard atual (tabela simples) em duas visões alternáveis — Visão Empresa (KPIs + tabela enriquecida) e Visão Obra (KPIs monetários + Curva S + distribuição por grupo + progresso físico).

**Architecture:** Backend: estender schemas existentes com `estado`, `total_com_bdi`, `tem_alertas` e adicionar `GET /obras/{id}/distribuicao-grupos`. Frontend: `DashboardPage` com toggle Empresa/Obra → monta `EmpresaView` ou `ObraView`; `CurvaSChart` é um componente puro que recebe `CurvaSPonto[]`; `ObraView` reutiliza `GET /versoes/{id}/relatorio-medicao` do Módulo 20 para progresso físico. Sem migration.

**Tech Stack:** FastAPI + SQLAlchemy async. React + TypeScript + Tailwind + Recharts (já instalado).

---

## File Map

### Backend — modificados
| Arquivo | Alteração |
|---------|-----------|
| `backend/app/schemas/dashboard.py` | Adicionar `estado`, `total_com_bdi`, `tem_alertas` a `DashboardResumoItem`; adicionar `total_com_bdi` a `ObraDashboardData`; adicionar `GrupoDistribuicao` + `DistribuicaoGruposOut` |
| `backend/app/routers/dashboard.py` | Estender lógica de `GET /dashboard` e `GET /obras/{id}/dashboard`; adicionar `GET /obras/{id}/distribuicao-grupos` |
| `tests/backend/test_dashboard.py` | Adicionar 7 novos testes |

### Frontend — novos
| Arquivo | Responsabilidade |
|---------|-----------------|
| `frontend/src/components/dashboard/CurvaSChart.tsx` | LineChart puro (sem chamadas API): recebe `CurvaSPonto[]`, renderiza planejado × realizado |
| `frontend/src/components/dashboard/EmpresaView.tsx` | KPI cards calculados client-side + tabela de obras enriquecida com `estado` e `tem_alertas` |
| `frontend/src/components/dashboard/ObraView.tsx` | Seletor de obra + KPIs monetários + CurvaSChart + distribuição por grupo + progresso físico |

### Frontend — modificados
| Arquivo | Alteração |
|---------|-----------|
| `frontend/src/types.ts` | Estender `DashboardResumoItem` e `ObraDashboardData`; adicionar `GrupoDistribuicao`, `DistribuicaoGruposOut` |
| `frontend/src/api/dashboard.ts` | Adicionar `getDistribuicaoGrupos` |
| `frontend/src/pages/DashboardPage.tsx` | Toggle Empresa/Obra + estado de `obraId` selecionada; monta `EmpresaView` ou `ObraView` |

---

## Task 1: Backend Schemas

**Files:**
- Modify: `backend/app/schemas/dashboard.py`

- [ ] **Step 1: Ler o arquivo atual**

```bash
cat /Users/vladimirirving/Desktop/orcaavml/backend/app/schemas/dashboard.py
```

O arquivo atual tem `DashboardResumoItem`, `CurvaSPonto`, `ObraDashboardData`.

- [ ] **Step 2: Substituir pelo conteúdo atualizado**

```python
# backend/app/schemas/dashboard.py
from typing import Literal, List, Optional
from decimal import Decimal
from pydantic import BaseModel


class DashboardResumoItem(BaseModel):
    obra_id: int
    obra_nome: str
    versao_id: Optional[int]
    total_sem_bdi: Optional[str]
    total_com_bdi: Optional[str]       # novo
    estado: str                         # novo: "em_elaboracao" | "concluido" | "arquivado"
    tem_alertas: bool                   # novo: True se algum item tem requer_revisao=True
    planejado_pct_hoje: Optional[float]
    realizado_pct: Optional[float]
    desvio: Optional[float]
    status: Literal["adiantado", "no_prazo", "atrasado", "sem_dados"]


class CurvaSPonto(BaseModel):
    mes: str            # "2025-01"
    planejado_acum: float
    realizado_acum: Optional[float]


class ObraDashboardData(BaseModel):
    versao_id: Optional[int]
    total_sem_bdi: Optional[str]
    total_com_bdi: Optional[str]       # novo
    planejado_pct_hoje: Optional[float]
    realizado_pct: Optional[float]
    desvio: Optional[float]
    status: Literal["adiantado", "no_prazo", "atrasado", "sem_dados"]
    curva_s: List[CurvaSPonto]


class GrupoDistribuicao(BaseModel):
    grupo_id: int
    grupo_nome: str
    total: Decimal
    participacao_pct: float


class DistribuicaoGruposOut(BaseModel):
    versao_id: int
    total_versao: Decimal
    grupos: List[GrupoDistribuicao]
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/dashboard.py
git commit -m "feat: estender schemas dashboard — estado, total_com_bdi, tem_alertas, GrupoDistribuicao"
```

---

## Task 2: Backend Router + Testes

**Files:**
- Modify: `backend/app/routers/dashboard.py`
- Modify: `tests/backend/test_dashboard.py`

- [ ] **Step 1: Escrever testes (TDD)**

Adicionar ao final de `tests/backend/test_dashboard.py`:

```python
# --- Novos testes Módulo 21 ---
from app.models.bdi import BDI


@pytest.mark.asyncio
async def test_dashboard_inclui_estado(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa, db_session
):
    """Campo estado retornado corretamente."""
    r = await client.get("/dashboard", headers=auth_headers)
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["estado"] == "em_elaboracao"


@pytest.mark.asyncio
async def test_dashboard_inclui_total_com_bdi(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa, db_session
):
    """Campo total_com_bdi presente quando versão ativa existe."""
    from decimal import Decimal
    versao_ativa.total_com_bdi = Decimal("9500.00")
    await db_session.flush()

    r = await client.get("/dashboard", headers=auth_headers)
    assert r.status_code == 200
    items = r.json()
    assert items[0]["total_com_bdi"] is not None
    assert float(items[0]["total_com_bdi"]) == pytest.approx(9500.0)


@pytest.mark.asyncio
async def test_dashboard_tem_alertas_true(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa,
    composicao_sinapi, db_session
):
    """tem_alertas=True quando item tem requer_revisao=True."""
    grupo = Grupo(versao_id=versao_ativa.id, nome="G", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, quantidade=Decimal("10"), unidade="M3",
        preco_unitario_sem_bdi=Decimal("50"), preco_unitario_com_bdi=Decimal("55"),
        requer_revisao=True,
    )
    db_session.add(item)
    await db_session.flush()

    r = await client.get("/dashboard", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()[0]["tem_alertas"] is True


@pytest.mark.asyncio
async def test_dashboard_tem_alertas_false(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa,
    composicao_sinapi, db_session
):
    """tem_alertas=False quando sem itens marcados."""
    grupo = Grupo(versao_id=versao_ativa.id, nome="G", ordem=0)
    db_session.add(grupo)
    await db_session.flush()
    item = Item(
        grupo_id=grupo.id, quantidade=Decimal("10"), unidade="M3",
        preco_unitario_sem_bdi=Decimal("50"), preco_unitario_com_bdi=Decimal("55"),
        requer_revisao=False,
    )
    db_session.add(item)
    await db_session.flush()

    r = await client.get("/dashboard", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()[0]["tem_alertas"] is False


@pytest.mark.asyncio
async def test_distribuicao_grupos_basico(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa,
    composicao_sinapi, db_session
):
    """Participação % correta, dois grupos."""
    from decimal import Decimal as D2
    grupo_a = Grupo(versao_id=versao_ativa.id, nome="Pavimentação", ordem=0)
    grupo_b = Grupo(versao_id=versao_ativa.id, nome="Terraplenagem", ordem=1)
    db_session.add_all([grupo_a, grupo_b])
    await db_session.flush()

    # grupo_a: 3 itens de 100 cada = 300; grupo_b: 1 item de 700 = 700; total=1000
    for _ in range(3):
        db_session.add(Item(
            grupo_id=grupo_a.id, quantidade=D2("1"), unidade="UN",
            preco_unitario_sem_bdi=D2("100"), preco_unitario_com_bdi=D2("110"),
        ))
    db_session.add(Item(
        grupo_id=grupo_b.id, quantidade=D2("1"), unidade="UN",
        preco_unitario_sem_bdi=D2("700"), preco_unitario_com_bdi=D2("770"),
    ))
    await db_session.flush()
    versao_ativa.total_sem_bdi = D2("1000")
    await db_session.flush()

    r = await client.get(f"/obras/{obra.id}/distribuicao-grupos", headers=auth_headers)
    assert r.status_code == 200
    data = r.json()
    assert data["versao_id"] == versao_ativa.id
    grupos = {g["grupo_nome"]: g for g in data["grupos"]}
    assert pytest.approx(grupos["Pavimentação"]["participacao_pct"], abs=0.1) == 30.0
    assert pytest.approx(grupos["Terraplenagem"]["participacao_pct"], abs=0.1) == 70.0
    total_pct = sum(g["participacao_pct"] for g in data["grupos"])
    assert pytest.approx(total_pct, abs=0.5) == 100.0


@pytest.mark.asyncio
async def test_distribuicao_grupos_sem_versao_ativa(
    client: AsyncClient, auth_headers: dict, obra, versao_ativa, db_session
):
    """Sem versão ativa: lista vazia."""
    versao_ativa.bloqueada = True
    await db_session.flush()

    r = await client.get(f"/obras/{obra.id}/distribuicao-grupos", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["grupos"] == []


@pytest.mark.asyncio
async def test_distribuicao_grupos_tenant_isolation(
    client: AsyncClient, obra, db_session
):
    """Obra de outra empresa → 404."""
    from app.models.empresa import Empresa
    from app.models.usuario import Usuario
    from app.services.auth_service import hash_password, create_access_token

    emp_b = Empresa(nome="Emp B", cnpj="33.333.333/0001-33")
    db_session.add(emp_b)
    await db_session.flush()
    user_b = Usuario(
        empresa_id=emp_b.id, nome="B", email="d4@b.com",
        senha_hash=hash_password("x"), papel="admin",
    )
    db_session.add(user_b)
    await db_session.flush()
    token_b = create_access_token({"sub": str(user_b.id), "papel": "admin", "empresa_id": emp_b.id})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    r = await client.get(f"/obras/{obra.id}/distribuicao-grupos", headers=headers_b)
    assert r.status_code == 404
```

Também adicionar imports que faltam ao topo de `test_dashboard.py`:

```python
from app.models.grupo import Grupo
from app.models.item import Item
from decimal import Decimal as D
```

(verificar se já existem — não duplicar)

- [ ] **Step 2: Rodar testes novos — devem falhar**

```bash
docker exec -w /app -e PYTHONPATH=/app orcaavml-backend-1 \
  python -m pytest tests/backend/test_dashboard.py -k "inclui_estado or inclui_total or tem_alertas or distribuicao" -v 2>&1 | tail -15
```

Esperado: FAIL (campos não existem / endpoint não existe).

- [ ] **Step 3: Atualizar router `dashboard.py`**

Modificar `backend/app/routers/dashboard.py`:

**3a — estender `get_dashboard`:** no bloco onde `versao is None`, adicionar `estado=obra.estado, total_com_bdi=None, tem_alertas=False`. No bloco com versão, adicionar:

```python
tem_alertas = any(i.requer_revisao for i in itens)
```

E incluir nos dois `DashboardResumoItem(...)`:

```python
estado=obra.estado,
total_com_bdi=str(versao.total_com_bdi) if versao else None,
tem_alertas=tem_alertas,
```

O trecho completo do endpoint fica:

```python
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
                versao_id=None, total_sem_bdi=None, total_com_bdi=None,
                estado=obra.estado, tem_alertas=False,
                planejado_pct_hoje=None, realizado_pct=None,
                desvio=None, status="sem_dados",
            ))
            continue
        itens = await _get_itens(versao.id, db)
        medicoes = await _get_medicoes(versao.id, db)
        calc = _calc(versao, itens, medicoes)
        tem_alertas = any(i.requer_revisao for i in itens)
        if calc is None:
            resultado.append(DashboardResumoItem(
                obra_id=obra.id, obra_nome=obra.nome,
                versao_id=versao.id, total_sem_bdi=str(versao.total_sem_bdi),
                total_com_bdi=str(versao.total_com_bdi),
                estado=obra.estado, tem_alertas=tem_alertas,
                planejado_pct_hoje=None, realizado_pct=None,
                desvio=None, status="sem_dados",
            ))
        else:
            resultado.append(DashboardResumoItem(
                obra_id=obra.id, obra_nome=obra.nome,
                versao_id=versao.id, total_sem_bdi=str(versao.total_sem_bdi),
                total_com_bdi=str(versao.total_com_bdi),
                estado=obra.estado, tem_alertas=tem_alertas,
                planejado_pct_hoje=calc["planejado_pct_hoje"],
                realizado_pct=calc["realizado_pct"],
                desvio=calc["desvio"],
                status=calc["status"],
            ))
    return resultado
```

**3b — estender `get_obra_dashboard`:** adicionar `total_com_bdi` ao retorno:

```python
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
            versao_id=None, total_sem_bdi=None, total_com_bdi=None,
            planejado_pct_hoje=None, realizado_pct=None,
            desvio=None, status="sem_dados", curva_s=[],
        )

    itens = await _get_itens(versao.id, db)
    medicoes = await _get_medicoes(versao.id, db)
    calc = _calc(versao, itens, medicoes)

    if calc is None:
        return ObraDashboardData(
            versao_id=versao.id, total_sem_bdi=str(versao.total_sem_bdi),
            total_com_bdi=str(versao.total_com_bdi),
            planejado_pct_hoje=None, realizado_pct=None,
            desvio=None, status="sem_dados", curva_s=[],
        )

    return ObraDashboardData(
        versao_id=versao.id,
        total_sem_bdi=str(versao.total_sem_bdi),
        total_com_bdi=str(versao.total_com_bdi),
        planejado_pct_hoje=calc["planejado_pct_hoje"],
        realizado_pct=calc["realizado_pct"],
        desvio=calc["desvio"],
        status=calc["status"],
        curva_s=calc["curva_s"],
    )
```

**3c — adicionar `GET /obras/{obra_id}/distribuicao-grupos`:** adicionar ao final de `dashboard.py`:

```python
from app.schemas.dashboard import GrupoDistribuicao, DistribuicaoGruposOut


@router.get("/obras/{obra_id}/distribuicao-grupos", response_model=DistribuicaoGruposOut)
async def get_distribuicao_grupos(
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
    if versao is None or versao.total_sem_bdi == 0:
        versao_id_out = versao.id if versao else 0
        return DistribuicaoGruposOut(
            versao_id=versao_id_out,
            total_versao=Decimal("0"),
            grupos=[],
        )

    # Grupos raiz e todos os grupos da versão
    grupos_r = await db.execute(
        select(Grupo).where(Grupo.versao_id == versao.id, Grupo.pai_id.is_(None))
    )
    grupos_raiz = grupos_r.scalars().all()
    grupos_raiz_ids = {g.id for g in grupos_raiz}

    todos_grupos_r = await db.execute(
        select(Grupo).where(Grupo.versao_id == versao.id)
    )
    todos_grupos = {g.id: g for g in todos_grupos_r.scalars().all()}

    # Todos os itens da versão
    todos_itens_r = await db.execute(
        select(Item)
        .join(Grupo, Item.grupo_id == Grupo.id)
        .where(Grupo.versao_id == versao.id)
    )
    todos_itens = todos_itens_r.scalars().all()

    # Agregar total por grupo raiz
    totais: dict[int, Decimal] = {g.id: Decimal("0") for g in grupos_raiz}
    for item in todos_itens:
        g = todos_grupos.get(item.grupo_id)
        if g is None:
            continue
        raiz_id = g.id if g.pai_id is None else (g.pai_id if g.pai_id in grupos_raiz_ids else None)
        if raiz_id is not None:
            totais[raiz_id] = totais.get(raiz_id, Decimal("0")) + (item.total or Decimal("0"))

    total_versao = versao.total_sem_bdi
    resultado = []
    for grupo in sorted(grupos_raiz, key=lambda g: totais.get(g.id, Decimal("0")), reverse=True):
        grupo_total = totais.get(grupo.id, Decimal("0"))
        pct = float(grupo_total / total_versao * 100) if total_versao else 0.0
        resultado.append(GrupoDistribuicao(
            grupo_id=grupo.id,
            grupo_nome=grupo.nome,
            total=grupo_total,
            participacao_pct=round(pct, 2),
        ))

    return DistribuicaoGruposOut(
        versao_id=versao.id,
        total_versao=total_versao,
        grupos=resultado,
    )
```

Adicionar import no topo de `dashboard.py`:
```python
from decimal import Decimal
from app.schemas.dashboard import GrupoDistribuicao, DistribuicaoGruposOut
```

(Verificar se `Grupo`, `Item` já estão importados — sim, estão.)

- [ ] **Step 4: Rodar todos os testes do dashboard**

```bash
docker exec -w /app -e PYTHONPATH=/app orcaavml-backend-1 \
  python -m pytest tests/backend/test_dashboard.py -v 2>&1 | tail -20
```

Esperado: todos PASS (anteriores + 7 novos).

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/dashboard.py tests/backend/test_dashboard.py
git commit -m "feat: dashboard — estado/total_com_bdi/tem_alertas + GET /obras/{id}/distribuicao-grupos + testes"
```

---

## Task 3: Frontend — Tipos + API

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api/dashboard.ts`

- [ ] **Step 1: Estender tipos em `types.ts`**

Substituir as interfaces `DashboardResumoItem` e `ObraDashboardData` existentes e adicionar `GrupoDistribuicao`/`DistribuicaoGruposOut`. Localizar as linhas atuais (linha ~92) e substituir:

```typescript
export interface DashboardResumoItem {
  obra_id: number
  obra_nome: string
  versao_id: number | null
  total_sem_bdi: string | null
  total_com_bdi: string | null        // novo
  estado: string                       // novo
  tem_alertas: boolean                 // novo
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
  total_com_bdi: string | null        // novo
  planejado_pct_hoje: number | null
  realizado_pct: number | null
  desvio: number | null
  status: string
  curva_s: CurvaSPonto[]
}

export interface GrupoDistribuicao {
  grupo_id: number
  grupo_nome: string
  total: string
  participacao_pct: number
}

export interface DistribuicaoGruposOut {
  versao_id: number
  total_versao: string
  grupos: GrupoDistribuicao[]
}
```

- [ ] **Step 2: Adicionar `getDistribuicaoGrupos` em `api/dashboard.ts`**

```typescript
// frontend/src/api/dashboard.ts
import { api } from '@/api/client'
import type { DashboardResumoItem, ObraDashboardData, DistribuicaoGruposOut } from '@/types'

export const getDashboard = (): Promise<DashboardResumoItem[]> =>
  api.get<DashboardResumoItem[]>('/dashboard').then(r => r.data)

export const getObraDashboard = (obraId: number): Promise<ObraDashboardData> =>
  api.get<ObraDashboardData>(`/obras/${obraId}/dashboard`).then(r => r.data)

export const getDistribuicaoGrupos = (obraId: number): Promise<DistribuicaoGruposOut> =>
  api.get<DistribuicaoGruposOut>(`/obras/${obraId}/distribuicao-grupos`).then(r => r.data)
```

- [ ] **Step 3: TypeCheck**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -20
```

Esperado: sem erros (ObraDashboard.tsx usa `ObraDashboardData` — verificar que o campo `total_com_bdi` é opcional no uso existente).

- [ ] **Step 4: Commit**

```bash
cd /Users/vladimirirving/Desktop/orcaavml && \
git add frontend/src/types.ts frontend/src/api/dashboard.ts && \
git commit -m "feat: tipos DashboardResumoItem/ObraDashboardData estendidos + GrupoDistribuicao + getDistribuicaoGrupos"
```

---

## Task 4: CurvaSChart

**Files:**
- Create: `frontend/src/components/dashboard/CurvaSChart.tsx`

- [ ] **Step 1: Criar componente**

```tsx
// frontend/src/components/dashboard/CurvaSChart.tsx
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ReferenceLine, ResponsiveContainer,
} from 'recharts'
import { fmtMesLabel } from '@/lib/utils'
import type { CurvaSPonto } from '@/types'

interface Props {
  data: CurvaSPonto[]
}

export default function CurvaSChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <p className="text-gray-400 text-sm text-center py-8">
        Sem dados de cronograma para exibir a Curva S.
      </p>
    )
  }

  const mesAtual = new Date().toISOString().slice(0, 7)
  const temHoje = data.some(p => p.mes === mesAtual)

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
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
          formatter={(value, name: string) => [
            typeof value === 'number' ? `${value.toFixed(1)}%` : '—',
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
git add frontend/src/components/dashboard/CurvaSChart.tsx && \
git commit -m "feat: CurvaSChart — LineChart puro para Curva S planejado × realizado"
```

---

## Task 5: EmpresaView

**Files:**
- Create: `frontend/src/components/dashboard/EmpresaView.tsx`

- [ ] **Step 1: Criar componente**

```tsx
// frontend/src/components/dashboard/EmpresaView.tsx
import { fmtBRL } from '@/lib/utils'
import type { DashboardResumoItem } from '@/types'

const ESTADO_BADGE: Record<string, string> = {
  em_elaboracao: 'bg-blue-100 text-blue-800',
  concluido: 'bg-green-100 text-green-800',
  arquivado: 'bg-gray-100 text-gray-500',
}

const ESTADO_LABEL: Record<string, string> = {
  em_elaboracao: 'elaboração',
  concluido: 'concluído',
  arquivado: 'arquivado',
}

const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string }> = {
  adiantado: { label: 'Adiantado', bg: 'bg-green-100', text: 'text-green-700' },
  no_prazo: { label: 'No prazo', bg: 'bg-blue-100', text: 'text-blue-700' },
  atrasado: { label: 'Atrasado', bg: 'bg-yellow-100', text: 'text-yellow-700' },
  sem_dados: { label: 'Sem dados', bg: 'bg-gray-100', text: 'text-gray-400' },
}

interface Props {
  items: DashboardResumoItem[]
  onSelectObra: (obraId: number) => void
}

export default function EmpresaView({ items, onSelectObra }: Props) {
  // KPIs calculados client-side
  const emElaboracao = items.filter(i => i.estado === 'em_elaboracao')
  const totalSemBdi = emElaboracao.reduce(
    (s, i) => s + parseFloat(i.total_sem_bdi ?? '0'), 0
  )
  const totalComBdi = emElaboracao.reduce(
    (s, i) => s + parseFloat(i.total_com_bdi ?? '0'), 0
  )
  const qtdAlertas = items.filter(i => i.tem_alertas).length

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-xl p-4">
          <div className="text-xs text-gray-500 mb-1 uppercase tracking-wide">Em elaboração (s/ BDI)</div>
          <div className="text-2xl font-bold text-blue-700">{fmtBRL(String(totalSemBdi.toFixed(2)))}</div>
          <div className="text-xs text-blue-400 mt-1">{emElaboracao.length} obra{emElaboracao.length !== 1 ? 's' : ''}</div>
        </div>
        <div className="bg-green-50 rounded-xl p-4">
          <div className="text-xs text-gray-500 mb-1 uppercase tracking-wide">Total com BDI</div>
          <div className="text-2xl font-bold text-green-700">{fmtBRL(String(totalComBdi.toFixed(2)))}</div>
        </div>
        <div className={`rounded-xl p-4 ${qtdAlertas > 0 ? 'bg-amber-50' : 'bg-gray-50'}`}>
          <div className="text-xs text-gray-500 mb-1 uppercase tracking-wide">Alertas</div>
          <div className={`text-2xl font-bold ${qtdAlertas > 0 ? 'text-amber-700' : 'text-gray-400'}`}>
            {qtdAlertas}
          </div>
          <div className="text-xs text-gray-400 mt-1">itens para revisar</div>
        </div>
      </div>

      {/* Tabela de obras */}
      {items.length === 0 ? (
        <p className="text-gray-400 text-center py-12 text-sm">Nenhuma obra cadastrada.</p>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-5 py-3 font-medium text-gray-600">Obra</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600 w-28">Estado</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600 w-32">Planejado %</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600 w-32">Realizado %</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600 w-28">Desvio</th>
                <th className="text-center px-4 py-3 font-medium text-gray-600 w-28">Status</th>
                <th className="w-8"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, idx) => {
                const cfg = STATUS_CONFIG[item.status] ?? STATUS_CONFIG.sem_dados
                const semDados = item.status === 'sem_dados'
                return (
                  <tr
                    key={item.obra_id}
                    className={`hover:bg-gray-50 transition-colors cursor-pointer ${
                      idx < items.length - 1 ? 'border-b border-gray-100' : ''
                    }`}
                    onClick={() => onSelectObra(item.obra_id)}
                  >
                    <td className="px-5 py-3">
                      <div className="font-medium text-gray-900 flex items-center gap-2">
                        {item.obra_nome}
                        {item.tem_alertas && (
                          <span className="text-amber-500 text-xs" title="Itens para revisar">⚠</span>
                        )}
                      </div>
                      {item.total_sem_bdi && (
                        <div className="text-xs text-gray-400 mt-0.5">{fmtBRL(item.total_sem_bdi)}</div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${ESTADO_BADGE[item.estado] ?? 'bg-gray-100 text-gray-500'}`}>
                        {ESTADO_LABEL[item.estado] ?? item.estado}
                      </span>
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
                      {semDados ? '—' : `${(item.desvio ?? 0) >= 0 ? '+' : ''}${item.desvio?.toFixed(1)}pp`}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${cfg.bg} ${cfg.text}`}>
                        {cfg.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-center text-xs">→</td>
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

- [ ] **Step 2: TypeCheck**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -10
```

Esperado: sem erros.

- [ ] **Step 3: Commit**

```bash
cd /Users/vladimirirving/Desktop/orcaavml && \
git add frontend/src/components/dashboard/EmpresaView.tsx && \
git commit -m "feat: EmpresaView — KPI cards + tabela enriquecida com estado e alertas"
```

---

## Task 6: ObraView

**Files:**
- Create: `frontend/src/components/dashboard/ObraView.tsx`

- [ ] **Step 1: Criar componente**

```tsx
// frontend/src/components/dashboard/ObraView.tsx
import { useEffect, useState } from 'react'
import { getObraDashboard, getDistribuicaoGrupos } from '@/api/dashboard'
import { getRelatorioMedicao } from '@/api/relatorios'
import { toast } from '@/hooks/useToast'
import { fmtBRL } from '@/lib/utils'
import type { ObraDashboardData, DistribuicaoGruposOut, RelatorioMedicaoOut } from '@/types'
import CurvaSChart from '@/components/dashboard/CurvaSChart'

interface Props {
  obraId: number
}

const GRUPO_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4']

export default function ObraView({ obraId }: Props) {
  const [dash, setDash] = useState<ObraDashboardData | null>(null)
  const [distrib, setDistrib] = useState<DistribuicaoGruposOut | null>(null)
  const [medicao, setMedicao] = useState<RelatorioMedicaoOut | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setDash(null); setDistrib(null); setMedicao(null)

    Promise.all([
      getObraDashboard(obraId),
      getDistribuicaoGrupos(obraId),
    ])
      .then(async ([d, dist]) => {
        setDash(d)
        setDistrib(dist)
        if (d.versao_id) {
          try {
            const med = await getRelatorioMedicao(d.versao_id)
            setMedicao(med)
          } catch {
            // progresso físico não essencial — ignorar erro
          }
        }
      })
      .catch(() => toast('Erro ao carregar dados da obra', 'error'))
      .finally(() => setLoading(false))
  }, [obraId])

  if (loading) return <div className="py-12 text-center text-gray-400 text-sm">Carregando…</div>
  if (!dash) return null

  const semDados = dash.status === 'sem_dados'

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
          <div className="text-xs text-gray-500 mb-1 uppercase tracking-wide">Total sem BDI</div>
          <div className="text-xl font-bold text-gray-900">{fmtBRL(dash.total_sem_bdi)}</div>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
          <div className="text-xs text-gray-500 mb-1 uppercase tracking-wide">Total com BDI</div>
          <div className="text-xl font-bold text-gray-900">{fmtBRL(dash.total_com_bdi)}</div>
        </div>
        <div className={`rounded-xl p-4 border ${semDados ? 'bg-gray-50 border-gray-200' : 'bg-green-50 border-green-200'}`}>
          <div className="text-xs text-gray-500 mb-1 uppercase tracking-wide">Realizado</div>
          {semDados ? (
            <div className="text-xl font-bold text-gray-400">—</div>
          ) : (
            <>
              <div className="text-xl font-bold text-green-700">{dash.realizado_pct?.toFixed(1)}%</div>
              <div className={`text-xs mt-1 font-medium ${(dash.desvio ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {(dash.desvio ?? 0) >= 0 ? '+' : ''}{dash.desvio?.toFixed(1)}pp vs planejado
              </div>
            </>
          )}
        </div>
      </div>

      {/* Curva S */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="text-sm font-semibold text-gray-700 mb-4">Curva S — Planejado × Realizado</div>
        {semDados ? (
          <p className="text-gray-400 text-sm text-center py-8">Cronograma ou medições não configurados.</p>
        ) : (
          <CurvaSChart data={dash.curva_s} />
        )}
      </div>

      {/* Distribuição por grupo + Progresso físico */}
      <div className="grid grid-cols-2 gap-4">
        {/* Distribuição por grupo */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="text-sm font-semibold text-gray-700 mb-4">Distribuição por Grupo</div>
          {!distrib || distrib.grupos.length === 0 ? (
            <p className="text-gray-400 text-sm text-center py-4">Sem grupos com valor.</p>
          ) : (
            <div className="space-y-2.5">
              {distrib.grupos.map((g, idx) => (
                <div key={g.grupo_id} className="flex items-center gap-3">
                  <div
                    className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
                    style={{ background: GRUPO_COLORS[idx % GRUPO_COLORS.length] }}
                  />
                  <div className="flex-1 text-sm text-gray-700 truncate">{g.grupo_nome}</div>
                  <div className="text-sm font-semibold text-gray-900 flex-shrink-0">
                    {g.participacao_pct.toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Progresso físico por grupo */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="text-sm font-semibold text-gray-700 mb-4">Progresso Físico por Grupo</div>
          {!medicao || medicao.grupos.length === 0 ? (
            <p className="text-gray-400 text-sm text-center py-4">Sem medições registradas.</p>
          ) : (
            <div className="space-y-3">
              {medicao.grupos.map(grupo => {
                const desvio = grupo.desvio_pct
                return (
                  <div key={grupo.grupo_id}>
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span className="truncate font-medium">{grupo.grupo_nome}</span>
                      <span className={`font-semibold flex-shrink-0 ml-2 ${desvio > 0 ? 'text-green-600' : desvio < 0 ? 'text-red-600' : 'text-gray-400'}`}>
                        {desvio > 0 ? '+' : ''}{desvio.toFixed(1)}%
                      </span>
                    </div>
                    <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
                      {/* Planejado (background) */}
                      <div
                        className="absolute top-0 left-0 h-full bg-gray-300 rounded-full"
                        style={{ width: `${Math.min(grupo.planejado_pct, 100)}%` }}
                      />
                      {/* Realizado (foreground) */}
                      <div
                        className={`absolute top-0 left-0 h-full rounded-full ${desvio >= 0 ? 'bg-blue-500' : 'bg-amber-400'}`}
                        style={{ width: `${Math.min(grupo.realizado_pct, 100)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-gray-400 mt-0.5">
                      <span>{grupo.realizado_pct.toFixed(0)}% realizado</span>
                      <span>{grupo.planejado_pct.toFixed(0)}% planejado</span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
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
git add frontend/src/components/dashboard/ObraView.tsx && \
git commit -m "feat: ObraView — KPIs monetários + CurvaS + distribuição + progresso físico"
```

---

## Task 7: DashboardPage Refatorada

**Files:**
- Modify: `frontend/src/pages/DashboardPage.tsx`

- [ ] **Step 1: Ler a página atual**

```bash
cat /Users/vladimirirving/Desktop/orcaavml/frontend/src/pages/DashboardPage.tsx
```

- [ ] **Step 2: Substituir pelo conteúdo refatorado**

```tsx
// frontend/src/pages/DashboardPage.tsx
import { useState, useEffect } from 'react'
import { getDashboard } from '@/api/dashboard'
import { toast } from '@/hooks/useToast'
import type { DashboardResumoItem } from '@/types'
import EmpresaView from '@/components/dashboard/EmpresaView'
import ObraView from '@/components/dashboard/ObraView'

type Visao = 'empresa' | 'obra'

export default function DashboardPage() {
  const [visao, setVisao] = useState<Visao>('empresa')
  const [items, setItems] = useState<DashboardResumoItem[]>([])
  const [loading, setLoading] = useState(true)
  const [obraId, setObraId] = useState<number | null>(null)

  useEffect(() => {
    getDashboard()
      .then(data => {
        setItems(data)
        if (data.length > 0) setObraId(data[0].obra_id)
      })
      .catch(() => toast('Erro ao carregar dashboard', 'error'))
      .finally(() => setLoading(false))
  }, [])

  function handleSelectObra(id: number) {
    setObraId(id)
    setVisao('obra')
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header com toggle */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <div className="flex items-center gap-3">
          {/* Seletor de obra (só Visão Obra) */}
          {visao === 'obra' && items.length > 0 && (
            <select
              value={obraId ?? ''}
              onChange={e => setObraId(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 max-w-xs"
            >
              {items.map(i => (
                <option key={i.obra_id} value={i.obra_id}>{i.obra_nome}</option>
              ))}
            </select>
          )}
          {/* Toggle pill */}
          <div className="flex bg-gray-100 rounded-lg p-1 gap-1">
            <button
              onClick={() => setVisao('empresa')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                visao === 'empresa'
                  ? 'bg-white shadow-sm text-gray-900'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              🏢 Empresa
            </button>
            <button
              onClick={() => setVisao('obra')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                visao === 'obra'
                  ? 'bg-white shadow-sm text-gray-900'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              🏗️ Obra
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-gray-400 text-sm text-center py-12">Carregando…</div>
      ) : (
        <>
          {visao === 'empresa' && (
            <EmpresaView items={items} onSelectObra={handleSelectObra} />
          )}
          {visao === 'obra' && obraId && (
            <ObraView obraId={obraId} />
          )}
          {visao === 'obra' && !obraId && (
            <p className="text-gray-400 text-sm text-center py-12">Nenhuma obra cadastrada.</p>
          )}
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
git add frontend/src/pages/DashboardPage.tsx && \
git commit -m "feat: DashboardPage — toggle Empresa/Obra + EmpresaView + ObraView"
```

---

## Task 8: Verificação Final

- [ ] **Step 1: Rodar todos os testes backend**

```bash
docker exec -w /app -e PYTHONPATH=/app orcaavml-backend-1 \
  python -m pytest tests/backend/ -q 2>&1 | tail -5
```

Esperado: todos PASS (≥ 191 testes).

- [ ] **Step 2: TypeCheck frontend**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -10
```

Esperado: sem erros.

- [ ] **Step 3: Verificar no browser** (http://localhost:5173)

1. Abrir `/` (Dashboard) → ver toggle "🏢 Empresa / 🏗️ Obra"
2. **Visão Empresa**: 3 KPI cards no topo; tabela com coluna Estado (badge azul), ícone ⚠ nas obras com alertas; clicar `→` em uma obra
3. Após clicar → toggle muda para Visão Obra automaticamente
4. **Visão Obra**: 3 KPIs (Total sem BDI, Total com BDI, Realizado); Curva S (com ou sem dados); Distribuição por grupo; Progresso físico
5. Seletor de obra visível no header da Visão Obra
6. Alternar toggle manualmente entre as visões — estado da obra selecionada é preservado

- [ ] **Step 4: Commit final se necessário**

```bash
cd /Users/vladimirirving/Desktop/orcaavml && \
git status --short | grep -v "^\?\?" && \
git add -p  # apenas arquivos modificados intencionalmente
git commit -m "feat: Módulo 21 completo — Dashboard Expandido (Visão Empresa + Visão Obra)"
```
