import { useState, useEffect, useRef } from 'react'
import { Search } from 'lucide-react'
import { searchComposicoes } from '@/api/composicoes'
import { vincularComposicao } from '@/api/itens'
import { useOrcamento } from '@/stores/orcamento'
import { toast } from '@/hooks/useToast'
import type { Composicao, Item } from '@/types'

export default function BuscaComposicao({ item }: { item: Item }) {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<Composicao[]>([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const { updateItemNoStore } = useOrcamento()
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (!query.trim()) { setResults([]); setOpen(false); return }
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(async () => {
      setLoading(true)
      try {
        const data = await searchComposicoes(query)
        setResults(data)
        setOpen(true)
      } finally {
        setLoading(false)
      }
    }, 300)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [query])

  async function handleSelect(comp: Composicao) {
    try {
      const updated = await vincularComposicao(item.id, comp.id)
      updateItemNoStore(updated)
      setQuery('')
      setResults([])
      setOpen(false)
      toast(`Composição vinculada: ${comp.codigo}`)
    } catch {
      toast('Erro ao vincular composição', 'error')
    }
  }

  const origemBadge = (origem: string) => {
    const map: Record<string, string> = {
      sinapi: 'bg-blue-100 text-blue-700',
      sicro: 'bg-purple-100 text-purple-700',
      propria: 'bg-green-100 text-green-700'
    }
    return map[origem] ?? 'bg-gray-100 text-gray-600'
  }

  return (
    <div className="relative">
      <label className="block text-xs font-medium text-gray-500 mb-1">Buscar composição</label>
      <div className="relative">
        <Search size={14} className="absolute left-3 top-2.5 text-gray-400" />
        <input
          value={query}
          onChange={e => setQuery(e.target.value)}
          placeholder="Código ou descrição..."
          className="w-full border border-gray-200 rounded-lg pl-8 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {loading && <span className="absolute right-3 top-2.5 text-xs text-gray-400">...</span>}
      </div>

      {open && results.length > 0 && (
        <div className="absolute z-10 w-full bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto mt-1">
          {results.map(comp => (
            <button
              key={comp.id}
              type="button"
              onClick={() => handleSelect(comp)}
              className="w-full text-left px-3 py-2 hover:bg-blue-50 border-b border-gray-100 last:border-0"
            >
              <div className="flex items-center gap-2">
                <span className={`text-xs px-1.5 py-0.5 rounded font-medium ${origemBadge(comp.origem)}`}>
                  {comp.origem.toUpperCase()}
                </span>
                <span className="text-xs font-mono text-gray-600">{comp.codigo}</span>
              </div>
              <p className="text-xs text-gray-700 truncate mt-0.5">{comp.descricao}</p>
              <p className="text-xs text-gray-400">{comp.unidade} · R$ {parseFloat(comp.preco_unitario).toFixed(2)}</p>
            </button>
          ))}
        </div>
      )}

      {open && results.length === 0 && !loading && (
        <div className="absolute z-10 w-full bg-white border border-gray-200 rounded-lg shadow-lg px-3 py-2 mt-1 text-xs text-gray-400">
          Nenhuma composição encontrada
        </div>
      )}

      {item.composicao_id && (
        <p className="text-xs text-gray-400 mt-1">Composição atual: #{item.composicao_id}</p>
      )}
    </div>
  )
}
