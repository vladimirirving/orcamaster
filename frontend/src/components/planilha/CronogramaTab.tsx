import { useState, useEffect } from 'react'
import { getCronograma } from '@/api/cronograma'
import type { CronogramaData } from '@/types'
import { useOrcamento } from '@/stores/orcamento'
import CronogramaConfigForm from './CronogramaConfigForm'
import CronogramaGrade from './CronogramaGrade'

interface Props {
  versaoId: number
  isReadOnly: boolean
}

export default function CronogramaTab({ versaoId, isReadOnly }: Props) {
  const { versao } = useOrcamento()
  const [data, setData] = useState<CronogramaData | null>(null)
  const [loading, setLoading] = useState(true)
  const [showConfig, setShowConfig] = useState(false)

  useEffect(() => {
    getCronograma(versaoId)
      .then(setData)
      .finally(() => setLoading(false))
  }, [versaoId])

  function handleConfigSaved(inicio: string, fim: string) {
    setData(prev => prev ? { ...prev, cronograma_inicio: inicio, cronograma_fim: fim } : null)
    setShowConfig(false)
  }

  function handleLinhaUpdated(itemId: number, distribuicao_json: Record<string, number>) {
    setData(prev => {
      if (!prev) return prev
      return {
        ...prev,
        linhas: prev.linhas.map(l =>
          l.item_id === itemId ? { ...l, distribuicao_json } : l
        ),
      }
    })
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center text-gray-400 text-sm">
        Carregando cronograma...
      </div>
    )
  }

  const configured = !!(data?.cronograma_inicio && data?.cronograma_fim)

  if (!configured || showConfig) {
    return (
      <CronogramaConfigForm
        versaoId={versaoId}
        initialInicio={data?.cronograma_inicio ?? ''}
        initialFim={data?.cronograma_fim ?? ''}
        onSaved={handleConfigSaved}
      />
    )
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {!isReadOnly && (
        <div className="flex items-center justify-end px-4 py-2 border-b border-gray-100 bg-white shrink-0">
          <button
            onClick={() => setShowConfig(true)}
            className="text-xs text-gray-500 hover:text-blue-600 border border-gray-200 px-3 py-1 rounded-lg"
          >
            Alterar período ({data!.cronograma_inicio} → {data!.cronograma_fim})
          </button>
        </div>
      )}
      <CronogramaGrade
        versaoId={versaoId}
        data={data!}
        totalSemBdi={parseFloat(versao?.total_sem_bdi ?? '0')}
        isReadOnly={isReadOnly}
        onLinhaUpdated={handleLinhaUpdated}
      />
    </div>
  )
}
