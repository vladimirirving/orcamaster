import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Building2 } from 'lucide-react'
import { listFornecedores, deleteFornecedor } from '@/api/fornecedores'
import { toast } from '@/hooks/useToast'
import type { Fornecedor } from '@/types'
import FornecedorModal from '@/components/fornecedores/FornecedorModal'

const CAT_LABELS: Record<string, string> = {
  material: 'Material', mao_obra: 'Mão de obra',
  equipamento: 'Equipamento', servico: 'Serviço',
}

export default function FornecedoresPage() {
  const [fornecedores, setFornecedores] = useState<Fornecedor[]>([])
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null)
  const navigate = useNavigate()

  async function reload(query = q) {
    const data = await listFornecedores(query ? { q: query } : {})
    setFornecedores(data)
  }

  useEffect(() => { reload().finally(() => setLoading(false)) }, [])
  useEffect(() => {
    const t = setTimeout(() => reload(q), 300)
    return () => clearTimeout(t)
  }, [q])

  async function handleDelete(id: number) {
    try {
      await deleteFornecedor(id)
      setFornecedores(prev => prev.filter(f => f.id !== id))
      setConfirmDelete(null)
      toast('Fornecedor excluído')
    } catch {
      toast('Erro ao excluir fornecedor', 'error')
      setConfirmDelete(null)
    }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Fornecedores</h1>
        <button
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium"
        >
          <Building2 size={16} /> Novo Fornecedor
        </button>
      </div>

      <input
        type="text"
        value={q}
        onChange={e => setQ(e.target.value)}
        placeholder="Buscar por nome ou CNPJ…"
        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
      />

      {loading && <p className="text-gray-500 text-sm">Carregando…</p>}
      {!loading && fornecedores.length === 0 && (
        <p className="text-gray-400 text-sm text-center py-12">Nenhum fornecedor cadastrado.</p>
      )}
      {!loading && fornecedores.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-xs text-gray-500 uppercase tracking-wide">
              <tr>
                <th className="text-left px-4 py-3">Nome</th>
                <th className="text-left px-4 py-3">CNPJ</th>
                <th className="text-left px-4 py-3">Telefone</th>
                <th className="text-left px-4 py-3">Categorias</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {fornecedores.map(f => (
                <tr key={f.id} className="border-t border-gray-100 hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/fornecedores/${f.id}`)}>
                  <td className="px-4 py-3 font-medium text-gray-900">{f.nome}</td>
                  <td className="px-4 py-3 text-gray-500">{f.cnpj ?? '—'}</td>
                  <td className="px-4 py-3 text-gray-500">{f.telefone ?? '—'}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {f.categorias ? f.categorias.split(',').map(c => (
                        <span key={c} className="text-xs bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded">
                          {CAT_LABELS[c] ?? c}
                        </span>
                      )) : <span className="text-gray-400">—</span>}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right" onClick={e => e.stopPropagation()}>
                    {confirmDelete === f.id ? (
                      <span className="flex items-center gap-2 justify-end">
                        <button onClick={() => handleDelete(f.id)} className="text-xs bg-red-600 text-white px-2 py-1 rounded">Confirmar</button>
                        <button onClick={() => setConfirmDelete(null)} className="text-xs text-gray-500">Cancelar</button>
                      </span>
                    ) : (
                      <button onClick={() => setConfirmDelete(f.id)}
                        className="text-gray-400 hover:text-red-500 text-xs"
                        aria-label={`Excluir ${f.nome}`}>🗑</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {showModal && (
        <FornecedorModal
          onClose={() => setShowModal(false)}
          onSuccess={f => {
            setFornecedores(prev => [f, ...prev])
            setShowModal(false)
            toast('Fornecedor criado')
          }}
        />
      )}
    </div>
  )
}
