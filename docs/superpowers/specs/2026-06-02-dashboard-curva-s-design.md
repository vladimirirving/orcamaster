# Dashboard / Curva S — Design Spec

**Data:** 2026-06-02
**Status:** Aprovado para implementação
**Módulo:** 7 de 11

---

## 1. Objetivo

Preencher o DashboardPage (`/`) com um portfólio de obras e adicionar uma aba Dashboard na ObraDetailPage com a Curva S (planejado × realizado em %) da versão ativa.

---

## 2. Duas superfícies

### 2.1 DashboardPage `/`

Tabela com uma linha por obra da empresa. Colunas:

| Obra | Planejado % hoje | Realizado % | Desvio | Status |
|---|---|---|---|---|
| Nome + total S/BDI | % acumulado planejado até o mês atual | % acumulado da última medição | realizado − planejado | badge colorido |

- Obras sem versão ativa, sem cronograma configurado ou sem medições mostram `—` nas colunas numéricas e badge **"Sem dados"**
- Obras ordenadas por nome (ordem alfabética)
- Cada linha é clicável → navega para `/obras/:id`
- Status badge: **Adiantado** (desvio > +3pp, verde) · **No prazo** (±3pp, azul) · **Atrasado** (< −3pp, amarelo) · **Sem dados** (cinza)

### 2.2 ObraDetailPage `/obras/:id`

Ganha sistema de abas no topo:

```
[ Versões ]  [ Dashboard ]
```

- Conteúdo atual (lista de versões, botão Nova Versão) move para aba **Versões**
- Aba **Dashboard** renderiza `<ObraDashboard obraId={obraId} />`
- Troca de aba não recarrega — os dados são carregados on-demand quando a aba Dashboard é aberta pela primeira vez

---

## 3. Curva S (ObraDashboard)

### 3.1 Gráfico

- `LineChart` do Recharts (já instalado)
- Eixo X: meses do cronograma, formatados como `Jan/25`
- Eixo Y: 0–100%, tickFormatter `${v}%`
- **Linha planejado:** azul (`#3b82f6`), tracejada, dataKey `planejado_acum`
- **Linha realizado:** verde (`#10b981`), sólida, dataKey `realizado_acum`, `connectNulls={false}` — não liga pontos sem medição
- `ReferenceLine` vertical no mês atual quando está dentro do período do cronograma, label "hoje"
- `Tooltip` customizado mostrando mês + planejado % + realizado % (ou `—` se null)
- `Legend`: Planejado · Realizado

### 3.2 KPI cards (3 acima do gráfico)

| Card | Valor | Cor |
|---|---|---|
| Planejado hoje | `planejado_pct_hoje%` | azul |
| Realizado | `realizado_pct%` | verde |
| Desvio | `+Xpp` / `−Xpp` | verde se ≥ 0, vermelho se < 0 |

### 3.3 Estados

- **loading:** skeleton
- **sem versão ativa / sem cronograma / sem medições:** mensagem "Versão ativa sem cronograma configurado ou sem medições registradas"
- **com dados:** KPI cards + gráfico

---

## 4. Modelo de dados

Nenhuma migração necessária. Os dados já existem:
- `CronogramaLinha.distribuicao_json` — distribuição planejada por mês
- `Medicao.linhas_json` — percentual acumulado realizado por item
- `Item.quantidade` × `Item.preco_unitario_sem_bdi` — total_sem_bdi por item
- `Versao.total_sem_bdi` — total da versão (campo computed já existente)

---

## 5. Backend

### 5.1 Router

Arquivo: `backend/app/routers/dashboard.py`  
Montado em `/dashboard` e `/obras/{obra_id}/dashboard`.  
Todos os endpoints exigem autenticação e verificam isolamento por empresa.

| Método | Path | Descrição |
|---|---|---|
| `GET` | `/dashboard` | Portfólio: resumo de todas as obras da empresa |
| `GET` | `/obras/{obra_id}/dashboard` | Curva S + KPIs da versão ativa da obra |

### 5.2 GET `/dashboard` — portfólio

Retorna lista de obras da empresa (incluindo obras sem versão ativa).

```json
[
  {
    "obra_id": 1,
    "obra_nome": "Rodovia SP-150",
    "versao_id": 3,
    "total_sem_bdi": "12400000.00",
    "planejado_pct_hoje": 40.0,
    "realizado_pct": 35.0,
    "desvio": -5.0,
    "status": "atrasado"
  },
  {
    "obra_id": 2,
    "obra_nome": "Ponte Tietê",
    "versao_id": null,
    "total_sem_bdi": null,
    "planejado_pct_hoje": null,
    "realizado_pct": null,
    "desvio": null,
    "status": "sem_dados"
  }
]
```

**Lógica de `status`:**
- `sem_dados`: versão ativa ausente, ou `total_sem_bdi == 0`, ou sem cronograma (`cronograma_inicio` null), ou sem medições
- `atrasado`: `desvio < -3`
- `no_prazo`: `-3 ≤ desvio ≤ 3`
- `adiantado`: `desvio > 3`

### 5.3 GET `/obras/{obra_id}/dashboard` — Curva S

```json
{
  "versao_id": 3,
  "total_sem_bdi": "12400000.00",
  "planejado_pct_hoje": 40.0,
  "realizado_pct": 35.0,
  "desvio": -5.0,
  "status": "atrasado",
  "curva_s": [
    {"mes": "2025-01", "planejado_acum": 8.2,  "realizado_acum": null},
    {"mes": "2025-02", "planejado_acum": 15.4, "realizado_acum": 12.1},
    {"mes": "2025-06", "planejado_acum": 40.0, "realizado_acum": 35.0}
  ]
}
```

Se a obra não tem versão ativa: retorna 200 com `versao_id: null, curva_s: [], status: "sem_dados"`.

**Cálculos:**

```python
# total_sem_bdi por item
total_item = float(item.quantidade) * float(item.preco_unitario_sem_bdi or 0)

# planejado_acum[mes] — % acumulado planejado até aquele mês
planejado_acum = 0.0
for mes in meses_cronograma_ate_M:
    for linha in linhas:
        pct_mes = linha.distribuicao_json.get(mes, 0)
        planejado_acum += pct_mes / 100 * total_item[linha.item_id]
planejado_acum_pct = planejado_acum / total_versao * 100

# realizado_acum[mes] — só para meses com medição
for medicao in medicoes:
    real = sum(
        medicao.linhas_json.get(str(item_id), 0) / 100 * total_item[item_id]
        for item_id in total_item
    )
    realizado_acum_pct = real / total_versao * 100

# planejado_pct_hoje — planejado_acum do mês atual
# se hoje < cronograma_inicio → 0.0
# se hoje > cronograma_fim → planejado_acum do último mês (≈ 100%)
mes_hoje = date.today().strftime("%Y-%m")
```

### 5.4 Schemas (`backend/app/schemas/dashboard.py`)

```python
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
    mes: str          # "2025-01"
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

### 5.5 Testes (`tests/backend/test_dashboard.py`)

- GET `/dashboard` retorna obras da empresa com status correto
- GET `/dashboard` obra sem versão ativa → status `sem_dados`, campos null
- GET `/dashboard` obra com cronograma mas sem medições → status `sem_dados`
- GET `/obras/{id}/dashboard` calcula `planejado_acum` corretamente
- GET `/obras/{id}/dashboard` calcula `realizado_acum` corretamente
- GET `/obras/{id}/dashboard` status `atrasado` quando desvio < −3
- GET `/obras/{id}/dashboard` status `adiantado` quando desvio > +3
- GET `/obras/{id}/dashboard` status `no_prazo` quando desvio ±3
- Isolamento: empresa B não acessa dashboard de empresa A

---

## 6. Frontend

### 6.1 Arquivos

**Novos:**
- `frontend/src/api/dashboard.ts`
- `frontend/src/components/obra/ObraDashboard.tsx`

**Modificados:**
- `frontend/src/types.ts` — adiciona 3 tipos
- `frontend/src/lib/utils.ts` — exporta `fmtMesLabel` (extraída de CronogramaGrade)
- `frontend/src/components/planilha/CronogramaGrade.tsx` — importa `fmtMesLabel` de utils em vez de definir localmente
- `frontend/src/pages/DashboardPage.tsx` — reescrito
- `frontend/src/pages/ObraDetailPage.tsx` — adiciona abas

### 6.2 Tipos (`types.ts`)

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

### 6.3 API (`api/dashboard.ts`)

```ts
export const getDashboard = (): Promise<DashboardResumoItem[]> =>
  api.get('/dashboard').then(r => r.data)

export const getObraDashboard = (obraId: number): Promise<ObraDashboardData> =>
  api.get(`/obras/${obraId}/dashboard`).then(r => r.data)
```

### 6.4 DashboardPage

- Carrega `getDashboard()` on mount
- Loading: spinner centralizado
- Vazio: "Nenhuma obra cadastrada"
- Tabela: colunas Obra · Planejado % · Realizado % · Desvio · Status
  - Coluna Obra: nome em negrito + total S/BDI formatado em BRL como subtítulo
  - Colunas numéricas: `—` quando `status === 'sem_dados'`; desvio formatado com sinal (`+5pp`, `−3pp`)
  - Status badge: cores por status (verde/azul/amarelo/cinza)
  - Linha clicável → `navigate('/obras/${item.obra_id}')`

### 6.5 ObraDetailPage

- Adiciona `type Tab = 'versoes' | 'dashboard'` com estado inicial `'versoes'`
- Barra de abas abaixo do cabeçalho: `[ Versões ]  [ Dashboard ]`
- Conteúdo atual (lista de versões + botão Nova Versão) condicionado a `tab === 'versoes'`
- `{tab === 'dashboard' && <ObraDashboard obraId={obraId} />}`
- Dados de ObraDashboard carregados apenas quando aba é aberta (lazy — `useEffect` dentro de ObraDashboard)

### 6.6 ObraDashboard

- Carrega `getObraDashboard(obraId)` on mount
- Loading: skeleton
- `status === 'sem_dados'`: mensagem "Versão ativa sem cronograma configurado ou sem medições registradas"
- KPI cards (3 em linha): Planejado hoje · Realizado · Desvio
- `LineChart` (Recharts):
  - `data={curva_s}` — array de `CurvaSPonto`
  - `XAxis dataKey="mes"` com `tickFormatter={fmtMesLabel}` (reutiliza função de CronogramaGrade)
  - `YAxis` domain `[0, 100]`, `tickFormatter={v => \`${v}%\`}`
  - `XAxis` usa `fmtMesLabel` — função extraída de CronogramaGrade para `src/lib/utils.ts` (shared)
  - `fmtMesLabel("2025-06")` → `"Jun/25"`
- `Line` planejado: `type="monotone"`, stroke `#3b82f6`, `strokeDasharray="5 3"`, `dot={false}`
  - `Line` realizado: `type="monotone"`, stroke `#10b981`, `dot={{ r: 3 }}`, `connectNulls={false}`
  - `ReferenceLine` vertical: `x={mesAtual}` se `mesAtual` está em `curva_s`, label `"hoje"`, stroke `#94a3b8`, `strokeDasharray="3 3"`
  - `Tooltip` customizado: mostra mês + planejado + realizado (ou `—`)
  - `Legend` na parte inferior

---

## 7. Fora do escopo deste módulo

- Relatório de desvios por grupo exportável (PDF/Excel)
- Comparativo entre versões (v1 planejado × v2 realizado)
- Filtros de período na Curva S
- Curva S em R$ (toggle)
- Alertas/notificações por email de desvio

---

## 8. Dependências

- `recharts` já instalado (`^2.15.0`)
- Nenhuma migração de banco de dados
- Nenhuma dependência nova de pacote
