# Plan 4a — BDI + Versionamento (Duplicar Versão) Design

**Data:** 2026-06-01
**Escopo:** Backend puro. Sem mudanças de frontend.

---

## Objetivo

Adicionar dois subsistemas ao backend do OrçaAVML:

1. **BDI por versão** — CRUD do BDI com aplicação automática do `preco_unitario_com_bdi` em todos os itens ao salvar.
2. **Duplicar versão** — clonar uma versão completa (grupos, subgrupos, itens, BDI) para uma nova versão com número incrementado.

---

## Contexto existente relevante

- `backend/app/models/bdi.py` — modelo já existe com campos `AC`, `SG`, `R`, `DF`, `lucro`, `ISS`, `PIS`, `COFINS`, `bdi_composto`, `historico_json`. `UniqueConstraint("versao_id")` já presente.
- `backend/app/models/item.py` — campo `preco_unitario_com_bdi: Optional[Decimal]` já existe. `total` é `GENERATED ALWAYS AS (quantidade * COALESCE(preco_unitario_sem_bdi, 0)) STORED` — nunca setar explicitamente.
- `backend/app/models/versao.py` — campos `total_sem_bdi` e `total_com_bdi` já existem.
- `backend/app/services/totais_service.py` — `recalc_totais_versao(versao_id, db)` calcula `total_sem_bdi`; **será estendido** para também calcular `total_com_bdi`.
- `backend/app/routers/versoes.py` — rotas existentes para CRUD de versões; **receberá** o endpoint `POST /versoes/{id}/duplicar`.

---

## Arquitetura

### Novos arquivos

| Arquivo | Responsabilidade |
|---------|-----------------|
| `backend/app/schemas/bdi.py` | `BDICreate`, `BDIOut` |
| `backend/app/services/bdi_service.py` | `aplicar_bdi_versao(versao_id, bdi_composto, db)` — bulk UPDATE dos itens |
| `backend/app/routers/bdi.py` | `GET/PUT/DELETE /versoes/{id}/bdi` |
| `tests/backend/test_bdi.py` | Testes do BDI |
| `tests/backend/test_duplicar_versao.py` | Testes de duplicação de versão |

### Arquivos modificados

| Arquivo | Mudança |
|---------|---------|
| `backend/app/services/totais_service.py` | Adicionar cálculo de `total_com_bdi` em `recalc_totais_versao` |
| `backend/app/routers/versoes.py` | Adicionar `POST /versoes/{id}/duplicar` |
| `backend/app/main.py` | Registrar `bdi.router` |

---

## BDI

### Fórmula

```
bdi_composto = ((1 + AC + SG + R + DF + lucro) / (1 - ISS - PIS - COFINS)) - 1
preco_unitario_com_bdi = preco_unitario_sem_bdi * (1 + bdi_composto)
```

Todos os campos percentuais são armazenados como decimais absolutos (ex: 3% = `0.0300`). `bdi_composto` tem precisão `Numeric(8, 6)`.

### Schemas (`backend/app/schemas/bdi.py`)

```python
class BDICreate(BaseModel):
    ac: Decimal       # Administração Central
    sg: Decimal       # Seguros e Garantias
    r: Decimal        # Riscos
    df: Decimal       # Despesas Financeiras
    lucro: Decimal    # Lucro
    iss: Decimal      # ISS
    pis: Decimal      # PIS
    cofins: Decimal   # COFINS

class BDIOut(BaseModel):
    model_config = {"from_attributes": True}
    id: int
    versao_id: int
    ac: Decimal
    sg: Decimal
    r: Decimal
    df: Decimal
    lucro: Decimal
    iss: Decimal
    pis: Decimal
    cofins: Decimal
    bdi_composto: Decimal
```

`bdi_composto` não é enviado pelo cliente — é calculado pelo backend.

### Service (`backend/app/services/bdi_service.py`)

`aplicar_bdi_versao(versao_id, bdi_composto, db)`:
1. Bulk UPDATE via subquery:
   ```sql
   UPDATE item
   SET preco_unitario_com_bdi = preco_unitario_sem_bdi * (1 + :bdi)
   WHERE grupo_id IN (SELECT id FROM grupo WHERE versao_id = :vid)
   AND preco_unitario_sem_bdi IS NOT NULL
   ```
2. Usa `.execution_options(synchronize_session=False)`
3. Caller faz `db.flush()` antes e `db.commit()` depois (via router)

`zerar_bdi_versao(versao_id, db)`:
1. Bulk UPDATE `preco_unitario_com_bdi = NULL` para todos os itens da versão

### Endpoints (`backend/app/routers/bdi.py`)

**`GET /versoes/{versao_id}/bdi`**
- Verifica acesso à versão (qualquer estado — read-only)
- Retorna BDI ou 404

**`PUT /versoes/{versao_id}/bdi`**
- Verifica versão ativa (não bloqueada, não deletada, mesma empresa)
- Calcula `bdi_composto` pela fórmula
- Upsert na tabela `bdi` (INSERT ou UPDATE via `merge` ou query existente)
- `db.flush()`
- Chama `aplicar_bdi_versao(versao_id, bdi_composto, db)`
- Chama `recalc_totais_versao(versao_id, db)` — agora também recalcula `total_com_bdi`
- `db.refresh(versao)` → `db.commit()`
- Retorna `BDIOut`

**`DELETE /versoes/{versao_id}/bdi`**
- Verifica versão ativa
- Chama `zerar_bdi_versao(versao_id, db)`
- `db.flush()`
- Deleta o registro BDI
- Chama `recalc_totais_versao(versao_id, db)`
- `db.refresh(versao)` → `db.commit()`
- Retorna 204

### `historico_json`

Deixado como lista vazia (`[]`) neste plano. Não é gravado nem lido. Campo reservado para auditoria futura.

---

## totais_service — extensão

`recalc_totais_versao(versao_id, db)` passa a calcular dois valores:

```python
# total_sem_bdi — mantém como está
total_sem_bdi = SELECT SUM(item.total) ...  # coluna GENERATED

# total_com_bdi — novo
total_com_bdi = SELECT SUM(quantidade * COALESCE(preco_unitario_com_bdi, 0)).cast(Numeric(15, 2)) ...
```

Ambos são escritos na `Versao` numa única operação de UPDATE. O caller faz `db.refresh(versao)` após.

---

## Versionamento — Duplicar Versão

### Endpoint: `POST /versoes/{versao_id}/duplicar`

Adicionado em `backend/app/routers/versoes.py`.

**Regra de negócio:**
- Só pode duplicar versão ativa (não bloqueada, não deletada) — retorna 409 caso contrário
- Nova versão: `numero = MAX(versao.numero WHERE obra_id = ?) + 1`, `bloqueada=False`, `deletada_em=None`, `total_sem_bdi=0`, `total_com_bdi=0`

**Algoritmo de cópia:**
```
1. Carrega versão original
2. Verifica versão ativa
3. Calcula próximo número
4. Cria nova Versao → db.flush() → obtém nova_versao.id
5. Para cada grupo raiz (pai_id IS NULL), ordered by ordem:
   a. Cria cópia do grupo (versao_id=nova_versao.id, pai_id=None)
   b. db.flush() → obtém novo_grupo.id
   c. Para cada subgrupo do grupo original:
      - Cria cópia (versao_id=nova_versao.id, pai_id=novo_grupo.id)
      - db.flush() → obtém novo_subgrupo.id
      - Para cada item do subgrupo original:
        - Cria cópia do item (grupo_id=novo_subgrupo.id)
   d. Para cada item do grupo raiz original:
      - Cria cópia do item (grupo_id=novo_grupo.id)
6. Se versão original tem BDI:
   - Cria cópia do BDI (versao_id=nova_versao.id)
7. db.flush()
8. recalc_totais_versao(nova_versao.id, db)
9. db.refresh(nova_versao) → db.commit()
10. Retorna VersaoOut da nova versão
```

**Itens copiados incluem:** `ordem`, `composicao_id`, `quantidade`, `unidade`, `preco_unitario_sem_bdi`, `preco_unitario_com_bdi`, `etiqueta_revisao`, `requer_revisao`. `total` é GENERATED — não copiar.

---

## Testes

### `tests/backend/test_bdi.py`

| Teste | Verifica |
|-------|----------|
| `test_put_bdi_cria_e_calcula_bdi_composto` | Formula correta: exemplo com valores conhecidos |
| `test_put_bdi_aplica_preco_com_bdi_nos_itens` | Itens recebem `preco_unitario_com_bdi` correto |
| `test_put_bdi_atualiza_total_com_bdi_versao` | `versao.total_com_bdi` calculado via `GET /obras/{id}/versoes` |
| `test_get_bdi_retorna_404_quando_nao_existe` | 404 para versão sem BDI |
| `test_get_bdi_retorna_bdi_existente` | GET retorna BDI criado |
| `test_put_bdi_atualiza_bdi_existente` | Segundo PUT sobrescreve e recalcula |
| `test_delete_bdi_zera_preco_com_bdi_nos_itens` | `preco_unitario_com_bdi = NULL` e `total_com_bdi = 0` |
| `test_put_bdi_em_versao_bloqueada_retorna_409` | 409 quando versão bloqueada |

### `tests/backend/test_duplicar_versao.py`

| Teste | Verifica |
|-------|----------|
| `test_duplicar_copia_grupos_subgrupos_itens` | Estrutura completa copiada com novos IDs |
| `test_duplicar_numero_incrementado` | `nova_versao.numero = original.numero + 1` |
| `test_duplicar_copia_bdi` | Nova versão tem BDI independente |
| `test_duplicar_versao_sem_bdi` | Nova versão sem BDI quando original não tem |
| `test_duplicar_versao_bloqueada_retorna_409` | 409 ao tentar duplicar versão bloqueada |
| `test_duplicar_bdi_independente` | Alterar BDI da nova versão não afeta a original |

---

## Regras de negócio consolidadas

1. `bdi_composto` é sempre calculado pelo backend — nunca enviado pelo cliente
2. Salvar BDI recalcula `preco_unitario_com_bdi` em **todos** os itens da versão (sem exceção)
3. `historico_json` fica vazio neste plano
4. Duplicar versão copia tudo: grupos, subgrupos, itens, BDI
5. Nova versão duplicada começa sempre desbloqueada
6. `Item.total` nunca é setado explicitamente (coluna GENERATED)
7. Todos os bulk UPDATEs usam `.execution_options(synchronize_session=False)`
8. Sequência padrão: `db.flush()` → operações → `recalc_totais_versao` → `db.refresh(versao)` → `db.commit()`
