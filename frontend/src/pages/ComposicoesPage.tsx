import { useState, useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { listComposicoesProprias, deleteComposicao } from '@/api/composicoes'
import { toast } from '@/hooks/useToast'
import { fmtBRL } from '@/lib/utils'
import type { Composicao } from '@/types'
import ComposicaoModal from '@/components/composicoes/ComposicaoModal'

export default function ComposicoesPage() {
  const { papel } = useAuth()
  const [composicoes, setComposicoes] = useState<Composicao[]>([])
  const [loading, setLoading] = useState(true)
  const [q, setQ] = useState('')
  const [modal, setModal] = useState<'criar' | 'editar' | null>(null)
  const [editTarget, setEditTarget] = useState<Composicao | null>(null)
  const [confirmDelete, setConfirmDelete] = useState<number | null>(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    if (papel !== 'admin') return
    const timer = setTimeout(() => {
      setLoading(true)
      listComposicoesProprias(q || undefined)
        .then(setComposicoes)
        .catch(() => toast('Erro ao carregar composições', 'error'))
        .finally(() => setLoading(false))
    }, q ? 300 : 0)
    return () => clearTimeout(timer)
  }, [q, papel])

  if (papel === null) return <div className="p-6 text-gray-400">Carregando...</div>
  if (papel !== 'admin') return <Navigate to="/obras" replace />

  async function handleDelete(id: number) {
    setDeleting(true)
    try {
      await deleteComposicao(id)
      setConfirmDelete(null)
      listComposicoesProprias(q || undefined)
        .then(setComposicoes)
        .catch(() => toast('Erro ao carregar composições', 'error'))
    } catch {
      toast('Erro ao excluir composição', 'error')
      setConfirmDelete(null)
    } finally {
      setDeleting(false)
    }
  }

  function handleSuccess() {
    setModal(null)
    setEditTarget(null)
    listComposicoesProprias(q || undefined)
      .then(setComposicoes)
      .catch(() => toast('Erro ao carregar composições', 'error'))
  }

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-xl font-bold text-gray-900 mb-4">Banco de Composições</h1>

      <div className="flex items-center gap-3 mb-4">
        <input
          type="text"
          placeholder="Buscar por código ou descrição…"
          value={q}
          onChange={e => setQ(e.target.value)}
          className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <button
          onClick={() => setModal('criar')}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 shrink-0"
        >
          + Nova composição
        </button>
      </div>

      {loading ? (
        <div className="bg-white rounded-xl border border-gray-200 divide-y divide-gray-100">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="px-4 py-3 flex gap-4 animate-pulse">
              <div className="h-4 bg-gray-200 rounded w-24" />
              <div className="h-4 bg-gray-200 rounded flex-1" />
              <div className="h-4 bg-gray-200 rounded w-12" />
              <div className="h-4 bg-gray-200 rounded w-20" />
            </div>
          ))}
        </div>
      ) : composicoes.length === 0 ? (
        <p className="text-sm text-gray-500">
          {q
            ? `Nenhum resultado para «${q}».`
            : 'Nenhuma composição própria cadastrada.'}
        </p>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Código
                </th>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Descrição
                </th>
                <th className="text-left px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Unidade
                </th>
                <th className="text-right px-4 py-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Preço Unit.
                </th>
                <th className="px-4 py-2 w-28" />
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {composicoes.map(c => (
                <tr key={c.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 font-mono text-xs text-gray-700">{c.codigo}</td>
                  <td className="px-4 py-3 text-gray-900">{c.descricao}</td>
                  <td className="px-4 py-3 text-gray-500">{c.unidade}</td>
                  <td className="px-4 py-3 text-right text-gray-900">{fmtBRL(c.preco_unitario)}</td>
                  <td className="px-4 py-3">
                    {confirmDelete === c.id ? (
                      <div className="flex items-center gap-2 justify-end">
                        <button
                          onClick={() => handleDelete(c.id)}
                          disabled={deleting}
                          aria-label={`Confirmar exclusão de ${c.codigo}`}
                          className="text-xs text-white bg-red-600 hover:bg-red-700 px-2 py-1 rounded disabled:opacity-40"
                        >
                          Confirmar
                        </button>
                        <button
                          onClick={() => setConfirmDelete(null)}
                          aria-label={`Cancelar exclusão de ${c.codigo}`}
                          className="text-xs text-gray-500 hover:text-gray-700"
                        >
                          Cancelar
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 justify-end">
                        <button
                          onClick={() => { setEditTarget(c); setModal('editar') }}
                          aria-label="Editar"
                          className="text-gray-400 hover:text-blue-600 p-1 text-base leading-none"
                        >
                          ✎
                        </button>
                        <button
                          onClick={() => setConfirmDelete(c.id)}
                          aria-label="Excluir"
                          className="text-gray-400 hover:text-red-600 p-1"
                        >
                          🗑
                        </button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {modal === 'criar' && (
        <ComposicaoModal onClose={() => setModal(null)} onSuccess={handleSuccess} />
      )}
      {modal === 'editar' && editTarget && (
        <ComposicaoModal
          composicao={editTarget}
          onClose={() => { setModal(null); setEditTarget(null) }}
          onSuccess={handleSuccess}
        />
      )}
    </div>
  )
}
