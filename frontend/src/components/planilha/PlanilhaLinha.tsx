import { ChevronRight, ChevronDown, AlertTriangle, Plus } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { Grupo, Item } from '@/types'

interface Props {
  tipo: 'grupo-raiz' | 'subgrupo' | 'item'
  grupo?: Grupo
  item?: Item
  aberto?: boolean
  selecionado?: boolean
  isReadOnly: boolean
  onToggle?: () => void
  onSelect: () => void
  onAddItem?: () => void
  onAddSubgrupo?: () => void
}

export default function PlanilhaLinha({
  tipo, grupo, item, aberto, selecionado, isReadOnly,
  onToggle, onSelect, onAddItem, onAddSubgrupo,
}: Props) {
  const isGrupo = tipo !== 'item'
  const indent = tipo === 'subgrupo' ? 'pl-6' : tipo === 'item' ? 'pl-12' : 'pl-2'

  return (
    <div
      onClick={onSelect}
      className={cn(
        'flex items-center gap-2 px-3 py-2 cursor-pointer select-none border-b border-gray-100 last:border-0',
        isGrupo ? 'bg-gray-50 font-semibold text-gray-800' : 'text-gray-700',
        selecionado ? 'bg-blue-50 border-l-2 border-l-blue-500' : 'hover:bg-gray-50',
        indent,
      )}
    >
      {/* Toggle collapse (grupos only) */}
      {isGrupo && (
        <button
          onClick={(e) => { e.stopPropagation(); onToggle?.() }}
          className="text-gray-400 hover:text-gray-600 flex-shrink-0"
        >
          {aberto ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </button>
      )}

      {/* Código */}
      <span className="w-16 text-xs text-gray-400 flex-shrink-0">
        {isGrupo ? grupo!.codigo : ''}
      </span>

      {/* Descrição */}
      <span className="flex-1 text-sm truncate">
        {isGrupo ? grupo!.nome : item!.unidade ? `${item!.unidade} — ` + (item!.etiqueta_revisao ?? '') : '—'}
        {!isGrupo && item && (
          <span className="ml-1">
            {item.requer_revisao && (
              <AlertTriangle size={12} className="inline text-yellow-500 ml-1" />
            )}
          </span>
        )}
      </span>

      {/* Colunas numéricas (item only) */}
      {!isGrupo && item && (
        <>
          <span className="w-8 text-xs text-gray-500 text-right">{item.unidade ?? ''}</span>
          <span className="w-20 text-xs text-right text-gray-700">
            {parseFloat(item.quantidade).toLocaleString('pt-BR')}
          </span>
          <span className="w-24 text-xs text-right text-gray-700">
            {item.preco_unitario_sem_bdi
              ? parseFloat(item.preco_unitario_sem_bdi).toLocaleString('pt-BR', { minimumFractionDigits: 2 })
              : '—'}
          </span>
          <span className="w-28 text-xs text-right font-medium text-gray-800">
            {parseFloat(item.total).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}
          </span>
        </>
      )}

      {/* Inline action buttons (grupos only, not readonly) */}
      {isGrupo && !isReadOnly && (
        <div className="flex items-center gap-1 ml-auto" onClick={e => e.stopPropagation()}>
          {tipo === 'grupo-raiz' && (
            <button
              onClick={onAddSubgrupo}
              title="Adicionar subgrupo"
              className="text-xs text-gray-400 hover:text-blue-600 px-1 py-0.5 rounded hover:bg-blue-50"
            >
              + Sub
            </button>
          )}
          <button
            onClick={onAddItem}
            title="Adicionar item"
            className="text-xs text-gray-400 hover:text-blue-600 px-1 py-0.5 rounded hover:bg-blue-50"
          >
            <Plus size={12} className="inline" /> Item
          </button>
        </div>
      )}
    </div>
  )
}
