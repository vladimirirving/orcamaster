// frontend/src/pages/ClientesPage.tsx
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { UserPlus } from 'lucide-react'
import { listClientes, deleteCliente } from '@/api/clientes'
import { toast } from '@/hooks/useToast'
import type { Cliente } from '@/types'
import ClienteModal from '@/components/clientes/ClienteModal'

export default function ClientesPage() {
  const [clientes, setClientes] = useState<Cliente[]>([])
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null)
  const navigate = useNavigate()

  async function reload(query = q) {
    const data = await listClientes(query || undefined)
    setClientes(data)
  }

  useEffect(() => {
    reload().finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    const t = setTimeout(() => reload(q), 300)
    return () => clearTimeout(t)
  }, [q])

  async function handleDelete(id: number) {
    try {
      await deleteCliente(id)
      setClientes(prev => prev.filter(c => c.id !== id))
      setConfirmDelete(null)
      toast('Cliente excluído')
    } catch (e: any) {
      if (e?.response?.status === 409) {
        toast('Cliente possui obras vinculadas e não pode ser excluído', 'error')
      } else {
        toast('Erro ao excluir cliente', 'error')
      }
      setConfirmDelete(null)
    }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Clientes</h1>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium"
        >
          <UserPlus size={16} /> Novo Cliente
        </button>
      </div>

      <input
        type="text"
        value={q}
        onChange={e => setQ(e.target.value)}
        placeholder="Buscar por nome ou CPF/CNPJ…"
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />

      {loading && <p className="text-gray-500 text-sm">Carregando…</p>}

      {!loading && clientes.length === 0 && (
        <p className="text-gray-400 text-sm text-center py-12">Nenhum cliente cadastrado.</p>
      )}

      {!loading && clientes.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
              <tr>
                <th className="text-left px-4 py-3">Nome</th>
                <th className="text-left px-4 py-3">CPF/CNPJ</th>
                <th className="text-left px-4 py-3">Email</th>
                <th className="text-left px-4 py-3">Telefone</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {clientes.map(c => (
                <tr
                  key={c.id}
                  className="border-t border-gray-100 hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/clientes/${c.id}`)}
                >
                  <td className="px-4 py-3 font-medium text-gray-900">
                    {c.nome}
                    <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full ${c.tipo === 'pj' ? 'bg-blue-100 text-blue-700' : 'bg-purple-100 text-purple-700'}`}>
                      {c.tipo === 'pj' ? 'PJ' : 'PF'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500">{c.cpf_cnpj ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-500">{c.email ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-500">{c.telefone ?? '—'}</td>
                  <td className="px-4 py-3 text-right" onClick={e => e.stopPropagation()}>
                    {confirmDelete === c.id ? (
                      <span className="flex items-center gap-2 justify-end">
                        <button onClick={() => handleDelete(c.id)} className="text-xs bg-red-600 text-white px-2 py-1 rounded">Confirmar</button>
                        <button onClick={() => setConfirmDelete(null)} className="text-xs text-gray-500">Cancelar</button>
                      </span>
                    ) : (
                      <button
                        onClick={() => setConfirmDelete(c.id)}
                        className="text-gray-400 hover:text-red-500 text-xs"
                        aria-label={`Excluir ${c.nome}`}
                      >
                        🗑
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <ClienteModal
          onClose={() => setShowModal(false)}
          onSuccess={c => {
            setClientes(prev => [c, ...prev])
            setShowModal(false)
            toast('Cliente criado')
          }}
        />
      )}
    </div>
  )
}
