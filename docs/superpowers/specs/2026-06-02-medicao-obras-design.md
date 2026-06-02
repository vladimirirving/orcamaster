# Medição de Obras — Design Spec

**Data:** 2026-06-02
**Status:** Aprovado para implementação
**Módulo:** 6 de 11

---

## 1. Objetivo

Adicionar ao editor de planilha a aba **Medição**, onde o orçamentista registra o percentual acumulado executado por item a cada período mensal. O sistema calcula automaticamente o avanço do período (delta), o valor financeiro medido e o acumulado, que serão usados na Curva S do Dashboard (Módulo 7).

---

## 2. Navegação

A Medição aparece como **terceira aba na PlanilhaPage** (`/obras/:obraId/versoes/:versaoId`):

```
[ Planilha ]  [ Cronograma ]  [ Medição ]
```

Trocar de aba não recarrega dados — o store `useOrcamento` mantém grupos/itens carregados. O BDI button e os totais do rodapé permanecem visíveis em todas as abas.

Versão ativa (não bloqueada): grade editável. Versão bloqueada: todas as medições em modo leitura.

---

## 3. Modelo de dados

O modelo `Medicao` já existe — nenhuma migração necessária:

```python
class Medicao(Base):
    __tablename__ = "medicao"
    id: Mapped[int]
    versao_id: Mapped[int]          # FK → versao
    periodo_inicio: Mapped[date]    # primeiro dia do mês selecionado
    periodo_fim: Mapped[date]       # último dia do mês selecionado
    criada_por: Mapped[Optional[int]]
    linhas_json: Mapped[dict]       # {"item_id_str": percentual_acumulado}
                                    # ex: {"42": 35.0, "43": 25.0}
```

`linhas_json` armazena o percentual **acumulado** executado (0–100) por item. O avanço do período é calculado por diferença entre medições consecutivas.

---

## 4. Backend

### 4.1 Router

Montado em `/versoes/{versao_id}/medicoes`. Todos os endpoints exigem autenticação e verificam isolamento por empresa.

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/versoes/{id}/medicoes` | Lista todas as medições da versão |
| `POST` | `/versoes/{id}/medicoes` | Cria nova medição para um mês |
| `PATCH` | `/versoes/{id}/medicoes/{medicao_id}` | Atualiza `linhas_json` de uma medição |

### 4.2 GET — Lista de medições

Retorna todas as medições da versão ordenadas por `periodo_inicio` decrescente (mais recente primeiro).

```json
[
  {
    "id": 3,
    "periodo_inicio": "2025-06-01",
    "periodo_fim": "2025-06-30",
    "linhas_json": {"42": 35.0, "43": 25.0},
    "criada_por": 1
  },
  {
    "id": 2,
    "periodo_inicio": "2025-05-01",
    "periodo_fim": "2025-05-31",
    "linhas_json": {"42": 22.0, "43": 15.0},
    "criada_por": 1
  }
]
```

### 4.3 POST — Criar medição

Body:
```json
{ "mes": "2025-06" }
```

- O backend calcula `periodo_inicio = primeiro dia do mês` e `periodo_fim = último dia do mês`
- Valida que não existe outra medição com `periodo_inicio` no mesmo mês para esta versão → 422 com mensagem `"Já existe uma medição para este mês"`
- Versão bloqueada → 409
- Cria com `linhas_json` pré-populado com os valores da medição anterior mais recente (se existir), ou `{}` se for a primeira
- Retorna o objeto `MedicaoOut` criado com status 201

### 4.4 PATCH — Atualizar linhas

Path: `/versoes/{id}/medicoes/{medicao_id}`

Body:
```json
{ "linhas_json": {"42": 35.0, "43": 25.0} }
```

- Versão bloqueada → 409
- Valida que a medição pertence à versão (e indiretamente à empresa) → 404 se não encontrada
- O mês (`periodo_inicio`/`periodo_fim`) é imutável — PATCH só atualiza `linhas_json`
- Sem validação de soma ou range no backend; o frontend valida 0–100

### 4.5 Regras de negócio

- **Isolamento:** todos os endpoints verificam `versao.obra.empresa_id == usuario.empresa_id`
- **Versão bloqueada:** POST e PATCH retornam 409
- **Mês duplicado:** POST retorna 422
- **Sem deleção:** não há endpoint DELETE — medições são imutáveis em identidade, editáveis em conteúdo
- **Sem validação de soma:** backend armazena qualquer percentual; frontend valida exibição

### 4.6 Testes (`tests/backend/test_medicoes.py`)

- GET lista medições ordenadas por periodo_inicio desc
- GET retorna lista vazia para versão sem medições
- POST cria medição com linhas_json vazio e periodo correto
- POST com mês duplicado retorna 422
- POST em versão bloqueada retorna 409
- PATCH atualiza linhas_json corretamente
- PATCH em versão bloqueada retorna 409
- Isolamento: empresa B não acessa medições de empresa A (GET e POST)

---

## 5. Frontend

### 5.1 Arquivos

**Novos:**
- `frontend/src/api/medicoes.ts`
- `frontend/src/components/planilha/MedicaoTab.tsx`
- `frontend/src/components/planilha/MedicaoGrade.tsx`

**Modificados:**
- `frontend/src/types.ts` — adiciona `MedicaoData`
- `frontend/src/pages/PlanilhaPage.tsx` — adiciona aba Medição

### 5.2 Tipos (`src/types.ts`)

```ts
export interface MedicaoData {
  id: number
  periodo_inicio: string   // "2025-06-01"
  periodo_fim: string      // "2025-06-30"
  linhas_json: Record<string, number>  // {"42": 35.0}
  criada_por: number | null
}
```

### 5.3 API (`src/api/medicoes.ts`)

```ts
getMedicoes(versaoId: number): Promise<MedicaoData[]>
postMedicao(versaoId: number, mes: string): Promise<MedicaoData>
patchMedicao(versaoId: number, medicaoId: number, linhas_json: Record<string, number>): Promise<void>
```

### 5.4 MedicaoTab

Orquestrador. Carrega em paralelo na montagem:
- `getCronograma(versaoId)` — lista de itens com descrição, total_sem_bdi e distribuicao_json
- `getMedicoes(versaoId)` — histórico de medições

**Estados:**
- **loading:** skeleton
- **sem medições:** mensagem "Nenhuma medição registrada" + botão "Nova Medição"
- **com medições:** dropdown de seleção + grade + botão "Nova Medição"

**"Nova Medição"** abre um modal simples com `<input type="month">`. Validação frontend: mês não pode ser igual a um já existente. Ao confirmar, chama `postMedicao` e seleciona a nova medição automaticamente.

**Seletor de medição:** dropdown no topo com todas as medições formatadas como "Jun/2025", "Mai/2025"... Trocar a seleção re-renderiza a grade com os dados da medição selecionada.

### 5.5 MedicaoGrade

**Estrutura da tabela:**

```
┌─────────────────────────┬──────────┬─────────┬──────────┬──────┬─────────────┐
│ Serviço          Total  │ Plan. %  │ Ant. %  │ Atual %  │ Δ %  │ Valor R$    │
├─────────────────────────┼──────────┼─────────┼──────────┼──────┼─────────────┤
│ ✓ Terraplanagem  R$45k  │   40%    │   22%   │ [ 35 ]   │ +13  │ R$ 15.750   │
│ ⚠ Pavimentação   R$120k │   30%    │   15%   │ [ 25 ]   │ +10  │ R$ 30.000   │
├─────────────────────────┼──────────┼─────────┼──────────┼──────┼─────────────┤
│ Período: R$ 45.750      │          │         │          │      │             │
│ Acumulado: R$ 124.500   │          │         │          │      │  38%        │
└─────────────────────────┴──────────┴──────────┴─────────┴──────┴─────────────┘
```

**Coluna Serviço:** descricao do item (via cronograma linhas) + total_sem_bdi formatado em BRL. Indicador ✓ verde se Atual% ≤ 100, ⚠ vermelho se ultrapassar.

**Coluna Plan. %:** soma dos percentuais do `distribuicao_json` do cronograma do item para todos os meses do cronograma até e incluindo o mês da medição selecionada. Coluna **oculta** se `cronograma_inicio == null`.

**Coluna Ant. %:** `linhas_json[item_id]` da medição imediatamente anterior (ordenadas por `periodo_inicio`); 0 se for a primeira medição.

**Coluna Atual %:** `<input type="number" min=0 max=100 step=0.01>`. Modo leitura em versão bloqueada. Auto-save com debounce 300ms no blur via `patchMedicao`. Spinner sutil durante o save.

**Coluna Δ %:** Atual% − Ant% calculado no frontend. Formatado com sinal (+13, −2). Texto verde se positivo, vermelho se negativo.

**Coluna Valor R$:** `(Atual% / 100) × total_sem_bdi` do item, formatado em BRL.

**Rodapé fixo (2 linhas, fundo escuro):**
- **Período R$:** `Σ (Δ% / 100 × total_sem_bdi)` — valor novo medido neste período
- **Acumulado R$:** `Σ (Atual% / 100 × total_sem_bdi)` — valor total executado até agora; percentual sobre `versao.total_sem_bdi`

**Teclado:** Enter move para o item abaixo/acima (mesmo padrão do CronogramaGrade).

---

## 6. Fora do escopo deste módulo

- Comparativo planejado × realizado como gráfico (Curva S — Módulo 7)
- Relatório de desvios por grupo exportável (Módulo 7)
- Medições em versões bloqueadas com comparação entre versões (Módulo 7)
- Importação de medições via Excel

---

## 7. Dependências

- Nenhuma dependência nova de pacote
- Reutiliza `getCronograma()` para obter a lista de itens com descrições e totais
- Modelo `Medicao` já existe no banco — sem migração
