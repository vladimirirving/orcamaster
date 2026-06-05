import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { ArrowLeft, Pencil } from 'lucide-react'
import { getFornecedor } from '@/api/fornecedores'
import { toast } from '@/hooks/useToast'
import type { Fornecedor } from '@/types'
import FornecedorModal from '@/components/fornecedores/FornecedorModal'

const CAT_LABELS: Record<string, string> = {
  material: 'Material', mao_obra: 'Mão de obra',
  equipamento: 'Equipamento', servico: 'Serviço',
}

type Tab = 'dados' | 'compras'

export default function FornecedorDetailPage() {
  const { id } = useParams<{ id: string }>()
  const fornecedorId = Number(id)
  const [fornecedor, setFornecedor] = useState<Fornecedor | null>(null)
  const [loading, setLoading] = useState(true)
  const [tab, setTab] = useState<Tab>('dados')
  const [editOpen, setEditOpen] = useState(false)

  useEffect(() => {
    getFornecedor(fornecedorId).then(setFornecedor).finally(() => setLoading(false))
  }, [fornecedorId])

  if (loading) return <div className="p-6 text-gray-500">Carregando…</div>
  if (!fornecedor) return <div className="p-6 text-red-500">Fornecedor não encontrado</div>

  const field = (label: string, value: string | null | undefined) => (
    <div key={label}>
      <p className="text-xs text-gray-500 uppercase tracking-wide mb-0.5">{label}</p>
      <p className="text-sm text-gray-900">{value || '—'}</p>
    </div>
  )

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <nav className="text-sm text-gray-500 mb-4 flex items-center gap-1">
        <Link to="/fornecedores" className="hover:text-blue-600 flex items-center gap-1">
          <ArrowLeft size={14} /> Fornecedores
        </Link>
        <span>›</span>
        <span className="text-gray-900 font-medium">{fornecedor.nome}</span>
      </nav>

      <div className="flex items-start justify-between mb-4">
        <h1 className="text-2xl font-bold text-gray-900">{fornecedor.nome}</h1>
        <button
          onClick={() => setEditOpen(true)}
          className="flex items-center gap-2 border border-gray-300 px-3 py-2 rounded-lg text-sm hover:bg-gray-50"
        >
          <Pencil size={14} /> Editar
        </button>
      </div>

      <div className="flex gap-0 border-b border-gray-200 mb-6">
        {(['dados', 'compras'] as Tab[]).map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t ? 'border-blue-600 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}>
            {t === 'dados' ? 'Dados' : 'Compras'}
          </button>
        ))}
      </div>

      {tab === 'dados' && (
        <div className="grid grid-cols-2 gap-x-8 gap-y-4">
          {field('CNPJ', fornecedor.cnpj)}
          {field('Email', fornecedor.email)}
          {field('Telefone', fornecedor.telefone)}
          {field('Endereço', fornecedor.endereco)}
          {field('Cidade', fornecedor.cidade)}
          {field('UF', fornecedor.estado)}
          {fornecedor.categorias && (
            <div className="col-span-2">
              <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Categorias</p>
              <div className="flex flex-wrap gap-1">
                {fornecedor.categorias.split(',').map(c => (
                  <span key={c} className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                    {CAT_LABELS[c] ?? c}
                  </span>
                ))}
              </div>
            </div>
          )}
          {fornecedor.observacoes && (
            <div className="col-span-2">{field('Observações', fornecedor.observacoes)}</div>
          )}
        </div>
      )}

      {tab === 'compras' && (
        <div className="text-center py-12 text-gray-400">
          <p className="text-sm">Disponível no Módulo 20 — Compras.</p>
        </div>
      )}

      {editOpen && (
        <FornecedorModal
          fornecedor={fornecedor}
          onClose={() => setEditOpen(false)}
          onSuccess={updated => {
            setFornecedor(updated)
            setEditOpen(false)
            toast('Fornecedor atualizado')
          }}
        />
      )}
    </div>
  )
}
