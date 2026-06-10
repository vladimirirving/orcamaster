import { useState, useEffect } from 'react'
import { getPropostaConfig, savePropostaConfig, downloadPropostaPdf } from '@/api/proposta'
import { toast } from '@/hooks/useToast'
import type { PropostaConfig } from '@/types'

interface Props {
  versaoId: number
}

const TODAY = new Date().toISOString().slice(0, 10)

export default function PropostaTab({ versaoId }: Props) {
  const [config, setConfig] = useState<PropostaConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [dirty, setDirty] = useState(false)

  const [validade, setValidade] = useState(60)
  const [dataProposta, setDataProposta] = useState(TODAY)
  const [declaracoes, setDeclaracoes] = useState('')

  useEffect(() => {
    setLoading(true)
    getPropostaConfig(versaoId)
      .then(pc => {
        setConfig(pc)
        setValidade(pc.validade_dias)
        setDataProposta(pc.data_proposta)
        setDeclaracoes(pc.declaracoes ?? '')
      })
      .catch(e => {
        if (e?.response?.status !== 404) {
          toast('Erro ao carregar proposta', 'error')
        }
      })
      .finally(() => setLoading(false))
  }, [versaoId])

  async function handleSave() {
    setSaving(true)
    try {
      const pc = await savePropostaConfig(versaoId, {
        validade_dias: validade,
        data_proposta: dataProposta,
        declaracoes: declaracoes || null,
      })
      setConfig(pc)
      setDirty(false)
      toast('Proposta salva')
    } catch {
      toast('Erro ao salvar proposta', 'error')
    } finally {
      setSaving(false)
    }
  }

  async function handleExport() {
    if (config === null) {
      toast('Salve a proposta antes de gerar o PDF', 'error')
      return
    }
    setExporting(true)
    try {
      await downloadPropostaPdf(versaoId)
    } catch {
      toast('Erro ao gerar PDF', 'error')
    } finally {
      setExporting(false)
    }
  }

  if (loading) return <div className="p-6 text-gray-400 text-sm">Carregando...</div>

  return (
    <div className="p-6 max-w-2xl space-y-5">
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Validade da proposta
          </label>
          <select
            value={validade}
            onChange={e => { setValidade(Number(e.target.value)); setDirty(true) }}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value={30}>30 dias</option>
            <option value={60}>60 dias</option>
            <option value={90}>90 dias</option>
            <option value={180}>180 dias</option>
          </select>
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">
            Data da proposta
          </label>
          <input
            type="date"
            value={dataProposta}
            onChange={e => { setDataProposta(e.target.value); setDirty(true) }}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-700 mb-1">Declarações</label>
        <textarea
          rows={8}
          value={declaracoes}
          onChange={e => { setDeclaracoes(e.target.value); setDirty(true) }}
          placeholder="Texto das declarações que aparecerá no documento..."
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
        />
      </div>

      <div className="flex gap-3">
        <button
          onClick={handleSave}
          disabled={!dirty || saving}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
        >
          {saving ? 'Salvando...' : 'Salvar'}
        </button>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-40"
        >
          {exporting ? 'Gerando...' : 'Baixar PDF'}
        </button>
      </div>
    </div>
  )
}
