import { useState, useEffect } from 'react'
import { updateObra } from '@/api/obras'
import { listUsuarios } from '@/api/usuarios'
import { toast } from '@/hooks/useToast'
import type { Obra, Usuario } from '@/types'

const TIPOS = [
  { value: 'rodovia', label: 'Rodovia' },
  { value: 'saneamento', label: 'Saneamento' },
  { value: 'ponte', label: 'Ponte' },
  { value: 'rede_eletrica', label: 'Rede Elétrica' },
  { value: 'outro', label: 'Outro' },
]

const ESTADOS = [
  { value: 'em_elaboracao', label: 'Em elaboração' },
  { value: 'concluido', label: 'Concluído' },
  { value: 'arquivado', label: 'Arquivado' },
]

const UFS = ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']

interface Props {
  obra: Obra
  onClose: () => void
  onSuccess: (updated: Obra) => void
}

export default function ObraEditModal({ obra, onClose, onSuccess }: Props) {
  const [nome, setNome] = useState(obra.nome)
  const [tipo, setTipo] = useState(obra.tipo_obra)
  const [estado, setEstado] = useState(obra.estado)
  const [numeroProcesso, setNumeroProcesso] = useState(obra.numero_processo ?? '')
  const [uf, setUf] = useState(obra.uf ?? '')
  const [municipio, setMunicipio] = useState(obra.municipio ?? '')
  const [dataPrazo, setDataPrazo] = useState(obra.data_prazo ?? '')
  const [responsavelId, setResponsavelId] = useState<number | ''>(obra.responsavel_id ?? '')
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    listUsuarios()
      .then(us => setUsuarios(us.filter(u => u.ativo)))
      .catch(() => {/* silencioso — campo fica sem sugestões */})
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!nome.trim()) return
    setSaving(true)
    try {
      const updated = await updateObra(obra.id, {
        nome: nome.trim(),
        tipo_obra: tipo,
        estado,
        numero_processo: numeroProcesso.trim() || null,
        uf: uf || null,
        municipio: municipio.trim() || null,
        data_prazo: dataPrazo || null,
        responsavel_id: responsavelId !== '' ? responsavelId : null,
      })
      onSuccess(updated)
      toast('Obra atualizada')
    } catch {
      toast('Erro ao atualizar obra', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 pb-4">
          <h2 className="text-base font-semibold text-gray-900">Editar obra</h2>
          <button
            onClick={onClose}
            aria-label="Fechar"
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="px-6 pb-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Nome *</label>
            <input
              required
              value={nome}
              onChange={e => setNome(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Tipo</label>
              <select
                value={tipo}
                onChange={e => setTipo(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {TIPOS.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Estado</label>
              <select
                value={estado}
                onChange={e => setEstado(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {ESTADOS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Número do processo</label>
            <input
              value={numeroProcesso}
              onChange={e => setNumeroProcesso(e.target.value)}
              placeholder="Ex: 2024/0089"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">UF</label>
              <select
                value={uf}
                onChange={e => setUf(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">—</option>
                {UFS.map(s => <option key={s} value={s}>{s}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Município</label>
              <input
                value={municipio}
                onChange={e => setMunicipio(e.target.value)}
                placeholder="Ex: Campinas"
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Data prazo</label>
              <input
                type="date"
                value={dataPrazo}
                onChange={e => setDataPrazo(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Responsável</label>
              <select
                value={responsavelId}
                onChange={e => setResponsavelId(e.target.value ? Number(e.target.value) : '')}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">—</option>
                {usuarios.map(u => (
                  <option key={u.id} value={u.id}>{u.nome}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
            >
              Cancelar
            </button>
            <button
              type="submit"
              disabled={saving || !nome.trim()}
              className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
            >
              {saving ? 'Salvando…' : 'Salvar'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
