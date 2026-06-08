import { useEffect, useState } from 'react'
import { getCurvaAbc, downloadCurvaAbcExcel } from '@/api/curvaAbc'
import { downloadPropostaPdf } from '@/api/proposta'
import { toast } from '@/hooks/useToast'
import type { CurvaAbcData, Versao } from '@/types'

const FAIXA_COLORS = {
  A: 'bg-green-100 text-green-800',
  B: 'bg-yellow-100 text-yellow-800',
  C: 'bg-red-100 text-red-800',
}

interface Props {
  versao: Versao | null
}

export default function CurvaAbcTab({ versao }: Props) {
  const [data, setData] = useState<CurvaAbcData | null>(null)
  const [loading, setLoading] = useState(false)
  const [downloading, setDownloading] = useState<'excel' | 'pdf' | null>(null)

  useEffect(() => {
    if (!versao) { setData(null); return }
    setLoading(true)
    getCurvaAbc(versao.id)
      .then(setData)
      .catch(() => toast('Erro ao carregar Curva ABC', 'error'))
      .finally(() => setLoading(false))
  }, [versao?.id])

  if (!versao) {
    return <p className="text-gray-400 text-sm py-8 text-center">Selecione uma obra para ver a Curva ABC.</p>
  }

  if (loading) return <p className="text-gray-400 text-sm py-8 text-center">Carregando…</p>

  if (!data || data.itens.length === 0) {
    return <p className="text-gray-400 text-sm py-8 text-center">Nenhum item com valor na versão ativa.</p>
  }

  const resumo = (['A', 'B', 'C'] as const).map(faixa => ({
    faixa,
    qtd: data.itens.filter(i => i.faixa === faixa).length,
    pct: data.itens.filter(i => i.faixa === faixa).reduce((s, i) => s + i.participacao_pct, 0),
  }))

  async function handleDownloadExcel() {
    if (!versao) return
    setDownloading('excel')
    try { await downloadCurvaAbcExcel(versao.id) }
    catch { toast('Erro ao baixar Excel', 'error') }
    finally { setDownloading(null) }
  }

  async function handleDownloadPdf() {
    if (!versao) return
    setDownloading('pdf')
    try { await downloadPropostaPdf(versao.id) }
    catch (e: any) {
      if (e?.response?.status === 404) toast('Proposta não configurada', 'error')
      else toast('Erro ao baixar PDF', 'error')
    }
    finally { setDownloading(null) }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-3">
        {resumo.map(({ faixa, qtd, pct }) => (
          <div key={faixa} className={`rounded-lg px-4 py-2 text-sm font-semibold ${FAIXA_COLORS[faixa]}`}>
            {faixa} — {qtd} {qtd === 1 ? 'serviço' : 'serviços'} · {pct.toFixed(1)}%
          </div>
        ))}
      </div>

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="text-left px-4 py-2 font-medium text-gray-600 w-8">#</th>
              <th className="text-left px-4 py-2 font-medium text-gray-600">Grupo</th>
              <th className="text-left px-4 py-2 font-medium text-gray-600">Serviço</th>
              <th className="text-left px-4 py-2 font-medium text-gray-600 w-16">Unid.</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600 w-28">Total</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600 w-20">Part%</th>
              <th className="text-right px-4 py-2 font-medium text-gray-600 w-20">Acum%</th>
              <th className="text-center px-4 py-2 font-medium text-gray-600 w-16">Classe</th>
            </tr>
          </thead>
          <tbody>
            {data.itens.map((item, idx) => (
              <tr key={item.rank} className={`border-t border-gray-100 ${idx % 2 === 1 ? 'bg-gray-50/50' : ''}`}>
                <td className="px-4 py-2 text-gray-400">{item.rank}</td>
                <td className="px-4 py-2 text-gray-600 truncate max-w-[120px]">{item.grupo_nome}</td>
                <td className="px-4 py-2 truncate max-w-[280px]">{item.descricao}</td>
                <td className="px-4 py-2 text-gray-500">{item.unidade}</td>
                <td className="px-4 py-2 text-right font-mono text-xs">
                  R$ {parseFloat(item.total).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
                </td>
                <td className="px-4 py-2 text-right">{item.participacao_pct.toFixed(2)}%</td>
                <td className="px-4 py-2 text-right">{item.acumulado_pct.toFixed(2)}%</td>
                <td className="px-4 py-2 text-center">
                  <span className={`text-xs font-bold px-2 py-0.5 rounded ${FAIXA_COLORS[item.faixa]}`}>
                    {item.faixa}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex gap-2">
        <button
          onClick={handleDownloadExcel}
          disabled={downloading === 'excel'}
          className="text-sm px-3 py-1.5 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-40"
        >
          {downloading === 'excel' ? 'Baixando…' : '↓ Excel'}
        </button>
        <button
          onClick={handleDownloadPdf}
          disabled={downloading === 'pdf'}
          className="text-sm px-3 py-1.5 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-40"
        >
          {downloading === 'pdf' ? 'Baixando…' : '↓ Proposta PDF'}
        </button>
      </div>
    </div>
  )
}
