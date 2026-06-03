import { useState, useEffect } from 'react'
import { getCurvaAbc, downloadCurvaAbcExcel } from '@/api/curvaAbc'
import { fmtBRL } from '@/lib/utils'
import { toast } from '@/hooks/useToast'
import type { CurvaAbcData } from '@/types'

interface Props {
  versaoId: number
}

const FAIXA_ROW: Record<string, string> = {
  A: 'bg-green-50',
  B: 'bg-yellow-50',
  C: 'bg-gray-50',
}

const FAIXA_BADGE: Record<string, string> = {
  A: 'bg-green-100 text-green-700',
  B: 'bg-yellow-100 text-yellow-700',
  C: 'bg-gray-100 text-gray-500',
}

export default function CurvaAbc({ versaoId }: Props) {
  const [data, setData] = useState<CurvaAbcData | null>(null)
  const [loading, setLoading] = useState(true)
  const [exporting, setExporting] = useState(false)

  useEffect(() => {
    getCurvaAbc(versaoId)
      .then(setData)
      .catch(() => toast('Erro ao carregar Curva ABC', 'error'))
      .finally(() => setLoading(false))
  }, [versaoId])

  async function handleExport() {
    setExporting(true)
    try {
      await downloadCurvaAbcExcel(versaoId)
    } catch {
      toast('Erro ao exportar Excel', 'error')
    } finally {
      setExporting(false)
    }
  }

  if (loading) {
    return <div className="p-6 text-gray-400 text-sm">Carregando...</div>
  }

  if (!data || data.itens.length === 0) {
    return (
      <div className="p-6 text-center text-gray-400 text-sm py-12">
        Nenhum item com valor cadastrado nesta versão
      </div>
    )
  }

  return (
    <div className="p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-500">
          Total da versão:{' '}
          <span className="font-semibold text-gray-900">{fmtBRL(data.total_versao)}</span>
        </div>
        <button
          onClick={handleExport}
          disabled={exporting}
          className="flex items-center gap-2 text-sm bg-green-600 text-white px-3 py-1.5 rounded-lg hover:bg-green-700 disabled:opacity-50 font-medium"
        >
          {exporting ? 'Exportando...' : 'Exportar Excel'}
        </button>
      </div>

      {/* Tabela */}
      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-50 border-b border-gray-200 text-xs font-medium text-gray-600 uppercase tracking-wide">
                <th className="text-right px-3 py-2.5 w-10">#</th>
                <th className="text-left px-3 py-2.5 w-36">Grupo</th>
                <th className="text-left px-3 py-2.5">Descrição</th>
                <th className="text-center px-3 py-2.5 w-16">Un</th>
                <th className="text-right px-3 py-2.5 w-24">Qtd</th>
                <th className="text-right px-3 py-2.5 w-32">Total (R$)</th>
                <th className="text-right px-3 py-2.5 w-20">Part%</th>
                <th className="text-right px-3 py-2.5 w-20">Acum%</th>
                <th className="text-center px-3 py-2.5 w-16">Faixa</th>
              </tr>
            </thead>
            <tbody>
              {data.itens.map((item, idx) => (
                <tr
                  key={item.rank}
                  className={`${FAIXA_ROW[item.faixa]} ${idx < data.itens.length - 1 ? 'border-b border-gray-100' : ''}`}
                >
                  <td className="text-right px-3 py-2 text-gray-400 text-xs">{item.rank}</td>
                  <td className="px-3 py-2 text-gray-500 text-xs truncate max-w-0">{item.grupo_nome}</td>
                  <td className="px-3 py-2 text-gray-900 text-xs">{item.descricao || '—'}</td>
                  <td className="text-center px-3 py-2 text-gray-500 text-xs">{item.unidade}</td>
                  <td className="text-right px-3 py-2 text-gray-500 text-xs">
                    {parseFloat(item.quantidade).toLocaleString('pt-BR')}
                  </td>
                  <td className="text-right px-3 py-2 font-medium text-gray-900 text-xs">
                    {fmtBRL(item.total)}
                  </td>
                  <td className="text-right px-3 py-2 text-gray-500 text-xs">
                    {item.participacao_pct.toFixed(1)}%
                  </td>
                  <td className="text-right px-3 py-2 text-gray-500 text-xs">
                    {item.acumulado_pct.toFixed(1)}%
                  </td>
                  <td className="text-center px-3 py-2">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${FAIXA_BADGE[item.faixa]}`}>
                      {item.faixa}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Legenda */}
      <div className="flex gap-4 text-xs text-gray-400">
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-green-200 inline-block" /> A — até 80% do valor
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-yellow-200 inline-block" /> B — 80–95%
        </span>
        <span className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-gray-200 inline-block" /> C — 95–100%
        </span>
      </div>
    </div>
  )
}
