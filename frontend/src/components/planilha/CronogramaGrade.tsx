import { useState, useRef } from 'react'
import { CheckCircle, AlertTriangle } from 'lucide-react'
import { patchCronogramaLinha } from '@/api/cronograma'
import { fmtBRL } from '@/lib/utils'
import type { CronogramaData } from '@/types'

interface Props {
  versaoId: number
  data: CronogramaData
  totalSemBdi: number
  isReadOnly: boolean
  onLinhaUpdated: (itemId: number, distribuicao_json: Record<string, number>) => void
}

function getMeses(inicio: string, fim: string): string[] {
  const meses: string[] = []
  const [sy, sm] = inicio.split('-').map(Number)
  const [ey, em] = fim.split('-').map(Number)
  let y = sy, m = sm
  while (y < ey || (y === ey && m <= em)) {
    meses.push(`${y}-${String(m).padStart(2, '0')}`)
    m++
    if (m > 12) { m = 1; y++ }
  }
  return meses
}

function fmtMesLabel(mes: string): string {
  const [y, m] = mes.split('-')
  const labels = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
  return `${labels[parseInt(m) - 1]}/${y.slice(2)}`
}

function somaPercentual(dist: Record<string, number>): number {
  return Object.values(dist).reduce((a, b) => a + b, 0)
}

export default function CronogramaGrade({ versaoId, data, totalSemBdi, isReadOnly, onLinhaUpdated }: Props) {
  const meses = getMeses(data.cronograma_inicio!, data.cronograma_fim!)

  const [localDist, setLocalDist] = useState<Record<number, Record<string, number>>>(
    () => Object.fromEntries(data.linhas.map(l => [l.item_id, { ...l.distribuicao_json }]))
  )
  const localDistRef = useRef(localDist)
  localDistRef.current = localDist

  const [saving, setSaving] = useState<Record<number, boolean>>({})
  const saveTimers = useRef<Record<number, ReturnType<typeof setTimeout>>>({})

  function scheduleSave(itemId: number) {
    if (saveTimers.current[itemId]) clearTimeout(saveTimers.current[itemId])
    saveTimers.current[itemId] = setTimeout(async () => {
      const dist = localDistRef.current[itemId]
      setSaving(s => ({ ...s, [itemId]: true }))
      try {
        await patchCronogramaLinha(versaoId, itemId, dist)
        onLinhaUpdated(itemId, dist)
      } catch {
        // silent fail — user sees no change in UI
      } finally {
        setSaving(s => ({ ...s, [itemId]: false }))
      }
    }, 300)
  }

  function handleChange(itemId: number, mes: string, value: string) {
    const num = parseFloat(value) || 0
    setLocalDist(prev => ({
      ...prev,
      [itemId]: { ...prev[itemId], [mes]: num },
    }))
  }

  function handleBlur(itemId: number) {
    scheduleSave(itemId)
  }

  function handleKeyDown(
    e: React.KeyboardEvent<HTMLInputElement>,
    rowIdx: number,
    colIdx: number
  ) {
    if (e.key === 'Tab') {
      e.preventDefault()
      const nextCol = colIdx + (e.shiftKey ? -1 : 1)
      if (nextCol >= 0 && nextCol < meses.length) {
        document.querySelector<HTMLInputElement>(
          `[data-row="${rowIdx}"][data-col="${nextCol}"]`
        )?.focus()
      }
    }
    if (e.key === 'Enter') {
      e.preventDefault()
      const nextRow = rowIdx + (e.shiftKey ? -1 : 1)
      if (nextRow >= 0 && nextRow < data.linhas.length) {
        document.querySelector<HTMLInputElement>(
          `[data-row="${nextRow}"][data-col="${colIdx}"]`
        )?.focus()
      }
    }
  }

  // Footer calculations
  const totalMensal: Record<string, number> = {}
  for (const mes of meses) {
    totalMensal[mes] = data.linhas.reduce((sum, linha) => {
      const pct = localDist[linha.item_id]?.[mes] ?? 0
      return sum + parseFloat(linha.total_sem_bdi) * pct / 100
    }, 0)
  }

  let acumulado = 0
  const acumuladoRS: Record<string, number> = {}
  const acumuladoPct: Record<string, number> = {}
  for (const mes of meses) {
    acumulado += totalMensal[mes]
    acumuladoRS[mes] = acumulado
    acumuladoPct[mes] = totalSemBdi > 0 ? (acumulado / totalSemBdi) * 100 : 0
  }

  const incompletos = data.linhas.filter(l => {
    const soma = somaPercentual(localDist[l.item_id] ?? {})
    return Math.abs(soma - 100) > 0.01
  }).length

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {incompletos > 0 && (
        <div className="mx-4 mt-3 px-3 py-2 bg-yellow-50 border border-yellow-200 rounded-lg text-xs text-yellow-700 shrink-0">
          {incompletos} {incompletos === 1 ? 'item sem' : 'itens sem'} distribuição completa (soma ≠ 100%)
        </div>
      )}

      <div className="flex-1 overflow-auto mt-2">
        <table className="border-collapse text-xs" style={{ minWidth: 'max-content' }}>
          <thead>
            <tr className="bg-gray-50 sticky top-0 z-10">
              <th className="text-left px-3 py-2 font-medium text-gray-600 border-b border-gray-200 sticky left-0 bg-gray-50 min-w-64">
                Serviço
              </th>
              <th className="text-right px-3 py-2 font-medium text-gray-600 border-b border-gray-200 sticky left-64 bg-gray-50 min-w-28">
                Total S/BDI
              </th>
              {meses.map(mes => (
                <th key={mes} className="text-center px-2 py-2 font-medium text-gray-600 border-b border-gray-200 min-w-16">
                  {fmtMesLabel(mes)}
                </th>
              ))}
            </tr>
          </thead>

          <tbody>
            {data.linhas.map((linha, rowIdx) => {
              const dist = localDist[linha.item_id] ?? {}
              const soma = somaPercentual(dist)
              const valida = Math.abs(soma - 100) <= 0.01
              const isSaving = saving[linha.item_id]

              return (
                <tr key={linha.item_id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-3 py-1.5 sticky left-0 bg-white hover:bg-gray-50 min-w-64 max-w-64">
                    <div className="flex items-center gap-1.5">
                      {valida
                        ? <CheckCircle size={12} className="text-green-500 shrink-0" />
                        : <AlertTriangle size={12} className="text-red-400 shrink-0" />
                      }
                      <span className="truncate text-gray-800">
                        {linha.descricao || <span className="text-gray-400">—</span>}
                      </span>
                      {isSaving && <span className="text-gray-300 text-xs ml-1">●</span>}
                    </div>
                  </td>
                  <td className="px-3 py-1.5 text-right text-gray-600 sticky left-64 bg-white hover:bg-gray-50 min-w-28">
                    {fmtBRL(linha.total_sem_bdi)}
                  </td>
                  {meses.map((mes, colIdx) => {
                    const val = dist[mes] ?? 0
                    return (
                      <td
                        key={mes}
                        className={`px-1 py-0.5 text-center min-w-16 ${val > 0 ? 'bg-blue-50' : ''}`}
                      >
                        {isReadOnly ? (
                          <span className="text-gray-700">{val > 0 ? `${val}%` : ''}</span>
                        ) : (
                          <input
                            type="number"
                            min={0}
                            max={100}
                            step={0.01}
                            value={val || ''}
                            disabled={isSaving}
                            data-row={rowIdx}
                            data-col={colIdx}
                            onChange={e => handleChange(linha.item_id, mes, e.target.value)}
                            onBlur={() => handleBlur(linha.item_id)}
                            onKeyDown={e => handleKeyDown(e, rowIdx, colIdx)}
                            placeholder="—"
                            className="w-full text-center bg-transparent text-gray-800 placeholder-gray-300 focus:outline-none focus:bg-white focus:ring-1 focus:ring-blue-400 rounded px-1 py-0.5 disabled:opacity-40"
                          />
                        )}
                      </td>
                    )
                  })}
                </tr>
              )
            })}
          </tbody>

          <tfoot className="sticky bottom-0">
            <tr className="bg-slate-800 text-slate-200">
              <td colSpan={2} className="px-3 py-1.5 font-medium text-xs sticky left-0 bg-slate-800">
                Total R$
              </td>
              {meses.map(mes => (
                <td key={mes} className="px-2 py-1.5 text-center text-xs">
                  {totalMensal[mes] > 0 ? fmtBRL(String(totalMensal[mes].toFixed(2))) : '—'}
                </td>
              ))}
            </tr>
            <tr className="bg-slate-700 text-slate-200">
              <td colSpan={2} className="px-3 py-1.5 font-medium text-xs sticky left-0 bg-slate-700">
                Acumulado R$
              </td>
              {meses.map(mes => (
                <td key={mes} className="px-2 py-1.5 text-center text-xs">
                  {acumuladoRS[mes] > 0 ? fmtBRL(String(acumuladoRS[mes].toFixed(2))) : '—'}
                </td>
              ))}
            </tr>
            <tr className="bg-slate-900 text-blue-300 font-semibold">
              <td colSpan={2} className="px-3 py-1.5 text-xs sticky left-0 bg-slate-900">
                Acumulado %
              </td>
              {meses.map(mes => (
                <td key={mes} className="px-2 py-1.5 text-center text-xs">
                  {acumuladoPct[mes] > 0 ? `${acumuladoPct[mes].toFixed(1)}%` : '—'}
                </td>
              ))}
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}
