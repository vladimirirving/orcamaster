import { X } from 'lucide-react'
import { useOrcamento } from '@/stores/orcamento'
import FormGrupo from './FormGrupo'
import FormItem from './FormItem'

export default function PainelLateral({ isReadOnly }: { isReadOnly: boolean }) {
  const { painel, fecharPainel } = useOrcamento()
  if (!painel) return null

  return (
    <div className="w-80 flex-shrink-0 bg-white border border-gray-200 rounded-lg flex flex-col overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <h3 className="text-sm font-semibold text-gray-800">
          {painel.tipo === 'grupo' ? (painel.data.pai_id ? 'Subgrupo' : 'Grupo') : 'Item'}
        </h3>
        <button onClick={fecharPainel} className="text-gray-400 hover:text-gray-600">
          <X size={16} />
        </button>
      </div>

      {/* Body */}
      <div className="flex-1 overflow-y-auto p-4">
        {painel.tipo === 'grupo' && (
          <FormGrupo key={painel.data.id} grupo={painel.data} isReadOnly={isReadOnly} />
        )}
        {painel.tipo === 'item' && (
          <FormItem key={painel.data.id} item={painel.data} isReadOnly={isReadOnly} />
        )}
      </div>
    </div>
  )
}
