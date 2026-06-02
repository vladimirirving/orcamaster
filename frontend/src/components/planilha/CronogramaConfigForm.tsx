import { useState } from 'react'
import { patchCronogramaConfig } from '@/api/cronograma'

interface Props {
  versaoId: number
  initialInicio: string
  initialFim: string
  onSaved: (inicio: string, fim: string) => void
}

export default function CronogramaConfigForm({ versaoId, initialInicio, initialFim, onSaved }: Props) {
  const [inicio, setInicio] = useState(initialInicio)
  const [fim, setFim] = useState(initialFim)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (fim < inicio) {
      setError('A data de fim deve ser igual ou posterior ao início')
      return
    }
    setError(null)
    setSaving(true)
    try {
      await patchCronogramaConfig(versaoId, { cronograma_inicio: inicio, cronograma_fim: fim })
      onSaved(inicio, fim)
    } catch {
      setError('Erro ao salvar período')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="flex flex-col items-center justify-center flex-1 gap-6">
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-8 w-full max-w-md">
        <h2 className="text-base font-semibold text-gray-900 mb-1">Definir período do cronograma</h2>
        <p className="text-sm text-gray-500 mb-5">Escolha o mês de início e fim da obra.</p>
        {error && (
          <div className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            {error}
          </div>
        )}
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Mês de início</label>
            <input
              required
              type="month"
              value={inicio}
              onChange={e => setInicio(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">Mês de fim</label>
            <input
              required
              type="month"
              value={fim}
              onChange={e => setFim(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            type="submit"
            disabled={saving}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Salvando...' : 'Definir período'}
          </button>
        </form>
      </div>
    </div>
  )
}
