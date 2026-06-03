import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getDashboard } from '@/api/dashboard'
import { fmtBRL } from '@/lib/utils'
import type { DashboardResumoItem } from '@/types'

const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string }> = {
  adiantado: { label: 'Adiantado', bg: 'bg-green-100', text: 'text-green-700' },
  no_prazo:  { label: 'No prazo',  bg: 'bg-blue-100',  text: 'text-blue-700'  },
  atrasado:  { label: 'Atrasado',  bg: 'bg-yellow-100', text: 'text-yellow-700' },
  sem_dados: { label: 'Sem dados', bg: 'bg-gray-100',  text: 'text-gray-400'  },
}

export default function DashboardPage() {
  const [items, setItems] = useState<DashboardResumoItem[]>([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    getDashboard()
      .then(setItems)
      .finally(() => setLoading(false))
  }, [])

  if (loading) {
    return <div className="p-8 text-gray-400 text-sm">Carregando...</div>
  }

  return (
    <div className="p-8 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

      {items.length === 0 && (
        <p className="text-gray-400 text-center py-12">Nenhuma obra cadastrada</p>
      )}

      {items.length > 0 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-5 py-3 font-medium text-gray-600">Obra</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600 w-32">Planejado %</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600 w-32">Realizado %</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600 w-28">Desvio</th>
                <th className="text-center px-4 py-3 font-medium text-gray-600 w-28">Status</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, idx) => {
                const cfg = STATUS_CONFIG[item.status] ?? STATUS_CONFIG.sem_dados
                const semDados = item.status === 'sem_dados'
                return (
                  <tr
                    key={item.obra_id}
                    onClick={() => navigate(`/obras/${item.obra_id}`)}
                    className={`cursor-pointer hover:bg-gray-50 transition-colors ${
                      idx < items.length - 1 ? 'border-b border-gray-100' : ''
                    }`}
                  >
                    <td className="px-5 py-3">
                      <div className="font-medium text-gray-900">{item.obra_nome}</div>
                      {item.total_sem_bdi && (
                        <div className="text-xs text-gray-400 mt-0.5">
                          {fmtBRL(item.total_sem_bdi)}
                        </div>
                      )}
                    </td>
                    <td className="px-4 py-3 text-right text-gray-500">
                      {semDados ? '—' : `${item.planejado_pct_hoje?.toFixed(1)}%`}
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-blue-600">
                      {semDados ? '—' : `${item.realizado_pct?.toFixed(1)}%`}
                    </td>
                    <td className={`px-4 py-3 text-right font-medium ${
                      semDados ? 'text-gray-400'
                      : (item.desvio ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {semDados
                        ? '—'
                        : `${(item.desvio ?? 0) >= 0 ? '+' : ''}${item.desvio?.toFixed(1)}pp`
                      }
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${cfg.bg} ${cfg.text}`}>
                        {cfg.label}
                      </span>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
