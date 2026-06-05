# Módulo 17 — Banco de Composições Próprias: Design Spec

**Data:** 2026-06-05
**Status:** Aprovado

---

## Objetivo

Criar a página `/composicoes` onde o administrador gerencia as composições próprias da empresa — criando, editando e excluindo serviços com preço direto que não existem no SINAPI/SICRO. Recoloca o link "Base de Comp." na TopBar.

---

## Contexto

O backend já tem CRUD completo:

| Endpoint | Responsabilidade |
|----------|-----------------|
| `GET /composicoes?origem=propria&q=...` | Listar próprias com busca |
| `POST /composicoes` | Criar (requer admin) |
| `PATCH /composicoes/{id}` | Editar (só próprias) |
| `DELETE /composicoes/{id}` | Excluir (só próprias, 204) |

`ComposicaoCreate` requer: `codigo`, `descricao`, `unidade`, `preco_unitario`.

O tipo `Composicao` em `types.ts` está simplificado — não tem `empresa_id`. Precisa de extensão para distinguir próprias de SINAPI/SICRO na UI.

---

## Arquitetura — apenas frontend

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `frontend/src/types.ts` | Modificar | Adicionar `empresa_id?: number \| null` ao `Composicao` |
| `frontend/src/api/composicoes.ts` | Modificar | Adicionar 4 funções CRUD |
| `frontend/src/pages/ComposicoesPage.tsx` | Criar | Tabela + busca + botão "Nova" |
| `frontend/src/components/composicoes/ComposicaoModal.tsx` | Criar | Modal criar/editar |
| `frontend/src/app.tsx` | Modificar | Rota `/composicoes` |
| `frontend/src/components/layout/TopBar.tsx` | Modificar | Readicionar "Base de Comp." |

---

## Tipos

Adicionar `empresa_id` ao `Composicao` em `types.ts`:

```ts
export interface Composicao {
  id: number
  empresa_id: number | null   // null = SINAPI/SICRO; number = própria
  origem: string
  codigo: string
  descricao: string
  unidade: string
  preco_unitario: string
}
```

---

## API (`frontend/src/api/composicoes.ts`)

```ts
export const listComposicoesProprias = (q?: string): Promise<Composicao[]> =>
  api.get<Composicao[]>('/composicoes', {
    params: { origem: 'propria', q: q || undefined, limit: 200 },
  }).then(r => r.data)

export const createComposicao = (data: {
  codigo: string; descricao: string; unidade: string; preco_unitario: string
}): Promise<Composicao> =>
  api.post<Composicao>('/composicoes', data).then(r => r.data)

export const updateComposicao = (
  id: number,
  data: { codigo?: string; descricao?: string; unidade?: string; preco_unitario?: string }
): Promise<Composicao> =>
  api.patch<Composicao>(`/composicoes/${id}`, data).then(r => r.data)

export const deleteComposicao = (id: number): Promise<void> =>
  api.delete(`/composicoes/${id}`)
```

---

## ComposicoesPage

### Acesso
Restrita a admin — redireciona para `/obras` se `papel !== 'admin'`.

### Layout

```
Banco de Composições
─────────────────────────────────────────────
[🔍 Buscar por código ou descrição     ] [+ Nova composição]

Código      Descrição                Unidade   Preço Unit.   Ações
SERV001     Limpeza de terreno       m²        R$ 12,00      ✎ 🗑
SERV002     Compactação manual       m³        R$ 35,00      ✎ 🗑
─────────────────────────────────────────────
```

- Busca dispara `listComposicoesProprias(q)` com debounce de 300ms
- Se busca vazia, carrega todas (`listComposicoesProprias()`)
- Tabela simples; sem paginação (limit=200)
- Coluna Ações: botão lápis abre `ComposicaoModal` pré-preenchido; botão lixeira mostra confirmação inline na linha (`[Confirmar exclusão] [Cancelar]`) antes de chamar `deleteComposicao`
- Estado vazio: "Nenhuma composição própria cadastrada."
- Estado vazio + busca: "Nenhum resultado para «{q}»."
- Loading: skeleton de 5 linhas

### Exclusão inline
Clicar em 🗑 substitui os botões da linha por `[Confirmar]` e `[Cancelar]`. `[Confirmar]` chama `deleteComposicao(id)` e recarrega a lista. Sem modal adicional.

---

## ComposicaoModal

### Props
```ts
interface Props {
  composicao?: Composicao  // undefined = criar; definido = editar
  onClose: () => void
  onSuccess: () => void
}
```

### Campos
| Campo | Tipo | Validação |
|-------|------|-----------|
| Código | texto | obrigatório |
| Descrição | texto | obrigatório |
| Unidade | texto | obrigatório |
| Preço Unitário | number (step 0.01) | > 0 |

- Título: "Nova composição" ou "Editar composição"
- Submit chama `createComposicao` ou `updateComposicao`
- Erro de duplicata exibido inline: "Código já cadastrado." (detectado via `response.status >= 400`)
- Após sucesso: `onSuccess()` → lista recarrega, modal fecha
- Botão submit desabilitado se algum campo inválido ou enquanto salva

---

## TopBar

Readicionar "Base de Comp." no array `NAV_ITEMS` entre "Obras" e "Relatórios":

```ts
const NAV_ITEMS = [
  { label: 'Dashboard', to: '/' },
  { label: 'Obras', to: '/obras' },
  { label: 'Base de Comp.', to: '/composicoes' },
  { label: 'Relatórios', to: '/relatorios' },
]
```

---

## app.tsx

Adicionar:
```tsx
import ComposicoesPage from '@/pages/ComposicoesPage'
// ...
<Route path="/composicoes" element={<ComposicoesPage />} />
```

---

## Testes

Nenhum teste de backend necessário (CRUD já coberto pelos testes existentes de composições). Verificação via `tsc --noEmit`.

---

## Fora de Escopo

- Edição de insumos (coeficientes mão-de-obra/material/equipamento) — módulo futuro
- Importação de arquivo CSV/XLSX de composições próprias
- Paginação além de 200 registros
- Acesso por orcamentista/visualizador (só admin gerencia o banco)
