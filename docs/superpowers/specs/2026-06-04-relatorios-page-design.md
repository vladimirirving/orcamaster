# Módulo 16 — Página de Relatórios: Design Spec

**Data:** 2026-06-04
**Status:** Aprovado

---

## Objetivo

Criar a página `/relatorios` (atualmente link morto na TopBar) que consolida todos os downloads disponíveis por obra/versão, e limpar os outros links mortos da TopBar.

---

## Contexto

- TopBar tem 6 links sem rota: `Orçamento`, `BDI`, `Cronograma`, `Medição`, `Relatórios`, `Base de Comp.` — apenas "Relatórios" merece página própria; os outros são funcionalidades internas ao fluxo de obra
- Exports já implementados no backend:
  - `GET /versoes/{id}/proposta/export` → PDF proposta
  - `GET /versoes/{id}/curva-abc/export` → XLSX curva ABC
- Funções de download já existem no frontend:
  - `downloadPropostaPdf(versaoId)` em `@/api/proposta`
  - `downloadCurvaAbcExcel(versaoId)` em `@/api/curvaAbc`

---

## Arquitetura — apenas frontend

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `frontend/src/pages/RelatoriosPage.tsx` | Criar | Lista obras com versão ativa + botões de download |
| `frontend/src/app.tsx` | Modificar | Registrar rota `/relatorios` → `<RelatoriosPage />` |
| `frontend/src/components/layout/TopBar.tsx` | Modificar | Remover 5 links mortos; manter Dashboard · Obras · Relatórios |

Nenhuma nova chamada de API — reutiliza `getObras`, `getVersoes`, `downloadPropostaPdf`, `downloadCurvaAbcExcel`.

---

## RelatoriosPage

### Carregamento

1. `getObras()` — busca todas as obras da empresa
2. Para cada obra, `getVersoes(obraId)` — em paralelo via `Promise.all`
3. Para cada obra, deriva a **versão ativa**: primeira versão com `bloqueada === false` e `deletada_em === null`; se não houver, a obra é omitida da listagem

### Layout

```
Relatórios
─────────────────────────────────────
Rodovia SP-150                    Versão 3
  [↓ PDF Proposta]  [↓ XLSX Curva ABC]

Ponte Rio Verde                   Versão 1
  [↓ PDF Proposta]  [↓ XLSX Curva ABC]
─────────────────────────────────────
```

- Cada obra em um card `bg-white rounded-xl border border-gray-200`
- Título da obra + chip "Versão N" à direita
- Dois botões de download lado a lado
- Durante o download de um botão, ele mostra spinner + "Baixando…" e fica disabled (o outro botão da mesma obra continua habilitado)
- Erro de download → toast `'Erro ao baixar <tipo>'`

### Estados especiais

- **Carregando:** skeleton de 3 cards
- **Nenhuma obra com versão ativa:** mensagem "Nenhuma obra com versão ativa encontrada."
- **Erro no fetch inicial:** toast de erro

---

## TopBar

Remover os 5 itens do array `NAV_ITEMS` que não têm rota:

```ts
// Remover:
{ label: 'Orçamento', to: '/orcamento' },
{ label: 'BDI', to: '/bdi' },
{ label: 'Cronograma', to: '/cronograma' },
{ label: 'Medição', to: '/medicao' },
{ label: 'Base de Comp.', to: '/composicoes' },

// Manter:
{ label: 'Dashboard', to: '/' },
{ label: 'Obras', to: '/obras' },
{ label: 'Relatórios', to: '/relatorios' },
```

---

## app.tsx

Adicionar:
```tsx
import RelatoriosPage from '@/pages/RelatoriosPage'
// ...
<Route path="/relatorios" element={<RelatoriosPage />} />
```

---

## Fora de Escopo

- Export de planilha orçamentária como PDF (novo serviço — módulo futuro)
- Filtros por período ou status
- Paginação (poucos registros esperados)
- Download em lote de múltiplas obras
