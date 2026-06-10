# Módulo 21 — Dashboard Expandido: Design Spec

**Data:** 2026-06-08
**Status:** Aprovado para implementação

---

## 1. Objetivo

Transformar o dashboard atual (tabela simples) no dashboard rico descrito na seção 3.11 do spec original, com duas visões alternáveis via toggle: **Visão Empresa** (portfólio de obras com KPIs) e **Visão Obra** (Curva S, distribuição por grupo, progresso físico).

---

## 2. Estrutura da UI

### Toggle

Botão pill no header do `DashboardPage` alterna entre Visão Empresa e Visão Obra. Ao clicar `→` em uma obra da tabela (Visão Empresa), o sistema muda para Visão Obra com aquela obra pré-selecionada.

### Visão Empresa

Composta por:
1. **3 KPI cards** (topo):
   - Total sem BDI em elaboração: soma de `total_sem_bdi` das versões ativas de obras em estado `em_elaboracao`
   - Total com BDI: soma de `total_com_bdi` das versões ativas
   - Alertas: contagem de obras com `tem_alertas = true`
2. **Tabela de obras** (existente, enriquecida):
   - Nova coluna `Estado` (badge colorido: elaboração=azul, concluído=verde, arquivado=cinza)
   - Seta `→` ao final de cada linha → navega para Visão Obra daquela obra

Os KPIs são calculados **client-side** a partir da lista retornada por `GET /dashboard` — sem endpoint extra.

### Visão Obra

Seletor de obra no header (dropdown). Composta por:
1. **3 KPI cards**: Total sem BDI | Total com BDI | Realizado %
2. **Curva S** (LineChart Recharts, full-width): planejado × realizado, dados de `GET /obras/{id}/dashboard`
3. **Distribuição por grupo** (lista com percentuais): participação de cada grupo raiz no total, dados de `GET /obras/{id}/distribuicao-grupos`
4. **Progresso físico por grupo** (barras horizontais): planejado vs realizado por grupo, dados de `GET /versoes/{id}/relatorio-medicao` (reutilizado do Módulo 20)

---

## 3. Backend

### 3.1 Schemas estendidos

**`DashboardResumoItem`** — adicionar campos:
```python
estado: str                  # "em_elaboracao" | "concluido" | "arquivado"
total_com_bdi: Optional[str] # str(versao.total_com_bdi) ou None
tem_alertas: bool            # True se qualquer item da versão ativa tem requer_revisao=True
```

**`ObraDashboardData`** — adicionar campo:
```python
total_com_bdi: Optional[str] # str(versao.total_com_bdi) ou None
```

### 3.2 `GET /dashboard` — lógica estendida

Para cada obra, além do que já existe, incluir:
- `estado`: `obra.estado`
- `total_com_bdi`: `str(versao.total_com_bdi)` se versão ativa existe
- `tem_alertas`: `True` se `SELECT EXISTS(... WHERE requer_revisao = true AND grupo.versao_id = versao.id)`

### 3.3 `GET /obras/{id}/dashboard` — lógica estendida

Adicionar ao retorno:
- `total_com_bdi`: `str(versao.total_com_bdi)` se versão ativa existe

### 3.4 Novo: `GET /obras/{obra_id}/distribuicao-grupos`

**Descrição:** Participação percentual de cada grupo raiz da versão ativa da obra no `total_sem_bdi`.

**Autorização:** tenant isolation por `empresa_id`.

**Algoritmo:**
1. Buscar versão ativa da obra (`bloqueada=False AND deletada_em IS NULL`)
2. Buscar todos os grupos raiz da versão (`pai_id IS NULL`)
3. Para cada grupo raiz: `total = SUM(item.total)` de todos os itens do grupo e seus subgrupos
4. `participacao_pct = grupo_total / versao.total_sem_bdi * 100`
5. Ordenar por `total` decrescente

**Response schema:**
```python
class GrupoDistribuicao(BaseModel):
    grupo_id: int
    grupo_nome: str
    total: Decimal
    participacao_pct: float

class DistribuicaoGruposOut(BaseModel):
    versao_id: int
    total_versao: Decimal
    grupos: list[GrupoDistribuicao]
```

Se não há versão ativa ou `total_sem_bdi == 0`: retornar lista vazia.

### 3.5 Endpoints reutilizados sem alteração

| Endpoint | Usado em |
|----------|----------|
| `GET /versoes/{id}/relatorio-medicao` | Progresso físico por grupo (Módulo 20) |

---

## 4. Frontend

### 4.1 Arquivos novos

| Arquivo | Responsabilidade |
|---------|-----------------|
| `frontend/src/components/dashboard/EmpresaView.tsx` | KPI cards + tabela de obras enriquecida |
| `frontend/src/components/dashboard/ObraView.tsx` | KPIs + Curva S + distribuição + progresso |
| `frontend/src/components/dashboard/CurvaSChart.tsx` | LineChart Recharts (planejado vs realizado) |

### 4.2 Arquivos modificados

| Arquivo | Alteração |
|---------|-----------|
| `frontend/src/pages/DashboardPage.tsx` | Toggle Empresa/Obra + seletor de obra, monta EmpresaView ou ObraView |
| `frontend/src/api/dashboard.ts` | Adicionar `getDistribuicaoGrupos` |
| `frontend/src/types.ts` | Adicionar `GrupoDistribuicao`, `DistribuicaoGruposOut`; estender `DashboardResumoItem` e `ObraDashboardData` |

### 4.3 CurvaSChart

Usa `LineChart` do Recharts com dois `Line`:
- Azul (`#3b82f6`): série `planejado_acum`
- Âmbar (`#f59e0b`): série `realizado_acum` (pontilhada, pode ter `null` nos meses futuros)

Eixo X: meses (`YYYY-MM`), formatados como `Jan/25`. Eixo Y: 0–100%. Tooltip com ambos os valores.

### 4.4 EmpresaView

- KPIs calculados client-side a partir de `DashboardResumoItem[]`
- Coluna `Estado` com badge colorido: `em_elaboracao` → azul, `concluido` → verde, `arquivado` → cinza
- Callback `onSelectObra(obraId)` ao clicar `→` → DashboardPage muda para Visão Obra

### 4.5 ObraView

Recebe `obraId: number`. Faz 3 chamadas em paralelo:
1. `getObraDashboard(obraId)` → KPIs + Curva S
2. `getDistribuicaoGrupos(obraId)` → lista de grupos
3. Se `versao_id` presente: `getRelatorioMedicao(versao_id)` → progresso por grupo

---

## 5. Testes Backend

| Teste | Cenário |
|-------|---------|
| `test_dashboard_inclui_estado` | Campo `estado` correto na resposta |
| `test_dashboard_inclui_total_com_bdi` | Campo `total_com_bdi` presente quando versão ativa existe |
| `test_dashboard_tem_alertas_true` | `tem_alertas=True` quando item tem `requer_revisao=True` |
| `test_dashboard_tem_alertas_false` | `tem_alertas=False` quando sem itens marcados |
| `test_distribuicao_grupos_basico` | Participação % correta, soma ≈ 100% |
| `test_distribuicao_grupos_sem_versao_ativa` | Retorna lista vazia quando sem versão ativa |
| `test_distribuicao_grupos_tenant_isolation` | Obra de outra empresa → 404 |

---

## 6. Fora do Escopo

- Rosca (PieChart) na Visão Empresa por estado — a tabela enriquecida é suficiente
- Delta vs versão anterior (complexidade extra sem valor imediato)
- Obras com alertas como painel separado — o badge `tem_alertas` na tabela é suficiente
- Atualização automática/polling — botão "Atualizar" manual se necessário
