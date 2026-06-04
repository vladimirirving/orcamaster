# Módulo 12 — Importação SINAPI/SICRO: Design Spec

**Data:** 2026-06-03
**Status:** Aprovado

---

## 1. Objetivo

Permitir que administradores façam upload do arquivo mensal SINAPI (CEF) ou SICRO (DNIT) — em CSV ou XLSX — pela interface web, atualizando o banco de composições sem acesso direto à API.

---

## 2. Escopo

**Inclui:**
- Suporte a `.xlsx` no serviço de importação (além do CSV já existente)
- Seção "Banco de Composições" em `EmpresaSettingsPage` com seletor SINAPI/SICRO, input de arquivo e feedback de resultado
- 1 novo teste backend para o path XLSX

**Fora do escopo:**
- Preview de linhas antes de confirmar importação
- Histórico de importações
- Validação detalhada por linha com relatório de erros

---

## 3. Backend

### 3.1 Arquivos

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `backend/app/services/composicao_service.py` | Modificar | Renomear `import_composicoes_csv` → `import_composicoes`; adicionar parsing XLSX |
| `backend/app/routers/composicoes.py` | Modificar | Passar `filename` ao serviço; atualizar import name |
| `tests/backend/test_composicoes.py` | Modificar | +1 teste XLSX |

### 3.2 Serviço (`composicao_service.py`)

Renomear `import_composicoes_csv` para `import_composicoes` e adicionar parâmetro `filename: str`.

Detecção de formato:
```python
ext = filename.rsplit(".", 1)[-1].lower()
if ext in ("xlsx", "xls"):
    rows = _parse_xlsx(conteudo)
else:
    rows = _parse_csv(conteudo)
```

**`_parse_csv(conteudo: bytes) -> list[dict]`** — lógica existente extraída para função separada.

**`_parse_xlsx(conteudo: bytes) -> list[dict]`** — usa `openpyxl.load_workbook(BytesIO(conteudo), read_only=True, data_only=True)`. Lê a primeira sheet. Linha 1 é cabeçalho; linhas seguintes são dados. Colunas aceitas (case-insensitive): `codigo, descricao, unidade, preco_unitario[, data_referencia]`. Retorna lista de dicts no mesmo formato que o CSV parser.

A lógica de upsert (que já existe) permanece igual — recebe `list[dict]` e não sabe de onde veio.

### 3.3 Router (`composicoes.py`)

```python
from app.services.composicao_service import import_composicoes

@router.post("/importar", response_model=ImportResultOut)
async def importar_composicoes(...):
    conteudo = await file.read()
    filename = file.filename or "upload.csv"
    return await import_composicoes(origem=origem, conteudo=conteudo, filename=filename, db=db)
```

### 3.4 Novo teste

```python
@pytest.mark.asyncio
async def test_import_sinapi_xlsx(client, auth_headers, db_session):
    # Gerar XLSX em memória com openpyxl
    from io import BytesIO
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["codigo", "descricao", "unidade", "preco_unitario"])
    ws.append(["X001", "SERVICO XLSX TESTE", "UN", 99.50])
    ws.append(["X002", "OUTRO SERVICO", "M3", 12.00])
    buf = BytesIO()
    wb.save(buf)

    resp = await client.post(
        "/composicoes/importar",
        data={"origem": "sinapi"},
        files={"file": ("sinapi.xlsx", buf.getvalue(),
               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["criadas"] == 2
    assert data["atualizadas"] == 0
```

---

## 4. Frontend

### 4.1 Arquivos

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `frontend/src/api/composicoes.ts` | Modificar | +`importarComposicoes(origem, file)` |
| `frontend/src/pages/EmpresaSettingsPage.tsx` | Modificar | +seção "Banco de Composições" |

### 4.2 API (`api/composicoes.ts`)

```ts
export async function importarComposicoes(
  origem: 'sinapi' | 'sicro',
  file: File,
): Promise<{ criadas: number; atualizadas: number; itens_marcados: number }> {
  const form = new FormData()
  form.append('origem', origem)
  form.append('file', file)
  return api.post('/composicoes/importar', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}
```

### 4.3 `EmpresaSettingsPage.tsx` — seção de importação

Nova seção abaixo do card de configurações existente:

```
┌─────────────────────────────────────────────────────┐
│ Banco de Composições                                  │
│                                                       │
│ Origem:  ○ SINAPI   ○ SICRO                          │
│                                                       │
│ Arquivo: [  sinapi-06-2026.xlsx  ] [Importar]        │
│                                                       │
│ ✓ 1.842 composições criadas, 234 atualizadas,        │
│   47 itens marcados para revisão                     │
└─────────────────────────────────────────────────────┘
```

Estados do botão "Importar":
- Desabilitado se nenhum arquivo selecionado
- `"Importando…"` com spinner durante o upload
- Resultado exibido inline após sucesso
- Toast de erro em caso de falha

Aceita `.csv, .xlsx`. Só visível para admins (já existe guard `papel === 'admin'` na página).

---

## 5. Testes Frontend

Manual apenas:
- Selecionar SINAPI + upload de .csv → ver contagens corretas
- Selecionar SICRO + upload de .xlsx → ver contagens corretas
- Arquivo inválido (ex: .pdf) → o browser bloqueia pelo `accept`
