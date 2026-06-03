# Módulo 11 — Agente IA para Montagem de Planilha: Design Spec

**Data:** 2026-06-03
**Status:** Aprovado

---

## 1. Objetivo

Permitir que o orçamentista descreva a obra em linguagem natural e receba uma proposta estruturada de grupos e itens orçamentários para revisão — acelerando a fase inicial de montagem da planilha. O agente busca composições exclusivamente no banco local (SINAPI, SICRO, próprias), garantindo preços atuais e rastreabilidade.

---

## 2. Escopo

**Inclui:**
- Campo de texto livre para descrição da obra
- Streaming em tempo real de progresso (SSE) enquanto o agente executa tool calls
- Tela de revisão com cards expansíveis por grupo (aceitar / editar inline / remover)
- Endpoint de importação que cria Grupo + Item na versão ativa (anexa ao final)
- Aba "Agente IA" em `ObraDetailPage`

**Fora do escopo:**
- Upload de PDF
- Painel de chat de refinamento pós-importação (Módulo 12)
- Cancelamento server-side do stream
- Histórico de sessões do agente

---

## 3. Arquitetura

```
Frontend (AgenteTab)
  │
  ├── POST /versoes/{id}/agente/gerar  → EventSource SSE
  │     └── agente_service.gerar_proposta_stream()
  │           └── Claude API (claude-sonnet-4-6, streaming + tool use)
  │                 ├── buscar_composicao(query, origem?)
  │                 ├── listar_grupos_tipicos(tipo_obra)
  │                 └── obter_composicao(composicao_id)
  │
  └── POST /versoes/{id}/agente/importar  → JSON
        └── Cria Grupo + Item + recalc_totais_versao
```

O agente **não** chama APIs externas — trabalha exclusivamente com o banco local.

---

## 4. Backend

### 4.1 Arquivos

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `backend/app/schemas/agente.py` | Criar | Schemas de request/response |
| `backend/app/services/agente_service.py` | Criar | Loop de tool use + gerador SSE |
| `backend/app/routers/agente.py` | Criar | 2 endpoints REST |
| `backend/app/main.py` | Modificar | Registrar `agente.router` |

### 4.2 Schemas (`app/schemas/agente.py`)

```python
from typing import Optional
from pydantic import BaseModel


class AgenteRequest(BaseModel):
    descricao: str


class PropostaItem(BaseModel):
    composicao_id: int
    descricao: str
    codigo: str
    unidade: str
    quantidade: float


class PropostaGrupo(BaseModel):
    nome: str
    itens: list[PropostaItem]


class PropostaSugerida(BaseModel):
    grupos: list[PropostaGrupo]


class ImportarRequest(BaseModel):
    grupos: list[PropostaGrupo]


class ImportarResult(BaseModel):
    grupos_criados: int
    itens_criados: int
```

### 4.3 Ferramentas do Agente (`agente_service.py`)

**`buscar_composicao(query: str, origem: str | None)`**
- `SELECT ... WHERE (empresa_id IS NULL OR empresa_id = ?) AND (codigo ILIKE ? OR descricao ILIKE ?)`
- Se `origem` fornecido, filtra por `Composicao.origem`
- Retorna até 10 resultados: `id, codigo, descricao, unidade, preco_unitario, origem`

**`listar_grupos_tipicos(tipo_obra: str)`**
- Dicionário hard-coded por tipo de obra:
  - `"rodovia"` → Terraplenagem, Drenagem Superficial, Pavimentação, Obras de Arte Correntes, Sinalização, Obras Complementares
  - `"saneamento"` → Serviços Preliminares, Escavação e Movimento de Terra, Redes Coletoras, Estações Elevatórias, ETE/ETA, Ligações Domiciliares
  - `"ponte"` → Fundações, Subestrutura, Superestrutura, Aparelhos de Apoio, Tabuleiro, Guarda-rodas e Defensas
  - `"rede_eletrica"` → Serviços Preliminares, Fundações e Estruturas, Equipamentos, Cabos e Condutores, Proteções e Medição
  - `"outro"` → retorna lista genérica: Serviços Preliminares, Infraestrutura, Superestrutura, Instalações, Acabamentos
- Retorna lista de strings (nomes dos grupos)

**`obter_composicao(composicao_id: int)`**
- Busca por `Composicao.id` com acesso permitido (SINAPI/SICRO ou da empresa)
- Retorna: `id, codigo, descricao, unidade, preco_unitario, origem` + lista de insumos

### 4.4 Serviço (`agente_service.py`)

```python
async def gerar_proposta_stream(
    descricao: str,
    versao_id: int,
    empresa_id: int,
    db: AsyncSession,
) -> AsyncGenerator[str, None]:
    """Gerador assíncrono que emite linhas SSE."""
```

Fluxo:
1. Emite `progress`: "Analisando descrição da obra…"
2. Chama Claude API com `stream=True`, `tools=[...]`, `model="claude-sonnet-4-6"`
3. A cada `tool_use` block no stream: executa a ferramenta (com `db`), emite evento `progress` descrevendo o que foi feito
4. Ao final do loop de tool use: extrai o texto estruturado do assistente como JSON (`PropostaSugerida`)
5. Emite evento `proposta` com o JSON
6. Em qualquer exceção: emite evento `error`

**Formato dos eventos SSE** (cada linha termina com `\n\n`):
```
data: {"type": "progress", "msg": "Identificando grupos para rodovia flexível..."}

data: {"type": "progress", "msg": "Buscando composições de terraplenagem... 8 encontradas"}

data: {"type": "proposta", "data": {"grupos": [...]}}

data: {"type": "error", "msg": "Erro interno ao gerar proposta"}
```

**System prompt para o agente:**
```
Você é um assistente de orçamentação de obras de infraestrutura brasileiras.
O usuário descreve uma obra e você deve sugerir uma estrutura de planilha orçamentária
com grupos de serviço e itens, usando composições do banco local (SINAPI, SICRO ou próprias).

Passos obrigatórios:
1. Chame listar_grupos_tipicos com o tipo de obra identificado
2. Para cada grupo relevante, chame buscar_composicao para encontrar composições adequadas
3. Use obter_composicao para verificar detalhes quando necessário
4. Sugira quantidades típicas com base no porte da obra descrito
5. Responda APENAS com um JSON válido no formato PropostaSugerida (sem markdown, sem texto extra)

Regras:
- Use apenas composições encontradas pelas ferramentas (nunca invente códigos)
- Prefira SINAPI para edificações/serviços gerais, SICRO para rodovias/infraestrutura
- Quantidades são estimativas — o orçamentista irá ajustá-las na revisão
```

### 4.5 Router (`agente.py`)

**`POST /versoes/{versao_id}/agente/gerar`**
- Verifica que a versão pertence à empresa (via `_get_versao_ativa`)
- Retorna `StreamingResponse(gerar_proposta_stream(...), media_type="text/event-stream")`

**`POST /versoes/{versao_id}/agente/importar`**
- Verifica versão ativa via `_get_versao_ativa` (bloqueada → 409)
- Para cada `PropostaGrupo`: cria `Grupo(versao_id=versao_id, nome=grupo.nome, ordem=próximo_livre)`
- Para cada `PropostaItem`: valida que `composicao_id` existe e é acessível → 422 se não existir; cria `Item(grupo_id=..., composicao_id=..., quantidade=..., unidade=..., preco_unitario_sem_bdi=composicao.preco_unitario)`
- Chama `recalc_totais_versao(versao_id, db)`
- Retorna `ImportarResult`

**`ordem` dos grupos:** `MAX(ordem) + 1` dos grupos existentes na versão (ou 0 se não houver), incrementando +1 a cada grupo importado, garantindo que ficam no final e em ordem.

**`ordem` dos itens dentro de cada grupo:** índice 0-based na lista recebida (`0, 1, 2, ...`).

---

## 5. Frontend

### 5.1 Arquivos

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `frontend/src/types.ts` | Modificar | +`PropostaItem`, `PropostaGrupo`, `PropostaSugerida` |
| `frontend/src/api/agente.ts` | Criar | `gerarProposta` (SSE), `importarProposta` |
| `frontend/src/components/obra/AgenteTab.tsx` | Criar | Componente com 4 fases |
| `frontend/src/pages/ObraDetailPage.tsx` | Modificar | +aba "Agente IA" |

### 5.2 Tipos (`types.ts`)

```ts
export interface PropostaItem {
  composicao_id: number
  descricao: string
  codigo: string
  unidade: string
  quantidade: number
}

export interface PropostaGrupo {
  nome: string
  itens: PropostaItem[]
}

export interface PropostaSugerida {
  grupos: PropostaGrupo[]
}
```

### 5.3 API (`api/agente.ts`)

```ts
export function gerarProposta(
  versaoId: number,
  descricao: string,
  onProgress: (msg: string) => void,
  onProposta: (proposta: PropostaSugerida) => void,
  onError: (msg: string) => void,
): () => void   // retorna função de cleanup (fecha EventSource)

export const importarProposta = (
  versaoId: number,
  grupos: PropostaGrupo[],
): Promise<{ grupos_criados: number; itens_criados: number }>
```

`gerarProposta` usa `fetch` com leitura do body como stream (não `EventSource` nativo, pois precisa enviar um POST com body). Lê os chunks, parseia as linhas `data: {...}` e chama os callbacks correspondentes.

### 5.4 `AgenteTab.tsx` — 4 fases

**Fase 1 — Idle:**
- Textarea com placeholder "Descreva a obra: tipo, extensão, especificações técnicas relevantes..."
- Botão "✨ Gerar proposta" (desabilitado se textarea vazio ou sem versão ativa)
- Se sem versão ativa: mensagem estática padrão

**Fase 2 — Streaming:**
- Lista de mensagens de progresso aparecendo em tempo real (mais recente no topo ou no final)
- Spinner animado
- Botão "Cancelar" fecha o stream (chama o cleanup retornado por `gerarProposta`)

**Fase 3 — Revisão:**
- Cabeçalho: "X grupos, Y itens sugeridos — revise antes de importar"
- Cards expansíveis por grupo (clique no cabeçalho expande/recolhe):
  - Cabeçalho do card: nome do grupo + botões Aceitar / Editar / Remover
  - Corpo expandido: tabela com Código, Descrição, Un, Qtd por item
  - Modo de edição: nome do grupo e quantidades tornam-se inputs; confirmar com "✓"
- Botão "Importar N grupos →" (apenas grupos não removidos)
- Botão "← Refazer" volta para a Fase 1

**Fase 4 — Importando/Concluído:**
- Spinner durante a importação
- Ao concluir: "✓ X grupos e Y itens adicionados à planilha" + link "Abrir planilha →"
- Botão "Gerar nova proposta" volta para Fase 1

---

## 6. Testes

### 6.1 Backend (`tests/backend/test_agente.py`)

| Teste | Descrição |
|-------|-----------|
| `test_gerar_proposta_stream` | Mock da Claude API; verifica que o SSE emite ao menos um evento `progress` e um evento `proposta` com `grupos` não vazio |
| `test_gerar_proposta_versao_nao_encontrada` | Versão de outra empresa → 404 |
| `test_importar_grupos_ok` | Importa 2 grupos com 3 itens cada; verifica `Grupo` e `Item` criados, ordem correta, `total_sem_bdi` atualizado |
| `test_importar_composicao_invalida` | `composicao_id` inexistente → 422 |
| `test_importar_versao_bloqueada` | Versão bloqueada → 409 |
| `test_buscar_composicao_tool` | Chama a função de tool diretamente; verifica filtro por query e por origem |
| `test_listar_grupos_tipicos_tool` | `"rodovia"` retorna lista com Terraplenagem e Drenagem |

### 6.2 Frontend (manual)
- Fluxo completo das 4 fases
- Edição inline de nome de grupo e quantidade de item
- Remover um grupo da proposta antes de importar
- Importação verificada na planilha (Curva ABC, totais atualizados)

---

## 7. Dependências

- `anthropic==0.40.0` — já em `pyproject.toml`
- `settings.anthropic_api_key` — já em `app/config.py`
- Sem novas tabelas ou migrações

---

## 8. Modelo/Custo Estimado

- **Modelo:** `claude-sonnet-4-6`
- **Tokens típicos por geração:** ~3.000–8.000 (input + tool results + output)
- Cada geração custa ~$0.01–0.03 — adequado para uso em produção sem throttle adicional na v1
