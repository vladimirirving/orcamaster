// frontend/src/pages/InsumosPage.tsx
import { useState, useEffect } from 'react'
import { useAuth } from '@/hooks/useAuth'
import { listInsumos, deleteInsumo } from '@/api/insumos_item'
import { toast } from '@/hooks/useToast'
import { fmtBRL } from '@/lib/utils'
import type { InsumoItem } from '@/types'
import InsumoItemModal from '@/components/insumos/InsumoItemModal'

const UFS = ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS',
             'MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC',
             'SP','SE','TO']

const BANCO_LABELS: Record<string, string> = {
  sinapi: 'SINAPI', sicro: 'SICRO', propria: 'Próprio',
}
const BANCO_BADGE: Record<string, string> = {
  sinapi: 'bg-blue-100 text-blue-700',
  sicro: 'bg-orange-100 text-orange-700',
  propria: 'bg-green-100 text-green-700',
}
const TIPO_LABELS: Record<string, string> = {
  mao_obra: 'Mão de Obra', material: 'Material', equipamento: 'Equipamento',
}
const PAGE_SIZE = 50

const inputCls =
  'w-full border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white'

export default function InsumosPage() {
  const { papel } = useAuth()
  const isAdmin = papel === 'admin'

  // Filter state
  const [q, setQ] = useState('')
  const [banco, setBanco] = useState('')
  const [estado, setEstado] = useState('')
  const [tipo, setTipo] = useState('')
  const [dataRef, setDataRef] = useState('')
  const [orderBy, setOrderBy] = useState('descricao')

  // Results
  const [items, setItems] = useState<InsumoItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [loading, setLoading] = useState(false)

  // Modal / delete state
  const [modal, setModal] = useState<'criar' | 'editar' | null>(null)
  const [editTarget, setEditTarget] = useState<InsumoItem | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null)
  const [deleting, setDeleting] = useState(false)

  async function buscar(pg: number) {
    setLoading(true)
    try {
      const data = await listInsumos({
        q: q || undefined,
        banco: banco || undefined,
        estado: estado || undefined,
        tipo: tipo || undefined,
        data_ref: dataRef || undefined,
        order_by: orderBy,
        page: pg,
      })
      setItems(data.items)
      setTotal(data.total)
      setPage(pg)
    } catch {
      toast('Erro ao carregar insumos', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { buscar(1) }, [])  // carga inicial

  async function handleDelete(id: number) {
    setDeleting(true)
    try {
      await deleteInsumo(id)
      setConfirmDelete(null)
      toast('Insumo excluído')
      buscar(page)
    } catch {
      toast('Erro ao excluir insumo', 'error')
      setConfirmDelete(null)
    } finally {
      setDeleting(false)
    }
  }

  function handleSuccess() {
    setModal(null)
    setEditTarget(null)
    buscar(page)
  }

  const totalPages = Math.ceil(total / PAGE_SIZE)
  const showFrom = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1
  const showTo = Math.min(page * PAGE_SIZE, total)

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h1 className="text-xl font-bold text-gray-900">Insumos</h1>
        {isAdmin && (
          <button
            onClick={() => setModal('criar')}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
          >
            + Novo Insumo
          </button>
        )}
      </div>

      {/* Search panel */}
      <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-4 mb-4">
        <div className="text-xs font-semibold text-indigo-700 uppercase tracking-wide mb-3">
          Pesquisa
        </div>
        {/* Row 1 */}
        <div className="grid grid-cols-3 gap-3 mb-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Filtro</label>
            <input
              type="text"
              value={q}
              onChange={e => setQ(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && buscar(1)}
              placeholder="Descrição ou Código"
              className={inputCls}
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Ordenar por</label>
            <select value={orderBy} onChange={e => setOrderBy(e.target.value)} className={inputCls}>
              <option value="descricao">Descrição</option>
              <option value="codigo">Código</option>
              <option value="preco_nao_desonerado">Preço Não Desonerado</option>
              <option value="preco_desonerado">Preço Desonerado</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Tipo</label>
            <select value={tipo} onChange={e => setTipo(e.target.value)} className={inputCls}>
              <option value="">Todos</option>
              <option value="mao_obra">Mão de Obra</option>
              <option value="material">Material</option>
              <option value="equipamento">Equipamento</option>
            </select>
          </div>
        </div>
        {/* Row 2 */}
        <div className="grid grid-cols-4 gap-3 items-end">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Banco</label>
            <select value={banco} onChange={e => setBanco(e.target.value)} className={inputCls}>
              <option value="">Todos</option>
              <option value="sinapi">SINAPI</option>
              <option value="sicro">SICRO</option>
              <option value="propria">Próprio</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Estado</label>
            <select value={estado} onChange={e => setEstado(e.target.value)} className={inputCls}>
              <option value="">Todos</option>
              {UFS.map(uf => <option key={uf} value={uf}>{uf}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Data Ref.</label>
            <input
              type="month"
              value={dataRef}
              onChange={e => setDataRef(e.target.value)}
              className={inputCls}
            />
          </div>
          <div>
            <button
              onClick={() => buscar(1)}
              className="w-full bg-blue-600 text-white px-4 py-1.5 rounded-lg text-sm font-medium hover:bg-blue-700"
            >
              🔍 Buscar
            </button>
          </div>
        </div>
      </div>

      {/* Table / loading / empty */}
      {loading ? (
        <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="px-4 py-3 flex gap-4 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-16" />
              <div className="h-4 bg-gray-200 rounded w-20" />
              <div className="h-4 bg-gray-200 rounded flex-1" />
              <div className="h-4 bg-gray-200 rounded w-10" />
              <div className="h-4 bg-gray-200 rounded w-20" />
              <div className="h-4 bg-gray-200 rounded w-24" />
              <div className="h-4 bg-gray-200 rounded w-24" />
            </div>
          ))}
        </div>
      ) : items.length === 0 ? (
        <p className="text-sm text-gray-500 py-6">
          Nenhum insumo encontrado para os filtros selecionados.
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-x-auto">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide whitespace-nowrap">Banco</th>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide whitespace-nowrap">Código</th>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">Descrição</th>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">Un.</th>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide whitespace-nowrap">Tipo</th>
                <th className="text-right px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide whitespace-nowrap">Não Deson.</th>
                <th className="text-right px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide whitespace-nowrap">Desonerado</th>
                {isAdmin && <th className="px-4 py-2 w-24" />}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {items.map(item => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 whitespace-nowrap">
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        BANCO_BADGE[item.banco] ?? 'bg-gray-100 text-gray-700'
                      }`}
                    >
                      {BANCO_LABELS[item.banco] ?? item.banco}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-gray-700 whitespace-nowrap">
                    {item.codigo}
                  </td>
                  <td className="px-4 py-3 text-gray-900 max-w-xs">
                    <span className="block truncate" title={item.descricao}>
                      {item.descricao}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap">{item.unidade}</td>
                  <td className="px-4 py-3 text-gray-500 whitespace-nowrap">
                    {TIPO_LABELS[item.tipo] ?? item.tipo}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-900 whitespace-nowrap">
                    {fmtBRL(item.preco_nao_desonerado)}
                  </td>
                  <td className="px-4 py-3 text-right text-gray-900 whitespace-nowrap">
                    {fmtBRL(item.preco_desonerado)}
                  </td>
                  {isAdmin && (
                    <td className="px-4 py-3">
                      {item.banco === 'propria' ? (
                        confirmDelete === item.id ? (
                          <div className="flex items-center gap-2 justify-end">
                            <button
                              onClick={() => handleDelete(item.id)}
                              disabled={deleting}
                              className="text-xs text-white bg-red-600 hover:bg-red-700 px-2 py-1 rounded disabled:opacity-40"
                            >
                              Confirmar
                            </button>
                            <button
                              onClick={() => setConfirmDelete(null)}
                              className="text-xs text-gray-500 hover:text-gray-700"
                            >
                              Cancelar
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2 justify-end">
                            <button
                              onClick={() => { setEditTarget(item); setModal('editar') }}
                              aria-label="Editar"
                              className="text-gray-400 hover:text-blue-600 p-1 text-base leading-none"
                            >
                              ✎
                            </button>
                            <button
                              onClick={() => setConfirmDelete(item.id)}
                              aria-label="Excluir"
                              className="text-gray-400 hover:text-red-600 p-1"
                            >
                              🗑
                            </button>
                          </div>
                        )
                      ) : null}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {total > 0 && (
        <div className="flex items-center justify-between mt-4">
          <button
            onClick={() => buscar(page - 1)}
            disabled={page <= 1}
            className="px-4 py-2 text-sm border border-gray-300 rounded-lg bg-white hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            ← Anterior
          </button>
          <span className="text-sm text-gray-500">
            {showFrom}–{showTo} de {total.toLocaleString('pt-BR')} insumos
          </span>
          <button
            onClick={() => buscar(page + 1)}
            disabled={page >= totalPages}
            className="px-4 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Próximo →
          </button>
        </div>
      )}

      {/* Modals */}
      {modal === 'criar' && (
        <InsumoItemModal onClose={() => setModal(null)} onSuccess={handleSuccess} />
      )}
      {modal === 'editar' && editTarget && (
        <InsumoItemModal
          insumo={editTarget}
          onClose={() => { setModal(null); setEditTarget(null) }}
          onSuccess={handleSuccess}
        />
      )}
    </div>
  )
}
