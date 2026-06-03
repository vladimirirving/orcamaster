import { useState, useEffect } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ReferenceLine, ResponsiveContainer,
} from 'recharts'
import { getObraDashboard } from '@/api/dashboard'
import { fmtMesLabel } from '@/lib/utils'
import { toast } from '@/hooks/useToast'
import type { ObraDashboardData } from '@/types'

interface Props {
  obraId: number
}

export default function ObraDashboard({ obraId }: Props) {
  const [data, setData] = useState<ObraDashboardData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getObraDashboard(obraId)
      .then(setData)
      .catch(() => toast('Erro ao carregar dashboard', 'error'))
      .finally(() => setLoading(false))
  }, [obraId])

  if (loading) {
    return <div className="p-6 text-gray-400 text-sm">Carregando...</div>
  }

  if (!data || data.status === 'sem_dados') {
    return (
      <div className="p-6 text-center text-gray-400 text-sm py-12">
        Versão ativa sem cronograma configurado ou sem medições registradas
      </div>
    )
  }

  const mesAtual = new Date().toISOString().slice(0, 7)
  const temHoje = data.curva_s.some(p => p.mes === mesAtual)

  return (
    <div className="p-6 space-y-6">
      {/* KPI Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-xl p-4 text-center">
          <div className="text-xs text-gray-500 mb-1">Planejado hoje</div>
          <div className="text-3xl font-bold text-blue-600">
            {data.planejado_pct_hoje?.toFixed(1)}%
          </div>
        </div>
        <div className="bg-green-50 rounded-xl p-4 text-center">
          <div className="text-xs text-gray-500 mb-1">Realizado</div>
          <div className="text-3xl font-bold text-green-600">
            {data.realizado_pct?.toFixed(1)}%
          </div>
        </div>
        <div className={`rounded-xl p-4 text-center ${(data.desvio ?? 0) >= 0 ? 'bg-green-50' : 'bg-red-50'}`}>
          <div className="text-xs text-gray-500 mb-1">Desvio</div>
          <div className={`text-3xl font-bold ${(data.desvio ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            {(data.desvio ?? 0) >= 0 ? '+' : ''}{data.desvio?.toFixed(1)}pp
          </div>
        </div>
      </div>

      {/* Curva S */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="text-sm font-medium text-gray-700 mb-4">Curva S — Planejado × Realizado</div>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data.curva_s} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
            <XAxis
              dataKey="mes"
              tickFormatter={fmtMesLabel}
              tick={{ fontSize: 11, fill: '#64748b' }}
            />
            <YAxis
              domain={[0, 100]}
              tickFormatter={(v: number) => `${v}%`}
              tick={{ fontSize: 11, fill: '#64748b' }}
              width={42}
            />
            <Tooltip
              formatter={(value, name: string) => [
                typeof value === 'number' ? `${value.toFixed(1)}%` : '—',
                name === 'planejado_acum' ? 'Planejado' : 'Realizado',
              ]}
              labelFormatter={(label: string) => fmtMesLabel(label)}
            />
            <Legend
              formatter={(name: string) =>
                name === 'planejado_acum' ? 'Planejado' : 'Realizado'
              }
            />
            {temHoje && (
              <ReferenceLine
                x={mesAtual}
                stroke="#94a3b8"
                strokeDasharray="3 3"
                label={{ value: 'hoje', position: 'top', fontSize: 10, fill: '#94a3b8' }}
              />
            )}
            <Line
              type="monotone"
              dataKey="planejado_acum"
              name="planejado_acum"
              stroke="#3b82f6"
              strokeDasharray="5 3"
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="realizado_acum"
              name="realizado_acum"
              stroke="#10b981"
              dot={{ r: 3, fill: '#10b981' }}
              connectNulls={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
