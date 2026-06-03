import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { Copy, Unlock, Trash2, Plus, ExternalLink } from 'lucide-react'
import { getObra, getVersoes, createVersao } from '@/api/obras'
import { duplicarVersao, softDeleteVersao, restoreVersao } from '@/api/versoes'
import { toast } from '@/hooks/useToast'
import { fmtBRL } from '@/lib/utils'
import type { Obra, Versao } from '@/types'
import ObraDashboard from '@/components/obra/ObraDashboard'
import CurvaAbc from '@/components/obra/CurvaAbc'

export default function ObraDetailPage() {
  const { id } = useParams<{ id: string }>()
  const obraId = Number(id)
  const navigate = useNavigate()
  const [obra, setObra] = useState<Obra | null>(null)
  const [versoes, setVersoes] = useState<Versao[]>([])
  const [loading, setLoading] = useState(true)
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null)
  const [tab, setTab] = useState<'versoes' | 'dashboard' | 'curva-abc'>('versoes')

  async function reload() {
    const [o, vs] = await Promise.all([getObra(obraId), getVersoes(obraId)])
    setObra(o)
    setVersoes(vs)
  }

  useEffect(() => {
    reload().finally(() => setLoading(false))
  }, [obraId])

  async function handleNovaVersao() {
    if (!confirm('A versão ativa será bloqueada. Continuar?')) return
    try {
      await createVersao(obraId)
      await reload()
      toast('Nova versão criada')
    } catch (e: any) {
      toast(e?.response?.data?.detail ?? 'Erro ao criar versão', 'error')
    }
  }

  async function handleDuplicar(versaoId: number) {
    try {
      await duplicarVersao(versaoId)
      await reload()
      toast('Versão duplicada')
    } catch (e: any) {
      toast(e?.response?.data?.detail ?? 'Erro ao duplicar', 'error')
    }
  }

  async function handleDelete(versaoId: number) {
    try {
      await softDeleteVersao(versaoId)
      setVersoes(prev => prev.filter(v => v.id !== versaoId))
      setConfirmDelete(null)
      toast('Versão removida')
    } catch {
      toast('Erro ao remover versão', 'error')
    }
  }

  async function handleRestore(versaoId: number) {
    try {
      const v = await restoreVersao(versaoId)
      setVersoes(prev => prev.map(x => x.id === v.id ? v : x))
      toast('Versão restaurada')
    } catch (e: any) {
      toast(e?.response?.data?.detail ?? 'Erro ao restaurar', 'error')
    }
  }

  if (loading) return <div className="p-6 text-gray-500">Carregando...</div>
  if (!obra) return <div className="p-6 text-red-500">Obra não encontrada</div>

  const versaoAtiva = versoes.find(v => !v.bloqueada && !v.deletada_em)

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <nav className="text-sm text-gray-500 mb-4">
        <Link to="/obras" className="hover:text-blue-600">Obras</Link>
        <span className="mx-2">›</span>
        <span className="text-gray-900 font-medium">{obra.nome}</span>
      </nav>

      <div className="flex items-center justify-between mb-0">
        <h1 className="text-2xl font-bold text-gray-900">{obra.nome}</h1>
        {tab === 'versoes' && (
          <button
            onClick={handleNovaVersao}
            className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium"
          >
            <Plus size={16} /> Nova Versão
          </button>
        )}
      </div>

      <div className="flex gap-0 border-b border-gray-200 mb-6 mt-4">
        {(['versoes', 'dashboard', 'curva-abc'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t === 'versoes' ? 'Versões' : t === 'dashboard' ? 'Dashboard' : 'Curva ABC'}
          </button>
        ))}
      </div>

      {tab === 'versoes' && (
        <>
          {versoes.length === 0 && (
            <p className="text-gray-400 text-center py-12">Nenhuma versão encontrada</p>
          )}

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            {versoes.map((v, idx) => {
              const isAtiva = !v.bloqueada && !v.deletada_em
              return (
                <div key={v.id} className={`flex items-center gap-4 px-5 py-4 ${idx < versoes.length - 1 ? 'border-b border-gray-100' : ''}`}>
                  <div className="w-8 text-center">
                    <span className="text-sm font-bold text-gray-400">#{v.numero}</span>
                  </div>

                  <div className="flex-1 min-w-0">
                    <span className="font-medium text-gray-900 text-sm">{v.nome ?? `Versão ${v.numero}`}</span>
                    <div className="flex gap-4 text-xs text-gray-500 mt-0.5">
                      <span>S/BDI: {fmtBRL(v.total_sem_bdi)}</span>
                      <span>C/BDI: {fmtBRL(v.total_com_bdi)}</span>
                    </div>
                  </div>

                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium
                    ${isAtiva ? 'bg-green-100 text-green-700' :
                      v.bloqueada ? 'bg-yellow-100 text-yellow-700' :
                      'bg-gray-100 text-gray-500'}`}>
                    {isAtiva ? 'ativa' : v.bloqueada ? 'bloqueada' : 'deletada'}
                  </span>

                  <div className="flex items-center gap-1">
                    {isAtiva && (
                      <button
                        onClick={() => navigate(`/obras/${obraId}/versoes/${v.id}`)}
                        title="Abrir planilha"
                        className="p-1.5 text-blue-600 hover:bg-blue-50 rounded"
                      >
                        <ExternalLink size={16} />
                      </button>
                    )}
                    <button
                      onClick={() => handleDuplicar(v.id)}
                      title="Duplicar"
                      className="p-1.5 text-gray-500 hover:bg-gray-50 rounded"
                    >
                      <Copy size={16} />
                    </button>
                    {v.bloqueada && !v.deletada_em && (
                      <button
                        onClick={() => handleRestore(v.id)}
                        title="Restaurar"
                        className="p-1.5 text-gray-500 hover:bg-gray-50 rounded"
                      >
                        <Unlock size={16} />
                      </button>
                    )}
                    {!v.bloqueada && (
                      <button
                        onClick={() => {
                          if (confirmDelete === v.id) {
                            handleDelete(v.id)
                          } else {
                            setConfirmDelete(v.id)
                            setTimeout(() => setConfirmDelete(null), 3000)
                          }
                        }}
                        title={confirmDelete === v.id ? 'Clique novamente para confirmar' : 'Remover'}
                        className={`p-1.5 rounded transition-colors ${confirmDelete === v.id ? 'text-red-600 bg-red-50' : 'text-gray-400 hover:bg-gray-50'}`}
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </>
      )}

      {tab === 'dashboard' && <ObraDashboard obraId={obraId} />}

      {tab === 'curva-abc' && (
        versaoAtiva
          ? <CurvaAbc versaoId={versaoAtiva.id} />
          : <div className="p-6 text-center text-gray-400 text-sm py-12">Nenhuma versão ativa para esta obra</div>
      )}
    </div>
  )
}
