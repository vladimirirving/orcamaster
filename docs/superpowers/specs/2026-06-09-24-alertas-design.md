# Módulo 24 — Notificações / Alertas: Design Spec

## Objetivo

Exibir alertas calculados em tempo real sobre contratos vencendo, desvios de orçamento, medições atrasadas e itens para revisar — via sino na sidebar com painel deslizante, acessível de qualquer página.

---

## Backend

### Endpoint

`GET /alertas` — autenticado, sem parâmetros. Retorna todos os alertas da empresa do usuário logado, calculados no momento da requisição.

### Tipos de alerta

| tipo | severidade | lógica |
|------|-----------|--------|
| `contrato_vencido` | alta | `data_fim_atual < hoje` |
| `contrato_vencendo` | média | `hoje <= data_fim_atual <= hoje + 30 dias` |
| `desvio_orcamento` | média | `realizado_pct > planejado_pct + 10` na versão ativa |
| `medicao_atrasada` | média | obra em elaboração + versão ativa com cronograma + sem medição no mês corrente |
| `item_revisao` | baixa | itens com `requer_revisao=True` na versão ativa (agrupados por obra, não por item) |

**Regras de geração:**
- `contrato_vencido` e `contrato_vencendo` são mutuamente exclusivos por contrato: se `data_fim_atual < hoje` gera `vencido`; se `hoje <= data_fim_atual <= hoje+30` gera `vencendo`.
- `item_revisao`: um alerta por obra, com `detalhe = "N itens aguardando revisão"`.
- Contratos sem `data_fim_atual` não geram alerta de prazo.
- Obras com estado `arquivado` ou `concluido` são ignoradas em todos os tipos.

### Schema de retorno

```python
class AlertaOut(BaseModel):
    tipo: str          # 'contrato_vencido' | 'contrato_vencendo' | 'desvio_orcamento'
                       # | 'medicao_atrasada' | 'item_revisao'
    severidade: str    # 'alta' | 'media' | 'baixa'
    obra_id: int
    obra_nome: str
    titulo: str        # Ex: "Contrato CT-2026-001 venceu há 3 dias"
    detalhe: str | None  # Ex: "Prazo: 2026-06-06" ou "Realizado 22% · Planejado 10%"
    link: str          # Rota frontend para navegar ao clicar — Ex: "/obras/1?tab=contratos"
```

Ordenação: alta → média → baixa; dentro de cada severidade, por `obra_nome`.

### Implementação

**Arquivo:** `backend/app/routers/alertas.py`

Consultas necessárias:
1. Contratos da empresa com `data_fim_atual` não-nula e estado obra `em_elaboracao`
2. Versões ativas das obras em elaboração → buscar `realizado_pct` e `planejado_pct` do endpoint de dashboard (reutilizar lógica existente ou query direta)
3. Versões ativas com cronograma configurado → verificar se há `Medicao` com `periodo_inicio` no mês corrente
4. Itens com `requer_revisao=True` na versão ativa de cada obra

Registrado em `main.py`: `app.include_router(alertas_router)`.

### Testes

`tests/backend/test_alertas.py` — ~8 testes:
- Lista vazia quando não há alertas
- Gera `contrato_vencido` corretamente
- Gera `contrato_vencendo` corretamente (30 dias)
- Não gera alerta para contrato sem data_fim_atual
- Não gera alerta para obra concluída/arquivada
- Gera `item_revisao` agrupado por obra
- Gera `medicao_atrasada` quando sem medição no mês
- Não gera `medicao_atrasada` quando já há medição no mês

---

## Frontend

### Componentes novos

#### `frontend/src/api/alertas.ts`

```typescript
export interface Alerta {
  tipo: string
  severidade: 'alta' | 'media' | 'baixa'
  obra_id: number
  obra_nome: string
  titulo: string
  detalhe: string | null
  link: string
}

export const getAlertas = () =>
  api.get<Alerta[]>('/alertas').then(r => r.data)
```

#### `frontend/src/components/layout/AlertasPanel.tsx`

Painel deslizante `fixed` posicionado à direita da sidebar (`left-56 top-0 h-full w-80`), com overlay escuro atrás. Fecha ao clicar no overlay ou no botão X.

- Agrupa alertas por severidade: ALTA → MÉDIA → BAIXA
- Cada alerta é um botão clicável que navega para `alerta.link` e fecha o painel
- Badge de cor por severidade: vermelho (alta), amarelo (média), cinza (baixa)
- Estado vazio: "Nenhum alerta no momento 🎉"

### Modificações em `Sidebar.tsx`

1. Importar `getAlertas` e estado `alertas: Alerta[]`
2. `useEffect` busca `getAlertas()` ao montar e a cada 5 minutos (polling com `setInterval`)
3. Ícone de sino antes de Configurações no rodapé, com badge vermelho quando `alertas.length > 0`
4. Estado `painelOpen: boolean` controla visibilidade do `AlertasPanel`

---

## Títulos gerados por tipo

| tipo | titulo | detalhe |
|------|--------|---------|
| `contrato_vencido` | `"Contrato {numero} venceu"` ou `"Contrato venceu"` | `"Prazo: {data_fim_atual}"` |
| `contrato_vencendo` | `"Contrato {numero} vence em {N} dias"` | `"Prazo: {data_fim_atual}"` |
| `desvio_orcamento` | `"Desvio de orçamento: +{N}%"` | `"Realizado {r}% · Planejado {p}%"` |
| `medicao_atrasada` | `"Medição de {Mês/Ano} não lançada"` | `null` |
| `item_revisao` | `"{N} itens aguardando revisão"` | `null` |

## Links de navegação por tipo

| tipo | link |
|------|------|
| `contrato_vencido` / `contrato_vencendo` | `/obras/{obra_id}?tab=contratos` |
| `desvio_orcamento` | `/obras/{obra_id}?tab=dashboard` |
| `medicao_atrasada` | versao ativa → `/obras/{obra_id}/versoes/{versao_id}` |
| `item_revisao` | versao ativa → `/obras/{obra_id}/versoes/{versao_id}` |

**Nota:** Os links usam query param `?tab=contratos` / `?tab=dashboard`. `ObraDetailPage` precisa ler esse param no mount para abrir a aba correta. Se não quiser essa complexidade, os links podem ser só `/obras/{obra_id}` sem tab param.

---

## Decisões de Design

- **Sem tabela de alertas:** calculado em tempo real — simples, sem jobs, sem estado stale
- **Polling a cada 5 minutos:** suficiente para alertas de prazo; evita WebSocket para algo não urgente
- **Obras concluídas/arquivadas ignoradas:** alertas só fazem sentido para obras ativas
- **item_revisao agrupado:** 1 alerta por obra, não 1 por item — evita flood no painel
- **link com ?tab=** é opcional — implementar somente se ObraDetailPage já suportar query param de tab (verificar durante implementação)
