# Módulo 14 — Gerenciamento de Usuários: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Adicionar aba "Usuários" em `/configuracoes` para que o admin liste, crie e edite membros da equipe.

**Architecture:** Apenas frontend — o backend já expõe `GET /usuarios`, `POST /usuarios` e `PATCH /usuarios/{id}`. Criamos `api/usuarios.ts`, o componente `UsuariosTab` com tabela + dois modais inline, e refatoramos `EmpresaSettingsPage` para ter um sistema de abas (Empresa · Importação SINAPI/SICRO · Usuários).

**Tech Stack:** React 19 · TypeScript · Tailwind CSS · Axios (via `@/api/client`)

---

## File Map

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `frontend/src/types.ts` | Modificar | Adicionar interface `Usuario` |
| `frontend/src/api/usuarios.ts` | Criar | `listUsuarios`, `createUsuario`, `updateUsuario` |
| `frontend/src/components/empresa/UsuariosTab.tsx` | Criar | Tabela de membros + modal criar + modal editar |
| `frontend/src/pages/EmpresaSettingsPage.tsx` | Modificar | Adicionar sistema de abas + aba Usuários |

---

### Task 1: Tipos + API

**Files:**
- Modify: `frontend/src/types.ts`
- Create: `frontend/src/api/usuarios.ts`

- [ ] **Step 1: Adicionar interface Usuario em frontend/src/types.ts**

Adicionar ao final do arquivo (após `PropostaSugerida`):

```ts
export interface Usuario {
  id: number
  empresa_id: number
  nome: string
  email: string
  papel: 'admin' | 'orcamentista' | 'visualizador'
  ativo: boolean
}
```

- [ ] **Step 2: Criar frontend/src/api/usuarios.ts**

```ts
import { api } from '@/api/client'
import type { Usuario } from '@/types'

export const listUsuarios = () =>
  api.get<Usuario[]>('/usuarios').then(r => r.data)

export const createUsuario = (data: {
  nome: string
  email: string
  senha: string
  papel: string
}) => api.post<Usuario>('/usuarios', data).then(r => r.data)

export const updateUsuario = (
  id: number,
  data: { papel?: string; ativo?: boolean },
) => api.patch<Usuario>(`/usuarios/${id}`, data).then(r => r.data)
```

- [ ] **Step 3: Confirmar que TypeScript compila**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: sem erros

- [ ] **Step 4: Commit**

```bash
git add frontend/src/types.ts frontend/src/api/usuarios.ts
git commit -m "feat: Usuario type + api/usuarios — listUsuarios, createUsuario, updateUsuario"
```

---

### Task 2: UsuariosTab + EmpresaSettingsPage

**Files:**
- Create: `frontend/src/components/empresa/UsuariosTab.tsx`
- Modify: `frontend/src/pages/EmpresaSettingsPage.tsx`

- [ ] **Step 1: Criar frontend/src/components/empresa/UsuariosTab.tsx**

```tsx
import { useState, useEffect } from 'react'
import { listUsuarios, createUsuario, updateUsuario } from '@/api/usuarios'
import { useAuth } from '@/hooks/useAuth'
import { toast } from '@/hooks/useToast'
import type { Usuario } from '@/types'

const PAPEL_LABELS: Record<string, string> = {
  admin: 'Administrador',
  orcamentista: 'Orçamentista',
  visualizador: 'Visualizador',
}

const PAPEL_BADGE: Record<string, string> = {
  admin: 'bg-purple-100 text-purple-700',
  orcamentista: 'bg-blue-100 text-blue-700',
  visualizador: 'bg-gray-100 text-gray-600',
}

export default function UsuariosTab() {
  const { userId } = useAuth()
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState<'criar' | 'editar' | null>(null)
  const [editTarget, setEditTarget] = useState<Usuario | null>(null)

  async function reload() {
    try {
      setUsuarios(await listUsuarios())
    } catch {
      toast('Erro ao carregar usuários', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { reload() }, [])

  function openEditar(u: Usuario) {
    setEditTarget(u)
    setModal('editar')
  }

  if (loading) {
    return <div className="py-8 text-center text-gray-400 text-sm">Carregando...</div>
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">
          {usuarios.length} membro{usuarios.length !== 1 ? 's' : ''}
        </p>
        <button
          onClick={() => setModal('criar')}
          className="bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          + Adicionar membro
        </button>
      </div>

      <div className="divide-y divide-gray-100 border border-gray-200 rounded-xl overflow-hidden">
        {usuarios.map(u => (
          <div key={u.id} className="flex items-center gap-3 px-4 py-3 bg-white">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {u.nome}
                {u.id === userId && (
                  <span className="ml-2 text-xs text-gray-400">(você)</span>
                )}
              </p>
              <p className="text-xs text-gray-500 truncate">{u.email}</p>
            </div>
            <span
              className={`text-xs font-medium px-2 py-0.5 rounded-full ${PAPEL_BADGE[u.papel] ?? 'bg-gray-100 text-gray-600'}`}
            >
              {PAPEL_LABELS[u.papel] ?? u.papel}
            </span>
            <span
              className={`text-xs font-medium px-2 py-0.5 rounded-full ${u.ativo ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'}`}
            >
              {u.ativo ? 'Ativo' : 'Inativo'}
            </span>
            <button
              onClick={() => openEditar(u)}
              disabled={u.id === userId}
              className="text-gray-400 hover:text-blue-600 disabled:opacity-30 disabled:cursor-not-allowed p-1 text-base leading-none"
              title={u.id === userId ? 'Não é possível editar seu próprio perfil' : 'Editar'}
            >
              ✎
            </button>
          </div>
        ))}
      </div>

      {modal === 'criar' && (
        <CriarModal
          onClose={() => setModal(null)}
          onSuccess={() => { setModal(null); reload() }}
        />
      )}
      {modal === 'editar' && editTarget && (
        <EditarModal
          usuario={editTarget}
          onClose={() => { setModal(null); setEditTarget(null) }}
          onSuccess={() => { setModal(null); setEditTarget(null); reload() }}
        />
      )}
    </div>
  )
}

function CriarModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void
  onSuccess: () => void
}) {
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [mostrarSenha, setMostrarSenha] = useState(false)
  const [papel, setPapel] = useState('orcamentista')
  const [saving, setSaving] = useState(false)
  const [emailError, setEmailError] = useState('')

  async function handleSubmit() {
    if (!nome || !email || senha.length < 8) return
    setSaving(true)
    setEmailError('')
    try {
      await createUsuario({ nome, email, senha, papel })
      onSuccess()
    } catch (e: any) {
      if (e?.response?.status === 400) {
        setEmailError('E-mail já cadastrado.')
      } else {
        toast('Erro ao criar usuário', 'error')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">Adicionar membro</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Nome</label>
            <input
              type="text"
              value={nome}
              onChange={e => setNome(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">E-mail</label>
            <input
              type="email"
              value={email}
              onChange={e => { setEmail(e.target.value); setEmailError('') }}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${emailError ? 'border-red-400' : 'border-gray-300'}`}
            />
            {emailError && <p className="text-xs text-red-500 mt-1">{emailError}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Senha</label>
            <div className="relative">
              <input
                type={mostrarSenha ? 'text' : 'password'}
                value={senha}
                onChange={e => setSenha(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 pr-16"
              />
              <button
                type="button"
                onClick={() => setMostrarSenha(v => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-500 hover:text-gray-700"
              >
                {mostrarSenha ? 'Ocultar' : 'Mostrar'}
              </button>
            </div>
            {senha.length > 0 && senha.length < 8 && (
              <p className="text-xs text-red-500 mt-1">Mínimo 8 caracteres</p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Papel</label>
            <select
              value={papel}
              onChange={e => setPapel(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="orcamentista">Orçamentista</option>
              <option value="visualizador">Visualizador</option>
              <option value="admin">Administrador</option>
            </select>
          </div>
        </div>

        <div className="flex gap-2 justify-end pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={!nome || !email || senha.length < 8 || saving}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
          >
            {saving ? 'Salvando…' : 'Adicionar'}
          </button>
        </div>
      </div>
    </div>
  )
}

function EditarModal({
  usuario,
  onClose,
  onSuccess,
}: {
  usuario: Usuario
  onClose: () => void
  onSuccess: () => void
}) {
  const [papel, setPapel] = useState<Usuario['papel']>(usuario.papel)
  const [ativo, setAtivo] = useState(usuario.ativo)
  const [saving, setSaving] = useState(false)

  async function handleSubmit() {
    setSaving(true)
    try {
      await updateUsuario(usuario.id, { papel, ativo })
      onSuccess()
    } catch {
      toast('Erro ao atualizar usuário', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">Editar membro</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <p className="text-xs font-medium text-gray-500 mb-0.5">Nome</p>
            <p className="text-sm text-gray-900">{usuario.nome}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-500 mb-0.5">E-mail</p>
            <p className="text-sm text-gray-900">{usuario.email}</p>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Papel</label>
            <select
              value={papel}
              onChange={e => setPapel(e.target.value as Usuario['papel'])}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="orcamentista">Orçamentista</option>
              <option value="visualizador">Visualizador</option>
              <option value="admin">Administrador</option>
            </select>
          </div>
          <div className="flex items-center gap-3">
            <label className="text-xs font-medium text-gray-700">Ativo</label>
            <button
              type="button"
              onClick={() => setAtivo(v => !v)}
              className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${ativo ? 'bg-blue-600' : 'bg-gray-300'}`}
            >
              <span
                className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${ativo ? 'translate-x-4' : 'translate-x-1'}`}
              />
            </button>
          </div>
        </div>

        <div className="flex gap-2 justify-end pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
          >
            {saving ? 'Salvando…' : 'Salvar'}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Substituir frontend/src/pages/EmpresaSettingsPage.tsx**

Reescrever o arquivo inteiro para adicionar o sistema de abas:

```tsx
import { useState, useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { getEmpresaConfig, updateEmpresaConfig } from '@/api/proposta'
import { importarComposicoes } from '@/api/composicoes'
import { toast } from '@/hooks/useToast'
import type { EmpresaConfig } from '@/types'
import UsuariosTab from '@/components/empresa/UsuariosTab'

type Tab = 'empresa' | 'sinapi' | 'usuarios'

export default function EmpresaSettingsPage() {
  const { papel } = useAuth()
  const [tab, setTab] = useState<Tab>('empresa')
  const [empresa, setEmpresa] = useState<EmpresaConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [representanteNome, setRepresentanteNome] = useState('')
  const [representanteCpf, setRepresentanteCpf] = useState('')
  const [declaracoesPadrao, setDeclaracoesPadrao] = useState('')
  const [importOrigem, setImportOrigem] = useState<'sinapi' | 'sicro'>('sinapi')
  const [importFile, setImportFile] = useState<File | null>(null)
  const [importing, setImporting] = useState(false)
  const [importResult, setImportResult] = useState<{
    criadas: number
    atualizadas: number
    itens_marcados: number
  } | null>(null)

  useEffect(() => {
    if (papel !== 'admin') return
    getEmpresaConfig()
      .then(e => {
        setEmpresa(e)
        setRepresentanteNome(e.representante_nome ?? '')
        setRepresentanteCpf(e.representante_cpf ?? '')
        setDeclaracoesPadrao(e.declaracoes_padrao ?? '')
      })
      .catch(() => toast('Erro ao carregar configurações', 'error'))
      .finally(() => setLoading(false))
  }, [papel])

  if (papel !== 'admin') return <Navigate to="/obras" replace />

  async function handleSave() {
    setSaving(true)
    try {
      const updated = await updateEmpresaConfig({
        representante_nome: representanteNome || null,
        representante_cpf: representanteCpf || null,
        declaracoes_padrao: declaracoesPadrao || null,
      })
      setEmpresa(updated)
      toast('Configurações salvas')
    } catch {
      toast('Erro ao salvar', 'error')
    } finally {
      setSaving(false)
    }
  }

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

  if (loading) return <div className="p-6 text-gray-400">Carregando...</div>

  const tabs: { key: Tab; label: string }[] = [
    { key: 'empresa', label: 'Empresa' },
    { key: 'sinapi', label: 'Importação SINAPI/SICRO' },
    { key: 'usuarios', label: 'Usuários' },
  ]

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <h1 className="text-xl font-bold text-gray-900 mb-1">Configurações</h1>
      {empresa && (
        <p className="text-sm text-gray-500 mb-4">
          {empresa.nome} · CNPJ: {empresa.cnpj}
        </p>
      )}

      {/* Tab bar */}
      <div className="flex border-b border-gray-200 mb-6">
        {tabs.map(t => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === t.key
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-800'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Empresa */}
      {tab === 'empresa' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Representante Legal
            </label>
            <input
              type="text"
              value={representanteNome}
              onChange={e => setRepresentanteNome(e.target.value)}
              placeholder="Nome completo"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              CPF do Representante
            </label>
            <input
              type="text"
              value={representanteCpf}
              onChange={e => setRepresentanteCpf(e.target.value)}
              placeholder="000.000.000-00"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Declarações Padrão
            </label>
            <textarea
              rows={6}
              value={declaracoesPadrao}
              onChange={e => setDeclaracoesPadrao(e.target.value)}
              placeholder="Texto pré-preenchido em novas propostas..."
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
            />
          </div>
          <button
            onClick={handleSave}
            disabled={saving}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
          >
            {saving ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      )}

      {/* Importação SINAPI/SICRO */}
      {tab === 'sinapi' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
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
      )}

      {/* Usuários */}
      {tab === 'usuarios' && <UsuariosTab />}
    </div>
  )
}
```

- [ ] **Step 3: Confirmar que TypeScript compila**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: sem erros

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/empresa/UsuariosTab.tsx \
        frontend/src/pages/EmpresaSettingsPage.tsx
git commit -m "feat: aba Usuários em /configuracoes — tabela, modal criar, modal editar — Módulo 14 completo"
```
