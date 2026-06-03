# Curva ABC — Design Spec

**Data:** 2026-06-02
**Status:** Aprovado para implementação
**Módulo:** 8 de 11

---

## 1. Objetivo

Adicionar uma aba **Curva ABC** na `ObraDetailPage` que exibe os itens da versão ativa ordenados por valor total decrescente, com participação percentual, acumulado e classificação em faixas A/B/C. Inclui exportação para Excel.

---

## 2. Localização na UI

`ObraDetailPage` (`/obras/:id`) ganha uma terceira aba:

```
[ Versões ]  [ Dashboard ]  [ Curva ABC ]
```

- Conteúdo carregado on-demand quando a aba é aberta pela primeira vez
- Usa o `versao_id` da versão ativa já carregado pela listagem de versões existente
- Se não houver versão ativa: mensagem "Nenhuma versão ativa para esta obra"

---

## 3. Backend

### 3.1 Router

Arquivo: `backend/app/routers/curva_abc.py`  
Montado em `/versoes/{versao_id}/curva-abc`.  
Todos os endpoints exigem autenticação e verificam isolamento por empresa.

| Método | Path | Descrição |
|---|---|---|
| `GET` | `/versoes/{versao_id}/curva-abc` | Retorna lista de itens classificados |
| `GET` | `/versoes/{versao_id}/curva-abc/export` | Retorna arquivo `.xlsx` para download |

### 3.2 GET `/versoes/{versao_id}/curva-abc`

```json
{
  "total_versao": "12400000.00",
  "itens": [
    {
      "rank": 1,
      "grupo_nome": "Pavimentação",
      "descricao": "CBUQ camada de rolamento",
      "unidade": "m²",
      "quantidade": "12000.000000",
      "total": "4200000.00",
      "participacao_pct": 33.87,
      "acumulado_pct": 33.87,
      "faixa": "A"
    },
    {
      "rank": 2,
      "grupo_nome": "Terraplenagem",
      "descricao": "Escavação mecanizada",
      "unidade": "m³",
      "quantidade": "50000.000000",
      "total": "3100000.00",
      "participacao_pct": 25.0,
      "acumulado_pct": 58.87,
      "faixa": "A"
    }
  ]
}
```

**Regras:**
- Itens com `total == 0` são excluídos da lista
- Ordenação: decrescente por `total`
- `participacao_pct = float(item.total) / total_versao * 100`
- `acumulado_pct` = soma cumulativa de `participacao_pct` até aquele item (inclusive)
- `faixa`: calculada pelo acumulado **após** incluir o item:
  - `"A"` se `acumulado_pct ≤ 80`
  - `"B"` se `acumulado_pct ≤ 95`
  - `"C"` caso contrário
- `total_versao` usa `Versao.total_sem_bdi` (campo armazenado)
- `descricao`: `item.composicao.descricao` se existir, caso contrário string vazia `""`
- `grupo_nome`: `item.grupo.nome`
- A query de itens usa `selectinload(Item.grupo)` e `selectinload(Item.composicao)` para evitar N+1

**Caso sem dados:** se não houver itens com `total > 0`, retorna `{"total_versao": str(versao.total_sem_bdi), "itens": []}`.  
Se `float(versao.total_sem_bdi) == 0`: retorna dados vazios sem tentar calcular participações.

### 3.3 GET `/versoes/{versao_id}/curva-abc/export`

Retorna `StreamingResponse` com:
- `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- `Content-Disposition: attachment; filename="curva-abc-v{versao_id}.xlsx"`

**Estrutura do Excel (openpyxl):**
- Linha 1: cabeçalho em negrito — `#`, `Grupo`, `Descrição`, `Unidade`, `Quantidade`, `Total (R$)`, `Part%`, `Acum%`, `Faixa`
- Linhas de dados: preenchimento de fundo por faixa:
  - A → `#DCFCE7` (verde claro)
  - B → `#FEF9C3` (amarelo claro)
  - C → `#F1F5F9` (cinza claro)
- Linha final: "Total" com soma de `Total (R$)` em negrito
- Larguras de coluna ajustadas (col A:5, B:20, C:40, D:10, E:15, F:18, G:10, H:10, I:8)

### 3.4 Schemas (`backend/app/schemas/curva_abc.py`)

```python
from typing import Literal, Optional
from pydantic import BaseModel


class CurvaAbcItem(BaseModel):
    rank: int
    grupo_nome: str
    descricao: str
    unidade: str
    quantidade: str
    total: str
    participacao_pct: float
    acumulado_pct: float
    faixa: Literal["A", "B", "C"]


class CurvaAbcData(BaseModel):
    total_versao: str
    itens: list[CurvaAbcItem]
```

### 3.5 Isolamento

O router verifica que a versão pertence a uma obra da empresa do usuário autenticado — mesmo padrão de `_get_versao_acesso` do `cronograma.py`:

```python
result = await db.execute(
    select(Versao)
    .join(Obra, Versao.obra_id == Obra.id)
    .where(Versao.id == versao_id, Obra.empresa_id == current_user.empresa_id)
)
versao = result.scalar_one_or_none()
if versao is None:
    raise HTTPException(status_code=404, detail="Versão não encontrada")
```

### 3.6 Testes (`tests/backend/test_curva_abc.py`)

| Teste | Descrição |
|---|---|
| `test_curva_abc_ordenada_por_total` | Itens retornados em ordem decrescente de total |
| `test_curva_abc_calcula_participacao` | `participacao_pct` e `acumulado_pct` corretos |
| `test_curva_abc_faixas_corretas` | Faixas A/B/C atribuídas nos limites 80/95 |
| `test_curva_abc_exclui_total_zero` | Item com `total == 0` não aparece |
| `test_curva_abc_vazio` | Versão sem itens → `itens: []` |
| `test_curva_abc_export_xlsx` | Export retorna 200 com content-type correto |
| `test_isolamento_empresa_b` | Empresa B recebe 404 |

---

## 4. Frontend

### 4.1 Arquivos

**Novos:**
- `frontend/src/api/curvaAbc.ts`
- `frontend/src/components/obra/CurvaAbc.tsx`

**Modificados:**
- `frontend/src/types.ts` — adiciona `CurvaAbcItem` e `CurvaAbcData`
- `frontend/src/pages/ObraDetailPage.tsx` — adiciona aba `'curva-abc'`

### 4.2 Tipos (`types.ts`)

```ts
export interface CurvaAbcItem {
  rank: number
  grupo_nome: string
  descricao: string
  unidade: string
  quantidade: string
  total: string
  participacao_pct: number
  acumulado_pct: number
  faixa: 'A' | 'B' | 'C'
}

export interface CurvaAbcData {
  total_versao: string
  itens: CurvaAbcItem[]
}
```

### 4.3 API (`api/curvaAbc.ts`)

```ts
import { api } from '@/api/client'
import type { CurvaAbcData } from '@/types'

export const getCurvaAbc = (versaoId: number): Promise<CurvaAbcData> =>
  api.get<CurvaAbcData>(`/versoes/${versaoId}/curva-abc`).then(r => r.data)

export async function downloadCurvaAbcExcel(versaoId: number): Promise<void> {
  const resp = await api.get(`/versoes/${versaoId}/curva-abc/export`, {
    responseType: 'blob',
  })
  const url = URL.createObjectURL(resp.data)
  const a = document.createElement('a')
  a.href = url
  a.download = `curva-abc-v${versaoId}.xlsx`
  a.click()
  URL.revokeObjectURL(url)
}
```

### 4.4 ObraDetailPage

- `type Tab = 'versoes' | 'dashboard' | 'curva-abc'`
- Terceira aba: label `"Curva ABC"`
- Para obter `versaoId`: filtra `versoes.find(v => !v.bloqueada && !v.deletada_em)?.id`
- `{tab === 'curva-abc' && versaoAtiva && <CurvaAbc versaoId={versaoAtiva.id} />}`
- Se `tab === 'curva-abc'` e não há versão ativa: mensagem "Nenhuma versão ativa para esta obra"

### 4.5 CurvaAbc.tsx

```
Props: { versaoId: number }

Estados:
- loading: skeleton / spinner
- vazio (itens.length === 0): "Nenhum item com valor cadastrado nesta versão"
- com dados: KPI + tabela + botão export

Layout:
┌─────────────────────────────────────────────────┐
│ Total da versão: R$ 12.400.000,00   [Exportar Excel] │
├─────────────────────────────────────────────────┤
│ #  │ Grupo │ Descrição │ Un │ Qtd │ Total │ Part% │ Acum% │ Faixa │
│ 1  │ Pavi  │ CBUQ...   │ m² │ 12k │ 4,2M  │ 33,9% │ 33,9% │  A   │  ← verde
│ 2  │ Terra │ Escav...  │ m³ │ 50k │ 3,1M  │ 25,0% │ 58,9% │  A   │  ← verde
│ 3  │ Dren  │ Bueiro... │ un │ 120 │ 2,6M  │ 21,0% │ 79,9% │  A   │  ← verde
│ 4  │ Sinal │ Pintura   │ m  │ 8k  │ 1,0M  │  8,1% │ 88,0% │  B   │  ← amarelo
│ 5  │ OAE   │ Pontilhão │ un │   2 │ 0,9M  │  7,3% │ 95,3% │  B   │  ← amarelo
│ 6  │ Admin │ Mob...    │ vb │   1 │ 0,6M  │  4,7% │100,0% │  C   │  ← cinza
└─────────────────────────────────────────────────┘

Cores de linha:
- Faixa A: bg-green-50
- Faixa B: bg-yellow-50
- Faixa C: bg-gray-50
```

---

## 5. Fora do escopo deste módulo

- Exportação em PDF (Módulo 10 — Geração de Documentos)
- Filtro por grupo ou faixa
- Curva ABC por `total_com_bdi`
- Comparativo entre versões

---

## 6. Dependências

- `openpyxl` já está na stack (usado por outros módulos futuros)
- Nenhuma migração de banco de dados
- Nenhum pacote novo de frontend
