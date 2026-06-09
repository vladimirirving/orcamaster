import { useState, useEffect } from 'react'
import { getDashboard } from '@/api/dashboard'
import { toast } from '@/hooks/useToast'
import type { DashboardResumoItem } from '@/types'
import EmpresaView from '@/components/dashboard/EmpresaView'
import ObraView from '@/components/dashboard/ObraView'

type Visao = 'empresa' | 'obra'

export default function DashboardPage() {
  const [visao, setVisao] = useState<Visao>('empresa')
  const [items, setItems] = useState<DashboardResumoItem[]>([])
  const [loading, setLoading] = useState(true)
  const [obraId, setObraId] = useState<number | null>(null)

  useEffect(() => {
    getDashboard()
      .then(data => {
        setItems(data)
        if (data.length > 0) setObraId(data[0].obra_id)
      })
      .catch(() => toast('Erro ao carregar dashboard', 'error'))
      .finally(() => setLoading(false))
  }, [])

  function handleSelectObra(id: number) {
    setObraId(id)
    setVisao('obra')
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header com toggle */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        <div className="flex items-center gap-3">
          {/* Seletor de obra (só Visão Obra) */}
          {visao === 'obra' && items.length > 0 && (
            <select
              value={obraId ?? ''}
              onChange={e => setObraId(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 max-w-xs"
            >
              {items.map(i => (
                <option key={i.obra_id} value={i.obra_id}>{i.obra_nome}</option>
              ))}
            </select>
          )}
          {/* Toggle pill */}
          <div className="flex bg-gray-100 rounded-lg p-1 gap-1">
            <button
              onClick={() => setVisao('empresa')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                visao === 'empresa'
                  ? 'bg-white shadow-sm text-gray-900'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              🏢 Empresa
            </button>
            <button
              onClick={() => setVisao('obra')}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-all ${
                visao === 'obra'
                  ? 'bg-white shadow-sm text-gray-900'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              🏗️ Obra
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-gray-400 text-sm text-center py-12">Carregando…</div>
      ) : (
        <>
          {visao === 'empresa' && (
            <EmpresaView items={items} onSelectObra={handleSelectObra} />
          )}
          {visao === 'obra' && obraId && (
            <ObraView obraId={obraId} />
          )}
          {visao === 'obra' && !obraId && (
            <p className="text-gray-400 text-sm text-center py-12">Nenhuma obra cadastrada.</p>
          )}
        </>
      )}
    </div>
  )
}
