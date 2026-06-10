# Módulo 18 — Clientes & Fornecedores: Design Spec

**Data:** 2026-06-05
**Status:** Aprovado
**Módulos anteriores:** 1–17 implementados

---

## Objetivo

Adicionar cadastro de Clientes e Fornecedores ao OrçaAVML, permitindo vincular obras a clientes e preparando a base para os módulos de Compras (20) e Gestão Financeira (22). É cadastro puro — sem lógica financeira ou de compras neste módulo.

---

## Decisões de Design

| Decisão | Escolha | Motivo |
|---|---|---|
| Navegação | Dropdown "Cadastros ▾" na TopBar | Não sobrecarrega a TopBar; agrupa Clientes, Fornecedores, Insumos |
| Ícones | SVG vetorizado (sem emoji) | Consistência visual e escalabilidade |
| Estrutura | Páginas separadas `/clientes` e `/fornecedores` | Entidades distintas com campos e fluxos diferentes |
| Detalhe | Página dedicada com abas (`/clientes/:id`) | Espaço para crescer (Obras, Propostas, Financeiro) |
| Vínculo obra | Nos dois lugares: criação + header da obra | Máxima flexibilidade sem complexidade extra |

---

## Modelo de Dados

### Tabela `cliente`

```sql
id           SERIAL PRIMARY KEY
empresa_id   INTEGER NOT NULL REFERENCES empresa(id)
tipo         VARCHAR(2) NOT NULL  -- 'pf' | 'pj'
nome         VARCHAR(200) NOT NULL
cpf_cnpj     VARCHAR(20)          -- único por empresa (nullable se não informado)
email        VARCHAR(200)
telefone     VARCHAR(30)
endereco     VARCHAR(300)
cidade       VARCHAR(100)
estado       VARCHAR(2)
observacoes  TEXT
created_at   TIMESTAMPTZ NOT NULL DEFAULT now()

-- índice parcial único (apenas quando cpf_cnpj não é NULL):
-- CREATE UNIQUE INDEX uq_cliente_empresa_cpfcnpj ON cliente(empresa_id, cpf_cnpj) WHERE cpf_cnpj IS NOT NULL
```

### Tabela `fornecedor`

```sql
id           SERIAL PRIMARY KEY
empresa_id   INTEGER NOT NULL REFERENCES empresa(id)
nome         VARCHAR(200) NOT NULL
cnpj         VARCHAR(20)          -- opcional
email        VARCHAR(200)
telefone     VARCHAR(30)
endereco     VARCHAR(300)
cidade       VARCHAR(100)
estado       VARCHAR(2)
categorias   VARCHAR(100)         -- CSV: 'material,mao_obra,equipamento,servico'
observacoes  TEXT
created_at   TIMESTAMPTZ NOT NULL DEFAULT now()

-- índice parcial único (apenas quando cnpj não é NULL):
-- CREATE UNIQUE INDEX uq_fornecedor_empresa_cnpj ON fornecedor(empresa_id, cnpj) WHERE cnpj IS NOT NULL
```

### Alteração em `obra`

```sql
ALTER TABLE obra ADD COLUMN cliente_id INTEGER REFERENCES cliente(id) ON DELETE SET NULL;
```

---

## Backend

### Arquivos novos

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/models/cliente.py` | Model SQLAlchemy `Cliente` |
| `backend/app/models/fornecedor.py` | Model SQLAlchemy `Fornecedor` |
| `backend/app/schemas/cliente.py` | `ClienteCreate`, `ClienteUpdate`, `ClienteOut`, `ClienteListOut` |
| `backend/app/schemas/fornecedor.py` | `FornecedorCreate`, `FornecedorUpdate`, `FornecedorOut` |
| `backend/app/routers/clientes.py` | CRUD + `/clientes/{id}/obras` |
| `backend/app/routers/fornecedores.py` | CRUD |
| `backend/alembic/versions/0005_clientes_fornecedores.py` | Migration |

### Arquivos modificados

| Arquivo | Alteração |
|---|---|
| `backend/app/models/obra.py` | Adicionar `cliente_id` FK e relationship |
| `backend/app/schemas/obra.py` | Incluir `cliente_id` em `ObraCreate` e `ObraOut` |
| `backend/app/routers/obras.py` | Aceitar `cliente_id` em create/update |
| `backend/app/main.py` | Registrar novos routers |
| `backend/app/models/__init__.py` | Importar novos models |

### Endpoints

```
GET    /clientes                   lista da empresa (busca por ?q=)
POST   /clientes                   cria cliente (409 se cpf_cnpj duplicado)
GET    /clientes/{id}              detalhe
PATCH  /clientes/{id}              atualiza
DELETE /clientes/{id}              remove (409 se tiver obras vinculadas)
GET    /clientes/{id}/obras        obras vinculadas

GET    /fornecedores               lista da empresa (busca por ?q=, ?categoria=)
POST   /fornecedores               cria fornecedor
GET    /fornecedores/{id}          detalhe
PATCH  /fornecedores/{id}          atualiza
DELETE /fornecedores/{id}          remove
```

**Regras:**
- Todos os endpoints escopados por `empresa_id` do usuário autenticado.
- `DELETE /clientes/{id}` retorna 409 se existirem obras com `cliente_id = id` (padrão do sistema — mesmo comportamento de composição com itens vinculados).
- `DELETE /fornecedores/{id}` retorna 409 se existirem compras vinculadas (Módulo 20 — por ora, deleção livre).

---

## Frontend

### Arquivos novos

| Arquivo | Responsabilidade |
|---|---|
| `frontend/src/api/clientes.ts` | `listClientes`, `getCliente`, `createCliente`, `updateCliente`, `deleteCliente`, `getClienteObras` |
| `frontend/src/api/fornecedores.ts` | `listFornecedores`, `getFornecedor`, `createFornecedor`, `updateFornecedor`, `deleteFornecedor` |
| `frontend/src/pages/ClientesPage.tsx` | Lista de clientes |
| `frontend/src/pages/ClienteDetailPage.tsx` | Detalhe com abas: Dados / Obras / Propostas |
| `frontend/src/pages/FornecedoresPage.tsx` | Lista de fornecedores |
| `frontend/src/pages/FornecedorDetailPage.tsx` | Detalhe com abas: Dados / Compras |
| `frontend/src/components/clientes/ClienteModal.tsx` | Modal criar/editar cliente |
| `frontend/src/components/fornecedores/FornecedorModal.tsx` | Modal criar/editar fornecedor |

### Arquivos modificados

| Arquivo | Alteração |
|---|---|
| `frontend/src/types/index.ts` | Adicionar tipos `Cliente`, `Fornecedor` |
| `frontend/src/components/layout/TopBar.tsx` | Dropdown "Cadastros ▾" com SVG icons |
| `frontend/src/App.tsx` | Rotas `/clientes`, `/clientes/:id`, `/fornecedores`, `/fornecedores/:id` |
| `frontend/vite.config.ts` | Adicionar `/clientes` e `/fornecedores` ao proxy bypass |
| `frontend/src/pages/ObraDetailPage.tsx` | Card de cliente no header |
| Modal de criação de obra | Campo select "Cliente" opcional |

### Páginas

#### `/clientes` — ClientesPage
- `<h1>Clientes</h1>` + busca + botão "+ Novo Cliente"
- Tabela: Nome, CPF/CNPJ, Email, Telefone, Obras (badge numérico), ações (✎ 🗑)
- Empty state: "Nenhum cliente cadastrado."
- Exclusão com confirmação inline (padrão do sistema)

#### `/clientes/:id` — ClienteDetailPage
- Breadcrumb: `Clientes › Nome do Cliente`
- Header: nome, tipo (badge PF/PJ), botão "Editar"
- **Aba Dados:** grade com todos os campos, botão "Editar" abre `ClienteModal`
- **Aba Obras:** tabela de obras vinculadas (Nome, Status, Total) com links para `/obras/:id`
- **Aba Propostas:** empty state "Em breve"

#### `/fornecedores` — FornecedoresPage
- Mesma estrutura de ClientesPage
- Tabela: Nome, CNPJ, Email, Telefone, Categorias (badges), ações
- Filtro por categoria

#### `/fornecedores/:id` — FornecedorDetailPage
- Mesma estrutura de ClienteDetailPage
- **Aba Dados:** campos + categorias como checkboxes (read-only, edita no modal)
- **Aba Compras:** empty state "Disponível no Módulo 20 — Compras"

#### TopBar — Dropdown "Cadastros ▾"
```
Cadastros ▾
├── [ícone SVG pessoa]    Clientes
├── [ícone SVG fábrica]   Fornecedores
└── [ícone SVG engrenagem] Insumos  → página "em breve"
```
Dropdown fecha ao clicar fora (mesmo padrão do menu Admin).

#### ObraDetailPage — card de cliente
```
┌──────────────────────────────────────┐
│ [ícone pessoa]  Cliente              │
│                 Construtora ABC →    │  [Vincular] ou [Alterar]
└──────────────────────────────────────┘
```
- Se sem cliente: mostra "Nenhum cliente vinculado" + botão "Vincular"
- Se com cliente: nome como link para `/clientes/:id` + botão "Alterar"
- "Vincular"/"Alterar" abre um select modal com busca

#### Modal "Nova Obra"
- Campo "Cliente" (opcional) antes do botão "Criar"
- Select com busca por nome, mostra nome + CNPJ/CPF

---

## O que este módulo NÃO inclui

- Múltiplos contatos por cliente (nome, cargo, telefone individual)
- Upload de documentos (contratos, procurações)
- Histórico financeiro (Módulo 22)
- Avaliação/rating de fornecedores (Módulo 20)
- Integração com CNPJ externo (consulta automática por CNPJ)
- Módulo Insumos — link no dropdown já existe, mas a página fica "em breve" (Módulo 21)

---

## Migration

`0005_clientes_fornecedores.py`:
1. Cria tabela `cliente`
2. Cria tabela `fornecedor`
3. Adiciona coluna `obra.cliente_id` com FK
4. Cria índices em `empresa_id` em ambas as tabelas

---

## Critérios de Aceitação

- [ ] CRUD completo de Clientes com validação de CPF/CNPJ único por empresa
- [ ] CRUD completo de Fornecedores
- [ ] Página de detalhe de Cliente mostra obras vinculadas
- [ ] Campo Cliente em "Nova Obra" (opcional)
- [ ] Card de cliente no header de ObraDetailPage com link e botão alterar
- [ ] Dropdown "Cadastros ▾" na TopBar com ícones SVG
- [ ] Navegação direta a `/clientes` e `/fornecedores` funciona (bypass no Vite proxy)
- [ ] DELETE de cliente com obras vinculadas retorna 409
- [ ] Busca por nome/CPF/CNPJ em ambas as listas
