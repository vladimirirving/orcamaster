import { useState } from 'react'
import { createAditivo, updateAditivo } from '@/api/contratos'
import { toast } from '@/hooks/useToast'
import type { Aditivo } from '@/types'

interface Props {
  contratoId: number
  aditivo?: Aditivo
  onClose: () => void
  onSuccess: (a: Aditivo) => void
}

export default function AditivoModal({ contratoId, aditivo, onClose, onSuccess }: Props) {
  const [tipo, setTipo] = useState<'valor' | 'prazo' | 'valor_prazo'>(
    aditivo?.tipo as 'valor' | 'prazo' | 'valor_prazo' ?? 'valor'
  )
  const [numero, setNumero] = useState(aditivo?.numero ?? '')
  const [deltaValor, setDeltaValor] = useState(
    aditivo?.delta_valor != null ? String(aditivo.delta_valor) : ''
  )
  const [novaDataFim, setNovaDataFim] = useState(aditivo?.nova_data_fim ?? '')
  const [justificativa, setJustificativa] = useState(aditivo?.justificativa ?? '')
  const [dataAssinatura, setDataAssinatura] = useState(aditivo?.data_assinatura ?? '')
  const [saving, setSaving] = useState(false)

  const showValor = tipo === 'valor' || tipo === 'valor_prazo'
  const showPrazo = tipo === 'prazo' || tipo === 'valor_prazo'

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const payload = {
        tipo,
        numero: numero.trim() || null,
        delta_valor: showValor && deltaValor ? Number(deltaValor) : null,
        nova_data_fim: showPrazo && novaDataFim ? novaDataFim : null,
        justificativa: justificativa.trim() || null,
        data_assinatura: dataAssinatura || null,
      }
      const result = aditivo
        ? await updateAditivo(aditivo.id, payload)
        : await createAditivo(contratoId, payload)
      onSuccess(result)
      toast(aditivo ? 'Aditivo atualizado' : 'Aditivo criado')
    } catch {
      toast('Erro ao salvar aditivo', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4">
        <div className="flex items-center justify-between p-6 pb-4">
          <h2 className="text-base font-semibold text-gray-900">
            {aditivo ? 'Editar aditivo' : 'Novo aditivo'}
          </h2>
          <button onClick={onClose} aria-label="Fechar" className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 pb-6 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Tipo *</label>
              <select
                value={tipo}
                onChange={e => setTipo(e.target.value as 'valor' | 'prazo' | 'valor_prazo')}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="valor">Valor</option>
                <option value="prazo">Prazo</option>
                <option value="valor_prazo">Valor + Prazo</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Número</label>
              <input
                value={numero}
                onChange={e => setNumero(e.target.value)}
                placeholder="Ex: 1º Aditivo"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          {showValor && (
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Variação de valor (R$) <span className="text-gray-400 font-normal">negativo = redução</span>
              </label>
              <input
                type="number"
                step="0.01"
                value={deltaValor}
                onChange={e => setDeltaValor(e.target.value)}
                placeholder="Ex: 20000.00"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          {showPrazo && (
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Nova data fim</label>
              <input
                type="date"
                value={novaDataFim}
                onChange={e => setNovaDataFim(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Justificativa</label>
            <textarea
              value={justificativa}
              onChange={e => setJustificativa(e.target.value)}
              rows={2}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Data de assinatura</label>
            <input
              type="date"
              value={dataAssinatura}
              onChange={e => setDataAssinatura(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
            >
              {saving ? 'Salvando…' : 'Salvar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
