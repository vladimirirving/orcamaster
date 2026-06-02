import { useState } from 'react'
import { Trash2, AlertTriangle, RefreshCw } from 'lucide-react'
import { updateItem, deleteItem, atualizarPreco } from '@/api/itens'
import { useOrcamento } from '@/stores/orcamento'
import { toast } from '@/hooks/useToast'
import type { Item } from '@/types'

interface Props {
  item: Item
  isReadOnly: boolean
}

export default function FormItem({ item, isReadOnly }: Props) {
  const [quantidade, setQuantidade] = useState(item.quantidade)
  const [unidade, setUnidade] = useState(item.unidade ?? '')
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [updatingPreco, setUpdatingPreco] = useState(false)
  const { updateItemNoStore, removeItemDoStore, fecharPainel } = useOrcamento()

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const updated = await updateItem(item.id, { quantidade, unidade: unidade || undefined })
      updateItemNoStore(updated)
      toast('Item salvo')
    } catch {
      toast('Erro ao salvar item', 'error')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    try {
      await deleteItem(item.id)
      removeItemDoStore(item)
      fecharPainel()
      toast('Item removido')
    } catch {
      toast('Erro ao remover item', 'error')
    }
  }

  async function handleAtualizarPreco() {
    setUpdatingPreco(true)
    try {
      const updated = await atualizarPreco(item.id)
      updateItemNoStore(updated)
      toast('Preço atualizado')
    } catch {
      toast('Erro ao atualizar preço', 'error')
    } finally {
      setUpdatingPreco(false)
    }
  }

  const precoFormatado = item.preco_unitario_sem_bdi
    ? parseFloat(item.preco_unitario_sem_bdi).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
    : '—'

  return (
    <form onSubmit={handleSave} className="flex flex-col gap-4">
      {item.requer_revisao && (
        <div className="flex items-center gap-2 bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-2 text-sm text-yellow-700">
          <AlertTriangle size={14} />
          <span>Preço desatualizado</span>
          <button
            type="button"
            onClick={handleAtualizarPreco}
            disabled={updatingPreco || isReadOnly}
            className="ml-auto flex items-center gap-1 text-xs bg-yellow-100 hover:bg-yellow-200 px-2 py-1 rounded disabled:opacity-50"
          >
            <RefreshCw size={12} />
            {updatingPreco ? 'Atualizando...' : 'Atualizar'}
          </button>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Quantidade</label>
          <input
            type="number"
            step="0.000001"
            value={quantidade}
            onChange={e => setQuantidade(e.target.value)}
            disabled={isReadOnly}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Unidade</label>
          <input
            value={unidade}
            onChange={e => setUnidade(e.target.value)}
            disabled={isReadOnly}
            placeholder="m3, un, m..."
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
          />
        </div>
      </div>

      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Preço unit. S/BDI</label>
        <div className="text-sm text-gray-700 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
          {precoFormatado}
          {item.composicao_id && <span className="text-xs text-gray-400 ml-2">(via composição)</span>}
        </div>
      </div>

      {/* BuscaComposicao will be inserted here in Task 7 */}
      <div id="busca-composicao-slot" />

      {!isReadOnly && (
        <div className="flex gap-2 pt-2">
          <button
            type="submit"
            disabled={saving}
            className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Salvando...' : 'Salvar'}
          </button>
          <button
            type="button"
            onClick={() => {
              if (confirmDelete) handleDelete()
              else { setConfirmDelete(true); setTimeout(() => setConfirmDelete(false), 3000) }
            }}
            className={`p-2 rounded-lg transition-colors ${confirmDelete ? 'bg-red-100 text-red-600' : 'text-gray-400 hover:bg-gray-100'}`}
          >
            <Trash2 size={16} />
          </button>
        </div>
      )}
    </form>
  )
}
