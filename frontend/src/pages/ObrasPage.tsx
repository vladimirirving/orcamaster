import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import * as Dialog from '@radix-ui/react-dialog'
import { Plus } from 'lucide-react'
import { getObras, createObra } from '@/api/obras'
import { toast } from '@/hooks/useToast'
import type { Obra } from '@/types'

const TIPOS = [
  { value: 'rodovia', label: 'Rodovia' },
  { value: 'saneamento', label: 'Saneamento' },
  { value: 'ponte', label: 'Ponte' },
  { value: 'rede_eletrica', label: 'Rede Elétrica' },
  { value: 'outro', label: 'Outro' },
]

export default function ObrasPage() {
  const [obras, setObras] = useState<Obra[]>([])
  const [loading, setLoading] = useState(true)
  const [open, setOpen] = useState(false)
  const [nome, setNome] = useState('')
  const [tipo, setTipo] = useState('rodovia')
  const [saving, setSaving] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    getObras().then(setObras).finally(() => setLoading(false))
  }, [])

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    try {
      const obra = await createObra({ nome, tipo_obra: tipo })
      setObras(prev => [...prev, obra])
      setOpen(false)
      setNome('')
      toast('Obra criada com sucesso')
    } catch {
      toast('Erro ao criar obra', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Obras</h1>
        <Dialog.Root open={open} onOpenChange={setOpen}>
          <Dialog.Trigger asChild>
            <button className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 text-sm font-medium">
              <Plus size={16} /> Nova Obra
            </button>
          </Dialog.Trigger>
          <Dialog.Portal>
            <Dialog.Overlay className="fixed inset-0 bg-black/50 z-40" />
            <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl p-6 z-50 w-full max-w-md">
              <Dialog.Title className="text-lg font-bold mb-4">Nova Obra</Dialog.Title>
              <form onSubmit={handleCreate} className="flex flex-col gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nome *</label>
                  <input
                    required
                    value={nome}
                    onChange={e => setNome(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Ex: Rodovia SP-150 trecho km 12-45"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
                  <select
                    value={tipo}
                    onChange={e => setTipo(e.target.value)}
                    className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {TIPOS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </div>
                <div className="flex justify-end gap-3 pt-2">
                  <Dialog.Close asChild>
                    <button type="button" className="px-4 py-2 text-sm text-gray-600 hover:text-gray-900">Cancelar</button>
                  </Dialog.Close>
                  <button
                    type="submit"
                    disabled={saving}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
                  >
                    {saving ? 'Criando...' : 'Criar'}
                  </button>
                </div>
              </form>
            </Dialog.Content>
          </Dialog.Portal>
        </Dialog.Root>
      </div>

      {loading && <p className="text-gray-500">Carregando...</p>}

      {!loading && obras.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg">Nenhuma obra cadastrada</p>
          <p className="text-sm mt-1">Clique em "Nova Obra" para começar</p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {obras.map(obra => (
          <button
            key={obra.id}
            onClick={() => navigate(`/obras/${obra.id}`)}
            className="text-left bg-white rounded-xl shadow-sm border border-gray-200 p-5 hover:border-blue-400 hover:shadow-md transition-all"
          >
            <h3 className="font-semibold text-gray-900 mb-1 line-clamp-2">{obra.nome}</h3>
            <p className="text-sm text-gray-500 capitalize">{obra.tipo_obra.replace('_', ' ')}</p>
            {obra.municipio && obra.uf && (
              <p className="text-xs text-gray-400 mt-1">{obra.municipio} / {obra.uf}</p>
            )}
            <span className={`inline-block mt-3 text-xs px-2 py-0.5 rounded-full font-medium
              ${obra.estado === 'em_elaboracao' ? 'bg-blue-100 text-blue-700' :
                obra.estado === 'concluido' ? 'bg-green-100 text-green-700' :
                'bg-gray-100 text-gray-600'}`}>
              {obra.estado.replace('_', ' ')}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
