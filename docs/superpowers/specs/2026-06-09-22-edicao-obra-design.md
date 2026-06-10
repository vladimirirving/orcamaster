# Módulo 22 — Edição de Obra: Design Spec

**Data:** 2026-06-09
**Status:** Aprovado para implementação

---

## 1. Objetivo

Expor os campos `numero_processo`, `uf`, `municipio`, `data_prazo`, `responsavel_id` e `estado` no frontend — tanto na criação quanto na edição de obras. O backend (`PATCH /obras/{id}` com `ObraUpdate`) já aceita todos esses campos; o trabalho é 100% frontend.

---

## 2. O que muda

### 2.1 `types.ts`

Adicionar campos ausentes à interface `Obra`:

```typescript
numero_processo: string | null
data_prazo: string | null         // ISO date "YYYY-MM-DD"
responsavel_id: number | null
```

### 2.2 `api/obras.ts`

Estender `updateObra` para aceitar todos os campos editáveis do `ObraUpdate`:

```typescript
updateObra(id, {
  nome?, tipo_obra?, numero_processo?, uf?, municipio?,
  data_prazo?, responsavel_id?, estado?, cliente_id?
})
```

### 2.3 Nova Obra (`ObrasPage.tsx`)

Adicionar campos opcionais ao formulário de criação (além de nome, tipo, cliente):
- Número do processo (text, opcional)
- UF (select dos 27 estados brasileiros, opcional)
- Município (text, opcional)

`data_prazo` e `responsavel_id` ficam fora da criação — são preenchidos após criação via edição.

### 2.4 `ObraEditModal.tsx` (novo componente)

Modal em `frontend/src/components/obra/ObraEditModal.tsx` com todos os campos editáveis:
- Nome * (obrigatório)
- Tipo obra (select)
- Estado (select: em elaboração / concluído / arquivado)
- Número do processo
- UF + Município
- Data prazo (date input)
- Responsável (dropdown de usuários via `listUsuarios()`)

Segue o padrão do projeto: Radix UI Dialog, Tailwind, sem libs externas novas.

### 2.5 `ObraDetailPage.tsx`

Botão "Editar" no header (ao lado do botão "Diário" existente) que abre `ObraEditModal`. Após salvar: atualiza o estado local da obra sem recarregar a página.

---

## 3. Backend

Nenhuma alteração. `PATCH /obras/{id}` já usa `ObraUpdate.model_dump(exclude_none=True)` e `ObraOut` já retorna todos os campos.

---

## 4. UF brasileiras

O select de UF usa a lista estática dos 26 estados + DF:
`AC, AL, AP, AM, BA, CE, DF, ES, GO, MA, MT, MS, MG, PA, PB, PR, PE, PI, RJ, RN, RS, RO, RR, SC, SP, SE, TO`

---

## 5. Testes

Sem testes novos no backend. TypeCheck frontend + verificação visual no browser é suficiente.

---

## 6. Fora do Escopo

- Campos de Nova Obra: `data_prazo` e `responsavel_id` (adicionados só na edição)
- Validação de UF no backend (já aceita qualquer string, limite 2 chars)
- Filtro por estado na listagem de obras (futuro)
