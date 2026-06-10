// frontend/src/components/insumos/InsumoItemModal.tsx
import { useState } from 'react'
import { createInsumo, updateInsumo } from '@/api/insumos_item'
import { toast } from '@/hooks/useToast'
import type { InsumoItem } from '@/types'

const UFS = ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS',
             'MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC',
             'SP','SE','TO']

interface Props {
  insumo?: InsumoItem
  onClose: () => void
  onSuccess: () => void
}

function toMonthInput(dateStr: string | undefined): string {
  if (!dateStr) return ''
  return dateStr.slice(0, 7)  // '2019-08-01' → '2019-08'
}

function fromMonthInput(month: string): string {
  return month ? `${month}-01` : ''  // '2019-08' → '2019-08-01'
}

const inputCls =
  'w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'

export default function InsumoItemModal({ insumo, onClose, onSuccess }: Props) {
  const isEdit = !!insumo
  const [codigo, setCodigo] = useState(insumo?.codigo ?? '')
  const [descricao, setDescricao] = useState(insumo?.descricao ?? '')
  const [unidade, setUnidade] = useState(insumo?.unidade ?? '')
  const [tipo, setTipo] = useState(insumo?.tipo ?? 'material')
  const [precoNaoDesonerado, setPrecoNaoDesonerado] = useState(
    insumo?.preco_nao_desonerado ?? ''
  )
  const [precoDesonerado, setPrecoDesonerado] = useState(
    insumo?.preco_desonerado ?? ''
  )
  const [estado, setEstado] = useState(insumo?.estado ?? '')
  const [dataRef, setDataRef] = useState(toMonthInput(insumo?.data_referencia))
  const [saving, setSaving] = useState(false)

  const isValid =
    codigo.trim() && descricao.trim() && unidade.trim() &&
    tipo && precoNaoDesonerado && precoDesonerado && dataRef

  async function handleSubmit() {
    if (!isValid) return
    setSaving(true)
    const payload = {
      codigo: codigo.trim(),
      descricao: descricao.trim(),
      unidade: unidade.trim(),
      tipo,
      preco_nao_desonerado: precoNaoDesonerado as any,
      preco_desonerado: precoDesonerado as any,
      estado: estado || null,
      data_referencia: fromMonthInput(dataRef),
    }
    try {
      if (isEdit && insumo) {
        await updateInsumo(insumo.id, payload)
      } else {
        await createInsumo(payload as any)
      }
      onSuccess()
    } catch {
      toast('Erro ao salvar insumo', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-xl mx-4 p-6 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-base font-semibold text-gray-900">
            {isEdit ? 'Editar insumo' : 'Novo insumo'}
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
          {/* Row 1: Banco + Tipo */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Banco
              </label>
              <input
                value="Próprio"
                readOnly
                className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm bg-gray-50 text-gray-400 cursor-not-allowed"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Tipo <span className="text-red-500">*</span>
              </label>
              <select
                value={tipo}
                onChange={e => setTipo(e.target.value)}
                className={inputCls}
              >
                <option value="mao_obra">Mão de Obra</option>
                <option value="material">Material</option>
                <option value="equipamento">Equipamento</option>
              </select>
            </div>
          </div>

          {/* Row 2: Código + Unidade */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Código <span className="text-red-500">*</span>
              </label>
              <input
                value={codigo}
                onChange={e => setCodigo(e.target.value)}
                placeholder="PRO-001"
                className={inputCls}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Unidade <span className="text-red-500">*</span>
              </label>
              <input
                value={unidade}
                onChange={e => setUnidade(e.target.value)}
                placeholder="M3, H, KG..."
                className={inputCls}
              />
            </div>
          </div>

          {/* Row 3: Descrição full width */}
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">
              Descrição <span className="text-red-500">*</span>
            </label>
            <input
              value={descricao}
              onChange={e => setDescricao(e.target.value)}
              placeholder="Descrição do insumo..."
              className={inputCls}
            />
          </div>

          {/* Row 4: Preços */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Preço Não Desonerado <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                step="0.000001"
                min="0"
                value={precoNaoDesonerado}
                onChange={e => setPrecoNaoDesonerado(e.target.value)}
                placeholder="0.000000"
                className={`${inputCls} text-right`}
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Preço Desonerado <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                step="0.000001"
                min="0"
                value={precoDesonerado}
                onChange={e => setPrecoDesonerado(e.target.value)}
                placeholder="0.000000"
                className={`${inputCls} text-right`}
              />
            </div>
          </div>

          {/* Row 5: Estado + Data Ref */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Estado{' '}
                <span className="text-gray-400 font-normal">(opcional)</span>
              </label>
              <select
                value={estado}
                onChange={e => setEstado(e.target.value)}
                className={inputCls}
              >
                <option value="">— nenhum —</option>
                {UFS.map(uf => (
                  <option key={uf} value={uf}>{uf}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">
                Data de Referência <span className="text-red-500">*</span>
              </label>
              <input
                type="month"
                value={dataRef}
                onChange={e => setDataRef(e.target.value)}
                className={inputCls}
              />
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-gray-100">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={!isValid || saving}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {saving ? 'Salvando...' : 'Salvar'}
          </button>
        </div>
      </div>
    </div>
  )
}
