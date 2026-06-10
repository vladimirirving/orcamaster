import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { ArrowLeft, BookOpen } from 'lucide-react'
import { listEntradas, deleteEntrada, getRdoUrl } from '@/api/diario'
import { getObra } from '@/api/obras'
import { toast } from '@/hooks/useToast'
import type { DiarioEntrada, Obra } from '@/types'
import DiarioEntradaModal from '@/components/diario/DiarioEntradaModal'

const CLIMA_ICONS: Record<string, string> = {
  ensolarado: '☀️',
  parcialmente_nublado: '⛅',
  nublado: '☁️',
  chuvoso: '🌧️',
}

function groupByMonth(entradas: DiarioEntrada[]): Record<string, DiarioEntrada[]> {
  const groups: Record<string, DiarioEntrada[]> = {}
  for (const e of entradas) {
    const [year, month] = e.data.split('-')
    const key = `${year}-${month}`
    if (!groups[key]) groups[key] = []
    groups[key].push(e)
  }
  return groups
}

function formatMonthLabel(key: string): string {
  const [year, month] = key.split('-')
  const date = new Date(Number(year), Number(month) - 1)
  return date.toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })
    .replace(/^\w/, c => c.toUpperCase())
}

function formatDayLabel(dateStr: string): string {
  const [year, month, day] = dateStr.split('-').map(Number)
  const date = new Date(year, month - 1, day)
  const weekday = date.toLocaleDateString('pt-BR', { weekday: 'short' })
    .replace('.', '').replace(/^\w/, c => c.toUpperCase())
  return `${weekday} ${String(day).padStart(2, '0')}`
}

export default function DiarioObraPage() {
  const { obraId } = useParams<{ obraId: string }>()
  const obraIdNum = Number(obraId)
  const navigate = useNavigate()
  const [obra, setObra] = useState<Obra | null>(null)
  const [entradas, setEntradas] = useState<DiarioEntrada[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)
  const [editEntry, setEditEntry] = useState<DiarioEntrada | undefined>(undefined)
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null)

  async function reload() {
    const [o, es] = await Promise.all([getObra(obraIdNum), listEntradas(obraIdNum)])
    setObra(o)
    setEntradas(es)
  }

  useEffect(() => {
    reload().finally(() => setLoading(false))
  }, [obraIdNum])

  async function handleDelete(id: number) {
    try {
      await deleteEntrada(obraIdNum, id)
      setEntradas(prev => prev.filter(e => e.id !== id))
      setConfirmDelete(null)
      toast('Entrada excluída')
    } catch {
      toast('Erro ao excluir entrada', 'error')
      setConfirmDelete(null)
    }
  }

  function handleOpenCreate() {
    setEditEntry(undefined)
    setModalOpen(true)
  }

  function handleOpenEdit(entry: DiarioEntrada) {
    setEditEntry({ ...entry, fotos: [] })
    setModalOpen(true)
  }

  if (loading) return <div className="p-6 text-gray-500">Carregando…</div>

  const groups = groupByMonth(entradas)
  const sortedKeys = Object.keys(groups).sort((a, b) => b.localeCompare(a))

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <nav className="text-sm text-gray-500 mb-4 flex items-center gap-2">
        <button
          onClick={() => navigate(`/obras/${obraIdNum}`)}
          className="hover:text-blue-600 flex items-center gap-1"
        >
          <ArrowLeft size={14} />
          {obra?.nome ?? 'Obras'}
        </button>
        <span>›</span>
        <span className="text-gray-900 font-medium">Diário</span>
      </nav>

      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <BookOpen size={20} className="text-gray-600" />
          <h1 className="text-2xl font-bold text-gray-900">Diário de Obras</h1>
        </div>
        <button
          onClick={handleOpenCreate}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium"
        >
          + Nova Entrada
        </button>
      </div>

      {entradas.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <p className="text-base">Nenhuma entrada registrada.</p>
          <p className="text-sm mt-1">Comece registrando o dia de hoje.</p>
        </div>
      )}

      {sortedKeys.map(key => (
        <div key={key} className="mb-8">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
            {formatMonthLabel(key)}
          </h2>
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            {groups[key].map((entry, idx) => (
              <div
                key={entry.id}
                className={`flex items-center gap-3 px-4 py-3 ${idx > 0 ? 'border-t border-gray-100' : ''}`}
              >
                <div className="bg-amber-50 text-amber-800 rounded-md px-2 py-1 text-xs font-semibold min-w-[56px] text-center flex-shrink-0">
                  {formatDayLabel(entry.data)}
                </div>

                <span className="text-lg flex-shrink-0" title={entry.clima}>
                  {CLIMA_ICONS[entry.clima] ?? '🌡️'}
                </span>

                <div className="flex-1 min-w-0">
                  <p className="text-sm text-gray-900 truncate">{entry.atividades}</p>
                  <p className="text-xs text-gray-500">
                    Efetivo: {entry.efetivo}
                    {entry.qtd_fotos ? ` · ${entry.qtd_fotos} foto${entry.qtd_fotos > 1 ? 's' : ''}` : ''}
                  </p>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  <a
                    href={getRdoUrl(obraIdNum, entry.id)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded hover:bg-blue-100 transition-colors"
                    title="Baixar RDO PDF"
                  >
                    ↓ RDO
                  </a>
                  <button
                    onClick={() => handleOpenEdit(entry)}
                    className="text-gray-400 hover:text-gray-700 text-sm"
                    aria-label="Editar entrada"
                  >
                    ✎
                  </button>
                  {confirmDelete === entry.id ? (
                    <span className="flex items-center gap-1">
                      <button
                        onClick={() => handleDelete(entry.id)}
                        className="text-xs bg-red-600 text-white px-2 py-1 rounded"
                      >
                        Confirmar
                      </button>
                      <button
                        onClick={() => setConfirmDelete(null)}
                        className="text-xs text-gray-500"
                      >
                        Cancelar
                      </button>
                    </span>
                  ) : (
                    <button
                      onClick={() => setConfirmDelete(entry.id)}
                      className="text-gray-400 hover:text-red-500 text-xs"
                      aria-label="Excluir entrada"
                    >
                      🗑
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}

      {modalOpen && (
        <DiarioEntradaModal
          obraId={obraIdNum}
          entrada={editEntry}
          onClose={() => { setModalOpen(false); setEditEntry(undefined) }}
          onSuccess={updated => {
            if (editEntry) {
              setEntradas(prev => prev.map(e => e.id === updated.id
                ? { ...updated, qtd_fotos: e.qtd_fotos }
                : e
              ))
            } else {
              setEntradas(prev => [{ ...updated, qtd_fotos: 0 }, ...prev])
              toast('Entrada criada')
            }
            setModalOpen(false)
            setEditEntry(undefined)
          }}
        />
      )}
    </div>
  )
}
