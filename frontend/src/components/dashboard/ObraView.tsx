import { useEffect, useState } from 'react'
import { getObraDashboard, getDistribuicaoGrupos } from '@/api/dashboard'
import { getRelatorioMedicao } from '@/api/relatorios'
import { toast } from '@/hooks/useToast'
import { fmtBRL } from '@/lib/utils'
import type { ObraDashboardData, DistribuicaoGruposOut, RelatorioMedicaoOut } from '@/types'
import CurvaSChart from '@/components/dashboard/CurvaSChart'

interface Props {
  obraId: number
}

const GRUPO_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444', '#06b6d4']

export default function ObraView({ obraId }: Props) {
  const [dash, setDash] = useState<ObraDashboardData | null>(null)
  const [distrib, setDistrib] = useState<DistribuicaoGruposOut | null>(null)
  const [medicao, setMedicao] = useState<RelatorioMedicaoOut | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setDash(null); setDistrib(null); setMedicao(null)

    Promise.all([
      getObraDashboard(obraId),
      getDistribuicaoGrupos(obraId),
    ])
      .then(async ([d, dist]) => {
        setDash(d)
        setDistrib(dist)
        if (d.versao_id) {
          try {
            const med = await getRelatorioMedicao(d.versao_id)
            setMedicao(med)
          } catch {
            // progresso físico não essencial — ignorar erro
          }
        }
      })
      .catch(() => toast('Erro ao carregar dados da obra', 'error'))
      .finally(() => setLoading(false))
  }, [obraId])

  if (loading) return <div className="py-12 text-center text-gray-400 text-sm">Carregando…</div>
  if (!dash) return null

  const semDados = dash.status === 'sem_dados'

  return (
    <div className="space-y-6">
      {/* KPI cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
          <div className="text-xs text-gray-500 mb-1 uppercase tracking-wide">Total sem BDI</div>
          <div className="text-xl font-bold text-gray-900">{fmtBRL(dash.total_sem_bdi)}</div>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-xl p-4">
          <div className="text-xs text-gray-500 mb-1 uppercase tracking-wide">Total com BDI</div>
          <div className="text-xl font-bold text-gray-900">{fmtBRL(dash.total_com_bdi)}</div>
        </div>
        <div className={`rounded-xl p-4 border ${semDados ? 'bg-gray-50 border-gray-200' : 'bg-green-50 border-green-200'}`}>
          <div className="text-xs text-gray-500 mb-1 uppercase tracking-wide">Realizado</div>
          {semDados ? (
            <div className="text-xl font-bold text-gray-400">—</div>
          ) : (
            <>
              <div className="text-xl font-bold text-green-700">{dash.realizado_pct?.toFixed(1)}%</div>
              <div className={`text-xs mt-1 font-medium ${(dash.desvio ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                {(dash.desvio ?? 0) >= 0 ? '+' : ''}{dash.desvio?.toFixed(1)}pp vs planejado
              </div>
            </>
          )}
        </div>
      </div>

      {/* Curva S */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <div className="text-sm font-semibold text-gray-700 mb-4">Curva S — Planejado × Realizado</div>
        {semDados ? (
          <p className="text-gray-400 text-sm text-center py-8">Cronograma ou medições não configurados.</p>
        ) : (
          <CurvaSChart data={dash.curva_s} />
        )}
      </div>

      {/* Distribuição por grupo + Progresso físico */}
      <div className="grid grid-cols-2 gap-4">
        {/* Distribuição por grupo */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="text-sm font-semibold text-gray-700 mb-4">Distribuição por Grupo</div>
          {!distrib || distrib.grupos.length === 0 ? (
            <p className="text-gray-400 text-sm text-center py-4">Sem grupos com valor.</p>
          ) : (
            <div className="space-y-2.5">
              {distrib.grupos.map((g, idx) => (
                <div key={g.grupo_id} className="flex items-center gap-3">
                  <div
                    className="w-2.5 h-2.5 rounded-sm flex-shrink-0"
                    style={{ background: GRUPO_COLORS[idx % GRUPO_COLORS.length] }}
                  />
                  <div className="flex-1 text-sm text-gray-700 truncate">{g.grupo_nome}</div>
                  <div className="text-sm font-semibold text-gray-900 flex-shrink-0">
                    {g.participacao_pct.toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Progresso físico por grupo */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <div className="text-sm font-semibold text-gray-700 mb-4">Progresso Físico por Grupo</div>
          {!medicao || medicao.grupos.length === 0 ? (
            <p className="text-gray-400 text-sm text-center py-4">Sem medições registradas.</p>
          ) : (
            <div className="space-y-3">
              {medicao.grupos.map(grupo => {
                const desvio = grupo.desvio_pct
                return (
                  <div key={grupo.grupo_id}>
                    <div className="flex justify-between text-xs text-gray-600 mb-1">
                      <span className="truncate font-medium">{grupo.grupo_nome}</span>
                      <span className={`font-semibold flex-shrink-0 ml-2 ${desvio > 0 ? 'text-green-600' : desvio < 0 ? 'text-red-600' : 'text-gray-400'}`}>
                        {desvio > 0 ? '+' : ''}{desvio.toFixed(1)}%
                      </span>
                    </div>
                    <div className="relative h-3 bg-gray-100 rounded-full overflow-hidden">
                      {/* Planejado (background) */}
                      <div
                        className="absolute top-0 left-0 h-full bg-gray-300 rounded-full"
                        style={{ width: `${Math.min(grupo.planejado_pct, 100)}%` }}
                      />
                      {/* Realizado (foreground) */}
                      <div
                        className={`absolute top-0 left-0 h-full rounded-full ${desvio >= 0 ? 'bg-blue-500' : 'bg-amber-400'}`}
                        style={{ width: `${Math.min(grupo.realizado_pct, 100)}%` }}
                      />
                    </div>
                    <div className="flex justify-between text-xs text-gray-400 mt-0.5">
                      <span>{grupo.realizado_pct.toFixed(0)}% realizado</span>
                      <span>{grupo.planejado_pct.toFixed(0)}% planejado</span>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
