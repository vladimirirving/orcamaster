import { useEffect, useState } from 'react'
import { useNavigate, useParams, Link } from 'react-router-dom'
import { Copy, Unlock, Trash2, Plus, ExternalLink } from 'lucide-react'
import { getObra, getVersoes, createVersao } from '@/api/obras'
import { updateObra } from '@/api/obras'
import { listClientes } from '@/api/clientes'
import { duplicarVersao, softDeleteVersao, restoreVersao } from '@/api/versoes'
import { toast } from '@/hooks/useToast'
import { fmtBRL } from '@/lib/utils'
import type { Obra, Versao, Cliente } from '@/types'
import ObraDashboard from '@/components/obra/ObraDashboard'
import ObraEditModal from '@/components/obra/ObraEditModal'
import CurvaAbc from '@/components/obra/CurvaAbc'
import PropostaTab from '@/components/obra/PropostaTab'
import PacoteTab from '@/components/obra/PacoteTab'
import AgenteTab from '@/components/obra/AgenteTab'
import ContratosTab from '@/components/obra/ContratosTab'

export default function ObraDetailPage() {
  const { id } = useParams<{ id: string }>()
  const obraId = Number(id)
  const navigate = useNavigate()
  const [obra, setObra] = useState<Obra | null>(null)
  const [versoes, setVersoes] = useState<Versao[]>([])
  const [loading, setLoading] = useState(true)
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null)
  const [tab, setTab] = useState<'versoes' | 'dashboard' | 'curva-abc' | 'proposta' | 'pacote' | 'agente' | 'contratos'>('versoes')
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [clienteSelectOpen, setClienteSelectOpen] = useState(false)
  const [clienteSearch, setClienteSearch] = useState('')
  const [editModalOpen, setEditModalOpen] = useState(false)

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

  useEffect(() => {
    if (clienteSelectOpen) {
      listClientes().then(setClientes)
    }
  }, [clienteSelectOpen])

  async function handleVincularCliente(clienteId: number | null) {
    try {
      const updated = await updateObra(obraId, { cliente_id: clienteId })
      setObra(updated)
      setClienteSelectOpen(false)
      setClienteSearch('')
      toast(clienteId ? 'Cliente vinculado' : 'Cliente desvinculado')
    } catch {
      toast('Erro ao vincular cliente', 'error')
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
        <div className="flex items-center gap-2">
          <button
            onClick={() => setEditModalOpen(true)}
            className="flex items-center gap-2 border border-gray-300 px-4 py-2 rounded-lg text-sm hover:bg-gray-50 transition-colors"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
            </svg>
            Editar
          </button>
          <button
            onClick={() => navigate(`/obras/${obraId}/diario`)}
            className="flex items-center gap-2 border border-gray-300 px-4 py-2 rounded-lg text-sm hover:bg-gray-50 transition-colors"
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
              <line x1="16" y1="13" x2="8" y2="13"/>
              <line x1="16" y1="17" x2="8" y2="17"/>
              <polyline points="10 9 9 9 8 9"/>
            </svg>
            Diário
          </button>
          {tab === 'versoes' && (
            <button
              onClick={handleNovaVersao}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium"
            >
              <Plus size={16} /> Nova Versão
            </button>
          )}
        </div>
      </div>

      {/* Card de cliente */}
      <div className="mt-3 flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6b7280" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>
          <circle cx="12" cy="7" r="4"/>
        </svg>
        <div className="flex-1">
          <p className="text-xs text-gray-500 uppercase tracking-wide leading-none mb-0.5">Cliente</p>
          {obra.cliente_id ? (
            <Link
              to={`/clientes/${obra.cliente_id}`}
              className="text-sm font-medium text-blue-600 hover:underline"
              onClick={e => e.stopPropagation()}
            >
              {obra.cliente_nome ?? obra.cliente ?? `Cliente #${obra.cliente_id}`} →
            </Link>
          ) : (
            <span className="text-sm text-gray-400">Nenhum cliente vinculado</span>
          )}
        </div>
        <button
          onClick={() => setClienteSelectOpen(true)}
          className="text-xs border border-gray-300 px-2 py-1 rounded hover:bg-white transition-colors text-gray-600"
        >
          {obra.cliente_id ? 'Alterar' : 'Vincular'}
        </button>
      </div>

      {/* Modal de seleção de cliente */}
      {clienteSelectOpen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-sm mx-4 p-5">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-gray-900">Vincular cliente</h3>
              <button onClick={() => setClienteSelectOpen(false)} className="text-gray-400 hover:text-gray-600 text-xl">×</button>
            </div>
            <input
              type="text"
              value={clienteSearch}
              onChange={e => setClienteSearch(e.target.value)}
              placeholder="Buscar cliente…"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-3 focus:outline-none focus:ring-2 focus:ring-blue-500"
              autoFocus
            />
            <div className="max-h-48 overflow-y-auto space-y-1">
              {obra.cliente_id && (
                <button
                  onClick={() => handleVincularCliente(null)}
                  className="w-full text-left px-3 py-2 rounded-lg text-sm text-red-600 hover:bg-red-50"
                >
                  Remover vínculo
                </button>
              )}
              {clientes
                .filter(c => !clienteSearch || c.nome.toLowerCase().includes(clienteSearch.toLowerCase()))
                .map(c => (
                  <button
                    key={c.id}
                    onClick={() => handleVincularCliente(c.id)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm hover:bg-blue-50 ${obra.cliente_id === c.id ? 'bg-blue-50 text-blue-700 font-medium' : 'text-gray-700'}`}
                  >
                    {c.nome}
                    {c.cpf_cnpj && <span className="ml-2 text-gray-400 text-xs">{c.cpf_cnpj}</span>}
                  </button>
                ))
              }
            </div>
          </div>
        </div>
      )}

      <div className="flex gap-0 border-b border-gray-200 mb-6 mt-4">
        {(['versoes', 'dashboard', 'curva-abc', 'proposta', 'pacote', 'agente', 'contratos'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t === 'versoes' ? 'Versões'
              : t === 'dashboard' ? 'Dashboard'
              : t === 'curva-abc' ? 'Curva ABC'
              : t === 'proposta' ? 'Proposta'
              : t === 'pacote' ? 'Pacote'
              : t === 'agente' ? 'Agente IA'
              : 'Contratos'}
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

      {tab === 'proposta' && (
        versaoAtiva
          ? <PropostaTab versaoId={versaoAtiva.id} />
          : <div className="p-6 text-center text-gray-400 text-sm py-12">Nenhuma versão ativa para esta obra</div>
      )}

      {tab === 'pacote' && (
        versaoAtiva
          ? <PacoteTab versaoId={versaoAtiva.id} />
          : <div className="p-6 text-center text-gray-400 text-sm py-12">Nenhuma versão ativa para esta obra</div>
      )}

      {tab === 'agente' && (
        versaoAtiva
          ? <AgenteTab versaoId={versaoAtiva.id} obraId={obraId} />
          : <div className="p-6 text-center text-gray-400 text-sm py-12">Nenhuma versão ativa para esta obra</div>
      )}

      {tab === 'contratos' && <ContratosTab obraId={obraId} />}

      {editModalOpen && obra && (
        <ObraEditModal
          obra={obra}
          onClose={() => setEditModalOpen(false)}
          onSuccess={updated => {
            setObra(updated)
            setEditModalOpen(false)
          }}
        />
      )}
    </div>
  )
}
