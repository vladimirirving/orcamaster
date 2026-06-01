# Sistema de Orçamento de Obras para Licitações

**Data:** 2026-05-31
**Status:** Aprovado para implementação
**Tipo de obra:** Infraestrutura (rodovias, saneamento, pontes, redes elétricas)

---

## 1. Contexto e Objetivo

Sistema web interno para empresas de engenharia de infraestrutura gerenciarem o ciclo completo de orçamentação de obras para licitações públicas. O sistema centraliza o processo que hoje é feito em múltiplas ferramentas (Excel, outros softwares), adicionando controle multiusuário, banco de composições unificado (SINAPI + SICRO + próprias) e um agente IA para acelerar a montagem de planilhas.

**Saída principal:** Pacote completo de documentos para licitação pública conforme TCU/CEF — planilha orçamentária, memorial de BDI, cronograma físico-financeiro com Curva S, composições analíticas e proposta para pregão.

---

## 2. Arquitetura e Stack

| Camada | Tecnologia |
|--------|-----------|
| Frontend | React + TypeScript + Vite |
| UI Components | shadcn/ui |
| Tabelas/grids | TanStack Table |
| Gráficos | Recharts |
| Backend | Python + FastAPI |
| Banco de dados | PostgreSQL |
| Agente IA | Claude API (claude-sonnet-4-6) com tool use |
| PDF | WeasyPrint |
| Excel | openpyxl |
| Auth | JWT com refresh token |
| Jobs agendados | APScheduler (embutido no processo FastAPI) |
| Infraestrutura | Docker Compose (on-premise ou VPS) |

Arquitetura monolítica — frontend e backend no mesmo repositório, deploy via Docker Compose. Sem dependências de serviços pagos obrigatórios.

**Jobs agendados (APScheduler):** dois jobs recorrentes registrados na inicialização do servidor:
- **Purge de versões excluídas** — roda diariamente; hard-deleta `Versao` onde `deletada_em + 90 dias < agora`, após remover PacoteJobs associados.
- **Expiração de pacotes** — roda diariamente; atualiza `PacoteJob.status = 'expirado'` onde `gerado_em + 7 dias < agora AND status = 'pronto'`.

---

## 3. Módulos do Sistema

### 3.1 Gestão de Obras

Cadastro central de cada licitação/obra:

- Nome, número do processo licitatório, cliente/órgão
- Localização (UF, município)
- Tipo: rodovia, saneamento, ponte, rede elétrica, outro
- Estado: `em_elaboracao` | `concluido` | `arquivado`
- Responsável (usuário da empresa)
- Datas de início/entrega do orçamento

Hierarquia de propriedade: **Obra → Versão → (Grupo, BDI, Item, Medição)**. CronogramaLinha é filho indireto de Versão via `item_id → Grupo → Versão` (sem FK direta em `versao_id` — ver seção 5). Obra é apenas o contêiner de identidade e metadados — todas as entidades de orçamento pertencem a uma Versão específica.

### 3.2 Banco de Composições

Repositório unificado com três origens:

- **SINAPI** — importado da CEF (CSV/Excel mensal). Referência para edificações e serviços gerais.
- **SICRO** — importado do DNIT (CSV/Excel). Referência obrigatória para obras rodoviárias e infraestrutura.
- **Próprias** — criadas pela equipe. Podem partir de zero ou derivar de uma composição SINAPI/SICRO editada.

Cada composição contém: código, descrição, unidade, lista de insumos (mão de obra, material, equipamento) com coeficientes e preço unitário calculado.

**Precisão numérica:** todos os campos monetários (preço de insumo, preço unitário de composição, coeficiente) são armazenados como `NUMERIC(15,6)` no banco. Totais de Item e Versão são arredondados para `NUMERIC(15,2)` apenas na camada de apresentação e nos documentos exportados. Cálculos intermediários nunca arredondam para preservar fidelidade com as tabelas SINAPI/SICRO.

### 3.3 Editor de Planilha Orçamentária

Coração do sistema. Estrutura hierárquica com **exatamente dois níveis de agrupamento**: Grupo → Subgrupo → Item. Profundidade máxima permitida: 2 (um Grupo pode conter Subgrupos, um Subgrupo não pode conter outros Subgrupos). O modelo de dados usa `pai_id` mas a API rejeita qualquer tentativa de criar um nó filho de um Subgrupo (profundidade > 2).

Funcionalidades:
- Busca de composições por código ou descrição (SINAPI, SICRO ou próprias)
- Entrada de quantidades; preço unitário **snapshot**: ao associar uma composição ao item, o sistema copia e armazena `preco_unitario` da composição naquele momento. Atualizações posteriores do SINAPI/SICRO não alteram itens já inseridos em versões existentes. O orçamentista clica em "Atualizar preço" no item (botão inline na grid da planilha) para aceitar o novo preço — isso sobrescreve o snapshot armazenado e limpa o flag `requer_revisao` do item. Cópia de template de obra anterior: os preços são sempre **refrescados** da tabela SINAPI/SICRO atual no momento da cópia — nunca herdados da obra-fonte.
- Cálculo automático de totais parciais e total geral (com e sem BDI)
- Importação de estrutura de obras anteriores (cópia de template)
- Importação via Excel (planilha própria da empresa)
- Etiquetas de revisão para marcar itens críticos ou em dúvida

### 3.4 Cálculo de BDI

Formulário configurável com parcelas:

- Administração central (AC)
- Seguro + Garantia (S+G)
- Risco (R)
- Despesas financeiras (DF)
- Lucro (L)
- Impostos: ISS, PIS, COFINS

Calcula BDI composto pela fórmula padrão TCU. A cada salvamento o sistema: (1) adiciona um snapshot ao `historico_json` do BDI; (2) recalcula e persiste `preco_unitario_com_bdi` em **todos os Items da versão** (`preco_unitario_sem_bdi × (1 + novo_bdi_composto)`); (3) recalcula e persiste `total_com_bdi` na Versão. Essa sequência garante que os snapshots por item nunca fiquem desatualizados em relação ao BDI vigente. Exibe aviso se parcelas estiverem fora dos limites referenciais do TCU (sem bloquear).

Na v1, um único BDI por versão de orçamento. BDIs diferenciados por tipo de serviço (ex: BDI reduzido para materiais com fornecimento) estão fora do escopo da v1.

### 3.5 Cronograma Físico-Financeiro

Grade com serviços nas linhas e meses nas colunas. O orçamentista distribui percentuais de execução por período.

Cálculos automáticos:
- Valor financeiro mensal por item
- Total financeiro mensal da obra
- Curva S (avanço financeiro acumulado %)
- Valor acumulado mensal

Validação: percentuais de cada item devem somar 100% antes de permitir exportação.

### 3.6 Medição de Obras

Registro do avanço físico real contra o planejado. A Medição pertence a uma **Versão** (não diretamente à Obra), garantindo que os `item_id` em `linhas_json` correspondam sempre aos itens da versão correta. O orçamentista registra o percentual **acumulado** executado por item (0–100) — não o incremento do período. O sistema calcula o avanço do período por diferença entre medições consecutivas da mesma versão.

**Baseline da primeira medição:** a primeira Medição de uma versão parte de 0% acumulado. Se uma nova versão é criada após progresso físico real, o orçamentista deve registrar uma medição de baseline (com os percentuais acumulados reais) antes de continuar o registro normal. Medições de versões anteriores **não são copiadas** para a nova versão — permanecem acessíveis pela versão de origem. O módulo Relatórios permite comparar medições entre versões distintas da mesma obra.

**Versão ativa para medição:** o módulo Medição sempre opera sobre a versão ativa da obra (a não bloqueada). Não é possível registrar medições em versões bloqueadas.

Relatórios gerados:
- Comparativo planejado × realizado por item
- Valor medido acumulado
- Desvios por grupo de serviço

### 3.7 Versionamento de Orçamentos

Cada Obra pode ter múltiplas versões (v1, v2, v3...). Ao iniciar revisão, o sistema cria nova versão com cópia automática da planilha atual. Versões anteriores ficam bloqueadas para edição mas disponíveis para:

- Consulta
- Comparação lado a lado com versão atual
- Restauração (cria nova versão a partir da antiga)

Versões excluídas ficam recuperáveis por 90 dias.

### 3.8 Curva ABC

Relatório automático que ordena os serviços da planilha por valor total decrescente, calculando participação percentual e percentual acumulado. Classifica em faixas A (80%), B (15%), C (5%). Gerado sob demanda e exportável em PDF/Excel.

### 3.9 Gerador de Proposta para Pregão

Documento formatado especificamente para licitações por pregão eletrônico. Inclui campos exigidos tipicamente em editais: identificação da empresa, CNPJ, representante legal, validade da proposta, declarações, planilha de preços unitários e totais. Template configurável pelo Administrador.

### 3.10 Geração de Documentos

O orçamentista aciona "Gerar pacote de licitação" na versão ativa. O sistema gera em background e disponibiliza um arquivo `.zip` contendo:

| Documento | Formatos |
|-----------|---------|
| Planilha orçamentária | PDF + Excel |
| Memorial de cálculo do BDI | PDF |
| Cronograma físico-financeiro | PDF + Excel |
| Curva S | PDF |
| Composições analíticas dos serviços | PDF |
| Curva ABC | PDF + Excel |
| Proposta para pregão (opcional) | PDF |

### 3.11 Dashboard

Tela inicial do sistema após login. Apresenta visão consolidada da empresa e da obra ativa em painéis visuais. Todos os dados são leitura pura — nenhuma lógica de negócio nova; todas as métricas são derivadas das entidades existentes.

**Dois níveis de visão, alternáveis via toggle:**

**Visão Empresa** — panorama de todas as obras da empresa:

| Painel | Conteúdo | Tipo de gráfico |
|--------|----------|----------------|
| Portfólio de obras | Cards por obra: nome, estado (`em_elaboracao` \| `concluido` \| `arquivado`), valor total com BDI, responsável, prazo | Cards com badge de estado |
| Valor total em elaboração | Soma de `total_com_bdi` de todas as versões ativas | KPI numérico destacado |
| Distribuição por estado | Quantidade e valor de obras por estado | Gráfico de rosca |
| Obras com alertas | Lista de obras com itens `requer_revisao = true` ou sem BDI configurado | Tabela de alertas |

**Visão Obra** — foco na obra/versão ativa selecionada na barra de contexto:

| Painel | Conteúdo | Tipo de gráfico |
|--------|----------|----------------|
| KPIs financeiros | Total sem BDI · Total com BDI · Delta vs. versão anterior (% e valor absoluto) | KPIs com variação colorida (verde/vermelho) |
| Distribuição por grupo | Participação percentual de cada Grupo de serviço no total sem BDI | Gráfico de rosca interativo — clicar no grupo abre a planilha filtrada |
| Curva S | Avanço financeiro planejado (cronograma) vs. realizado (medições), mês a mês | Gráfico de linha com duas séries + área sombreada entre elas |
| Progresso físico | % acumulado executado por Grupo (último período de Medição) vs. planejado | Barras horizontais lado a lado |

**Algoritmo da série "realizado" da Curva S:** para cada mês do cronograma, localizar a Medição com `MAX(periodo_fim) ≤ último dia do mês` — em caso de empate em `periodo_fim`, desempatar por `MAX(id)`. Para cada Item, multiplicar `percentual_executado_acumulado` pelo `Item.total_com_bdi` (snapshot). Somar todos os itens para obter o valor financeiro acumulado realizado no mês. A série exibe o acumulado (não incremental), espelhando a Curva S planejada do cronograma.

**"Último período de Medição"** (painéis Progresso físico e Curva S): `MAX(periodo_fim)`, desempate por `MAX(id)`. Nunca por `criado_em` ou ordem de inserção arbitrária.
| Status do orçamento | Itens: total · sem composição · com `requer_revisao` · com `etiqueta_revisao` | Gráfico de barras empilhadas ou donut com legenda |
| Banco de composições | Contagem de composições por origem (SINAPI · SICRO · Próprias) e quantas estão em uso na versão ativa | Gráfico de barras agrupadas |
| Histórico de BDI | Evolução do `bdi_composto` ao longo das entradas em `historico_json` | Gráfico de linha |
| Alertas ativos | BDI fora dos limites TCU · pacote expirado · cronograma incompleto · itens sem preço | Lista priorizada com link direto para a tela do problema |

**Biblioteca de gráficos:** Recharts (já incluso no ecossistema React + TypeScript; não adiciona dependência externa significativa).

**Atualização:** os dados do dashboard são carregados sob demanda (sem WebSocket ou polling automático). Botão "Atualizar" no canto superior direito recarrega os painéis manualmente.

---

## 4. Agente IA

### 4.1 Objetivo

Permitir que o orçamentista descreva a obra em linguagem natural ou suba um edital em PDF, e o agente gere uma proposta estruturada de planilha para revisão — acelerando a fase inicial de montagem.

### 4.2 Modelo e Ferramentas

**Modelo:** Claude API (claude-sonnet-4-6) com tool use.

**Ferramentas disponíveis para o agente:**

- `buscar_composicao(query, base)` — busca composições no banco local (SINAPI, SICRO, próprias) por texto ou código
- `listar_grupos_tipicos(tipo_obra)` — retorna grupos de serviço típicos para o tipo de obra (ex: rodovia flexível → Terraplenagem, Drenagem, Pavimentação, OAC, Sinalização)
- `obter_composicao(codigo, base)` — retorna detalhes completos de uma composição

O agente **não** chama APIs externas — trabalha exclusivamente com o banco local. Isso garante preços atuais (conforme última importação) e rastreabilidade.

### 4.3 Entradas

**Texto livre:** O orçamentista descreve a obra em linguagem natural. Exemplo:
> "Rodovia estadual de 25km, 2 faixas de rolamento, pavimento flexível com CBUQ, relevo ondulado, solo de 1ª e 2ª categoria, drenagem superficial, sinalização horizontal e vertical, obras de arte correntes."

**Upload de PDF:** O sistema extrai o texto do edital/memorial descritivo, envia ao agente que identifica serviços exigidos, especificações técnicas e quantitativos indicados no documento.

Ambas as entradas podem ser usadas juntas (PDF + complemento em texto).

### 4.4 Tela de Revisão (obrigatória)

O agente nunca altera a planilha diretamente. Gera uma proposta exibida em tela de revisão onde o orçamentista pode, grupo por grupo:

- **Aceitar** — importa o grupo com todos os seus itens
- **Editar** — abre o grupo para ajuste antes de importar (itens, quantidades, códigos)
- **Remover** — descarta o grupo da proposta

Após revisar todos os grupos, o orçamentista clica em "Importar para planilha" e o sistema adiciona os itens aceitos/editados à planilha da versão ativa.

### 4.5 Chat de Refinamento

Após importar, um painel de chat lateral fica disponível dentro da obra. O orçamentista pode continuar interagindo:

- Adicionar serviços esquecidos
- Buscar códigos específicos
- Solicitar explicação de uma composição
- Pedir sugestão de quantitativos típicos por extensão/área

Respostas que implicam alteração na planilha são apresentadas como sugestão com botão de confirmação — nunca aplicadas automaticamente.

---

## 5. Modelo de Dados

### Entidades principais

**Obra**
```
id, empresa_id, nome, numero_processo, cliente, uf, municipio,
tipo_obra, estado, responsavel_id, data_criacao, data_prazo
```

**Versao**
```
id, obra_id, numero (1,2,3...), nome, criada_em, criada_por,
bloqueada (bool), total_sem_bdi, total_com_bdi,
deletada_em (timestamp nullable — null = ativa ou bloqueada, preenchido = soft-deleted)
```
`total_sem_bdi` e `total_com_bdi` são recalculados e persistidos sempre que um Item é inserido, editado ou removido, e sempre que o BDI da versão é salvo. Não são calculados em tempo de consulta — são caches atualizados na escrita. `deletada_em` suporta a recuperação por 90 dias: versões excluídas são soft-deleted (campo preenchido), ocultadas da UI, e purgadas permanentemente por job agendado após `deletada_em + 90 dias`.

> **Definição canônica de "versão ativa":** `bloqueada = false AND deletada_em IS NULL`. Todo código que filtra "versões ativas" — incluindo Dashboard, propagação SINAPI/SICRO, módulo Medição e relatórios — deve aplicar **ambas** as condições. Versões bloqueadas (`bloqueada = true`) e versões soft-deleted (`deletada_em IS NOT NULL`) são excluídas mesmo que satisfaçam a outra condição.

**Grupo / Subgrupo**
```
id, versao_id, pai_id (null para grupos raiz), ordem, nome, codigo
```

**Item**
```
id, grupo_id, ordem, composicao_id (nullable — null quando item criado sem composição associada),
quantidade, unidade,
preco_unitario_sem_bdi (snapshot — NUMERIC(15,6), armazenado na inserção/atualização; null se composicao_id for null),
preco_unitario_com_bdi (snapshot — derivado de preco_unitario_sem_bdi × (1 + BDI), armazenado; null se composicao_id for null),
total (gerado — quantidade × COALESCE(preco_unitario_sem_bdi, 0), coluna GENERATED ALWAYS AS STORED; retorna 0 quando preco_unitario_sem_bdi for null — itens sem composição contribuem com zero ao total da versão, sem serem silenciosamente excluídos do SUM),
etiqueta_revisao (bool, manual — marcado pelo orçamentista),
requer_revisao (bool, automático — setado pelo sistema quando a composição base foi atualizada no SINAPI/SICRO)
```
`preco_unitario_sem_bdi` e `preco_unitario_com_bdi` **não são calculados em tempo de consulta** — são snapshots armazenados. `total` é uma coluna `GENERATED ALWAYS AS (quantidade * preco_unitario_sem_bdi) STORED` no PostgreSQL, suportando índice funcional para Curva ABC.

**Composicao**
```
id, empresa_id (null para SINAPI/SICRO), origem (sinapi|sicro|propria),
codigo, descricao, unidade, preco_unitario, data_referencia,
base_origem_id (para próprias derivadas)
```

**Insumo**
```
id, composicao_id, tipo (mao_obra|material|equipamento),
descricao, unidade, coeficiente, preco_unitario
```

**BDI**
```
id, versao_id UNIQUE, ac, sg, r, df, lucro, iss, pis, cofins,
bdi_composto (armazenado — calculado em cada salvamento, NOT GENERATED), historico_json
```
`UNIQUE(versao_id)` é enforçado no banco — existe exatamente um registro BDI por Versão. `bdi_composto` é uma coluna plain armazenada (não `GENERATED ALWAYS`): a fórmula TCU é calculada na camada de aplicação antes do upsert e gravada explicitamente. O endpoint usa upsert com `bdi_composto` presente em **ambos** os branches (INSERT e ON CONFLICT):
```sql
INSERT INTO bdi (versao_id, ac, sg, r, df, lucro, iss, pis, cofins, bdi_composto, historico_json)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, <valor_calculado>, '[<snapshot_inicial>]'::jsonb)
ON CONFLICT (versao_id) DO UPDATE SET
  ac=..., sg=..., r=..., df=..., lucro=..., iss=..., pis=..., cofins=...,
  bdi_composto=<valor_calculado>,
  historico_json = historico_json || novo_snapshot
```
O branch INSERT inicializa `historico_json` com o primeiro snapshot; o branch UPDATE faz append. Em ambos os casos `bdi_composto` nunca é NULL após o upsert.

`historico_json` é um array append-only de snapshots: `[{timestamp, ac, sg, r, df, lucro, iss, pis, cofins, bdi_composto}]`. A cada salvamento um novo snapshot é **adicionado ao array** — nunca substituído. O estado atual é sempre o último elemento. Isso preserva rastreabilidade para auditoria TCU.

**CronogramaLinha**
```
id, item_id (FK → Item ON DELETE CASCADE), distribuicao_json ({mes: percentual})
```
`total_percentual` **não é armazenado** — é calculado dinamicamente pela aplicação como `SUM(distribuicao_json.values())` a cada leitura e validação. Armazená-lo separadamente criaria risco de divergência com o JSON sem trigger ou constraint que garantisse consistência. A validação de exportação (seção 9) lê diretamente a soma dos valores do JSON.

`versao_id` é omitido: a versão é derivada via `item_id → Grupo → Versao`. A query de cópia no workflow de versionamento usa:
```sql
INSERT INTO cronograma_linha (item_id, distribuicao_json)
SELECT mapa_itens.novo_item_id, cl.distribuicao_json
FROM cronograma_linha cl JOIN mapa_itens ON cl.item_id = mapa_itens.item_id_antigo;
```
`ON DELETE CASCADE` em `item_id`: ao remover um item da planilha, sua CronogramaLinha é eliminada automaticamente, prevenindo linhas órfãs que bloqueariam a validação de exportação.

**Medicao**
```
id, versao_id, periodo_inicio, periodo_fim, criada_por,
linhas_json ({item_id: percentual_executado_acumulado})
```
Vinculada à Versão (não à Obra) para garantir que os `item_id` em `linhas_json` sempre referenciem itens da versão correta. `percentual_executado_acumulado` é o percentual total executado até esse período (0–100) — não o avanço incremental.

**PacoteJob**
```
id, empresa_id, versao_id, status (pendente|processando|pronto|erro|expirado),
criado_em, atualizado_em, url_download (nullable), erro_mensagem (nullable), gerado_em (nullable)
```
Registra cada solicitação de geração de pacote de licitação. O limite de 2 jobs simultâneos por empresa é enforçado verificando `COUNT(*) WHERE empresa_id = ? AND status IN ('pendente','processando')` dentro de uma transação serializable antes de inserir novo job. Arquivo expira após 7 dias (`expirado` setado por job agendado quando `gerado_em + 7 dias < agora`).

`versao_id` FK: `ON DELETE CASCADE` — ao hard-purgar uma Versão (após 90 dias de soft-delete), todos os seus PacoteJobs são eliminados em cascata. O job de purge de versões (APScheduler) executa na seguinte ordem: (1) cancela jobs `pendente|processando` da versão; (2) deleta a Versão (CASCADE elimina os PacoteJobs restantes). Isso garante que o prazo de 7 dias dos arquivos nunca excede o prazo de 90 dias da versão.

**Usuario**
```
id, empresa_id, nome, email, papel (admin|orcamentista|visualizador),
ativo
```

---

## 6. Papéis de Usuário

| Ação | Admin | Orçamentista | Visualizador |
|------|-------|-------------|-------------|
| Gerenciar usuários | ✓ | — | — |
| Importar SINAPI/SICRO | ✓ | — | — |
| Publicar composições próprias | ✓ | — | — |
| Criar/editar obras | ✓ | ✓ | — |
| Usar agente IA | ✓ | ✓ | — |
| Gerar documentos | ✓ | ✓ | — |
| Registrar medições | ✓ | ✓ | — |
| Visualizar obras e relatórios | ✓ | ✓ | ✓ |
| Exportar documentos | ✓ | ✓ | — |

Na v1 as permissões são por empresa — o Orçamentista acessa todas as obras da empresa.

---

## 7. Workflows Críticos

### Atualização SINAPI/SICRO

1. Admin acessa "Administração → Bases de Preços"
2. Faz upload do arquivo CSV/Excel da CEF (SINAPI) ou DNIT (SICRO)
3. Sistema processa e exibe diff: novos itens, itens alterados (preço/descrição), itens desativados
4. Admin revisa o diff e confirma a importação
5. Sistema atualiza o banco; composições próprias derivadas de itens alterados recebem flag `requer_revisao = true` na tabela `Composicao`; todos os `Item` em **versões ativas** (`bloqueada = false AND deletada_em IS NULL`) que referenciam essas composições recebem `requer_revisao = true` na tabela `Item`. Versões bloqueadas e versões soft-deleted são registros imutáveis — seus Items **não recebem** o flag
6. Notificação enviada para Orçamentistas listando obras/versões com itens marcados

### Geração do Pacote de Licitação

1. Orçamentista acessa a versão ativa da obra
2. Verifica alertas de validação (itens sem composição, BDI não configurado, cronograma incompleto)
3. Clica em "Gerar pacote de licitação"
4. Sistema processa em background (tarefa assíncrona via FastAPI BackgroundTasks)
5. Frontend faz polling no endpoint `GET /versoes/{versao_id}/pacote/status` a cada 5 segundos. O endpoint retorna o **PacoteJob mais recente** da versão (`ORDER BY criado_em DESC LIMIT 1`) — garantindo que após "Tentar novamente" o status do novo job substitua o anterior. Resposta:
   ```json
   { "status": "pendente"|"processando"|"pronto"|"erro"|"expirado",
     "url_download": "<url ou null>",
     "erro_mensagem": "<string ou null>",
     "gerado_em": "<ISO8601 ou null>" }
   ```
   Loop termina em `pronto`, `erro` ou `expirado`. Em `erro`, UI exibe mensagem e botão "Tentar novamente".
6. Arquivo fica disponível por 7 dias (`expirado` após esse prazo); pode ser regerado a qualquer momento. Máximo 2 jobs simultâneos por empresa — tentativas adicionais retornam `status: "pendente"` na fila.

### Cópia de Template de Obra Anterior

1. Orçamentista acessa "Obras → Nova obra" e seleciona "Usar obra anterior como template"
2. Escolhe a obra-fonte e qual versão copiar
3. Sistema cria a nova Obra com metadados zerados (nome, processo, cliente, etc. devem ser preenchidos)
4. Cria a Versão 1 da nova obra com cópia dos Grupos e Itens da versão-fonte; preços dos Itens são **refrescados** da Composição atual (SINAPI/SICRO vigente) — nunca herdados da obra-fonte. `requer_revisao` é resetado para `false` em todos os Itens. `etiqueta_revisao` é **resetado para `false`** — as marcações manuais da obra-fonte não fazem sentido no contexto da nova obra
5. BDI: se a versão-fonte **tem** BDI configurado, é copiado com as mesmas parcelas (ac, sg, r, df, lucro, iss, pis, cofins) e `historico_json` inicia com um único snapshot (timestamp = agora) refletindo o BDI copiado — o histórico pré-cópia da obra-fonte não é transferido. Se a versão-fonte **não tem** BDI configurado (nenhuma linha BDI no banco para aquele `versao_id`), a nova versão é criada igualmente sem BDI — o orçamentista deverá configurar o BDI antes de exportar documentos. Não é erro; o sistema exibe o aviso padrão de "BDI ausente"
6. CronogramaLinha: **não copiada**. A nova obra tem um cronograma em branco. Os meses da obra-fonte não correspondem necessariamente à nova obra — o orçamentista preenche o cronograma manualmente
7. Medições: **não copiadas**. Permanecem na obra-fonte

### Versionamento

1. Orçamentista acessa obra e clica em "Nova revisão"
2. Sistema cria versão N+1 com cópia completa da planilha (Grupos, Itens com snapshots de preço refrescados da Composição atual), BDI e cronograma da versão anterior. **Medições não são copiadas** — permanecem na versão de origem e são acessíveis via histórico dessa versão. Como os preços são refrescados no momento da cópia, `requer_revisao` é resetado para `false` em todos os Itens da nova versão — os preços acabaram de ser atualizados e não há alertas pendentes. `etiqueta_revisao` é **copiado verbatim** da versão anterior — marcações manuais do orçamentista são contexto relevante para a revisão em andamento.
3. Versão anterior é bloqueada automaticamente
4. Orçamentista trabalha na nova versão normalmente
5. Tela "Versões" permite comparar qualquer duas versões lado a lado (diff de itens, valores)

---

## 8. Estrutura de UI

**Navegação:** Top bar com módulos principais + barra de contexto mostrando a obra ativa.

```
[⬡ AVML] [Dashboard] [Obras] [Orçamento▼] [BDI] [Cronograma] [Medição] [Relatórios] [Base de Comp.]
──────────────────────────────────────────────────────────────────────────────────────────────────────
OBRA ATIVA: Rodovia SP-150 — Ampliação km 42 ao km 67  ·  Proc. 2024/0089    [trocar ▾]
```

**Dashboard** é o destino padrão após login. Não tem subtabs — a alternância Empresa/Obra é feita por toggle interno ao próprio painel.

**Subtabs por módulo:**

- **Orçamento:** Planilha Orçamentária | Composições | Memorial de Cálculo do BDI | Curva ABC | Versões
- **Cronograma:** Cronograma Físico-Financeiro | Curva S
- **Relatórios:** Curva ABC | Medições | Comparativo de Versões

A **Curva ABC** aparece tanto em Orçamento quanto em Relatórios — ambas as entradas rotam para o mesmo componente, escopado à versão ativa. Não há duas implementações separadas.
- **Base de Comp.:** SINAPI | SICRO | Composições Próprias | Importar Base

**Agente IA:** Acessível via botão flutuante "✦ Assistente IA" disponível em qualquer tela dentro de uma obra. Abre painel lateral com histórico de conversa e acesso ao fluxo de geração de proposta.

---

## 9. Validações de Negócio

| Validação | Comportamento |
|-----------|--------------|
| Item sem composição associada | Alerta inline na planilha (ícone de aviso na linha do item) durante edição; bloqueia geração de documentos ao exportar |
| BDI com parcelas fora dos limites TCU | Aviso não-bloqueante com link para tabela de referência |
| Cronograma com % ≠ 100% por item | Bloqueia exportação do cronograma |
| Versão bloqueada sendo editada | Erro imediato, redireciona para versão ativa |
| Importação SINAPI/SICRO com formato inválido | Erro com linha e coluna problemática |
| Medição com item_id inexistente na versão | Erro de validação na importação/save |
| BDI ausente na versão ao gerar pacote | Bloqueia geração com mensagem clara |
| Item com `requer_revisao = true` ao gerar pacote | Aviso não-bloqueante listando os itens afetados |
| CronogramaLinha órfã (item_id inexistente) | Impedido por ON DELETE CASCADE — não pode ocorrer |

---

## 10. Testes

**Testes de integração (obrigatórios):**
- Cálculo de BDI composto para todas as combinações de parcelas
- Totais da planilha com hierarquia de 3 níveis
- Fluxo financeiro mensal e Curva S do cronograma
- Geração de PDF/Excel com fixtures de obras reais de infraestrutura

**Testes unitários:**
- Ferramentas do agente IA (busca, listagem, detalhes)
- Parser de importação SINAPI e SICRO (CSV/Excel)
- Validações de negócio

**Testes manuais (antes de cada release):**
- Fluxo completo: criar obra → agente IA → revisar planilha → configurar BDI → cronograma → gerar pacote
- Upload de PDF real de edital e verificação da proposta gerada

---

## 11. Fora do Escopo (v1)

- Integração BIM
- Plugin Power BI
- App mobile (diário de obras)
- Módulo de compras / gestão de fornecedores
- Integração com ERPs externos
- Multiempresa / SaaS público
- Permissões por obra individual
- BDIs diferenciados por tipo de serviço (ex: BDI reduzido para materiais com fornecimento)

Estas funcionalidades podem compor versões futuras.
