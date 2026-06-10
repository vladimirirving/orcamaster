import { useEffect, useState } from 'react'
import { getRelatorioMedicao } from '@/api/relatorios'
import { toast } from '@/hooks/useToast'
import { fmtBRL } from '@/lib/utils'
import type { RelatorioMedicaoOut, Versao } from '@/types'

interface Props {
  versao: Versao | null
}

export default function MedicoesTab({ versao }: Props) {
  const [data, setData] = useState<RelatorioMedicaoOut | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!versao) { setData(null); return }
    setLoading(true)
    getRelatorioMedicao(versao.id)
      .then(setData)
      .catch(() => toast('Erro ao carregar relatório de medições', 'error'))
      .finally(() => setLoading(false))
  }, [versao?.id])

  if (!versao) {
    return <p className="text-gray-400 text-sm py-8 text-center">Selecione uma obra para ver as medições.</p>
  }

  if (loading) return <p className="text-gray-400 text-sm py-8 text-center">Carregando…</p>

  if (!data || data.grupos.length === 0) {
    return <p className="text-gray-400 text-sm py-8 text-center">Nenhum grupo com itens na versão ativa.</p>
  }

  return (
    <div className="space-y-4">
      {data.ultima_medicao_id === null && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 text-sm text-amber-700">
          Nenhuma medição registrada — percentuais realizados exibidos como 0%.
        </div>
      )}
      {data.periodo_fim && (
        <p className="text-xs text-gray-500">
          Baseado na medição de{' '}
          <strong>
            {new Date(data.periodo_fim + 'T12:00:00').toLocaleDateString('pt-BR', { month: 'long', year: 'numeric' })}
          </strong>
        </p>
      )}

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-2 font-medium text-gray-600">Grupo</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600 w-28">Planejado %</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600 w-28">Realizado %</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600 w-24">Desvio</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600 w-36">Valor medido</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600 w-36">Total grupo</th>
            </tr>
          </thead>
          <tbody>
            {data.grupos.map((grupo, idx) => {
              const desvio = grupo.desvio_pct
              return (
                <tr key={grupo.grupo_id} className={`border-t border-gray-100 ${idx % 2 === 1 ? 'bg-gray-50/50' : ''}`}>
                  <td className="px-4 py-2 font-medium">{grupo.grupo_nome}</td>
                  <td className="px-4 py-2 text-right text-gray-600">{grupo.planejado_pct.toFixed(1)}%</td>
                  <td className="px-4 py-2 text-right">{grupo.realizado_pct.toFixed(1)}%</td>
                  <td className={`px-4 py-2 text-right font-semibold ${desvio > 0 ? 'text-green-600' : desvio < 0 ? 'text-red-600' : 'text-gray-400'}`}>
                    {desvio > 0 ? '+' : ''}{desvio.toFixed(1)}%
                  </td>
                  <td className="px-4 py-2 text-right font-mono text-xs">{fmtBRL(grupo.valor_medido)}</td>
                  <td className="px-4 py-2 text-right font-mono text-xs text-gray-500">{fmtBRL(grupo.valor_total)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
