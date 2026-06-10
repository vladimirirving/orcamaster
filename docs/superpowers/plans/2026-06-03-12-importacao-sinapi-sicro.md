# Módulo 12 — Importação SINAPI/SICRO: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar suporte a XLSX no serviço de importação e uma UI admin para upload de arquivos SINAPI/SICRO em `EmpresaSettingsPage`.

**Architecture:** Backend: `import_composicoes_csv` é renomeado para `import_composicoes` com parâmetro `filename` para detecção de formato; `_parse_xlsx` usa openpyxl. Frontend: nova função `importarComposicoes` via FormData + seção "Banco de Composições" em `EmpresaSettingsPage`.

**Tech Stack:** FastAPI · openpyxl (já instalado) · React 19 · TypeScript · Tailwind CSS

---

## File Map

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `backend/app/services/composicao_service.py` | Modificar | Renomear função + adicionar `_parse_xlsx` + extrair `_parse_csv` |
| `backend/app/routers/composicoes.py` | Modificar | Passar `filename` ao serviço; atualizar import |
| `tests/backend/test_composicoes.py` | Modificar | +1 teste XLSX |
| `frontend/src/api/composicoes.ts` | Modificar | +`importarComposicoes` |
| `frontend/src/pages/EmpresaSettingsPage.tsx` | Modificar | +seção de importação |

---

### Task 1: Backend XLSX support + teste

**Files:**
- Modify: `backend/app/services/composicao_service.py`
- Modify: `backend/app/routers/composicoes.py`
- Modify: `tests/backend/test_composicoes.py`

- [ ] **Step 1: Escrever o teste XLSX ao final de tests/backend/test_composicoes.py**

```python

@pytest.mark.asyncio
async def test_import_sinapi_xlsx(
    client: AsyncClient, auth_headers: dict, db_session: AsyncSession
):
    from io import BytesIO
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["codigo", "descricao", "unidade", "preco_unitario"])
    ws.append(["X001", "SERVICO XLSX TESTE", "UN", 99.50])
    ws.append(["X002", "OUTRO SERVICO XLSX", "M3", 12.00])
    buf = BytesIO()
    wb.save(buf)

    resp = await client.post(
        "/composicoes/importar",
        data={"origem": "sinapi"},
        files={"file": (
            "sinapi.xlsx",
            buf.getvalue(),
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["criadas"] == 2
    assert data["atualizadas"] == 0
    assert data["itens_marcados"] == 0

    result = await db_session.execute(
        select(Composicao).where(Composicao.codigo == "X001", Composicao.origem == "sinapi")
    )
    comp = result.scalar_one_or_none()
    assert comp is not None
    assert comp.descricao == "SERVICO XLSX TESTE"
```

- [ ] **Step 2: Confirmar que o teste falha (XLSX não suportado)**

```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH" && docker compose exec backend pytest tests/backend/test_composicoes.py::test_import_sinapi_xlsx -v
```

Expected: FAIL (CSV parser não consegue ler bytes XLSX)

- [ ] **Step 3: Substituir o conteúdo completo de backend/app/services/composicao_service.py**

```python
import csv
import io
from datetime import date
from decimal import Decimal
from typing import Optional

import openpyxl
from sqlalchemy import Numeric, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.composicao import Composicao
from app.models.insumo import Insumo
from app.models.item import Item

_ZERO = Decimal("0")
_NUM = Numeric(15, 6)


async def recalc_preco_composicao(composicao_id: int, db: AsyncSession) -> None:
    """Recalculate composicao.preco_unitario = SUM(coeficiente * preco_unitario) over its insumos.
    If price changed, bulk-marks items using this composicao with requer_revisao=True.
    Callers must db.flush() before (so in-flight insumo changes are visible).
    Callers must db.commit() after.
    """
    r = await db.execute(
        select(
            func.coalesce(
                func.sum(Insumo.coeficiente * Insumo.preco_unitario), _ZERO
            ).cast(_NUM)
        ).where(Insumo.composicao_id == composicao_id)
    )
    novo_preco = Decimal(str(r.scalar() or _ZERO))

    r2 = await db.execute(
        select(Composicao.preco_unitario).where(Composicao.id == composicao_id)
    )
    preco_atual = Decimal(str(r2.scalar() or _ZERO))

    await db.execute(
        update(Composicao)
        .where(Composicao.id == composicao_id)
        .values(preco_unitario=novo_preco)
        .execution_options(synchronize_session=False)
    )

    if novo_preco != preco_atual:
        await db.execute(
            update(Item)
            .where(Item.composicao_id == composicao_id)
            .values(requer_revisao=True)
            .execution_options(synchronize_session=False)
        )


def _parse_csv(conteudo: bytes) -> list[dict]:
    text = conteudo.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return [
        {k.strip().lower(): v.strip() for k, v in row.items()}
        for row in reader
    ]


def _parse_xlsx(conteudo: bytes) -> list[dict]:
    wb = openpyxl.load_workbook(io.BytesIO(conteudo), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    if not rows:
        return []
    header = [str(h).strip().lower() if h is not None else "" for h in rows[0]]
    result = []
    for row in rows[1:]:
        d = {key: (str(val).strip() if val is not None else "") for key, val in zip(header, row)}
        if d.get("codigo", ""):
            result.append(d)
    return result


async def import_composicoes(
    origem: str,
    conteudo: bytes,
    filename: str,
    db: AsyncSession,
) -> dict:
    """Upsert composições from CSV or XLSX by (origem, codigo).
    After upserting, bulk-marks items with requer_revisao=True where preco_unitario changed.
    Returns {"criadas": int, "atualizadas": int, "itens_marcados": int}.

    CSV format (UTF-8, BOM-tolerant) or XLSX first sheet:
        codigo, descricao, unidade, preco_unitario[, data_referencia]
    Decimal separator in CSV: dot or comma.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "csv"
    rows = _parse_xlsx(conteudo) if ext in ("xlsx", "xls") else _parse_csv(conteudo)

    result = await db.execute(
        select(Composicao).where(
            Composicao.origem == origem, Composicao.empresa_id.is_(None)
        )
    )
    existing: dict[str, Composicao] = {c.codigo: c for c in result.scalars().all()}

    criadas = 0
    atualizadas = 0
    changed_ids: list[int] = []

    for row in rows:
        codigo = row.get("codigo", "").strip()
        if not codigo:
            continue
        descricao = row.get("descricao", "").strip()
        unidade = row.get("unidade", "").strip()
        preco_raw = row.get("preco_unitario", "0").strip().replace(",", ".")
        novo_preco = Decimal(preco_raw) if preco_raw else _ZERO
        data_ref: Optional[date] = None
        raw_data = row.get("data_referencia", "").strip()
        if raw_data:
            data_ref = date.fromisoformat(raw_data)

        if codigo in existing:
            comp = existing[codigo]
            if Decimal(str(comp.preco_unitario)) != novo_preco:
                comp.preco_unitario = novo_preco
                if comp.id is not None:
                    changed_ids.append(comp.id)
            comp.descricao = descricao
            comp.unidade = unidade
            if data_ref:
                comp.data_referencia = data_ref
            atualizadas += 1
        else:
            nova = Composicao(
                empresa_id=None,
                origem=origem,
                codigo=codigo,
                descricao=descricao,
                unidade=unidade,
                preco_unitario=novo_preco,
                data_referencia=data_ref,
            )
            db.add(nova)
            existing[codigo] = nova
            criadas += 1

    await db.flush()

    itens_marcados = 0
    if changed_ids:
        r = await db.execute(
            update(Item)
            .where(Item.composicao_id.in_(changed_ids))
            .values(requer_revisao=True)
            .execution_options(synchronize_session=False)
        )
        itens_marcados = r.rowcount

    await db.commit()
    return {"criadas": criadas, "atualizadas": atualizadas, "itens_marcados": itens_marcados}
```

- [ ] **Step 4: Atualizar backend/app/routers/composicoes.py**

Localizar o endpoint `importar_composicoes` e substituir as 3 linhas internas:

```python
    from app.services.composicao_service import import_composicoes_csv
    conteudo = await file.read()
    return await import_composicoes_csv(origem=origem, conteudo=conteudo, db=db)
```

Por:

```python
    from app.services.composicao_service import import_composicoes
    conteudo = await file.read()
    filename = file.filename or "upload.csv"
    return await import_composicoes(origem=origem, conteudo=conteudo, filename=filename, db=db)
```

- [ ] **Step 5: Confirmar que todos os testes de composicoes passam**

```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH" && docker compose exec backend pytest tests/backend/test_composicoes.py -v
```

Expected: todos PASSED (incluindo `test_import_sinapi_xlsx`)

- [ ] **Step 6: Confirmar que a suíte completa passa**

```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH" && docker compose exec backend pytest tests/backend/ -v 2>&1 | tail -10
```

Expected: sem novas falhas

- [ ] **Step 7: Commit**

```bash
git add backend/app/services/composicao_service.py \
        backend/app/routers/composicoes.py \
        tests/backend/test_composicoes.py
git commit -m "feat: importação SINAPI/SICRO suporta XLSX além de CSV"
```

---

### Task 2: Frontend — API + seção de importação

**Files:**
- Modify: `frontend/src/api/composicoes.ts`
- Modify: `frontend/src/pages/EmpresaSettingsPage.tsx`

- [ ] **Step 1: Adicionar importarComposicoes em frontend/src/api/composicoes.ts**

Acrescentar ao final do arquivo:

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

- [ ] **Step 2: Atualizar frontend/src/pages/EmpresaSettingsPage.tsx**

**2a.** Adicionar import de `importarComposicoes` no topo:
```ts
import { importarComposicoes } from '@/api/composicoes'
```

**2b.** Adicionar 4 novos estados após os estados existentes (antes de `useEffect`):
```ts
  const [importOrigem, setImportOrigem] = useState<'sinapi' | 'sicro'>('sinapi')
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState<{ criadas: number; atualizadas: number; itens_marcados: number } | null>(null)
```

**2c.** Adicionar handler `handleImportar` após `handleSave`:
```ts
  async function handleImportar() {
    if (!importFile) return
    setImporting(true)
    setImportResult(null)
    try {
      const result = await importarComposicoes(importOrigem, importFile)
      setImportResult(result)
      setImportFile(null)
    } catch {
      toast('Erro ao importar composições', 'error')
    } finally {
      setImporting(false)
    }
  }
```

**2d.** Adicionar seção de importação no JSX, após o `</div>` que fecha o card de configurações (antes do `</div>` final):

```tsx
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4 mt-6">
        <h2 className="text-sm font-semibold text-gray-800">Banco de Composições</h2>
        <p className="text-xs text-gray-500">
          Importe a tabela mensal do SINAPI (CEF) ou SICRO (DNIT). Aceita CSV ou XLSX.
        </p>

        <div className="flex gap-4">
          {(['sinapi', 'sicro'] as const).map(o => (
            <label key={o} className="flex items-center gap-2 cursor-pointer text-sm">
              <input
                type="radio"
                name="importOrigem"
                value={o}
                checked={importOrigem === o}
                onChange={() => setImportOrigem(o)}
                className="accent-blue-600"
              />
              {o.toUpperCase()}
            </label>
          ))}
        </div>

        <div className="flex gap-3 items-center">
          <label className="flex-1">
            <span className="sr-only">Arquivo</span>
            <input
              type="file"
              accept=".csv,.xlsx"
              onChange={e => {
                setImportFile(e.target.files?.[0] ?? null)
                setImportResult(null)
              }}
              className="block w-full text-sm text-gray-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
            />
          </label>
          <button
            onClick={handleImportar}
            disabled={!importFile || importing}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40 shrink-0"
          >
            {importing ? 'Importando…' : 'Importar'}
          </button>
        </div>

        {importResult && (
          <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-sm text-green-800">
            ✓ {importResult.criadas} composições criadas,{' '}
            {importResult.atualizadas} atualizadas
            {importResult.itens_marcados > 0 && (
              <span className="text-yellow-700">
                {' '}— {importResult.itens_marcados} itens marcados para revisão
              </span>
            )}
          </div>
        )}
      </div>
```

- [ ] **Step 3: Confirmar que TypeScript compila**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: sem erros

- [ ] **Step 4: Commit**

```bash
git add frontend/src/api/composicoes.ts frontend/src/pages/EmpresaSettingsPage.tsx
git commit -m "feat: UI de importação SINAPI/SICRO em /configuracoes — Módulo 12 completo"
```
