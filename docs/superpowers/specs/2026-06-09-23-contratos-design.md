# Módulo 23 — Gestão de Contratos: Design Spec

## Objetivo

Permitir registrar, acompanhar e arquivar contratos vinculados às obras, incluindo aditivos de valor e/ou prazo, com upload do PDF de cada instrumento.

---

## Modelo de Dados

### Tabela `contratos`

| Campo | Tipo | Restrições |
|---|---|---|
| `id` | serial PK | |
| `obra_id` | integer FK obras | NOT NULL, ON DELETE CASCADE |
| `numero` | varchar(100) | nullable — ex: "CT-2024-001" |
| `objeto` | text | NOT NULL |
| `valor_original` | numeric(15,2) | NOT NULL |
| `data_assinatura` | date | nullable |
| `data_inicio` | date | nullable |
| `data_fim` | date | nullable — prazo original |
| `contratante_nome` | varchar(255) | nullable |
| `contratante_cnpj` | varchar(18) | nullable |
| `contratado_nome` | varchar(255) | nullable |
| `contratado_cnpj` | varchar(18) | nullable |
| `arquivo_path` | varchar(500) | nullable — caminho em `/data/contratos/` |
| `criado_em` | timestamp | NOT NULL, default now() |

### Tabela `aditivos`

| Campo | Tipo | Restrições |
|---|---|---|
| `id` | serial PK | |
| `contrato_id` | integer FK contratos | NOT NULL, ON DELETE CASCADE |
| `numero` | varchar(100) | nullable — ex: "1º Aditivo" |
| `tipo` | varchar(20) | NOT NULL — enum: `valor`, `prazo`, `valor_prazo` |
| `delta_valor` | numeric(15,2) | nullable — positivo ou negativo |
| `nova_data_fim` | date | nullable |
| `justificativa` | text | nullable |
| `data_assinatura` | date | nullable |
| `arquivo_path` | varchar(500) | nullable |
| `criado_em` | timestamp | NOT NULL, default now() |

### Campos calculados (não persistidos)

- `valor_atual` = `valor_original` + Σ `delta_valor` dos aditivos do contrato
- `data_fim_atual` = `nova_data_fim` do aditivo mais recente com prazo preenchido, ou `data_fim` original se nenhum aditivo alterar prazo

---

## Backend

### Migration

`alembic/versions/0007_contratos_aditivos.py` — cria `contratos` e `aditivos` com FKs e índices em `obra_id` e `contrato_id`.

### Models SQLAlchemy

`backend/app/models/contrato.py` — `Contrato` e `Aditivo` com relações lazy-loaded (usar `set_committed_value` no router para evitar lazy loading assíncrono).

### Schemas Pydantic

`backend/app/schemas/contrato.py`:
- `ContratoCreate` — campos editáveis (objeto obrigatório, valor_original obrigatório)
- `ContratoUpdate` — todos os campos opcionais
- `AditivoCreate` — tipo obrigatório
- `AditivoUpdate` — todos os campos opcionais
- `AditivoOut` — todos os campos do model
- `ContratoOut` — todos os campos + `valor_atual: float` + `data_fim_atual: date | None` + `aditivos: list[AditivoOut]`

### Router

`backend/app/routers/contratos.py` — registrado em `main.py`:

| Método | Rota | Descrição |
|---|---|---|
| GET | `/obras/{obra_id}/contratos` | Lista contratos da obra com aditivos e campos calculados |
| POST | `/obras/{obra_id}/contratos` | Cria contrato |
| PATCH | `/contratos/{id}` | Edita metadados |
| DELETE | `/contratos/{id}` | Remove contrato (cascade nos aditivos) |
| POST | `/contratos/{id}/upload` | Upload PDF → `/data/contratos/c{id}.pdf` |
| GET | `/contratos/{id}/download` | Serve o PDF |
| POST | `/contratos/{id}/aditivos` | Cria aditivo |
| PATCH | `/aditivos/{id}` | Edita aditivo |
| DELETE | `/aditivos/{id}` | Remove aditivo |
| POST | `/aditivos/{id}/upload` | Upload PDF → `/data/contratos/a{id}.pdf` |
| GET | `/aditivos/{id}/download` | Serve PDF do aditivo |

### Volume Docker

Adicionar ao `docker-compose.yml`:
```yaml
volumes:
  contratos_data:/data/contratos
```
Montar no serviço `backend`: `contratos_data:/data/contratos`.

### Testes

`backend/tests/test_contratos.py` — ~15 testes:
- CRUD completo de contrato
- CRUD completo de aditivo
- `valor_atual` = valor_original + delta de aditivos (incluindo negativos)
- `data_fim_atual` = nova_data_fim do aditivo mais recente com prazo
- Upload/download de PDF (mock do arquivo)
- 404 para contrato/aditivo inexistente

---

## Frontend

### Tipos (`types.ts`)

```typescript
interface Aditivo {
  id: number
  contrato_id: number
  numero: string | null
  tipo: 'valor' | 'prazo' | 'valor_prazo'
  delta_valor: number | null
  nova_data_fim: string | null
  justificativa: string | null
  data_assinatura: string | null
  arquivo_path: string | null
  criado_em: string
}

interface Contrato {
  id: number
  obra_id: number
  numero: string | null
  objeto: string
  valor_original: number
  valor_atual: number
  data_assinatura: string | null
  data_inicio: string | null
  data_fim: string | null
  data_fim_atual: string | null
  contratante_nome: string | null
  contratante_cnpj: string | null
  contratado_nome: string | null
  contratado_cnpj: string | null
  arquivo_path: string | null
  criado_em: string
  aditivos: Aditivo[]
}
```

### API (`api/contratos.ts`)

- `getContratos(obraId)` — GET lista
- `createContrato(obraId, data)` — POST
- `updateContrato(id, data)` — PATCH
- `deleteContrato(id)` — DELETE
- `uploadContratoFile(id, file)` — POST multipart
- `downloadContratoUrl(id)` — string da URL para `<a href>` ou `window.open`
- `createAditivo(contratoId, data)` — POST
- `updateAditivo(id, data)` — PATCH
- `deleteAditivo(id)` — DELETE
- `uploadAditivoFile(id, file)` — POST multipart
- `downloadAditivoUrl(id)` — string da URL

### Componentes

#### `ContratosTab.tsx`
- Busca `getContratos(obraId)` ao montar
- Estado vazio: "Nenhum contrato cadastrado" + botão "Novo Contrato"
- Lista de `ContratoCard` + botão "Novo Contrato" no topo
- Abre `ContratoModal` para criar

#### `ContratoCard.tsx`
- **Fechado:** número (ou "Sem número"), objeto truncado, valor atual formatado em BRL, badge de status, ícone de clipe se tiver PDF
- **Aberto** (clique para expandir): todos os campos do contrato, botões Editar / Upload PDF / Download PDF / Novo Aditivo / Excluir, lista de `AditivoRow` inline
- Badge de status calculado no frontend:
  - `data_fim_atual < hoje` → "Vencido" (vermelho)
  - `data_fim_atual` entre hoje e hoje+30 dias → "Vence em breve" (amarelo)
  - `data_fim_atual >= hoje+30` → "Vigente" (verde)
  - Sem data → sem badge

#### `ContratoModal.tsx`
- Modal `fixed inset-0` (padrão ObraEditModal)
- Campos: objeto*, valor_original*, numero, data_assinatura, data_inicio, data_fim, contratante_nome, contratante_cnpj, contratado_nome, contratado_cnpj
- Usado tanto para criação quanto edição (prop `contrato?: Contrato`)

#### `AditivoModal.tsx`
- Modal menor: numero, tipo (select), delta_valor (condicional: visível se tipo ≠ prazo), nova_data_fim (condicional: visível se tipo ≠ valor), justificativa, data_assinatura
- Usado para criação e edição

### Integração em `ObraDetailPage`

- Adicionar `'contratos'` ao union type do estado `tab`
- Adicionar item "Contratos" na row de tabs
- Renderizar `<ContratosTab obraId={obraId} />` quando `tab === 'contratos'`
- Importar `ContratosTab`

---

## Fluxo de Upload de PDF

1. Usuário clica "Upload PDF" no `ContratoCard` → `<input type="file" accept=".pdf">` hidden acionado via ref
2. `onChange` → `uploadContratoFile(id, file)` → `POST /contratos/{id}/upload` com `FormData`
3. Backend salva em `/data/contratos/c{id}.pdf`, atualiza `arquivo_path` no banco, retorna `ContratoOut` atualizado
4. Frontend atualiza o contrato na lista local → ícone de clipe aparece no card

Mesmo fluxo para aditivos (`/aditivos/{id}/upload` → `/data/contratos/a{id}.pdf`).

---

## Decisões de Design

- **Hard delete** no contrato: sem dependentes externos (versões não referenciam contratos), cascade nos aditivos é suficiente
- **`objeto` obrigatório**: é o campo de identificação mínima legal do contrato
- **`valor_original` obrigatório**: sem valor não há contrato significativo
- **Partes opcionais**: flexibilidade para contratos ainda em negociação
- **Arquivo por id, não por nome**: evita colisão e exposição do nome original
