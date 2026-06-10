# Módulo 13 — Importação de Planilha Excel: Design Spec

**Data:** 2026-06-03
**Status:** Aprovado

---

## 1. Objetivo

Permitir que o orçamentista importe a estrutura de grupos/subgrupos/itens de uma planilha `.xlsx` para a versão ativa de uma obra, com template fixo fornecido pelo sistema.

---

## 2. Escopo

**Inclui:**
- Endpoint para download do template XLSX
- Endpoint para upload e processamento do arquivo preenchido
- Serviço que cria Grupo + Subgrupo (se houver) + Item para cada linha
- Itens sem composição encontrada: criados com `requer_revisao=True`
- Botão "Importar Excel" em `PlanilhaPage` (apenas quando versão não está bloqueada)
- Modal com link de download do template + upload + resultado

**Fora do escopo:**
- Preview de linhas antes de confirmar
- Histórico de importações
- Suporte a outros formatos (CSV, ODS)
- Substituição dos grupos existentes (sempre anexa ao final)

---

## 3. Template XLSX

Colunas A–F, linha 1 = cabeçalho, linha 2 = exemplo (fundo cinza, fonte itálica):

| A: grupo | B: subgrupo | C: codigo_composicao | D: descricao | E: unidade | F: quantidade |
|---|---|---|---|---|---|
| *Terraplenagem* | | *94966* | *Escavação mecânica* | *M3* | *12000* |

- **grupo** (obrigatório) — nome do grupo raiz
- **subgrupo** (opcional) — se preenchido, cria/reutiliza subgrupo dentro do grupo
- **codigo_composicao** (opcional) — código buscado no banco; prioridade sobre `descricao`
- **descricao** (opcional) — usado quando `codigo_composicao` não encontrado
- **unidade** (obrigatório) — ex: M3, M2, M, UN, VB
- **quantidade** (obrigatório) — valor numérico

---

## 4. Backend

### 4.1 Arquivos

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `backend/app/schemas/planilha_import.py` | Criar | `ImportarPlanilhaResult` schema |
| `backend/app/services/importar_planilha_service.py` | Criar | `gerar_template_bytes()` + `importar_planilha()` |
| `backend/app/routers/planilha_import.py` | Criar | 2 endpoints REST |
| `backend/app/main.py` | Modificar | Registrar `planilha_import.router` |
| `tests/backend/test_planilha_import.py` | Criar | 3 testes |

### 4.2 Serviço (`importar_planilha_service.py`)

**`gerar_template_bytes() -> bytes`**

```python
def gerar_template_bytes() -> bytes:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Planilha"
    headers = ["grupo", "subgrupo", "codigo_composicao", "descricao", "unidade", "quantidade"]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="DDDDDD")
    ws.append(["Terraplenagem", "", "94966", "Escavação mecânica de vala", "M3", 12000])
    for cell in ws[2]:
        cell.font = Font(italic=True, color="888888")
        cell.fill = PatternFill("solid", fgColor="F5F5F5")
    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 18
    ws.column_dimensions["C"].width = 20
    ws.column_dimensions["D"].width = 35
    ws.column_dimensions["E"].width = 8
    ws.column_dimensions["F"].width = 12
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
```

**`importar_planilha(versao_id, empresa_id, conteudo, db) -> dict`**

Fluxo:
1. Lê XLSX com openpyxl (read_only, data_only). Linha 1 = cabeçalho (ignorada se não começa com "grupo"). Ignora linhas onde `grupo` está vazio.
2. Calcula `next_grupo_ordem = MAX(ordem dos grupos existentes da versão) + 1` (0 se vazio).
3. Mantém dicionário `grupo_cache: dict[str, Grupo]` e `subgrupo_cache: dict[tuple, Grupo]` para não criar duplicatas.
4. Para cada linha:
   - Cria ou reutiliza grupo raiz por nome.
   - Se `subgrupo` preenchido: cria ou reutiliza subgrupo `(grupo_id, nome_subgrupo)`.
   - Para o item: busca `codigo_composicao` no banco (`empresa_id IS NULL OR empresa_id = empresa_id`). Se encontrado: usa `composicao.preco_unitario` como `preco_unitario_sem_bdi`. Se não encontrado ou código vazio: `composicao_id=None`, `requer_revisao=True`, `preco_unitario_sem_bdi=None`.
   - Cria `Item(grupo_id=grupo_pai_id, composicao_id=..., quantidade=..., unidade=..., preco_unitario_sem_bdi=..., ordem=j, requer_revisao=...)`.
5. `await db.flush()` → `await recalc_totais_versao(versao_id, db)` → `await db.commit()`.
6. Retorna `{"grupos_criados": int, "itens_criados": int, "itens_sem_composicao": int}`.

**Parsing XLSX:** mesma abordagem do `_parse_xlsx` do composicao_service: `iter_rows(values_only=True)`, row 0 = header, todas as células → `str(val).strip() if val is not None else ""`.

### 4.3 Router (`planilha_import.py`)

```python
@router.get("/versoes/{versao_id}/planilha/template")
async def download_template(
    versao_id: int,
    current_user: Usuario = Depends(get_current_user),
):
    content = gerar_template_bytes()
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="template-planilha-v{versao_id}.xlsx"'},
    )


@router.post("/versoes/{versao_id}/planilha/importar", response_model=ImportarPlanilhaResult)
async def importar(
    versao_id: int,
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_versao_ativa(versao_id, current_user, db)
    conteudo = await file.read()
    return await importar_planilha(versao_id, current_user.empresa_id, conteudo, db)
```

**Schema `ImportarPlanilhaResult`** (em `app/schemas/planilha_import.py`):
```python
class ImportarPlanilhaResult(BaseModel):
    grupos_criados: int
    itens_criados: int
    itens_sem_composicao: int
```

### 4.4 Testes (`tests/backend/test_planilha_import.py`)

| Teste | Descrição |
|-------|-----------|
| `test_importar_planilha_ok` | XLSX com 2 grupos, 3 itens, todos com `codigo_composicao` válido → `grupos_criados=2`, `itens_criados=3`, `itens_sem_composicao=0`, `total_sem_bdi > 0` |
| `test_importar_sem_composicao` | 1 item com código inexistente → `itens_sem_composicao=1`, item criado com `requer_revisao=True` |
| `test_importar_versao_bloqueada` | Versão bloqueada → 409 |

---

## 5. Frontend

### 5.1 Arquivos

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `frontend/src/api/planilhaImport.ts` | Criar | `downloadTemplate`, `importarPlanilha` |
| `frontend/src/components/planilha/ImportarPlanilhaModal.tsx` | Criar | Modal com 3 estados: form / importando / resultado |
| `frontend/src/pages/PlanilhaPage.tsx` | Modificar | +botão "Importar Excel" + estado do modal |

### 5.2 API (`api/planilhaImport.ts`)

```ts
export async function downloadTemplate(versaoId: number): Promise<void> {
  const resp = await api.get<Blob>(`/versoes/${versaoId}/planilha/template`, {
    responseType: 'blob',
  })
  const url = URL.createObjectURL(resp.data)
  const a = document.createElement('a')
  a.href = url
  a.download = `template-planilha-v${versaoId}.xlsx`
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 100)
}

export const importarPlanilha = (
  versaoId: number,
  file: File,
): Promise<{ grupos_criados: number; itens_criados: number; itens_sem_composicao: number }> => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/versoes/${versaoId}/planilha/importar`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}
```

### 5.3 Modal (`ImportarPlanilhaModal.tsx`)

Props: `{ versaoId: number; onClose: () => void; onSuccess: () => void }`

3 fases:
1. **Form** — link "Baixar template" (chama `downloadTemplate`) + file input (`.xlsx`) + botão "Importar"
2. **Importando** — spinner
3. **Resultado** — `"X grupos criados, Y itens importados"` + aviso amarelo se `itens_sem_composicao > 0` ("Z itens sem composição vinculada — verifique os itens marcados para revisão") + botão "Fechar" (chama `onSuccess`)

### 5.4 PlanilhaPage

- Adicionar `importModalOpen: boolean` ao estado
- No toolbar, após o botão BDI, adicionar (apenas quando `!isReadOnly`):
  ```tsx
  <button onClick={() => setImportModalOpen(true)}
    className="text-sm text-gray-600 hover:text-blue-600 border border-gray-200 px-3 py-1 rounded-lg">
    ↑ Importar Excel
  </button>
  ```
- Renderizar `<ImportarPlanilhaModal>` quando `importModalOpen === true`
- `onSuccess`: chama `getGrupos(numVersaoId).then(setGrupos)` + fecha modal

---

## 6. Notas de implementação

- **Deduplicação de grupos:** dentro do lote importado, linhas com o mesmo nome de `grupo` vão para o mesmo `Grupo` (cache em memória durante a importação). **Não** mescla com grupos preexistentes da versão — sempre cria grupos novos no final.
- **Deduplicação de subgrupos:** mesma lógica para `(grupo_id, nome_subgrupo)`
- **Exemplo row no template:** linha 2 com fundo cinza/itálico é detectada e ignorada pelo parser se o campo `grupo` não for vazio mas igual a "Terraplenagem" — na prática, o parser não tem lógica especial: a linha de exemplo pode simplesmente ser importada se o usuário não a apagar. Isso é aceitável (vira um grupo "Terraplenagem" com 1 item de exemplo que o usuário pode deletar)
