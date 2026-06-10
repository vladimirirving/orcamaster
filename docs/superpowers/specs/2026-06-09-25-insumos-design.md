# Módulo 25 — Catálogo de Insumos

## Objetivo

Página autônoma `/insumos` para cadastro, consulta e gerenciamento de insumos de referência de preços (SINAPI, SICRO e Próprio), com barra de pesquisa completa e paginação.

---

## Modelo de dados

**Nova tabela: `insumo_item`** (separada da tabela `insumo` existente, que é BOM line item dentro de composição)

| Campo | Tipo | Notas |
|---|---|---|
| `id` | int PK | |
| `banco` | str(10) | `sinapi` \| `sicro` \| `propria` |
| `codigo` | str(50) | |
| `descricao` | str(500) | |
| `unidade` | str(20) | |
| `tipo` | str(20) | `mao_obra` \| `material` \| `equipamento` |
| `preco_nao_desonerado` | Decimal(15,6) | |
| `preco_desonerado` | Decimal(15,6) | |
| `estado` | str(2) nullable | UF (ex: SP, AP). Obrigatório para `sinapi`/`sicro`, nulo para `propria` |
| `data_referencia` | date | Primeiro dia do mês de referência (ex: 2019-08-01 → exibido como 08/2019) |
| `empresa_id` | FK nullable → empresa.id | Nulo para SINAPI/SICRO (global), preenchido para `propria` |

**Índice**: `(banco, estado, data_referencia)` para filtros rápidos.

---

## Backend

### Arquivos novos
- `backend/app/models/insumo_item.py`
- `backend/app/schemas/insumo_item.py`
- `backend/app/routers/insumo_item.py`
- `backend/alembic/versions/0008_insumo_item.py`

### Schemas
- `InsumoItemCreate`: banco (fixo `propria`), codigo, descricao, unidade, tipo, preco_nao_desonerado, preco_desonerado, estado (opcional), data_referencia
- `InsumoItemUpdate`: todos os campos opcionais
- `InsumoItemOut`: todos os campos + id
- `InsumoItemListOut`: `{ items: List[InsumoItemOut], total: int }`

### Rotas (`/insumos`)

| Método | Rota | Auth | Restrição |
|---|---|---|---|
| `GET` | `/insumos` | logado | Filtros: `q`, `banco`, `estado`, `tipo`, `data_ref` (YYYY-MM-DD), `order_by` (codigo\|descricao\|preco_nao_desonerado\|preco_desonerado), `page` (default 1). 50 itens/página. Retorna `{ items, total }` |
| `POST` | `/insumos` | admin | Apenas `banco=propria`. `empresa_id` setado automaticamente do usuário logado |
| `PATCH` | `/insumos/{id}` | admin | Apenas insumos `propria` da empresa do usuário |
| `DELETE` | `/insumos/{id}` | admin | Apenas insumos `propria` da empresa do usuário |

Tentativa de editar/deletar SINAPI ou SICRO → HTTP 403.

### Registro em `main.py`
```python
from app.routers import insumo_item
app.include_router(insumo_item.router)
```

---

## Frontend

### Arquivos novos
- `frontend/src/api/insumos_item.ts`
- `frontend/src/pages/InsumosPage.tsx`
- `frontend/src/components/insumos/InsumoItemModal.tsx`

### Arquivos modificados
- `frontend/src/App.tsx` — substituir placeholder `/insumos` por `<InsumosPage />`
- `frontend/vite.config.ts` — adicionar `/insumos` ao proxy (já existe entrada `/alertas` como referência)

### InsumosPage

**Layout: painel de pesquisa fixo no topo + tabela + paginação**

**Header:**
- Título "Insumos"
- Botão "+ Novo Insumo" (visível apenas para `papel === 'admin'`, abre modal com banco fixo em `propria`)

**Painel de pesquisa (fundo azul-índigo claro, com borda):**
- Linha 1: Filtro (text input "Descrição ou Código") | Ordenar por (dropdown) | Tipo (dropdown)
- Linha 2: Banco (dropdown) | Estado (dropdown) | Data Ref. (dropdown com meses disponíveis) | botão "🔍 Buscar"
- Busca acionada pelo botão (não ao vivo), exceto ao limpar o campo (retorna ao estado inicial)

**Dropdowns:**
- Ordenar por: Descrição (default), Código, Preço Não Desonerado, Preço Desonerado
- Tipo: Todos (default), Mão de Obra, Material, Equipamento
- Banco: Todos (default), SINAPI, SICRO, Próprio
- Estado: Todos (default) + 27 UFs em ordem alfabética
- Data Ref.: "Todas" (default) + lista de datas distintas presentes no banco (formato MM/YYYY)

**Tabela:**

| Coluna | Notas |
|---|---|
| Banco | Badge colorido: SINAPI=azul, SICRO=laranja, Próprio=verde |
| Código | Fonte monospace |
| Descrição | Coluna principal, truncada com tooltip |
| Unidade | |
| Tipo | |
| Não Desonerado | Alinhado à direita, `fmtBRL` |
| Desonerado | Alinhado à direita, `fmtBRL` |
| Ações | ✎ sempre visível para admin em `propria`; 🗑 com confirm inline. SINAPI/SICRO sem ações |

**Paginação:**
- `← Anterior` (desabilitado na página 1) | `X–Y de Z insumos` | `Próximo →` (desabilitado na última página)
- 50 itens por página

**Estados:**
- Loading: skeleton de 5 linhas
- Vazio: "Nenhum insumo encontrado para os filtros selecionados."
- Erro: toast de erro

### InsumoItemModal

Modal com grid 2 colunas:
- Linha 1: Banco (fixo "Próprio" ao criar, read-only) | Tipo (dropdown obrigatório)
- Linha 2: Código (obrigatório) | Unidade (obrigatório)
- Linha 3: Descrição (full width, obrigatório)
- Linha 4: Preço Não Desonerado | Preço Desonerado (ambos obrigatórios)
- Linha 5: Estado (opcional, dropdown 27 UFs) | Data de Referência (input `type=month`, obrigatório)
- Footer: Cancelar | Salvar

Validação no frontend: campos obrigatórios marcados com `*`, desabilita Salvar durante submit.

---

## Controle de acesso

- Qualquer usuário logado: pode listar/consultar (GET)
- Admin: pode criar, editar, deletar (somente `propria` da própria empresa)
- SINAPI/SICRO: somente leitura — sem botões de ação na tabela

---

## Testes backend

Arquivo: `backend/tests/test_insumo_item.py`

Casos:
1. Listar sem filtros → paginado
2. Filtrar por banco=sinapi
3. Filtrar por estado=SP
4. Filtrar por tipo=material
5. Filtrar por data_ref
6. Busca textual por código
7. Busca textual por descrição
8. Ordenar por preco_nao_desonerado
9. Admin cria insumo `propria`
10. Admin edita insumo `propria`
11. Admin deleta insumo `propria`
12. Admin tenta editar SINAPI → 403
13. Usuário comum tenta criar → 403
