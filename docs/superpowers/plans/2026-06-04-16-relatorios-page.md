# Módulo 16 — Página de Relatórios: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Criar a página `/relatorios` que lista todas as obras com versão ativa e seus downloads disponíveis (PDF Proposta + XLSX Curva ABC), e limpar os 5 links mortos da TopBar.

**Architecture:** Apenas frontend — reutiliza `getObras`/`getVersoes` de `@/api/obras`, `downloadPropostaPdf` de `@/api/proposta` e `downloadCurvaAbcExcel` de `@/api/curvaAbc`. Nenhum endpoint novo no backend. A RelatoriosPage carrega obras e versões em paralelo, deriva a versão ativa de cada obra e exibe cards com botões de download.

**Tech Stack:** React 19 · TypeScript · Tailwind CSS

---

## File Map

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `frontend/src/pages/RelatoriosPage.tsx` | Criar | Cards por obra com download PDF + XLSX |
| `frontend/src/app.tsx` | Modificar | Registrar rota `/relatorios` |
| `frontend/src/components/layout/TopBar.tsx` | Modificar | Remover 5 links mortos |

---

### Task 1: RelatoriosPage + Rota

**Files:**
- Create: `frontend/src/pages/RelatoriosPage.tsx`
- Modify: `frontend/src/app.tsx`

- [ ] **Step 1: Criar frontend/src/pages/RelatoriosPage.tsx**

```tsx
import { useState, useEffect } from 'react'
import { getObras, getVersoes } from '@/api/obras'
import { downloadPropostaPdf } from '@/api/proposta'
import { downloadCurvaAbcExcel } from '@/api/curvaAbc'
import { toast } from '@/hooks/useToast'
import type { Obra, Versao } from '@/types'

interface ObraComVersao {
  obra: Obra
  versao: Versao
}

export default function RelatoriosPage() {
  const [items, setItems] = useState<ObraComVersao[]>([])
  const [loading, setLoading] = useState(true)
  const [downloading, setDownloading] = useState<Record<string, boolean>>({})

  useEffect(() => {
    async function load() {
      try {
        const obras = await getObras()
        const results = await Promise.all(
          obras.map(async obra => {
            const versoes = await getVersoes(obra.id)
            const ativa = versoes.find(v => !v.bloqueada && v.deletada_em === null)
            return ativa ? { obra, versao: ativa } : null
          })
        )
        setItems(results.filter((r): r is ObraComVersao => r !== null))
      } catch {
        toast('Erro ao carregar obras', 'error')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [])

  async function handleDownload(
    key: string,
    fn: () => Promise<void>,
    label: string,
  ) {
    setDownloading(prev => ({ ...prev, [key]: true }))
    try {
      await fn()
    } catch {
      toast(`Erro ao baixar ${label}`, 'error')
    } finally {
      setDownloading(prev => ({ ...prev, [key]: false }))
    }
  }

  if (loading) {
    return (
      <div className="p-6 max-w-2xl mx-auto space-y-4">
        <h1 className="text-xl font-bold text-gray-900 mb-4">Relatórios</h1>
        {[1, 2, 3].map(i => (
          <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-1/2 mb-3" />
            <div className="flex gap-3">
              <div className="h-8 bg-gray-200 rounded w-32" />
              <div className="h-8 bg-gray-200 rounded w-36" />
            </div>
          </div>
        ))}
      </div>
    )
  }

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-xl font-bold text-gray-900 mb-4">Relatórios</h1>

      {items.length === 0 ? (
        <p className="text-sm text-gray-500">Nenhuma obra com versão ativa encontrada.</p>
      ) : (
        <div className="space-y-4">
          {items.map(({ obra, versao }) => {
            const pdfKey = `pdf-${versao.id}`
            const xlsxKey = `xlsx-${versao.id}`
            return (
              <div key={obra.id} className="bg-white rounded-xl border border-gray-200 p-5">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-sm font-semibold text-gray-900">{obra.nome}</h2>
                  <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                    Versão {versao.numero}
                  </span>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={() =>
                      handleDownload(pdfKey, () => downloadPropostaPdf(versao.id), 'proposta PDF')
                    }
                    disabled={downloading[pdfKey]}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-gray-200 rounded-lg text-gray-700 hover:border-blue-400 hover:text-blue-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    {downloading[pdfKey] ? (
                      <>
                        <span className="inline-block w-3.5 h-3.5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                        Baixando…
                      </>
                    ) : (
                      '↓ PDF Proposta'
                    )}
                  </button>
                  <button
                    onClick={() =>
                      handleDownload(xlsxKey, () => downloadCurvaAbcExcel(versao.id), 'Curva ABC')
                    }
                    disabled={downloading[xlsxKey]}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-sm border border-gray-200 rounded-lg text-gray-700 hover:border-green-400 hover:text-green-600 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
                  >
                    {downloading[xlsxKey] ? (
                      <>
                        <span className="inline-block w-3.5 h-3.5 border-2 border-green-600 border-t-transparent rounded-full animate-spin" />
                        Baixando…
                      </>
                    ) : (
                      '↓ XLSX Curva ABC'
                    )}
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 2: Registrar rota em frontend/src/app.tsx**

Adicionar import após os imports existentes de pages:
```tsx
import RelatoriosPage from '@/pages/RelatoriosPage'
```

Adicionar rota dentro do bloco `<Routes>` interno (após a rota de `/configuracoes`):
```tsx
<Route path="/relatorios" element={<RelatoriosPage />} />
```

- [ ] **Step 3: Verificar TypeScript**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: sem erros (saída vazia)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/pages/RelatoriosPage.tsx \
        frontend/src/app.tsx
git commit -m "feat: RelatoriosPage — cards de download por obra com versão ativa"
```

---

### Task 2: Limpeza da TopBar

**Files:**
- Modify: `frontend/src/components/layout/TopBar.tsx`

- [ ] **Step 1: Substituir NAV_ITEMS em frontend/src/components/layout/TopBar.tsx**

Localizar o array `NAV_ITEMS` que atualmente tem 8 itens e substituí-lo por:

```ts
const NAV_ITEMS = [
  { label: 'Dashboard', to: '/' },
  { label: 'Obras', to: '/obras' },
  { label: 'Relatórios', to: '/relatorios' },
]
```

- [ ] **Step 2: Verificar TypeScript**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: sem erros

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/layout/TopBar.tsx
git commit -m "fix: TopBar — remover 5 links mortos, manter Dashboard · Obras · Relatórios"
```
