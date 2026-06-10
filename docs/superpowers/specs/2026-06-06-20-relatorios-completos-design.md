# Módulo 20 — Relatórios Completos: Design Spec

**Data:** 2026-06-06
**Status:** Aprovado para implementação

---

## 1. Objetivo

Expandir a página `/relatorios` — atualmente uma lista de botões de download — em três subtabs funcionais conforme definido na seção 8 do design spec original:

> **Relatórios:** Curva ABC | Medições | Comparativo de Versões

Nenhuma tabela nova é criada. Todo o conteúdo é derivado de dados já existentes.

---

## 2. Estrutura da Página

`RelatoriosPage` passa a ter três subtabs com estado independente:

| Aba | Conteúdo |
|-----|----------|
| Curva ABC | Tabela de ranking com faixas A/B/C + downloads Excel/PDF |
| Medições | Planejado × Realizado por grupo com desvio — baseado na última medição da versão ativa |
| Comparativo de Versões | Diff item a item entre duas versões de uma mesma obra |

Cada aba tem seu próprio seletor de obra (e versão onde aplicável). O seletor de obra é compartilhado entre as três abas via estado local em `RelatoriosPage`.

Os botões de download existentes (Proposta PDF, Curva ABC Excel) movem para dentro das abas correspondentes.

---

## 3. Backend

### 3.1 Endpoints existentes (sem alteração)

| Endpoint | Usado em |
|----------|----------|
| `GET /versoes/{id}/curva-abc` | Aba Curva ABC |
| `GET /versoes/{id}/curva-abc/xlsx` | Botão download Excel |
| `GET /versoes/{id}/proposta/pdf` | Mantido na aba Curva ABC |

### 3.2 Novo: `GET /versoes/{versao_id}/relatorio-medicao`

**Descrição:** Agrega planejado (cronograma) e realizado (última medição) por grupo da versão.

**Autorização:** tenant isolation por `empresa_id`.

**Algoritmo:**
1. Carregar todos os `Item` da versão com `CronogramaLinha` e `Grupo` via `selectinload`
2. Identificar a última medição da versão: `MAX(periodo_fim)`, desempate por `MAX(id)`
3. Para cada grupo raiz:
   - `planejado_pct`: para cada item do grupo que tem `CronogramaLinha`, somar os valores de `distribuicao_json` cujas chaves (formato `YYYY-MM`) sejam ≤ ao mês corrente (`datetime.now().strftime("%Y-%m")`); calcular média ponderada pelo `item.total` entre os itens do grupo
   - `realizado_pct`: média ponderada de `percentual_executado_acumulado` de `linhas_json` da última medição, ponderada por `item.total`
   - `valor_medido`: `SUM(item.total * realizado_pct / 100)` por grupo
   - `desvio_pct`: `realizado_pct - planejado_pct`
4. Se não há medições: retornar lista com `realizado_pct = 0` para todos os grupos

**Response schema:**
```python
class RelatorioMedicaoGrupo(BaseModel):
    grupo_id: int
    grupo_nome: str
    planejado_pct: float   # % planejado acumulado até hoje
    realizado_pct: float   # % realizado acumulado (última medição)
    desvio_pct: float      # realizado - planejado
    valor_medido: Decimal  # R$ medido
    valor_total: Decimal   # R$ total do grupo (referência)

class RelatorioMedicaoOut(BaseModel):
    versao_id: int
    ultima_medicao_id: Optional[int]
    periodo_fim: Optional[date]
    grupos: list[RelatorioMedicaoGrupo]
```

### 3.3 Novo: `GET /obras/{obra_id}/comparar`

**Query params:** `v1` (int), `v2` (int) — IDs de duas versões da mesma obra.

**Autorização:** obra e ambas as versões devem pertencer à `empresa_id` do usuário. Versões de outra obra → HTTP 400.

**Algoritmo:**
1. Carregar todos os `Item` de V1 e V2 com `selectinload(Item.grupo)` e `selectinload(Item.composicao)` (para obter `composicao.descricao` e `composicao.unidade`)
2. Join por `composicao_id` (itens com mesma composição são o "mesmo item"). Itens sem `composicao_id` não têm par identificável — são sempre classificados como NOVO (V2) ou REMOVIDO (V1)
3. Classificar cada item pareado:
   - `novo`: presente em V2, ausente em V1
   - `removido`: presente em V1, ausente em V2
   - `alterado`: presente em ambos, com `preco_unitario_sem_bdi` ou `quantidade` diferente
   - `igual`: presente em ambos, sem diferença
4. Itens `igual` são incluídos na resposta mas filtráveis no frontend

**Response schema:**
```python
class ComparativoItem(BaseModel):
    status: Literal["novo", "removido", "alterado", "igual"]
    grupo_nome: str
    descricao: str   # composicao.descricao (ou "Item sem composição" se composicao_id=None)
    unidade: str     # composicao.unidade ou item.unidade
    v1_preco_unit: Optional[Decimal]
    v2_preco_unit: Optional[Decimal]
    v1_quantidade: Optional[Decimal]
    v2_quantidade: Optional[Decimal]
    v1_total: Optional[Decimal]
    v2_total: Optional[Decimal]
    delta_total: Decimal   # v2_total - v1_total (0 se um lado ausente)

class ComparativoOut(BaseModel):
    obra_id: int
    v1_id: int
    v2_id: int
    v1_nome: str
    v2_nome: str
    v1_total: Decimal
    v2_total: Decimal
    delta_total: Decimal
    delta_pct: float
    qtd_novos: int
    qtd_removidos: int
    qtd_alterados: int
    itens: list[ComparativoItem]
```

---

## 4. Frontend

### 4.1 Arquivos novos

| Arquivo | Responsabilidade |
|---------|-----------------|
| `frontend/src/components/relatorios/CurvaAbcTab.tsx` | Tabela com badges A/B/C, resumo por faixa, downloads |
| `frontend/src/components/relatorios/MedicoesTab.tsx` | Tabela grupos × planejado/realizado com desvio colorido |
| `frontend/src/components/relatorios/ComparativoTab.tsx` | Seletores V1/V2, badges resumo, tabela diff |
| `frontend/src/api/relatorios.ts` | `getRelatorioMedicao`, `getComparativo` |

### 4.2 Arquivos modificados

| Arquivo | Alteração |
|---------|-----------|
| `frontend/src/pages/RelatoriosPage.tsx` | Adicionar 3 subtabs, seletor de obra compartilhado, remover botões soltos |

### 4.3 Comportamento por aba

**Curva ABC:**
- Seletor de obra → carrega versão ativa automaticamente → exibe tabela
- Badge de resumo por faixa (A: N serviços · X%, B: ..., C: ...)
- Cores: verde (A), amarelo (B), vermelho (C)
- Botões: ↓ Excel, ↓ PDF

**Medições:**
- Seletor de obra → carrega versão ativa → chama `relatorio-medicao`
- Tabela: Grupo | Planejado % | Realizado % | Desvio | Valor medido
- Desvio positivo = verde, negativo = vermelho
- Empty state quando não há medições registradas

**Comparativo:**
- Seletor de obra → lista todas as versões (ativas e bloqueadas) → dois dropdowns V1 / V2
- Só habilita "Comparar" quando V1 ≠ V2
- Badges: adicionados (verde), removidos (laranja), alterados (azul)
- Checkbox "Mostrar itens iguais" (off por padrão)
- Linha colorida por status: verde (novo), laranja (removido), branco (alterado/igual)

---

## 5. Testes Backend

| Teste | Cenário |
|-------|---------|
| `test_relatorio_medicao_sem_medicoes` | Retorna grupos com realizado_pct = 0 |
| `test_relatorio_medicao_com_medicao` | realizado_pct e valor_medido corretos |
| `test_relatorio_medicao_tenant_isolation` | Versão de outra empresa → 404 |
| `test_comparativo_item_novo` | Item em V2 sem par em V1 → status "novo" |
| `test_comparativo_item_removido` | Item em V1 sem par em V2 → status "removido" |
| `test_comparativo_preco_alterado` | Mesmo composicao_id, preço diferente → status "alterado" |
| `test_comparativo_versoes_de_obras_diferentes` | V1 e V2 de obras distintas → 400 |
| `test_comparativo_tenant_isolation` | Versão de outra empresa → 404 |

---

## 6. Fora do Escopo

- Exportação do comparativo em PDF/Excel (pode ser adicionado depois)
- Gráfico de barras para medições (tabela é suficiente para v1)
- Comparativo de BDI entre versões
- Filtro por grupo no comparativo
