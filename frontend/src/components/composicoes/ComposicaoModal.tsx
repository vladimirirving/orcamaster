import { useState, useEffect } from 'react'
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
  const [precoUnitario, setPrecoUnitario] = useState(
    composicao?.preco_unitario != null ? String(parseFloat(String(composicao.preco_unitario))) : ''
  )
  const [saving, setSaving] = useState(false)
  const [codigoError, setCodigoError] = useState('')

  const isValid =
    codigo.trim().length > 0 &&
    descricao.trim().length > 0 &&
    unidade.trim().length > 0 &&
    parseFloat(String(precoUnitario).replace(',', '.')) > 0

  async function handleSubmit() {
    if (!isValid) return
    setSaving(true)
    setCodigoError('')
    const data = {
      codigo: codigo.trim(),
      descricao: descricao.trim(),
      unidade: unidade.trim(),
      preco_unitario: String(precoUnitario).replace(',', '.'),
    }
    try {
      if (isEdit && composicao) {
        await updateComposicao(composicao.id, data)
      } else {
        await createComposicao(data)
      }
      onSuccess()
    } catch (e: any) {
      if (e?.response?.status === 409) {
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
            <label htmlFor="campo-codigo" className="block text-xs font-medium text-gray-700 mb-1">Código</label>
            <input
              id="campo-codigo"
              type="text"
              value={codigo}
              onChange={e => { setCodigo(e.target.value); setCodigoError('') }}
              aria-describedby={codigoError ? 'codigo-error' : undefined}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${codigoError ? 'border-red-400' : 'border-gray-300'}`}
            />
            {codigoError && <p id="codigo-error" role="alert" className="text-xs text-red-500 mt-1">{codigoError}</p>}
          </div>
          <div>
            <label htmlFor="campo-descricao" className="block text-xs font-medium text-gray-700 mb-1">Descrição</label>
            <input
              id="campo-descricao"
              type="text"
              value={descricao}
              onChange={e => setDescricao(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="campo-unidade" className="block text-xs font-medium text-gray-700 mb-1">Unidade</label>
              <input
                id="campo-unidade"
                type="text"
                value={unidade}
                onChange={e => setUnidade(e.target.value)}
                placeholder="m², UN, m³…"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label htmlFor="campo-preco" className="block text-xs font-medium text-gray-700 mb-1">Preço Unitário (R$)</label>
              <input
                id="campo-preco"
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
