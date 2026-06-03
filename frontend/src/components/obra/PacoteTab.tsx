import { useState, useEffect, useRef } from 'react'
import { createPacote, getPacote, downloadPacote } from '@/api/pacote'
import { toast } from '@/hooks/useToast'
import type { PacoteJob } from '@/types'

interface Props {
  versaoId: number
}

const TERMINAL = new Set(['pronto', 'erro', 'expirado'])

export default function PacoteTab({ versaoId }: Props) {
  const [job, setJob] = useState<PacoteJob | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [downloading, setDownloading] = useState(false)
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null)

  function clearPolling() {
    if (intervalRef.current !== null) {
      clearInterval(intervalRef.current)
      intervalRef.current = null
    }
  }

  function startPolling(currentJob: PacoteJob) {
    if (TERMINAL.has(currentJob.status)) return
    clearPolling()
    intervalRef.current = setInterval(async () => {
      try {
        const updated = await getPacote(versaoId)
        setJob(updated)
        if (TERMINAL.has(updated.status)) clearPolling()
      } catch {
        clearPolling()
      }
    }, 3000)
  }

  useEffect(() => {
    setLoading(true)
    getPacote(versaoId)
      .then(j => {
        setJob(j)
        startPolling(j)
      })
      .catch(e => {
        if (e?.response?.status !== 404) toast('Erro ao carregar status', 'error')
      })
      .finally(() => setLoading(false))
    return clearPolling
  }, [versaoId])

  async function handleGerar() {
    setGenerating(true)
    try {
      const newJob = await createPacote(versaoId)
      setJob(newJob)
      startPolling(newJob)
    } catch (e: any) {
      toast(e?.response?.data?.detail ?? 'Erro ao iniciar geração', 'error')
    } finally {
      setGenerating(false)
    }
  }

  async function handleDownload() {
    setDownloading(true)
    try {
      await downloadPacote(versaoId)
    } catch {
      toast('Erro ao baixar pacote', 'error')
    } finally {
      setDownloading(false)
    }
  }

  const canGenerate =
    job === null ||
    job.status === 'erro' ||
    job.status === 'expirado'

  const isInProgress =
    job?.status === 'pendente' || job?.status === 'processando'

  if (loading) return <div className="p-6 text-gray-400 text-sm">Carregando...</div>

  return (
    <div className="p-6 max-w-xl space-y-5">
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-4">
        <h2 className="text-sm font-semibold text-gray-800">Pacote de Licitação</h2>
        <p className="text-xs text-gray-500">
          Gera um arquivo ZIP com a Proposta (PDF), a Planilha Orçamentária (XLSX) e o
          Cronograma Físico-Financeiro (XLSX) da versão ativa.
        </p>

        {job && (
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Status:</span>
              <StatusBadge status={job.status} />
            </div>
            {isInProgress && (
              <div className="flex items-center gap-2 text-xs text-blue-600">
                <span className="inline-block w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                Processando...
              </div>
            )}
            {job.status === 'erro' && job.erro_mensagem && (
              <p className="text-xs text-red-600 bg-red-50 rounded p-2 break-words">
                {job.erro_mensagem}
              </p>
            )}
            {job.status === 'expirado' && (
              <p className="text-xs text-yellow-700">Pacote expirado — gere um novo.</p>
            )}
          </div>
        )}

        <div className="flex gap-3">
          <button
            onClick={handleGerar}
            disabled={!canGenerate || generating || isInProgress}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
          >
            {generating ? 'Iniciando...' : 'Gerar Pacote'}
          </button>

          {job?.status === 'pronto' && (
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 disabled:opacity-40"
            >
              {downloading ? 'Baixando...' : 'Baixar ZIP'}
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

function StatusBadge({ status }: { status: PacoteJob['status'] }) {
  const styles: Record<PacoteJob['status'], string> = {
    pendente:    'bg-gray-100 text-gray-600',
    processando: 'bg-blue-100 text-blue-700',
    pronto:      'bg-green-100 text-green-700',
    erro:        'bg-red-100 text-red-700',
    expirado:    'bg-yellow-100 text-yellow-700',
  }
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${styles[status]}`}>
      {status}
    </span>
  )
}
