import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ReferenceLine, ResponsiveContainer,
} from 'recharts'
import { fmtMesLabel } from '@/lib/utils'
import type { CurvaSPonto } from '@/types'

interface Props {
  data: CurvaSPonto[]
}

export default function CurvaSChart({ data }: Props) {
  if (data.length === 0) {
    return (
      <p className="text-gray-400 text-sm text-center py-8">
        Sem dados de cronograma para exibir a Curva S.
      </p>
    )
  }

  const mesAtual = new Date().toISOString().slice(0, 7)
  const temHoje = data.some(p => p.mes === mesAtual)

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
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
  )
}
