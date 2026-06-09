import { fmtBRL } from '@/lib/utils'
import type { DashboardResumoItem } from '@/types'

const ESTADO_BADGE: Record<string, string> = {
  em_elaboracao: 'bg-blue-100 text-blue-800',
  concluido: 'bg-green-100 text-green-800',
  arquivado: 'bg-gray-100 text-gray-500',
}

const ESTADO_LABEL: Record<string, string> = {
  em_elaboracao: 'elaboração',
  concluido: 'concluído',
  arquivado: 'arquivado',
}

const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string }> = {
  adiantado: { label: 'Adiantado', bg: 'bg-green-100', text: 'text-green-700' },
  no_prazo: { label: 'No prazo', bg: 'bg-blue-100', text: 'text-blue-700' },
  atrasado: { label: 'Atrasado', bg: 'bg-yellow-100', text: 'text-yellow-700' },
  sem_dados: { label: 'Sem dados', bg: 'bg-gray-100', text: 'text-gray-400' },
}

interface Props {
  items: DashboardResumoItem[]
  onSelectObra: (obraId: number) => void
}

export default function EmpresaView({ items, onSelectObra }: Props) {
  // KPIs calculados client-side
  const emElaboracao = items.filter(i => i.estado === 'em_elaboracao')
  const totalSemBdi = emElaboracao.reduce(
    (s, i) => s + parseFloat(i.total_sem_bdi ?? '0'), 0
  )
  const totalComBdi = emElaboracao.reduce(
    (s, i) => s + parseFloat(i.total_com_bdi ?? '0'), 0
  )
  const qtdAlertas = items.filter(i => i.tem_alertas).length

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 rounded-xl p-4">
          <div className="text-xs text-gray-500 mb-1 uppercase tracking-wide">Em elaboração (s/ BDI)</div>
          <div className="text-2xl font-bold text-blue-700">{fmtBRL(String(totalSemBdi.toFixed(2)))}</div>
          <div className="text-xs text-blue-400 mt-1">{emElaboracao.length} obra{emElaboracao.length !== 1 ? 's' : ''}</div>
        </div>
        <div className="bg-green-50 rounded-xl p-4">
          <div className="text-xs text-gray-500 mb-1 uppercase tracking-wide">Total com BDI</div>
          <div className="text-2xl font-bold text-green-700">{fmtBRL(String(totalComBdi.toFixed(2)))}</div>
        </div>
        <div className={`rounded-xl p-4 ${qtdAlertas > 0 ? 'bg-amber-50' : 'bg-gray-50'}`}>
          <div className="text-xs text-gray-500 mb-1 uppercase tracking-wide">Alertas</div>
          <div className={`text-2xl font-bold ${qtdAlertas > 0 ? 'text-amber-700' : 'text-gray-400'}`}>
            {qtdAlertas}
          </div>
          <div className="text-xs text-gray-400 mt-1">itens para revisar</div>
        </div>
      </div>

      {/* Tabela de obras */}
      {items.length === 0 ? (
        <p className="text-gray-400 text-center py-12 text-sm">Nenhuma obra cadastrada.</p>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200">
                <th className="text-left px-5 py-3 font-medium text-gray-600">Obra</th>
                <th className="text-left px-4 py-3 font-medium text-gray-600 w-28">Estado</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600 w-32">Planejado %</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600 w-32">Realizado %</th>
                <th className="text-right px-4 py-3 font-medium text-gray-600 w-28">Desvio</th>
                <th className="text-center px-4 py-3 font-medium text-gray-600 w-28">Status</th>
                <th className="w-8"></th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, idx) => {
                const cfg = STATUS_CONFIG[item.status] ?? STATUS_CONFIG.sem_dados
                const semDados = item.status === 'sem_dados'
                return (
                  <tr
                    key={item.obra_id}
                    className={`hover:bg-gray-50 transition-colors cursor-pointer ${
                      idx < items.length - 1 ? 'border-b border-gray-100' : ''
                    }`}
                    onClick={() => onSelectObra(item.obra_id)}
                  >
                    <td className="px-5 py-3">
                      <div className="font-medium text-gray-900 flex items-center gap-2">
                        {item.obra_nome}
                        {item.tem_alertas && (
                          <span className="text-amber-500 text-xs" title="Itens para revisar">⚠</span>
                        )}
                      </div>
                      {item.total_sem_bdi && (
                        <div className="text-xs text-gray-400 mt-0.5">{fmtBRL(item.total_sem_bdi)}</div>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${ESTADO_BADGE[item.estado] ?? 'bg-gray-100 text-gray-500'}`}>
                        {ESTADO_LABEL[item.estado] ?? item.estado}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right text-gray-500">
                      {semDados ? '—' : `${item.planejado_pct_hoje?.toFixed(1)}%`}
                    </td>
                    <td className="px-4 py-3 text-right font-medium text-blue-600">
                      {semDados ? '—' : `${item.realizado_pct?.toFixed(1)}%`}
                    </td>
                    <td className={`px-4 py-3 text-right font-medium ${
                      semDados ? 'text-gray-400'
                      : (item.desvio ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {semDados ? '—' : `${(item.desvio ?? 0) >= 0 ? '+' : ''}${item.desvio?.toFixed(1)}pp`}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${cfg.bg} ${cfg.text}`}>
                        {cfg.label}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-400 text-center text-xs">→</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
