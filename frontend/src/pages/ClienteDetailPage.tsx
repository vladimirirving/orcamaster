// frontend/src/pages/ClienteDetailPage.tsx
import { useEffect, useState } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Pencil } from 'lucide-react'
import { getCliente, getClienteObras } from '@/api/clientes'
import { toast } from '@/hooks/useToast'
import type { Cliente, Obra } from '@/types'
import ClienteModal from '@/components/clientes/ClienteModal'

type Tab = 'dados' | 'obras' | 'propostas'

export default function ClienteDetailPage() {
  const { id } = useParams<{ id: string }>()
  const clienteId = Number(id)
  const navigate = useNavigate()
  const [cliente, setCliente] = useState<Cliente | null>(null)
  const [obras, setObras] = useState<Obra[]>([])
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<Tab>('dados')
  const [editOpen, setEditOpen] = useState(false)

  async function reload() {
    const [c, os] = await Promise.all([getCliente(clienteId), getClienteObras(clienteId)])
    setCliente(c)
    setObras(os)
  }

  useEffect(() => {
    reload().finally(() => setLoading(false))
  }, [clienteId])

  if (loading) return <div className="p-6 text-gray-500">Carregando…</div>
  if (!cliente) return <div className="p-6 text-red-500">Cliente não encontrado</div>

  const field = (label: string, value: string | null | undefined) => (
    <div key={label}>
      <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">{label}</p>
      <p className="text-sm text-gray-900">{value || '—'}</p>
    </div>
  )

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <nav className="text-sm text-gray-500 mb-4 flex items-center gap-1">
        <Link to="/clientes" className="hover:text-blue-600 flex items-center gap-1">
          <ArrowLeft size={14} /> Clientes
        </Link>
        <span>›</span>
        <span className="text-gray-900 font-medium">{cliente.nome}</span>
      </nav>

      <div className="flex items-start justify-between mb-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{cliente.nome}</h1>
          <span className={`text-xs px-2 py-0.5 rounded-full mt-1 inline-block ${cliente.tipo === 'pj' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}`}>
            {cliente.tipo === 'pj' ? 'Pessoa Jurídica' : 'Pessoa Física'}
          </span>
        </div>
        <button
          onClick={() => setEditOpen(true)}
          className="flex items-center gap-2 border border-gray-300 px-3 py-2 rounded-lg text-sm hover:bg-gray-50"
        >
          <Pencil size={14} /> Editar
        </button>
      </div>

      <div className="flex gap-0 border-b border-gray-200 mb-6">
        {(['dados', 'obras', 'propostas'] as Tab[]).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            {t === 'dados' ? 'Dados' : t === 'obras' ? `Obras (${obras.length})` : 'Propostas'}
          </button>
        ))}
      </div>

      {tab === 'dados' && (
        <div className="grid grid-cols-2 gap-x-8 gap-y-4">
          {field(cliente.tipo === 'pj' ? 'CNPJ' : 'CPF', cliente.cpf_cnpj)}
          {field('Email', cliente.email)}
          {field('Telefone', cliente.telefone)}
          {field('Endereço', cliente.endereco)}
          {field('Cidade', cliente.cidade)}
          {field('UF', cliente.estado)}
          {cliente.observacoes && (
            <div className="col-span-2">
              {field('Observações', cliente.observacoes)}
            </div>
          )}
        </div>
      )}

      {tab === 'obras' && (
        <>
          {obras.length === 0 ? (
            <p className="text-gray-400 text-sm text-center py-12">Nenhuma obra vinculada.</p>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
                  <tr>
                    <th className="text-left px-4 py-3">Obra</th>
                    <th className="text-left px-4 py-3">Tipo</th>
                    <th className="text-left px-4 py-3">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {obras.map(o => (
                    <tr
                      key={o.id}
                      className="border-t border-gray-100 hover:bg-gray-50 cursor-pointer"
                      onClick={() => navigate(`/obras/${o.id}`)}
                    >
                      <td className="px-4 py-3 font-medium text-gray-900">{o.nome}</td>
                      <td className="px-4 py-3 text-gray-500 capitalize">{o.tipo_obra.replace(/_/g, ' ')}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          o.estado === 'em_elaboracao' ? 'bg-blue-100 text-blue-700' :
                          o.estado === 'concluido' ? 'bg-green-100 text-green-700' :
                          'bg-gray-100 text-gray-600'
                        }`}>
                          {o.estado.replace(/_/g, ' ')}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {tab === 'propostas' && (
        <div className="text-center py-12 text-gray-400">
          <p className="text-sm">Propostas comerciais disponíveis em breve.</p>
        </div>
      )}

      {editOpen && (
        <ClienteModal
          cliente={cliente}
          onClose={() => setEditOpen(false)}
          onSuccess={updated => {
            setCliente(updated)
            setEditOpen(false)
            toast('Cliente atualizado')
          }}
        />
      )}
    </div>
  )
}
