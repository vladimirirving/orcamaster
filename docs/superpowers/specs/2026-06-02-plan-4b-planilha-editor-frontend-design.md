# Plan 4b — Planilha Editor Frontend Design

**Data:** 2026-06-02
**Escopo:** Frontend puro. Backend já implementado (Plans 1–4a).

---

## Objetivo

Construir a interface de usuário do editor de orçamento: listagem de obras, gestão de versões e o editor de planilha hierárquico (grupos, subgrupos, itens, BDI, composições).

---

## Páginas e rotas

| Rota | Componente | Descrição |
|------|-----------|-----------|
| `/obras` | `ObrasPage` | Lista de obras em cards; botão "Nova Obra" |
| `/obras/:id` | `ObraDetailPage` | Versões da obra; ações por versão |
| `/obras/:obraId/versoes/:versaoId` | `PlanilhaPage` | Editor completo da versão |

Rotas adicionadas em `App.tsx` dentro do `<ProtectedRoute>` existente.

---

## Estrutura de arquivos

```
frontend/src/
├── api/
│   ├── client.ts              (existente — não modificar)
│   ├── obras.ts               GET /obras, POST /obras
│   ├── versoes.ts             GET /obras/:id/versoes, POST /obras/:id/versoes,
│   │                          POST /versoes/:id/duplicar, DELETE /versoes/:id,
│   │                          POST /versoes/:id/restore
│   ├── grupos.ts              GET /versoes/:id/grupos, POST /versoes/:id/grupos,
│   │                          POST /grupos/:id/subgrupos, PATCH /grupos/:id,
│   │                          DELETE /grupos/:id
│   ├── itens.ts               GET /grupos/:id/itens, POST /grupos/:id/itens,
│   │                          PATCH /itens/:id, DELETE /itens/:id,
│   │                          PATCH /itens/:id/composicao,
│   │                          POST /itens/:id/atualizar-preco
│   ├── bdi.ts                 GET/PUT/DELETE /versoes/:id/bdi
│   └── composicoes.ts         GET /composicoes (com query param q=)
├── stores/
│   └── orcamento.ts           Zustand store
├── pages/
│   ├── ObrasPage.tsx
│   ├── ObraDetailPage.tsx
│   └── PlanilhaPage.tsx
└── components/
    └── planilha/
        ├── PlanilhaTabela.tsx
        ├── PlanilhaLinha.tsx
        ├── PainelLateral.tsx
        ├── FormItem.tsx
        ├── FormGrupo.tsx
        ├── BuscaComposicao.tsx
        └── BDIModal.tsx
```

---

## TypeScript types

```ts
// Espelham os schemas do backend

interface Obra {
  id: number
  nome: string
  tipo_obra: string
  estado: string
  data_criacao: string
}

interface Versao {
  id: number
  obra_id: number
  numero: number
  nome: string | null
  bloqueada: boolean
  deletada_em: string | null
  total_sem_bdi: string
  total_com_bdi: string
}

interface Grupo {
  id: number
  versao_id: number
  pai_id: number | null
  nome: string
  codigo: string | null
  ordem: number
  filhos: Grupo[]
}

interface Item {
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

interface BDI {
  id: number
  versao_id: number
  ac: string; sg: string; r: string; df: string; lucro: string
  iss: string; pis: string; cofins: string
  bdi_composto: string
}

interface Composicao {
  id: number
  origem: string
  codigo: string
  descricao: string
  unidade: string
  preco_unitario: string
}
```

---

## Zustand store (`stores/orcamento.ts`)

```ts
interface OrcamentoState {
  versao: Versao | null
  bdi: BDI | null
  grupos: Grupo[]           // grupos raiz com filhos aninhados
  itens: Record<number, Item[]>  // grupo_id → itens
  gruposAbertos: Set<number>
  painelSelecionado: { tipo: 'item' | 'grupo'; id: number } | null

  setVersao: (v: Versao) => void
  setBdi: (b: BDI | null) => void
  setGrupos: (gs: Grupo[]) => void
  setItens: (grupoId: number, is: Item[]) => void
  toggleGrupo: (grupoId: number) => void
  selecionarPainel: (s: { tipo: 'item' | 'grupo'; id: number } | null) => void
}
```

---

## Componentes

### `ObrasPage`

- Monta: `GET /obras` → lista de obras
- Layout: grid de cards (nome, tipo_obra, estado)
- Botão "Nova Obra": modal com campos `nome` (obrigatório), `tipo_obra` (select), `estado` (select, default `em_elaboracao`), `data_criacao` (date, default hoje)
- Clicar no card: navega para `/obras/:id`

### `ObraDetailPage`

- Monta: `GET /obras/:id` (para nome da obra) + `GET /obras/:id/versoes`
- Tabela de versões: número, nome, estado (badge: ativa / bloqueada / deletada), total S/BDI, total C/BDI
- Ações por linha:
  - **Abrir**: navega para `/obras/:obraId/versoes/:versaoId`
  - **Duplicar**: `POST /versoes/:id/duplicar` → recarrega lista
  - **Bloquear/restaurar**: `DELETE /versoes/:id` (soft-delete) ou `POST /versoes/:id/restore`
- Botão "Nova Versão": `POST /obras/:id/versoes` com `numero` calculado automaticamente (max + 1 feito no backend)
- Breadcrumb: Obras › [nome da obra]

### `PlanilhaPage`

**Toolbar:**
- Breadcrumb: Obras › [nome da obra] › Versão [numero]
- Badge BDI: mostra `bdi_composto` em % se configurado, ou "Sem BDI" — clicar abre `BDIModal`
- Botão "+ Grupo"

**Corpo:**
- `PlanilhaTabela` ocupa a área central
- `PainelLateral` aparece à direita quando algo está selecionado (largura fixa 320px; planilha encolhe)

**Footer:**
- Total S/BDI: `versao.total_sem_bdi`
- Total C/BDI: `versao.total_com_bdi`

**Montagem:**
1. `GET /versoes/:id/grupos` → popula `grupos` na store
2. `GET /versoes/:id/bdi` → popula `bdi` (404 = sem BDI, não é erro)
3. `GET /obras/:obraId` → para breadcrumb

### `PlanilhaTabela`

Tabela com colunas: Cód, Descrição, Un, Qtde, Preço unit S/BDI, Total.

Hierarquia de linhas (via `PlanilhaLinha`):
- **Linha de grupo raiz**: fundo escuro, fonte bold, toggle collapse. Colunas: descrição (colspan), total acumulado. Botões inline: "+ Subgrupo", "+ Item direto".
- **Linha de subgrupo**: recuo 1 nível, mesma estrutura. Botão inline: "+ Item".
- **Linha de item**: recuo 2 níveis se em subgrupo, 1 nível se em grupo raiz. Badge ⚠️ amarelo se `requer_revisao=true`. Todas as colunas preenchidas.

Clicar numa linha chama `selecionarPainel`. Linha selecionada tem highlight azul sutil.

Itens são carregados lazily: ao expandir um grupo, se `itens[grupo.id]` não existir, chama `GET /grupos/:id/itens`.

### `PainelLateral`

Painel fixo à direita (320px), fechável com ✕.

**Modo grupo/subgrupo** (`FormGrupo`):
- Campos: nome (text), código (text, opcional), ordem (number)
- Botões: Salvar (`PATCH /grupos/:id`), Excluir (confirma inline → `DELETE /grupos/:id`)
- Link "+ Adicionar item aqui" → cria item vazio no grupo via `POST /grupos/:id/itens`

**Modo item** (`FormItem`):
- Campos: quantidade (number), unidade (text), ordem (number)
- Badge ⚠️ + botão "Atualizar preço" se `requer_revisao=true` → `POST /itens/:id/atualizar-preco`
- Seção "Composição vinculada": mostra código + descrição atual (ou "Nenhuma")
- `BuscaComposicao` abaixo: campo de busca para trocar a composição
- Botões: Salvar (`PATCH /itens/:id`), Excluir (confirma inline → `DELETE /itens/:id`)

### `BuscaComposicao`

- Input com debounce 300ms → `GET /composicoes?q=<texto>`
- Lista resultados: código, descrição, unidade, preço
- Clicar num resultado: `PATCH /itens/:id/composicao` com `{ composicao_id }` → fecha lista, atualiza item no painel

### `BDIModal`

- Abre via Radix Dialog
- 8 campos numéricos (AC, SG, R, DF, Lucro, ISS, PIS, COFINS) — todos como percentual (ex: digitar `5` = 0.05 enviado)
- Preview calculado em tempo real: `bdi_composto = ((1 + ac + sg + r + df + lucro) / (1 - iss - pis - cofins)) - 1`
- Validação frontend: ISS + PIS + COFINS < 100% (bloqueia submit)
- Botão Salvar: `PUT /versoes/:id/bdi`
- Botão "Remover BDI" (se BDI existe): `DELETE /versoes/:id/bdi` com confirmação inline
- Ao fechar: re-chama `GET /obras/:obraId/versoes` e atualiza `versao` na store para refletir `total_com_bdi` recalculado no footer

---

## API modules

Cada arquivo em `api/` exporta funções tipadas que usam o `client` Axios existente:

```ts
// api/obras.ts
export const getObras = (): Promise<Obra[]>
export const createObra = (data: {...}): Promise<Obra>

// api/versoes.ts
export const getVersoes = (obraId: number): Promise<Versao[]>
export const createVersao = (obraId: number): Promise<Versao>
export const duplicarVersao = (versaoId: number): Promise<Versao>
export const softDeleteVersao = (versaoId: number): Promise<void>
export const restoreVersao = (versaoId: number): Promise<Versao>

// api/grupos.ts
export const getGrupos = (versaoId: number): Promise<Grupo[]>
export const createGrupo = (versaoId: number, data: {...}): Promise<Grupo>
export const createSubgrupo = (grupoId: number, data: {...}): Promise<Grupo>
export const updateGrupo = (grupoId: number, data: Partial<{...}>): Promise<Grupo>
export const deleteGrupo = (grupoId: number): Promise<void>

// api/itens.ts
export const getItens = (grupoId: number): Promise<Item[]>
export const createItem = (grupoId: number, data: {...}): Promise<Item>
export const updateItem = (itemId: number, data: Partial<{...}>): Promise<Item>
export const deleteItem = (itemId: number): Promise<void>
export const vincularComposicao = (itemId: number, composicaoId: number): Promise<Item>
export const atualizarPreco = (itemId: number): Promise<Item>

// api/bdi.ts
export const getBdi = (versaoId: number): Promise<BDI>
export const upsertBdi = (versaoId: number, data: {...}): Promise<BDI>
export const deleteBdi = (versaoId: number): Promise<void>

// api/composicoes.ts
export const searchComposicoes = (q: string): Promise<Composicao[]>
```

---

## Feedback ao usuário

- **Toasts** (Radix Toast): todas as ações de escrita mostram toast de sucesso ("Item salvo", "BDI aplicado", "Versão duplicada") ou erro (mensagem do backend).
- **Loading states**: botões mostram spinner durante request; tabela mostra skeleton na montagem inicial.
- **Confirmação inline**: deletar grupo/item/BDI mostra botão "Confirmar" na mesma área — sem modal separado.

---

## Testes

### Unitários (Vitest)

```ts
// src/utils/bdi.test.ts
describe('calcBdiComposto', () => {
  it('calcula corretamente com ac=5%, resto zero', () => {
    expect(calcBdiComposto(0.05, 0, 0, 0, 0, 0, 0, 0)).toBeCloseTo(0.05, 5)
  })
  it('lança erro quando ISS+PIS+COFINS >= 1', () => {
    expect(() => calcBdiComposto(0, 0, 0, 0, 0, 0.5, 0.3, 0.2)).toThrow()
  })
})
```

### Checklist manual

- [ ] Criar obra → aparece na lista
- [ ] Criar versão → aparece na tabela com número incrementado
- [ ] Duplicar versão → nova versão aparece com mesma estrutura
- [ ] Adicionar grupo → aparece na planilha
- [ ] Adicionar subgrupo → aparece com recuo dentro do grupo
- [ ] Adicionar item → aparece com campos em branco
- [ ] Buscar composição e vincular → `preco_unitario_sem_bdi` preenchido, total atualizado
- [ ] Badge ⚠️ aparece quando `requer_revisao=true`; "Atualizar preço" limpa o badge
- [ ] Configurar BDI → footer mostra total C/BDI atualizado
- [ ] Remover BDI → total C/BDI volta a zero
- [ ] Deletar item → desaparece da planilha; totais recalculados

---

## Regras de negócio consolidadas

1. Versão bloqueada: planilha em modo somente leitura (painel lateral desabilitado, botões ocultos)
2. Versão deletada: não aparece na lista por padrão (filtrar `deletada_em != null`)
3. `Item.total` nunca é enviado ao backend — calculado pelo PostgreSQL
4. `bdi_composto` nunca é enviado — calculado pelo backend
5. Percentuais BDI são armazenados como decimais (5% → `0.0500`); o frontend exibe multiplicado por 100
6. Busca de composição usa debounce 300ms para evitar flood de requests
7. Itens carregados lazily por grupo (não no mount da página inteira)
