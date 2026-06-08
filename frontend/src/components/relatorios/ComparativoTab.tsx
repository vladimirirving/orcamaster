import { useEffect, useState } from 'react'
import { getVersoes } from '@/api/obras'
import { getComparativo } from '@/api/relatorios'
import { toast } from '@/hooks/useToast'
import { fmtBRL } from '@/lib/utils'
import type { ComparativoOut, Obra, Versao } from '@/types'

const STATUS_ROW_COLORS: Record<string, string> = {
  novo: 'bg-green-50',
  removido: 'bg-orange-50',
  alterado: '',
  igual: '',
}

const STATUS_BADGES: Record<string, string> = {
  novo: 'bg-green-100 text-green-800',
  removido: 'bg-orange-100 text-orange-800',
  alterado: 'bg-blue-100 text-blue-800',
}

interface Props {
  obra: Obra | null
}

export default function ComparativoTab({ obra }: Props) {
  const [versoes, setVersoes] = useState<Versao[]>([])
  const [v1Id, setV1Id] = useState<number | null>(null)
  const [v2Id, setV2Id] = useState<number | null>(null)
  const [data, setData] = useState<ComparativoOut | null>(null)
  const [loading, setLoading] = useState(false)
  const [mostrarIguais, setMostrarIguais] = useState(false)

  useEffect(() => {
    if (!obra) { setVersoes([]); setV1Id(null); setV2Id(null); setData(null); return }
    getVersoes(obra.id)
      .then(vs => {
        const sorted = [...vs].sort((a, b) => a.numero - b.numero)
        setVersoes(sorted)
        if (sorted.length >= 2) {
          setV1Id(sorted[sorted.length - 2].id)
          setV2Id(sorted[sorted.length - 1].id)
        } else if (sorted.length === 1) {
          setV1Id(sorted[0].id)
          setV2Id(sorted[0].id)
        }
      })
      .catch(() => toast('Erro ao carregar versões', 'error'))
    setData(null)
  }, [obra?.id])

  async function handleComparar() {
    if (!obra || !v1Id || !v2Id || v1Id === v2Id) return
    setLoading(true)
    try {
      const result = await getComparativo(obra.id, v1Id, v2Id)
      setData(result)
    } catch (e: any) {
      toast(e?.response?.data?.detail ?? 'Erro ao comparar versões', 'error')
    } finally {
      setLoading(false)
    }
  }

  if (!obra) {
    return <p className="text-gray-400 text-sm py-8 text-center">Selecione uma obra para comparar versões.</p>
  }

  if (versoes.length < 2) {
    return <p className="text-gray-400 text-sm py-8 text-center">Esta obra precisa de pelo menos 2 versões para comparar.</p>
  }

  const versaoLabel = (v: Versao) =>
    `Versão ${v.numero}${v.nome ? ` — ${v.nome}` : ''}${!v.bloqueada && v.deletada_em === null ? ' (ativa)' : v.bloqueada ? ' (bloqueada)' : ''}`

  const itensFiltrados = data
    ? (mostrarIguais ? data.itens : data.itens.filter(i => i.status !== 'igual'))
    : []

  const deltaVal = data ? parseFloat(data.delta_total) : 0

  return (
    <div className="space-y-4">
      {/* Seletores */}
      <div className="flex items-center gap-3 flex-wrap">
        <select
          value={v1Id ?? ''}
          onChange={e => { setV1Id(Number(e.target.value)); setData(null) }}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {versoes.map(v => (
            <option key={v.id} value={v.id}>{versaoLabel(v)}</option>
          ))}
        </select>

        <span className="text-gray-500 text-sm font-medium">vs</span>

        <select
          value={v2Id ?? ''}
          onChange={e => { setV2Id(Number(e.target.value)); setData(null) }}
          className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          {versoes.map(v => (
            <option key={v.id} value={v.id}>{versaoLabel(v)}</option>
          ))}
        </select>

        <button
          onClick={handleComparar}
          disabled={loading || !v1Id || !v2Id || v1Id === v2Id}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
        >
          {loading ? 'Comparando…' : 'Comparar'}
        </button>
      </div>

      {v1Id === v2Id && (
        <p className="text-xs text-amber-600">Selecione versões diferentes para comparar.</p>
      )}

      {/* Resultado */}
      {data && (
        <div className="space-y-4">
          {/* Resumo */}
          <div className="flex flex-wrap gap-3 items-center">
            <div className="bg-green-50 border border-green-200 rounded-lg px-3 py-2 text-sm text-green-800">
              <strong>{data.qtd_novos}</strong> adicionado{data.qtd_novos !== 1 ? 's' : ''}
            </div>
            <div className="bg-orange-50 border border-orange-200 rounded-lg px-3 py-2 text-sm text-orange-800">
              <strong>{data.qtd_removidos}</strong> removido{data.qtd_removidos !== 1 ? 's' : ''}
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-2 text-sm text-blue-800">
              <strong>{data.qtd_alterados}</strong> alterado{data.qtd_alterados !== 1 ? 's' : ''}
            </div>
            <div className="ml-auto text-sm text-gray-600">
              <span className="text-gray-400">{data.v1_nome}:</span> {fmtBRL(data.v1_total)}
              {' → '}
              <span className="text-gray-400">{data.v2_nome}:</span>{' '}
              <strong>{fmtBRL(data.v2_total)}</strong>
              {' '}
              <span className={deltaVal >= 0 ? 'text-red-600' : 'text-green-600'}>
                ({deltaVal >= 0 ? '+' : ''}{fmtBRL(data.delta_total)}, {data.delta_pct >= 0 ? '+' : ''}{data.delta_pct.toFixed(1)}%)
              </span>
            </div>
          </div>

          {/* Filtro iguais */}
          <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
            <input
              type="checkbox"
              checked={mostrarIguais}
              onChange={e => setMostrarIguais(e.target.checked)}
            />
            Mostrar itens iguais
          </label>

          {/* Tabela */}
          <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Grupo</th>
                  <th className="text-left px-4 py-2 font-medium text-gray-600">Serviço</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-600 w-28">V1 preço unit.</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-600 w-28">V2 preço unit.</th>
                  <th className="text-right px-4 py-2 font-medium text-gray-600 w-28">Δ total</th>
                  <th className="text-center px-4 py-2 font-medium text-gray-600 w-24">Status</th>
                </tr>
              </thead>
              <tbody>
                {itensFiltrados.map((item, idx) => {
                  const delta = parseFloat(item.delta_total)
                  return (
                    <tr key={idx} className={`border-t border-gray-100 ${STATUS_ROW_COLORS[item.status]}`}>
                      <td className="px-4 py-2 text-gray-600 text-xs">{item.grupo_nome}</td>
                      <td className="px-4 py-2 truncate max-w-[240px]">{item.descricao}</td>
                      <td className="px-4 py-2 text-right font-mono text-xs text-gray-500">
                        {item.v1_preco_unit
                          ? `R$ ${parseFloat(item.v1_preco_unit).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
                          : '—'}
                      </td>
                      <td className="px-4 py-2 text-right font-mono text-xs">
                        {item.v2_preco_unit
                          ? `R$ ${parseFloat(item.v2_preco_unit).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}`
                          : '—'}
                      </td>
                      <td className={`px-4 py-2 text-right font-mono text-xs font-semibold ${delta > 0 ? 'text-red-600' : delta < 0 ? 'text-green-600' : 'text-gray-400'}`}>
                        {delta !== 0 ? `${delta > 0 ? '+' : ''}${fmtBRL(item.delta_total)}` : '—'}
                      </td>
                      <td className="px-4 py-2 text-center">
                        {item.status !== 'igual' && (
                          <span className={`text-xs px-2 py-0.5 rounded font-medium ${STATUS_BADGES[item.status]}`}>
                            {item.status === 'novo' ? 'NOVO' : item.status === 'removido' ? 'REMOVIDO' : 'ALTERADO'}
                          </span>
                        )}
                      </td>
                    </tr>
                  )
                })}
                {itensFiltrados.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-8 text-center text-gray-400 text-sm">
                      Nenhuma diferença encontrada entre as versões.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
