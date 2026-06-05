# Módulo 17 — Banco de Composições Próprias: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar a página `/composicoes` para o admin gerenciar composições próprias da empresa (CRUD com preço direto), recolocando o link "Base de Comp." na TopBar.

**Architecture:** Apenas frontend — backend CRUD já existe em `/composicoes`. Três tasks independentes: (1) tipos + API, (2) modal + página, (3) rota + TopBar. Reutiliza `fmtBRL` de `@/lib/utils`, o padrão de modal de `PerfilModal` e o guard de admin de `EmpresaSettingsPage`.

**Tech Stack:** React 19 · TypeScript · Tailwind CSS · Axios (via `@/api/client`)

---

## File Map

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `frontend/src/types.ts` | Modificar | Adicionar `empresa_id` ao `Composicao` |
| `frontend/src/api/composicoes.ts` | Modificar | 4 funções CRUD (`listComposicoesProprias`, `createComposicao`, `updateComposicao`, `deleteComposicao`) |
| `frontend/src/components/composicoes/ComposicaoModal.tsx` | Criar | Modal criar/editar (4 campos) |
| `frontend/src/pages/ComposicoesPage.tsx` | Criar | Tabela + busca + exclusão inline |
| `frontend/src/app.tsx` | Modificar | Rota `/composicoes` |
| `frontend/src/components/layout/TopBar.tsx` | Modificar | Readicionar "Base de Comp." |

---

### Task 1: Tipos + API

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api/composicoes.ts`

- [ ] **Step 1: Adicionar `empresa_id` ao tipo `Composicao` em `frontend/src/types.ts`**

Localizar a interface `Composicao` (linha ~57) e adicionar o campo `empresa_id`:

```ts
export interface Composicao {
  id: number
  empresa_id: number | null   // null = SINAPI/SICRO; number = própria da empresa
  origem: string
  codigo: string
  descricao: string
  unidade: string
  preco_unitario: string
}
```

- [ ] **Step 2: Adicionar 4 funções CRUD em `frontend/src/api/composicoes.ts`**

Adicionar ao final do arquivo (após `importarComposicoes`):

```ts
export const listComposicoesProprias = (q?: string): Promise<Composicao[]> =>
  api.get<Composicao[]>('/composicoes', {
    params: { origem: 'propria', q: q || undefined, limit: 200 },
  }).then(r => r.data)

export const createComposicao = (data: {
  codigo: string
  descricao: string
  unidade: string
  preco_unitario: string
}): Promise<Composicao> =>
  api.post<Composicao>('/composicoes', data).then(r => r.data)

export const updateComposicao = (
  id: number,
  data: { codigo?: string; descricao?: string; unidade?: string; preco_unitario?: string },
): Promise<Composicao> =>
  api.patch<Composicao>(`/composicoes/${id}`, data).then(r => r.data)

export const deleteComposicao = (id: number): Promise<void> =>
  api.delete(`/composicoes/${id}`)
```

- [ ] **Step 3: Verificar TypeScript**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: sem erros

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types.ts frontend/src/api/composicoes.ts
git commit -m "feat: Composicao.empresa_id + CRUD api — listComposicoesProprias, createComposicao, updateComposicao, deleteComposicao"
```

---

### Task 2: ComposicaoModal + ComposicoesPage

**Files:**
- Create: `frontend/src/components/composicoes/ComposicaoModal.tsx`
- Create: `frontend/src/pages/ComposicoesPage.tsx`

- [ ] **Step 1: Criar `frontend/src/components/composicoes/ComposicaoModal.tsx`**

```tsx
import { useState } from 'react'
import { createComposicao, updateComposicao } from '@/api/composicoes'
import { toast } from '@/hooks/useToast'
import type { Composicao } from '@/types'

interface Props {
  composicao?: Composicao
  onClose: () => void
  onSuccess: () => void
}

export default function ComposicaoModal({ composicao, onClose, onSuccess }: Props) {
  const isEdit = !!composicao
  const [codigo, setCodigo] = useState(composicao?.codigo ?? '')
  const [descricao, setDescricao] = useState(composicao?.descricao ?? '')
  const [unidade, setUnidade] = useState(composicao?.unidade ?? '')
  const [precoUnitario, setPrecoUnitario] = useState(composicao?.preco_unitario ?? '')
  const [saving, setSaving] = useState(false)
  const [codigoError, setCodigoError] = useState('')

  const isValid =
    codigo.trim().length > 0 &&
    descricao.trim().length > 0 &&
    unidade.trim().length > 0 &&
    parseFloat(precoUnitario.replace(',', '.')) > 0

  async function handleSubmit() {
    if (!isValid) return
    setSaving(true)
    setCodigoError('')
    const data = {
      codigo: codigo.trim(),
      descricao: descricao.trim(),
      unidade: unidade.trim(),
      preco_unitario: precoUnitario.replace(',', '.'),
    }
    try {
      if (isEdit && composicao) {
        await updateComposicao(composicao.id, data)
      } else {
        await createComposicao(data)
      }
      onSuccess()
    } catch (e: any) {
      if (e?.response?.status >= 400 && e?.response?.status < 500) {
        setCodigoError('Código já cadastrado.')
      } else {
        toast('Erro ao salvar composição', 'error')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">
            {isEdit ? 'Editar composição' : 'Nova composição'}
          </h2>
          <button
            onClick={onClose}
            aria-label="Fechar"
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Código</label>
            <input
              type="text"
              value={codigo}
              onChange={e => { setCodigo(e.target.value); setCodigoError('') }}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${codigoError ? 'border-red-400' : 'border-gray-300'}`}
            />
            {codigoError && <p className="text-xs text-red-500 mt-1">{codigoError}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Descrição</label>
            <input
              type="text"
              value={descricao}
              onChange={e => setDescricao(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Unidade</label>
              <input
                type="text"
                value={unidade}
                onChange={e => setUnidade(e.target.value)}
                placeholder="m², UN, m³…"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Preço Unitário (R$)</label>
              <input
                type="number"
                min="0.01"
                step="0.01"
                value={precoUnitario}
                onChange={e => setPrecoUnitario(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        <div className="flex gap-2 justify-end pt-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={!isValid || saving}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
          >
            {saving ? 'Salvando…' : isEdit ? 'Salvar' : 'Criar'}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Criar `frontend/src/pages/ComposicoesPage.tsx`**

```tsx
import { useState, useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { listComposicoesProprias, deleteComposicao } from '@/api/composicoes'
import { toast } from '@/hooks/useToast'
import { fmtBRL } from '@/lib/utils'
import type { Composicao } from '@/types'
import ComposicaoModal from '@/components/composicoes/ComposicaoModal'

export default function ComposicoesPage() {
  const { papel } = useAuth()
  const [composicoes, setComposicoes] = useState<Composicao[]>([])
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')
  const [modal, setModal] = useState<'criar' | 'editar' | null>(null)
  const [editTarget, setEditTarget] = useState<Composicao | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (papel !== 'admin') return
    const timer = setTimeout(() => {
      setLoading(true)
      listComposicoesProprias(q || undefined)
        .then(setComposicoes)
        .catch(() => toast('Erro ao carregar composições', 'error'))
        .finally(() => setLoading(false))
    }, q ? 300 : 0)
    return () => clearTimeout(timer)
  }, [q, papel])

  if (papel === null) return <div className="p-6 text-gray-400">Carregando...</div>
  if (papel !== 'admin') return <Navigate to="/obras" replace />

  async function handleDelete(id: number) {
    setDeleting(true)
    try {
      await deleteComposicao(id)
      setConfirmDelete(null)
      listComposicoesProprias(q || undefined).then(setComposicoes)
    } catch {
      toast('Erro ao excluir composição', 'error')
    } finally {
      setDeleting(false)
    }
  }

  function handleSuccess() {
    setModal(null)
    setEditTarget(null)
    listComposicoesProprias(q || undefined).then(setComposicoes)
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-xl font-bold text-gray-900 mb-4">Banco de Composições</h1>

      <div className="flex items-center gap-3 mb-4">
        <input
          type="text"
          placeholder="Buscar por código ou descrição…"
          value={q}
          onChange={e => setQ(e.target.value)}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={() => setModal('criar')}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 shrink-0"
        >
          + Nova composição
        </button>
      </div>

      {loading ? (
        <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="px-4 py-3 flex gap-4 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-24" />
              <div className="h-4 bg-gray-200 rounded flex-1" />
              <div className="h-4 bg-gray-200 rounded w-12" />
              <div className="h-4 bg-gray-200 rounded w-20" />
            </div>
          ))}
        </div>
      ) : composicoes.length === 0 ? (
        <p className="text-sm text-gray-500">
          {q
            ? `Nenhum resultado para «${q}».`
            : 'Nenhuma composição própria cadastrada.'}
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Código
                </th>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Descrição
                </th>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Unidade
                </th>
                <th className="text-right px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Preço Unit.
                </th>
                <th className="px-4 py-2 w-28" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {composicoes.map(c => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs text-gray-700">{c.codigo}</td>
                  <td className="px-4 py-3 text-gray-900">{c.descricao}</td>
                  <td className="px-4 py-3 text-gray-500">{c.unidade}</td>
                  <td className="px-4 py-3 text-right text-gray-900">{fmtBRL(c.preco_unitario)}</td>
                  <td className="px-4 py-3">
                    {confirmDelete === c.id ? (
                      <div className="flex items-center gap-2 justify-end">
                        <button
                          onClick={() => handleDelete(c.id)}
                          disabled={deleting}
                          className="text-xs text-white bg-red-600 hover:bg-red-700 px-2 py-1 rounded disabled:opacity-40"
                        >
                          Confirmar
                        </button>
                        <button
                          onClick={() => setConfirmDelete(null)}
                          className="text-xs text-gray-500 hover:text-gray-700"
                        >
                          Cancelar
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 justify-end">
                        <button
                          onClick={() => { setEditTarget(c); setModal('editar') }}
                          aria-label="Editar"
                          className="text-gray-400 hover:text-blue-600 p-1 text-base leading-none"
                        >
                          ✎
                        </button>
                        <button
                          onClick={() => setConfirmDelete(c.id)}
                          aria-label="Excluir"
                          className="text-gray-400 hover:text-red-600 p-1"
                        >
                          🗑
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modal === 'criar' && (
        <ComposicaoModal onClose={() => setModal(null)} onSuccess={handleSuccess} />
      )}
      {modal === 'editar' && editTarget && (
        <ComposicaoModal
          composicao={editTarget}
          onClose={() => { setModal(null); setEditTarget(null) }}
          onSuccess={handleSuccess}
        />
      )}
    </div>
  )
}
```

- [ ] **Step 3: Verificar TypeScript**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: sem erros

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/composicoes/ComposicaoModal.tsx \
        frontend/src/pages/ComposicoesPage.tsx
git commit -m "feat: ComposicaoModal + ComposicoesPage — CRUD de composições próprias"
```

---

### Task 3: Rota + TopBar

**Files:**
- Modify: `frontend/src/app.tsx`
- Modify: `frontend/src/components/layout/TopBar.tsx`

- [ ] **Step 1: Registrar rota em `frontend/src/app.tsx`**

Adicionar import:
```tsx
import ComposicoesPage from '@/pages/ComposicoesPage'
```

Adicionar rota (após `/configuracoes`):
```tsx
<Route path="/composicoes" element={<ComposicoesPage />} />
```

- [ ] **Step 2: Readicionar "Base de Comp." em `frontend/src/components/layout/TopBar.tsx`**

Substituir o array `NAV_ITEMS` por:

```ts
const NAV_ITEMS = [
  { label: 'Dashboard', to: '/' },
  { label: 'Obras', to: '/obras' },
  { label: 'Base de Comp.', to: '/composicoes' },
  { label: 'Relatórios', to: '/relatorios' },
]
```

- [ ] **Step 3: Verificar TypeScript**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: sem erros

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app.tsx \
        frontend/src/components/layout/TopBar.tsx
git commit -m "feat: rota /composicoes + link Base de Comp. na TopBar — Módulo 17 completo"
```
