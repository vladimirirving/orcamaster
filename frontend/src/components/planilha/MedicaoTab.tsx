// frontend/src/components/planilha/MedicaoTab.tsx
import { useState, useEffect } from 'react'
import { getCronograma } from '@/api/cronograma'
import { getMedicoes, postMedicao } from '@/api/medicoes'
import type { CronogramaData, MedicaoData } from '@/types'
import { toast } from '@/hooks/useToast'
import MedicaoGrade from './MedicaoGrade'

interface Props {
  versaoId: number
  isReadOnly: boolean
}

function fmtMedicaoLabel(m: MedicaoData): string {
  const [y, month] = m.periodo_inicio.split('-')
  const labels = ['Jan','Fev','Mar','Abr','Mai','Jun','Jul','Ago','Set','Out','Nov','Dez']
  return `${labels[parseInt(month) - 1]}/${y}`
}

export default function MedicaoTab({ versaoId, isReadOnly }: Props) {
  const [cronogramaData, setCronogramaData] = useState<CronogramaData | null>(null)
  const [medicoes, setMedicoes] = useState<MedicaoData[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [loading, setLoading] = useState(true)
  const [showModal, setShowModal] = useState(false)
  const [novaMes, setNovaMes] = useState('')
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    Promise.all([getCronograma(versaoId), getMedicoes(versaoId)])
      .then(([crono, meds]) => {
        setCronogramaData(crono)
        setMedicoes(meds)
        if (meds.length > 0) setSelectedId(meds[0].id)
      })
      .finally(() => setLoading(false))
  }, [versaoId])

  async function handleNovaMedicao() {
    if (!novaMes) return
    const exists = medicoes.some(m => m.periodo_inicio.slice(0, 7) === novaMes)
    if (exists) {
      toast('Já existe uma medição para este mês', 'error')
      return
    }
    setCreating(true)
    try {
      const nova = await postMedicao(versaoId, novaMes)
      setMedicoes(prev => [nova, ...prev])
      setSelectedId(nova.id)
      setShowModal(false)
      setNovaMes('')
    } catch {
      toast('Erro ao criar medição', 'error')
    } finally {
      setCreating(false)
    }
  }

  function handleLinhasUpdated(linhas_json: Record<string, number>) {
    setMedicoes(prev => prev.map(m =>
      m.id === selectedId ? { ...m, linhas_json } : m
    ))
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
        Carregando medições...
      </div>
    )
  }

  // Sorted descending: selectedIdx+1 is the immediately previous measurement
  const selectedMedicao = medicoes.find(m => m.id === selectedId) ?? null
  const selectedIdx = medicoes.findIndex(m => m.id === selectedId)
  const antMedicao = selectedIdx >= 0 && selectedIdx + 1 < medicoes.length
    ? medicoes[selectedIdx + 1]
    : null

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center gap-3 px-4 py-2 border-b border-gray-100 bg-white shrink-0">
        {medicoes.length > 0 && (
          <select
            value={selectedId ?? ''}
            onChange={e => setSelectedId(Number(e.target.value))}
            className="border border-gray-200 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            {medicoes.map(m => (
              <option key={m.id} value={m.id}>{fmtMedicaoLabel(m)}</option>
            ))}
          </select>
        )}
        {!isReadOnly && (
          <button
            onClick={() => setShowModal(true)}
            className="bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-blue-700"
          >
            Nova Medição
          </button>
        )}
      </div>

      {/* Empty state */}
      {medicoes.length === 0 && (
        <div className="flex-1 flex flex-col items-center justify-center gap-2 text-gray-400">
          <p className="text-sm">Nenhuma medição registrada</p>
        </div>
      )}

      {/* Grade */}
      {selectedMedicao && (
        <MedicaoGrade
          versaoId={versaoId}
          medicao={selectedMedicao}
          antMedicao={antMedicao}
          cronogramaData={cronogramaData}
          isReadOnly={isReadOnly}
          onLinhasUpdated={handleLinhasUpdated}
        />
      )}

      {/* Nova Medição Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-lg p-6 w-80">
            <h3 className="text-base font-semibold text-gray-900 mb-4">Nova Medição</h3>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              Mês de referência
            </label>
            <input
              type="month"
              value={novaMes}
              onChange={e => setNovaMes(e.target.value)}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 mb-4"
            />
            <div className="flex justify-end gap-2">
              <button
                onClick={() => { setShowModal(false); setNovaMes('') }}
                className="px-3 py-1.5 text-sm text-gray-600 hover:text-gray-900 border border-gray-200 rounded-lg"
              >
                Cancelar
              </button>
              <button
                onClick={handleNovaMedicao}
                disabled={!novaMes || creating}
                className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {creating ? 'Criando...' : 'Criar'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
