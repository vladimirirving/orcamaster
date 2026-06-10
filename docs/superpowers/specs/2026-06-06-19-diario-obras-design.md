# Módulo 19 — Diário de Obras: Design Spec

**Data:** 2026-06-06
**Status:** Aprovado
**Módulos anteriores:** 1–18 implementados

---

## Objetivo

Adicionar um Diário de Obras ao OrçaAVML para que o responsável técnico registre diariamente as condições do canteiro (clima, equipes, atividades, ocorrências e fotos) e gere o RDO (Relatório Diário de Obras) em PDF para documentação formal ao contratante.

---

## Decisões de Design

| Decisão | Escolha | Motivo |
|---|---|---|
| Vínculo | Por obra (não por versão) | O diário documenta o canteiro, independente do orçamento |
| Fotos | Até 5/entrada, disco local, máx 5MB cada | Projeto já usa FileResponse/volume Docker; S3 é evolução futura |
| PDF | RDO gerado sob demanda por entrada | WeasyPrint — mesmo padrão do módulo Proposta |
| Navegação | Página separada `/obras/:id/diario` | Cresce bem com muitas entradas; evita apertar barra de abas |
| Layout | Lista agrupada por mês + modal criar/editar | Consistente com padrão do sistema |
| Fotos no create | Somente no modo edição | Simplifica fluxo: cria entrada → adiciona fotos |

---

## Modelo de Dados

### Tabela `diario_obra`

```sql
id           SERIAL PRIMARY KEY
obra_id      INTEGER NOT NULL REFERENCES obra(id) ON DELETE CASCADE
empresa_id   INTEGER NOT NULL REFERENCES empresa(id)
data         DATE NOT NULL
clima        VARCHAR(20) NOT NULL  -- ensolarado|parcialmente_nublado|nublado|chuvoso
turnos       VARCHAR(30)           -- CSV: 'manha,tarde,noite'
efetivo      INTEGER NOT NULL DEFAULT 0
equipes      TEXT                  -- texto livre
equipamentos TEXT                  -- opcional
atividades   TEXT NOT NULL         -- descrição principal obrigatória
ocorrencias  TEXT                  -- opcional
criado_por   INTEGER REFERENCES usuario(id) ON DELETE SET NULL
created_at   TIMESTAMPTZ NOT NULL DEFAULT now()

UNIQUE(obra_id, data)
```

### Tabela `diario_foto`

```sql
id              SERIAL PRIMARY KEY
diario_id       INTEGER NOT NULL REFERENCES diario_obra(id) ON DELETE CASCADE
nome_original   VARCHAR(255) NOT NULL
caminho         VARCHAR(500) NOT NULL   -- path relativo em DIARIO_DIR
tamanho_bytes   INTEGER NOT NULL
criado_em       TIMESTAMPTZ NOT NULL DEFAULT now()
```

### Alteração em `docker-compose.yml`

```yaml
# backend service environment:
DIARIO_DIR: /app/diario

# volumes:
- diario_data:/app/diario

# top-level volumes:
diario_data:
```

---

## Backend

### Arquivos novos

| Arquivo | Responsabilidade |
|---|---|
| `backend/app/models/diario.py` | Models `DiarioObra`, `DiarioFoto` |
| `backend/app/schemas/diario.py` | `DiarioCreate`, `DiarioUpdate`, `DiarioOut`, `DiarioFotoOut` |
| `backend/app/routers/diario.py` | CRUD + fotos + RDO PDF |
| `backend/app/services/diario_pdf.py` | `gerar_rdo_pdf(entry, empresa, obra, fotos)` → bytes |
| `backend/app/templates/rdo.html` | Template Jinja2 para o PDF |
| `backend/alembic/versions/0006_diario_obras.py` | Migration |
| `tests/backend/test_diario.py` | Testes CRUD + upload foto + RDO |

### Arquivos modificados

| Arquivo | Alteração |
|---|---|
| `backend/app/main.py` | Registrar `diario_router` |
| `backend/app/models/__init__.py` | Importar `DiarioObra`, `DiarioFoto` |
| `docker-compose.yml` | Volume `diario_data` + env `DIARIO_DIR` |

### Endpoints

```
GET    /obras/{obra_id}/diario
       → lista entradas ordenadas por data desc
       → cada item inclui: id, data, clima, turnos, efetivo, atividades (truncado 100 chars), qtd_fotos

POST   /obras/{obra_id}/diario
       body: DiarioCreate (data, clima, turnos?, efetivo, equipes?, equipamentos?, atividades, ocorrencias?)
       → 201 com DiarioOut
       → 409 se já existe entrada para essa data nessa obra

GET    /obras/{obra_id}/diario/{entry_id}
       → DiarioOut completo com lista de DiarioFotoOut

PATCH  /obras/{obra_id}/diario/{entry_id}
       body: DiarioUpdate (todos os campos opcionais)
       → 200 com DiarioOut

DELETE /obras/{obra_id}/diario/{entry_id}
       → 204
       → deleta todas as fotos do disco (DIARIO_DIR)

POST   /obras/{obra_id}/diario/{entry_id}/fotos
       form: file (UploadFile)
       → 201 com DiarioFotoOut
       → 422 se já existem 5 fotos para esta entrada
       → 422 se arquivo > 5MB
       → 422 se content-type não é image/jpeg, image/png, image/webp

DELETE /obras/{obra_id}/diario/{entry_id}/fotos/{foto_id}
       → 204
       → remove arquivo do disco + registro do DB

GET    /obras/{obra_id}/diario/{entry_id}/fotos/{foto_id}
       → FileResponse com o arquivo de imagem

GET    /obras/{obra_id}/diario/{entry_id}/rdo.pdf
       → StreamingResponse com PDF do RDO
       → Content-Disposition: attachment; filename="RDO_<obra>_<data>.pdf"
```

**Regras de segurança:**
- Todos os endpoints verificam `obra.empresa_id == current_user.empresa_id`
- `GET /fotos/{foto_id}` também verifica o tenant via join com `diario_obra`

### RDO PDF — Estrutura

| Seção | Conteúdo |
|---|---|
| Cabeçalho | Nome da empresa, nome da obra, data da entrada |
| Condições | Clima + turnos trabalhados |
| Equipe | Efetivo (nº) + descrição de equipes |
| Equipamentos | Texto livre (omitido se vazio) |
| Atividades Executadas | Texto completo |
| Ocorrências | Texto completo (omitido se vazio) |
| Fotos | Grid 2 colunas com nome do arquivo abaixo |
| Rodapé | Responsável: nome do criador + data/hora de geração |

---

## Frontend

### Arquivos novos

| Arquivo | Responsabilidade |
|---|---|
| `frontend/src/api/diario.ts` | `listEntradas`, `getEntrada`, `createEntrada`, `updateEntrada`, `deleteEntrada`, `uploadFoto`, `deleteFoto`, `getFotoUrl`, `getRdoUrl` |
| `frontend/src/pages/DiarioObraPage.tsx` | Lista de entradas agrupadas por mês |
| `frontend/src/components/diario/DiarioEntradaModal.tsx` | Modal criar/editar entrada + gestão de fotos |

### Arquivos modificados

| Arquivo | Alteração |
|---|---|
| `frontend/src/types.ts` | Adicionar `DiarioEntrada`, `DiarioFoto` |
| `frontend/src/App.tsx` | Rota `/obras/:id/diario` |
| `frontend/vite.config.ts` | Sem alteração (proxy já cobre `/obras`) |
| `frontend/src/pages/ObraDetailPage.tsx` | Botão "Diário" no header |

### Tipos TypeScript

```typescript
export interface DiarioEntrada {
  id: number
  obra_id: number
  data: string           // YYYY-MM-DD
  clima: 'ensolarado' | 'parcialmente_nublado' | 'nublado' | 'chuvoso'
  turnos: string | null  // CSV
  efetivo: number
  equipes: string | null
  equipamentos: string | null
  atividades: string
  ocorrencias: string | null
  criado_por: number | null
  created_at: string
  fotos: DiarioFoto[]
  qtd_fotos?: number     // presente apenas na listagem
}

export interface DiarioFoto {
  id: number
  diario_id: number
  nome_original: string
  tamanho_bytes: number
  criado_em: string
}
```

### DiarioObraPage (`/obras/:id/diario`)

- Breadcrumb: `Obras › Rodovia 232 › Diário`
- Header: "Diário de Obras", botão "+ Nova Entrada"
- Agrupado por mês em seções colapsáveis simples (sem toggle, apenas label)
- Cada linha: badge data (ex: "Qui 05"), ícone clima, efetivo, atividades truncadas, badge "N fotos" (se > 0), botão "↓ RDO", botão "✎"
- Empty state: "Nenhuma entrada registrada. Comece registrando o dia de hoje."
- Clique em "✎" abre `DiarioEntradaModal` no modo edição
- Clique em "↓ RDO" abre `GET /rdo.pdf` em nova aba

### DiarioEntradaModal

**Modo criação:**
- Data (date input, padrão = hoje)
- Clima: 4 opções com ícone (☀️ Ensolarado / ⛅ Parcialmente Nublado / ☁️ Nublado / 🌧️ Chuvoso)
- Turnos: checkboxes Manhã / Tarde / Noite
- Efetivo: number input (mín 0)
- Equipes: textarea
- Equipamentos: textarea
- Atividades*: textarea (obrigatório)
- Ocorrências: textarea
- *(sem seção de fotos — adicionar após criar)*

**Modo edição:**
- Todos os campos acima pré-preenchidos
- Seção "Fotos" no final: grid 3×2 de thumbnails, botão "+" para adicionar (até 5), "×" em cada foto para remover
- Fotos são carregadas/removidas inline (sem precisar salvar o formulário)

### ObraDetailPage — Botão Diário

No header da obra, ao lado do botão "Nova Versão" (quando ativo), adicionar:

```tsx
<button onClick={() => navigate(`/obras/${obraId}/diario`)}
  className="flex items-center gap-2 border border-gray-300 px-4 py-2 rounded-lg text-sm hover:bg-gray-50">
  <svg ...>...</svg> Diário
</button>
```

---

## O que este módulo NÃO inclui

- Vínculo de atividades com grupos/itens do orçamento (Módulo 20 — Compras)
- Exportação consolidada em XLS de múltiplos dias
- Relatório mensal consolidado
- App mobile com funcionamento offline
- Notificações/alertas por dias sem registro

---

## Migration

`0006_diario_obras.py`:
1. Cria tabela `diario_obra` com índice em `(obra_id)` e constraint única em `(obra_id, data)`
2. Cria tabela `diario_foto` com índice em `(diario_id)`

---

## Critérios de Aceitação

- [ ] CRUD completo de entradas com validação de data única por obra
- [ ] Upload de até 5 fotos por entrada (JPEG/PNG/WebP, máx 5MB)
- [ ] Download individual de foto via FileResponse
- [ ] Download de RDO PDF com todas as seções
- [ ] Fotos aparecem no RDO PDF quando presentes
- [ ] DELETE de entrada remove fotos do disco
- [ ] Botão "Diário" em ObraDetailPage navega para `/obras/:id/diario`
- [ ] Entradas agrupadas por mês em ordem desc
- [ ] Tenant isolation: só acessa entradas da própria empresa
