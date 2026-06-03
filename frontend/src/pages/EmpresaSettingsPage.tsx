import { useState, useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { getEmpresaConfig, updateEmpresaConfig } from '@/api/proposta'
import { toast } from '@/hooks/useToast'
import type { EmpresaConfig } from '@/types'

export default function EmpresaSettingsPage() {
  const { papel } = useAuth()
  if (papel !== 'admin') return <Navigate to="/obras" replace />

  const [empresa, setEmpresa] = useState<EmpresaConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [representanteNome, setRepresentanteNome] = useState('')
  const [representanteCpf, setRepresentanteCpf] = useState('')
  const [declaracoesPadrao, setDeclaracoesPadrao] = useState('')

  useEffect(() => {
    getEmpresaConfig()
      .then(e => {
        setEmpresa(e)
        setRepresentanteNome(e.representante_nome ?? '')
        setRepresentanteCpf(e.representante_cpf ?? '')
        setDeclaracoesPadrao(e.declaracoes_padrao ?? '')
      })
      .catch(() => toast('Erro ao carregar configurações', 'error'))
      .finally(() => setLoading(false))
  }, [])

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

  if (loading) return <div className="p-6 text-gray-400">Carregando...</div>

  return (
    <div className="p-6 max-w-xl mx-auto">
      <h1 className="text-xl font-bold text-gray-900 mb-1">Configurações da Empresa</h1>
      {empresa && (
        <p className="text-sm text-gray-500 mb-6">
          {empresa.nome} · CNPJ: {empresa.cnpj}
        </p>
      )}
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
    </div>
  )
}
