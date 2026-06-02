# Cronograma Físico-Financeiro — Design Spec

**Data:** 2026-06-02
**Status:** Aprovado para implementação
**Módulo:** 5 de 11

---

## 1. Objetivo

Adicionar ao editor de planilha a aba **Cronograma**, onde o orçamentista distribui percentuais de execução por mês para cada item da planilha. O sistema calcula automaticamente o total financeiro mensal e o percentual acumulado (base da Curva S), que serão usados na geração de documentos (Módulo 7) e no Dashboard (Módulo 7).

---

## 2. Navegação

O cronograma vive como **aba dentro de `PlanilhaPage`** (`/obras/:obraId/versoes/:versaoId`). A toolbar ganha dois tabs:

```
[ Planilha ]  [ Cronograma ]
```

Trocar de aba não recarrega dados — o store `useOrcamento` mantém grupos/itens já carregados. O BDI button e os totais do rodapé permanecem visíveis em ambas as abas.

---

## 3. Período do Cronograma

O período é definido por dois campos no modelo `Versao`: `cronograma_inicio` e `cronograma_fim` (formato `YYYY-MM`, nullable).

**Primeiro acesso:** se o período não estiver configurado, o tab exibe `CronogramaConfigForm` — dois inputs `<input type="month">` (nativo HTML) e botão "Definir período". Ao salvar, a grade é exibida imediatamente.

**Período já configurado:** a grade é exibida diretamente. O toolbar do tab exibe botão "Alterar período" que reabre o formulário de configuração (mantendo as linhas existentes — alterar o período não apaga `distribuicao_json`, apenas muda as colunas visíveis).

---

## 4. Backend

### 4.1 Migration

```sql
ALTER TABLE versao ADD COLUMN cronograma_inicio VARCHAR(7);
ALTER TABLE versao ADD COLUMN cronograma_fim VARCHAR(7);
```

Ambos nullable. Sem valor padrão.

### 4.2 Router

Montado em `/versoes/{versao_id}/cronograma`. Todos os endpoints exigem autenticação e verificam que a versão pertence à empresa do usuário autenticado.

| Método | Path | Descrição |
|--------|------|-----------|
| `GET` | `/versoes/{id}/cronograma` | Retorna config + todas as linhas |
| `PATCH` | `/versoes/{id}/cronograma/config` | Atualiza `cronograma_inicio` e `cronograma_fim` |
| `PATCH` | `/versoes/{id}/cronograma/linhas/{item_id}` | Upsert do `distribuicao_json` de um item |

### 4.3 Schema de resposta — GET

```json
{
  "cronograma_inicio": "2025-01",
  "cronograma_fim": "2026-12",
  "linhas": [
    {
      "item_id": 42,
      "descricao": "Terraplanagem",
      "unidade": "m³",
      "quantidade": "500.000000",
      "total_sem_bdi": "45000.00",
      "distribuicao_json": {"2025-01": 40.0, "2025-02": 60.0}
    }
  ]
}
```

As linhas são ordenadas por `grupo.ordem`, `item.ordem`. Itens sem `CronogramaLinha` aparecem com `distribuicao_json: {}`.

`descricao` = `item.composicao.descricao` se o item tiver composição vinculada; caso contrário, string vazia `""`. O model `Item` recebe um relacionamento `composicao` (lazy joined) para viabilizar isso sem query extra. O frontend exibe `"—"` para itens sem composição.

### 4.4 Regras de negócio

- **Versão bloqueada:** PATCH config e PATCH linha retornam 403.
- **Armazenamento de zeros:** o PATCH linha remove do JSON meses com percentual = 0 antes de persistir (ex: `{"2025-01": 0.0, "2025-02": 60.0}` → `{"2025-02": 60.0}`).
- **Sem validação de soma no backend:** a validação de soma = 100% é responsabilidade do frontend para exibição; o backend só armazena o que recebe.
- **Isolamento:** todos os endpoints verificam `versao.obra.empresa_id == usuario.empresa_id`.

### 4.5 Testes (`tests/backend/test_cronograma.py`)

- GET retorna linhas de todos os itens da versão (com e sem CronogramaLinha existente)
- PATCH config persiste `cronograma_inicio` e `cronograma_fim`
- PATCH linha cria `CronogramaLinha` se não existir (upsert)
- PATCH linha atualiza linha existente
- PATCH linha remove zeros do JSON antes de persistir
- Versão bloqueada retorna 403 em ambos os PATCHs
- Isolamento: usuário de empresa B não acessa versão de empresa A

---

## 5. Frontend

### 5.1 Arquivos

**Novos:**
- `frontend/src/api/cronograma.ts`
- `frontend/src/components/planilha/CronogramaTab.tsx`
- `frontend/src/components/planilha/CronogramaConfigForm.tsx`
- `frontend/src/components/planilha/CronogramaGrade.tsx`

**Modificados:**
- `frontend/src/pages/PlanilhaPage.tsx` — adiciona tab state e renderiza `<CronogramaTab>`
- `frontend/src/types.ts` — adiciona `CronogramaLinhaData`, `CronogramaConfig`, e campos `cronograma_inicio`/`cronograma_fim` em `Versao`
- `backend/app/models/item.py` — adiciona relacionamento `composicao` (Optional, lazy joined)

### 5.2 Tipos novos (`src/types.ts`)

```ts
// Adicionado em Versao:
cronograma_inicio: string | null
cronograma_fim: string | null

// Novos:
interface CronogramaLinhaData {
  item_id: number
  descricao: string
  unidade: string
  quantidade: string
  total_sem_bdi: string
  distribuicao_json: Record<string, number>  // {"2025-01": 40.0}
}

interface CronogramaConfig {
  cronograma_inicio: string | null
  cronograma_fim: string | null
  linhas: CronogramaLinhaData[]
}
```

### 5.3 API (`src/api/cronograma.ts`)

```ts
getCronograma(versaoId: number): Promise<CronogramaConfig>
patchCronogramaConfig(versaoId: number, data: { cronograma_inicio: string; cronograma_fim: string }): Promise<void>
patchCronogramaLinha(versaoId: number, itemId: number, distribuicao_json: Record<string, number>): Promise<void>
```

### 5.4 PlanilhaPage — tab state

```tsx
const [tab, setTab] = useState<'planilha' | 'cronograma'>('planilha')
```

Dois botões de tab abaixo da toolbar existente. O conteúdo do body (`PlanilhaTabela` + `PainelLateral` ou `CronogramaTab`) é condicionado ao tab ativo. Ambas as abas compartilham o rodapé de totais existente.

### 5.5 CronogramaTab

Orquestrador. Carrega `getCronograma(versaoId)` na montagem. Estados:

- **loading:** skeleton
- **sem período configurado** (`cronograma_inicio == null`): renderiza `<CronogramaConfigForm>`
- **período configurado:** renderiza `<CronogramaGrade>` + botão "Alterar período" no toolbar

### 5.6 CronogramaConfigForm

Dois `<input type="month">` (Início e Fim). Validação frontend: fim deve ser ≥ início. Botão "Definir período" dispara `patchCronogramaConfig` e atualiza o estado local do `CronogramaTab`.

### 5.7 CronogramaGrade

**Estrutura da tabela:**

```
┌─────────────────────────┬──────┬──────┬──────┬──────┐
│ Serviço          Total  │ Jan  │ Fev  │ Mar  │ ...  │  ← header (sticky top)
├─────────────────────────┼──────┼──────┼──────┼──────┤
│ ✓ Terraplanagem  R$45k  │ 40%  │ 60%  │      │      │  ← linha de item
│ ⚠ Pavimentação   R$120k │      │ 30%  │ 50%  │      │
├─────────────────────────┼──────┼──────┼──────┼──────┤
│ Total R$                │ 18k  │ 90k  │ 60k  │      │  ← rodapé fixo
│ Acumulado R$            │ 18k  │108k  │168k  │      │
│ Acumulado %             │ 11%  │ 64%  │ 100% │      │  ← azul
└─────────────────────────┴──────┴──────┴──────┴──────┘
```

**Coluna esquerda:** largura fixa, não rola com os meses. Exibe indicador de validação (✓ verde / ⚠ vermelho) + descrição do item + total sem BDI formatado em BRL.

**Colunas de meses:** geradas dinamicamente entre `cronograma_inicio` e `cronograma_fim`. Scroll horizontal. Cada célula:

- Estado normal: exibe o percentual formatado (`40%`) ou vazio
- Fundo azul claro (`bg-blue-50`) se percentual > 0
- Ao clicar: `<input type="number" min=0 max=100 step=0.01>` substitui o display
- Tab: move para próximo mês (mesmo item)
- Enter / Shift+Enter: move para mesmo mês no item abaixo / acima
- Blur: dispara `patchCronogramaLinha` com o `distribuicao_json` atualizado daquele item; célula fica desabilitada durante o save (spinner sutil)

**Rodapé (3 linhas fixas, fundo escuro):**

- **Total R$** por mês: `Σ (item.total_sem_bdi × percentual / 100)` para todos os itens naquele mês
- **Acumulado R$**: soma corrente do Total R$
- **Acumulado %**: `acumulado_R$ / versao.total_sem_bdi × 100`, formatado com 1 casa decimal, texto azul

**Validação por item:** `Σ percentuais === 100` (tolerância ±0.01). Ícone ✓ verde se válido, ⚠ vermelho se não. Banner no topo da grade: `"N itens sem distribuição completa"` em amarelo — informativo, não bloqueia o save.

---

## 6. Fora do escopo deste módulo

- Curva S como gráfico (vai para Módulo 7 — Geração de Documentos / Dashboard)
- Importação de cronograma via Excel
- Múltiplos BDIs por tipo de serviço
- Comparação de cronogramas entre versões

---

## 7. Dependências

- Nenhuma dependência nova de pacote
- `input[type=month]` é nativo HTML5 — suportado em todos os browsers modernos
- Recharts não é necessário neste módulo
