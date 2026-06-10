import { useNavigate } from 'react-router-dom'
import type { Alerta } from '@/types'

interface Props {
  alertas: Alerta[]
  onClose: () => void
}

const SEV_LABEL: Record<string, string> = {
  alta: 'ALTA',
  media: 'MÉDIA',
  baixa: 'BAIXA',
}

const SEV_COLORS: Record<string, string> = {
  alta: 'text-red-600 bg-red-50 border-red-200',
  media: 'text-yellow-700 bg-yellow-50 border-yellow-200',
  baixa: 'text-gray-600 bg-gray-50 border-gray-200',
}

const SEV_DOT: Record<string, string> = {
  alta: 'bg-red-500',
  media: 'bg-yellow-500',
  baixa: 'bg-gray-400',
}

const TIPO_ICON: Record<string, string> = {
  contrato_vencido: '📋',
  contrato_vencendo: '📋',
  desvio_orcamento: '📊',
  medicao_atrasada: '📅',
  item_revisao: '⚠️',
}

export default function AlertasPanel({ alertas, onClose }: Props) {
  const navigate = useNavigate()

  const grupos = (['alta', 'media', 'baixa'] as const).map(sev => ({
    sev,
    items: alertas.filter(a => a.severidade === sev),
  })).filter(g => g.items.length > 0)

  function handleClick(alerta: Alerta) {
    onClose()
    navigate(alerta.link)
  }

  return (
    <>
      {/* Overlay */}
      <div className="fixed inset-0 z-40" onClick={onClose} />

      {/* Painel */}
      <div className="fixed top-0 left-56 h-full w-80 bg-white shadow-2xl z-50 flex flex-col border-r border-gray-200">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4 text-gray-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
              <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
            </svg>
            <span className="font-semibold text-gray-900 text-sm">Alertas</span>
            {alertas.length > 0 && (
              <span className="bg-red-100 text-red-700 text-xs font-medium px-1.5 py-0.5 rounded-full">
                {alertas.length}
              </span>
            )}
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg leading-none" aria-label="Fechar">
            ×
          </button>
        </div>

        {/* Lista */}
        <div className="flex-1 overflow-y-auto py-2">
          {alertas.length === 0 ? (
            <div className="text-center py-16 px-4">
              <div className="text-3xl mb-3">🎉</div>
              <p className="text-sm text-gray-500">Nenhum alerta no momento</p>
              <p className="text-xs text-gray-400 mt-1">Todas as obras estão em dia</p>
            </div>
          ) : (
            grupos.map(({ sev, items }) => (
              <div key={sev} className="mb-2">
                <div className="px-4 py-1.5">
                  <span className={`text-xs font-semibold tracking-wider px-2 py-0.5 rounded border ${SEV_COLORS[sev]}`}>
                    {SEV_LABEL[sev]}
                  </span>
                </div>
                {items.map((alerta, i) => (
                  <button
                    key={i}
                    onClick={() => handleClick(alerta)}
                    className="w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors border-b border-gray-50 flex items-start gap-3"
                  >
                    <span className={`mt-1.5 w-2 h-2 rounded-full shrink-0 ${SEV_DOT[sev]}`} />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 font-medium leading-snug">
                        {TIPO_ICON[alerta.tipo]} {alerta.titulo}
                      </p>
                      <p className="text-xs text-gray-500 mt-0.5 truncate">{alerta.obra_nome}</p>
                      {alerta.detalhe && (
                        <p className="text-xs text-gray-400 mt-0.5">{alerta.detalhe}</p>
                      )}
                    </div>
                  </button>
                ))}
              </div>
            ))
          )}
        </div>
      </div>
    </>
  )
}
