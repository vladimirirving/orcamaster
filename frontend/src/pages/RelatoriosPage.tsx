import { useEffect, useState } from 'react'
import { getObras, getVersoes } from '@/api/obras'
import { toast } from '@/hooks/useToast'
import type { Obra, Versao } from '@/types'
import CurvaAbcTab from '@/components/relatorios/CurvaAbcTab'
import MedicoesTab from '@/components/relatorios/MedicoesTab'
import ComparativoTab from '@/components/relatorios/ComparativoTab'

type Tab = 'curva-abc' | 'medicoes' | 'comparativo'

const TABS: { id: Tab; label: string }[] = [
  { id: 'curva-abc', label: 'Curva ABC' },
  { id: 'medicoes', label: 'Medições' },
  { id: 'comparativo', label: 'Comparativo de Versões' },
]

export default function RelatoriosPage() {
  const [tab, setTab] = useState<Tab>('curva-abc')
  const [obras, setObras] = useState<Obra[]>([])
  const [obraId, setObraId] = useState<number | null>(null)
  const [versaoAtiva, setVersaoAtiva] = useState<Versao | null>(null)
  const [loadingObras, setLoadingObras] = useState(true)

  useEffect(() => {
    getObras()
      .then(os => {
        setObras(os)
        if (os.length > 0) setObraId(os[0].id)
      })
      .catch(() => toast('Erro ao carregar obras', 'error'))
      .finally(() => setLoadingObras(false))
  }, [])

  useEffect(() => {
    if (!obraId) { setVersaoAtiva(null); return }
    getVersoes(obraId).then(vs => {
      const ativa = vs.find(v => !v.bloqueada && v.deletada_em === null) ?? null
      setVersaoAtiva(ativa)
    }).catch(() => setVersaoAtiva(null))
  }, [obraId])

  const obraAtual = obras.find(o => o.id === obraId) ?? null

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Relatórios</h1>

        {!loadingObras && obras.length > 0 && (
          <select
            value={obraId ?? ''}
            onChange={e => setObraId(Number(e.target.value))}
            className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 max-w-xs"
          >
            {obras.map(o => (
              <option key={o.id} value={o.id}>{o.nome}</option>
            ))}
          </select>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-gray-200 mb-6">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t.id
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Conteúdo */}
      {loadingObras ? (
        <p className="text-gray-400 text-sm">Carregando obras…</p>
      ) : obras.length === 0 ? (
        <p className="text-gray-400 text-sm py-8 text-center">Nenhuma obra cadastrada.</p>
      ) : (
        <>
          {tab === 'curva-abc' && <CurvaAbcTab versao={versaoAtiva} />}
          {tab === 'medicoes' && <MedicoesTab versao={versaoAtiva} />}
          {tab === 'comparativo' && <ComparativoTab obra={obraAtual} />}
        </>
      )}
    </div>
  )
}
