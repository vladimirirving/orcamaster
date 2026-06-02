import { useState } from 'react'
import { Trash2 } from 'lucide-react'
import { updateGrupo, deleteGrupo } from '@/api/grupos'
import { useOrcamento } from '@/stores/orcamento'
import { toast } from '@/hooks/useToast'
import type { Grupo } from '@/types'

export default function FormGrupo({ grupo, isReadOnly }: { grupo: Grupo; isReadOnly: boolean }) {
  const [nome, setNome] = useState(grupo.nome)
  const [codigo, setCodigo] = useState(grupo.codigo ?? '')
  const [ordem, setOrdem] = useState(String(grupo.ordem))
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const { updateGrupoNoStore, removeGrupoDoStore, fecharPainel } = useOrcamento()

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const updated = await updateGrupo(grupo.id, {
        nome,
        codigo: codigo || undefined,
        ordem: Number(ordem),
      })
      updateGrupoNoStore({ ...updated, filhos: grupo.filhos })
      toast('Grupo salvo')
    } catch {
      toast('Erro ao salvar grupo', 'error')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    try {
      await deleteGrupo(grupo.id)
      removeGrupoDoStore(grupo.id)
      fecharPainel()
      toast('Grupo removido')
    } catch {
      toast('Erro ao remover grupo', 'error')
    }
  }

  return (
    <form onSubmit={handleSave} className="flex flex-col gap-4">
      <div>
        <label className="block text-xs font-medium text-gray-500 mb-1">Nome</label>
        <input
          value={nome}
          onChange={e => setNome(e.target.value)}
          disabled={isReadOnly}
          className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
        />
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Código</label>
          <input
            value={codigo}
            onChange={e => setCodigo(e.target.value)}
            disabled={isReadOnly}
            placeholder="Opcional"
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-gray-500 mb-1">Ordem</label>
          <input
            type="number"
            value={ordem}
            onChange={e => setOrdem(e.target.value)}
            disabled={isReadOnly}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
          />
        </div>
      </div>

      {!isReadOnly && (
        <div className="flex gap-2 pt-2">
          <button
            type="submit"
            disabled={saving}
            className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Salvando...' : 'Salvar'}
          </button>
          <button
            type="button"
            onClick={() => {
              if (confirmDelete) handleDelete()
              else { setConfirmDelete(true); setTimeout(() => setConfirmDelete(false), 3000) }
            }}
            className={`p-2 rounded-lg text-sm transition-colors ${confirmDelete ? 'bg-red-100 text-red-600' : 'text-gray-400 hover:bg-gray-100'}`}
            title={confirmDelete ? 'Confirmar exclusão' : 'Excluir grupo'}
          >
            <Trash2 size={16} />
          </button>
        </div>
      )}
    </form>
  )
}
