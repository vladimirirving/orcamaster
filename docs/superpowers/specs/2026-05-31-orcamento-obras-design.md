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
| Backend | Python + FastAPI |
| Banco de dados | PostgreSQL |
| Agente IA | Claude API (claude-sonnet-4-6) com tool use |
| PDF | WeasyPrint |
| Excel | openpyxl |
| Auth | JWT com refresh token |
| Infraestrutura | Docker Compose (on-premise ou VPS) |

Arquitetura monolítica — frontend e backend no mesmo repositório, deploy via Docker Compose. Sem dependências de serviços pagos obrigatórios.

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

Todas as demais entidades (planilha, BDI, cronograma, medições) são filhas de uma Obra.

### 3.2 Banco de Composições

Repositório unificado com três origens:

- **SINAPI** — importado da CEF (CSV/Excel mensal). Referência para edificações e serviços gerais.
- **SICRO** — importado do DNIT (CSV/Excel). Referência obrigatória para obras rodoviárias e infraestrutura.
- **Próprias** — criadas pela equipe. Podem partir de zero ou derivar de uma composição SINAPI/SICRO editada.

Cada composição contém: código, descrição, unidade, lista de insumos (mão de obra, material, equipamento) com coeficientes e preço unitário calculado.

### 3.3 Editor de Planilha Orçamentária

Coração do sistema. Estrutura hierárquica: **Grupo → Subgrupo → Item**.

Funcionalidades:
- Busca de composições por código ou descrição (SINAPI, SICRO ou próprias)
- Entrada de quantidades; preço unitário sempre calculado a partir da composição
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

Calcula BDI composto pela fórmula padrão TCU. Gera memorial de cálculo automaticamente. Exibe aviso se parcelas estiverem fora dos limites referenciais do TCU (sem bloquear).

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

Registro do avanço físico real contra o planejado. Por período de medição, o orçamentista registra o percentual executado por item.

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
bloqueada (bool), total_sem_bdi, total_com_bdi
```

**Grupo / Subgrupo**
```
id, versao_id, pai_id (null para grupos raiz), ordem, nome, codigo
```

**Item**
```
id, grupo_id, ordem, composicao_id, quantidade, unidade,
preco_unitario_sem_bdi (calculado), preco_unitario_com_bdi (calculado),
total (calculado), etiqueta_revisao (bool)
```

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
id, versao_id, ac, sg, r, df, lucro, iss, pis, cofins,
bdi_composto (calculado), memorial_json
```

**CronogramaLinha**
```
id, versao_id, item_id, distribuicao_json ({mes: percentual}),
total_percentual (deve = 100)
```

**Medicao**
```
id, obra_id, periodo_inicio, periodo_fim, criada_por,
linhas_json ({item_id: percentual_executado})
```

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
5. Sistema atualiza o banco; composições próprias derivadas de itens alterados recebem flag `requer_revisao`
6. Notificação enviada para Orçamentistas sobre itens que precisam de revisão

### Geração do Pacote de Licitação

1. Orçamentista acessa a versão ativa da obra
2. Verifica alertas de validação (itens sem composição, BDI não configurado, cronograma incompleto)
3. Clica em "Gerar pacote de licitação"
4. Sistema processa em background (tarefa assíncrona)
5. Notificação quando o zip estiver pronto para download
6. Arquivo fica disponível por 7 dias; pode ser regerado a qualquer momento

### Versionamento

1. Orçamentista acessa obra e clica em "Nova revisão"
2. Sistema cria versão N+1 com cópia completa da planilha, BDI e cronograma da versão anterior
3. Versão anterior é bloqueada automaticamente
4. Orçamentista trabalha na nova versão normalmente
5. Tela "Versões" permite comparar qualquer duas versões lado a lado (diff de itens, valores)

---

## 8. Estrutura de UI

**Navegação:** Top bar com módulos principais + barra de contexto mostrando a obra ativa.

```
[⬡ AVML] [Obras] [Orçamento▼] [BDI] [Cronograma] [Medição] [Relatórios] [Base de Comp.]
─────────────────────────────────────────────────────────────────────────────────────────
OBRA ATIVA: Rodovia SP-150 — Ampliação km 42 ao km 67  ·  Proc. 2024/0089    [trocar ▾]
```

**Subtabs por módulo:**

- **Orçamento:** Planilha Orçamentária | Composições | Memória de Cálculo | Curva ABC | Versões
- **Cronograma:** Cronograma Físico-Financeiro | Curva S
- **Relatórios:** Curva ABC | Medições | Comparativo de Versões
- **Base de Comp.:** SINAPI | SICRO | Composições Próprias | Importar Base

**Agente IA:** Acessível via botão flutuante "✦ Assistente IA" disponível em qualquer tela dentro de uma obra. Abre painel lateral com histórico de conversa e acesso ao fluxo de geração de proposta.

---

## 9. Validações de Negócio

| Validação | Comportamento |
|-----------|--------------|
| Item sem composição associada | Bloqueia geração de documentos |
| BDI com parcelas fora dos limites TCU | Aviso não-bloqueante com link para tabela de referência |
| Cronograma com % ≠ 100% por item | Bloqueia exportação do cronograma |
| Versão bloqueada sendo editada | Erro imediato, redireciona para versão ativa |
| Importação SINAPI/SICRO com formato inválido | Erro com linha e coluna problemática |

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
