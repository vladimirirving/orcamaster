// frontend/src/components/planilha/MedicaoGrade.tsx
import { useState, useRef, useEffect } from 'react'
import { CheckCircle, AlertTriangle } from 'lucide-react'
import { patchMedicao } from '@/api/medicoes'
import { fmtBRL } from '@/lib/utils'
import { toast } from '@/hooks/useToast'
import type { MedicaoData, CronogramaData } from '@/types'

interface Props {
  versaoId: number
  medicao: MedicaoData
  antMedicao: MedicaoData | null
  cronogramaData: CronogramaData | null
  isReadOnly: boolean
  onLinhasUpdated: (linhas_json: Record<string, number>) => void
}

export default function MedicaoGrade({
  versaoId, medicao, antMedicao, cronogramaData, isReadOnly, onLinhasUpdated
}: Props) {
  const items = cronogramaData?.linhas ?? []
  const selectedMes = medicao.periodo_inicio.slice(0, 7)
  const showPlanCol = !!(cronogramaData?.cronograma_inicio)

  const [localLinhas, setLocalLinhas] = useState<Record<string, number>>(
    () => ({ ...medicao.linhas_json })
  )
  const localLinhasRef = useRef(localLinhas)
  localLinhasRef.current = localLinhas

  const [saving, setSaving] = useState(false)
  const saveTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (saveTimer.current) clearTimeout(saveTimer.current)
    setLocalLinhas({ ...medicao.linhas_json })
  }, [medicao.id])

  useEffect(() => {
    return () => { if (saveTimer.current) clearTimeout(saveTimer.current) }
  }, [])

  function scheduleSave() {
    if (saveTimer.current) clearTimeout(saveTimer.current)
    saveTimer.current = setTimeout(async () => {
      setSaving(true)
      try {
        await patchMedicao(versaoId, medicao.id, localLinhasRef.current)
        onLinhasUpdated(localLinhasRef.current)
      } catch {
        toast('Erro ao salvar medição', 'error')
      } finally {
        setSaving(false)
      }
    }, 300)
  }

  function handleChange(itemId: number, value: string) {
    const num = parseFloat(value) || 0
    setLocalLinhas(prev => ({ ...prev, [String(itemId)]: num }))
  }

  function handleBlur() {
    scheduleSave()
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>, rowIdx: number) {
    if (e.key === 'Enter') {
      e.preventDefault()
      const nextRow = rowIdx + (e.shiftKey ? -1 : 1)
      if (nextRow >= 0 && nextRow < items.length) {
        document.querySelector<HTMLInputElement>(`[data-row="${nextRow}"]`)?.focus()
      }
    }
  }

  function getPlanPct(itemId: number): number {
    const linha = cronogramaData?.linhas.find(l => l.item_id === itemId)
    if (!linha) return 0
    return Object.entries(linha.distribuicao_json)
      .filter(([mes]) => mes <= selectedMes)
      .reduce((sum, [, pct]) => sum + pct, 0)
  }

  function getAntPct(itemId: number): number {
    if (!antMedicao) return 0
    return antMedicao.linhas_json[String(itemId)] ?? 0
  }

  function getAtualPct(itemId: number): number {
    return localLinhas[String(itemId)] ?? 0
  }

  // Footer totals
  let periodoRS = 0
  let acumuladoRS = 0
  let acumuladoBase = 0
  for (const item of items) {
    const totalSemBdi = parseFloat(item.total_sem_bdi) || 0
    const atualPct = getAtualPct(item.item_id)
    const antPct = getAntPct(item.item_id)
    periodoRS += ((atualPct - antPct) / 100) * totalSemBdi
    acumuladoRS += (atualPct / 100) * totalSemBdi
    acumuladoBase += totalSemBdi
  }
  const acumuladoPct = acumuladoBase > 0 ? (acumuladoRS / acumuladoBase) * 100 : 0

  // colSpan: label spans all columns except Valor R$
  const labelSpan = showPlanCol ? 5 : 4

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      <div className="flex-1 overflow-auto mt-2">
        <table className="border-collapse text-xs w-full">
          <thead>
            <tr className="bg-gray-50 sticky top-0 z-10">
              <th className="text-left px-3 py-2 font-medium text-gray-600 border-b border-gray-200 sticky left-0 bg-gray-50 min-w-64">
                Serviço
              </th>
              {showPlanCol && (
                <th className="text-center px-3 py-2 font-medium text-gray-600 border-b border-gray-200 min-w-20">
                  Plan. %
                </th>
              )}
              <th className="text-center px-3 py-2 font-medium text-gray-600 border-b border-gray-200 min-w-20">
                Ant. %
              </th>
              <th className="text-center px-3 py-2 font-medium text-blue-600 border-b border-blue-200 bg-blue-50 min-w-20">
                Atual %
              </th>
              <th className="text-center px-3 py-2 font-medium text-gray-600 border-b border-gray-200 min-w-16">
                Δ %
              </th>
              <th className="text-right px-3 py-2 font-medium text-gray-600 border-b border-gray-200 min-w-28">
                Valor R$
              </th>
            </tr>
          </thead>

          <tbody>
            {items.map((item, rowIdx) => {
              const atualPct = getAtualPct(item.item_id)
              const antPct = getAntPct(item.item_id)
              const planPct = showPlanCol ? getPlanPct(item.item_id) : 0
              const deltaPct = atualPct - antPct
              const totalSemBdi = parseFloat(item.total_sem_bdi) || 0
              const valorRS = (atualPct / 100) * totalSemBdi
              const over100 = atualPct > 100

              return (
                <tr key={item.item_id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="px-3 py-1.5 sticky left-0 bg-white hover:bg-gray-50 min-w-64 max-w-64">
                    <div className="flex items-center gap-1.5">
                      {over100
                        ? <AlertTriangle size={12} className="text-red-400 shrink-0" />
                        : <CheckCircle size={12} className="text-green-500 shrink-0" />
                      }
                      <span className="truncate text-gray-800">
                        {item.descricao || <span className="text-gray-400">—</span>}
                      </span>
                      {saving && <span className="text-gray-300 text-xs ml-1">●</span>}
                    </div>
                    <div className="text-gray-400 text-xs ml-5">{fmtBRL(item.total_sem_bdi)}</div>
                  </td>
                  {showPlanCol && (
                    <td className="px-3 py-1.5 text-center text-gray-500 min-w-20">
                      {planPct > 0 ? `${planPct.toFixed(1)}%` : '—'}
                    </td>
                  )}
                  <td className="px-3 py-1.5 text-center text-gray-500 min-w-20">
                    {antPct > 0 ? `${antPct.toFixed(1)}%` : '—'}
                  </td>
                  <td className="px-1 py-0.5 bg-blue-50 min-w-20">
                    {isReadOnly ? (
                      <span className="block text-center text-gray-700">
                        {atualPct > 0 ? `${atualPct}%` : '—'}
                      </span>
                    ) : (
                      <input
                        type="number"
                        min={0}
                        max={100}
                        step={0.01}
                        value={atualPct || ''}
                        disabled={saving}
                        data-row={rowIdx}
                        onChange={e => handleChange(item.item_id, e.target.value)}
                        onBlur={handleBlur}
                        onKeyDown={e => handleKeyDown(e, rowIdx)}
                        placeholder="0"
                        className="w-full text-center bg-transparent text-gray-800 placeholder-gray-300 focus:outline-none focus:bg-white focus:ring-1 focus:ring-blue-400 rounded px-1 py-1 disabled:opacity-40"
                      />
                    )}
                  </td>
                  <td className={`px-3 py-1.5 text-center min-w-16 font-medium ${
                    deltaPct > 0 ? 'text-green-600' : deltaPct < 0 ? 'text-red-500' : 'text-gray-400'
                  }`}>
                    {deltaPct !== 0 ? `${deltaPct > 0 ? '+' : ''}${deltaPct.toFixed(1)}` : '—'}
                  </td>
                  <td className="px-3 py-1.5 text-right text-gray-700 min-w-28">
                    {valorRS > 0 ? fmtBRL(String(valorRS.toFixed(2))) : '—'}
                  </td>
                </tr>
              )
            })}
          </tbody>

          <tfoot className="sticky bottom-0">
            <tr className="bg-slate-800 text-slate-200">
              <td colSpan={labelSpan} className="px-3 py-1.5 font-medium text-xs sticky left-0 bg-slate-800">
                Período R$
              </td>
              <td className="px-3 py-1.5 text-right text-xs font-semibold">
                {fmtBRL(String(periodoRS.toFixed(2)))}
              </td>
            </tr>
            <tr className="bg-slate-900 text-blue-300 font-semibold">
              <td colSpan={labelSpan} className="px-3 py-1.5 text-xs sticky left-0 bg-slate-900">
                Acumulado R$
              </td>
              <td className="px-3 py-1.5 text-right text-xs">
                {fmtBRL(String(acumuladoRS.toFixed(2)))}
                <span className="text-slate-400 ml-2">{acumuladoPct.toFixed(1)}%</span>
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}
