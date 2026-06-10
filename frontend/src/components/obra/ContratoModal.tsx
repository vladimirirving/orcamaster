import { useState } from 'react'
import { createContrato, updateContrato } from '@/api/contratos'
import { toast } from '@/hooks/useToast'
import type { Contrato } from '@/types'

interface Props {
  obraId: number
  contrato?: Contrato
  onClose: () => void
  onSuccess: (c: Contrato) => void
}

export default function ContratoModal({ obraId, contrato, onClose, onSuccess }: Props) {
  const [objeto, setObjeto] = useState(contrato?.objeto ?? '')
  const [valorOriginal, setValorOriginal] = useState(
    contrato?.valor_original != null ? String(contrato.valor_original) : ''
  )
  const [numero, setNumero] = useState(contrato?.numero ?? '')
  const [dataAssinatura, setDataAssinatura] = useState(contrato?.data_assinatura ?? '')
  const [dataInicio, setDataInicio] = useState(contrato?.data_inicio ?? '')
  const [dataFim, setDataFim] = useState(contrato?.data_fim ?? '')
  const [contratanteNome, setContratanteNome] = useState(contrato?.contratante_nome ?? '')
  const [contratanteCnpj, setContratanteCnpj] = useState(contrato?.contratante_cnpj ?? '')
  const [contratadoNome, setContratadoNome] = useState(contrato?.contratado_nome ?? '')
  const [contratadoCnpj, setContratadoCnpj] = useState(contrato?.contratado_cnpj ?? '')
  const [saving, setSaving] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!objeto.trim() || !valorOriginal) return
    setSaving(true)
    try {
      const payload = {
        objeto: objeto.trim(),
        valor_original: Number(valorOriginal),
        numero: numero.trim() || null,
        data_assinatura: dataAssinatura || null,
        data_inicio: dataInicio || null,
        data_fim: dataFim || null,
        contratante_nome: contratanteNome.trim() || null,
        contratante_cnpj: contratanteCnpj.trim() || null,
        contratado_nome: contratadoNome.trim() || null,
        contratado_cnpj: contratadoCnpj.trim() || null,
      }
      const result = contrato
        ? await updateContrato(contrato.id, payload)
        : await createContrato(obraId, payload)
      onSuccess(result)
      toast(contrato ? 'Contrato atualizado' : 'Contrato criado')
    } catch {
      toast('Erro ao salvar contrato', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 pb-4">
          <h2 className="text-base font-semibold text-gray-900">
            {contrato ? 'Editar contrato' : 'Novo contrato'}
          </h2>
          <button onClick={onClose} aria-label="Fechar" className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 pb-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Objeto *</label>
            <textarea
              required
              value={objeto}
              onChange={e => setObjeto(e.target.value)}
              rows={2}
              placeholder="Ex: Execução de obra de pavimentação da Rodovia SP-232"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Valor original (R$) *</label>
              <input
                required
                type="number"
                min="0"
                step="0.01"
                value={valorOriginal}
                onChange={e => setValorOriginal(e.target.value)}
                placeholder="Ex: 500000.00"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Número</label>
              <input
                value={numero}
                onChange={e => setNumero(e.target.value)}
                placeholder="Ex: CT-2024-001"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Assinatura</label>
              <input type="date" value={dataAssinatura} onChange={e => setDataAssinatura(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Início</label>
              <input type="date" value={dataInicio} onChange={e => setDataInicio(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Prazo fim</label>
              <input type="date" value={dataFim} onChange={e => setDataFim(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>

          <div className="border-t border-gray-100 pt-3">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Contratante</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Razão social</label>
                <input value={contratanteNome} onChange={e => setContratanteNome(e.target.value)}
                  placeholder="Ex: DNIT"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">CNPJ</label>
                <input value={contratanteCnpj} onChange={e => setContratanteCnpj(e.target.value)}
                  placeholder="00.000.000/0001-00"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
          </div>

          <div className="border-t border-gray-100 pt-3">
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">Contratada</p>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">Razão social</label>
                <input value={contratadoNome} onChange={e => setContratadoNome(e.target.value)}
                  placeholder="Ex: Construtora ABC Ltda"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-700 mb-1">CNPJ</label>
                <input value={contratadoCnpj} onChange={e => setContratadoCnpj(e.target.value)}
                  placeholder="00.000.000/0001-00"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
              </div>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button type="button" onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving || !objeto.trim() || !valorOriginal}
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
