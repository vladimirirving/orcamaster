import { useEffect, useState } from 'react'
import { getContratos } from '@/api/contratos'
import { toast } from '@/hooks/useToast'
import { fmtBRL } from '@/lib/utils'
import type { Contrato } from '@/types'
import ContratoCard from './ContratoCard'
import ContratoModal from './ContratoModal'

interface Props {
  obraId: number
}

export default function ContratosTab({ obraId }: Props) {
  const [contratos, setContratos] = useState<Contrato[]>([])
  const [loading, setLoading] = useState(true)
  const [modalOpen, setModalOpen] = useState(false)

  useEffect(() => {
    getContratos(obraId)
      .then(setContratos)
      .catch(() => toast('Erro ao carregar contratos', 'error'))
      .finally(() => setLoading(false))
  }, [obraId])

  function handleUpdate(updated: Contrato) {
    setContratos(prev => prev.map(c => c.id === updated.id ? updated : c))
  }

  function handleDelete(id: number) {
    setContratos(prev => prev.filter(c => c.id !== id))
  }

  if (loading) return <div className="p-6 text-gray-400 text-sm">Carregando contratos…</div>

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold text-gray-900">Contratos</h2>
          {contratos.length > 0 && (
            <p className="text-xs text-gray-500 mt-0.5">
              {contratos.length} contrato{contratos.length > 1 ? 's' : ''} · valor total atual: {fmtBRL(String(contratos.reduce((s, c) => s + c.valor_atual, 0)))}
            </p>
          )}
        </div>
        <button
          onClick={() => setModalOpen(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium"
        >
          + Novo Contrato
        </button>
      </div>

      {contratos.length === 0 ? (
        <div className="text-center py-16 text-gray-400">
          <svg className="w-10 h-10 mx-auto mb-3 text-gray-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
            <polyline points="14 2 14 8 20 8"/>
            <line x1="16" y1="13" x2="8" y2="13"/>
            <line x1="16" y1="17" x2="8" y2="17"/>
          </svg>
          <p className="text-sm">Nenhum contrato cadastrado</p>
          <p className="text-xs mt-1">Clique em "Novo Contrato" para começar</p>
        </div>
      ) : (
        <div className="space-y-3">
          {contratos.map(c => (
            <ContratoCard
              key={c.id}
              contrato={c}
              obraId={obraId}
              onUpdate={handleUpdate}
              onDelete={handleDelete}
            />
          ))}
        </div>
      )}

      {modalOpen && (
        <ContratoModal
          obraId={obraId}
          onClose={() => setModalOpen(false)}
          onSuccess={novo => {
            setContratos(prev => [...prev, novo])
            setModalOpen(false)
          }}
        />
      )}
    </div>
  )
}
