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
