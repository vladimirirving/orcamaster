import { useState } from 'react'
import { createFornecedor, updateFornecedor } from '@/api/fornecedores'
import { toast } from '@/hooks/useToast'
import type { Fornecedor } from '@/types'

const UFS = ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']
const CATEGORIAS = [
  { value: 'material', label: 'Material' },
  { value: 'mao_obra', label: 'Mão de obra' },
  { value: 'equipamento', label: 'Equipamento' },
  { value: 'servico', label: 'Serviço' },
]

interface Props {
  fornecedor?: Fornecedor
  onClose: () => void
  onSuccess: (f: Fornecedor) => void
}

export default function FornecedorModal({ fornecedor, onClose, onSuccess }: Props) {
  const isEdit = !!fornecedor
  const [nome, setNome] = useState(fornecedor?.nome ?? '')
  const [cnpj, setCnpj] = useState(fornecedor?.cnpj ?? '')
  const [email, setEmail] = useState(fornecedor?.email ?? '')
  const [telefone, setTelefone] = useState(fornecedor?.telefone ?? '')
  const [endereco, setEndereco] = useState(fornecedor?.endereco ?? '')
  const [cidade, setCidade] = useState(fornecedor?.cidade ?? '')
  const [estado, setEstado] = useState(fornecedor?.estado ?? '')
  const [cats, setCats] = useState<string[]>(
    fornecedor?.categorias ? fornecedor.categorias.split(',') : []
  )
  const [observacoes, setObservacoes] = useState(fornecedor?.observacoes ?? '')
  const [saving, setSaving] = useState(false)
  const [cnpjError, setCnpjError] = useState('')

  const toggleCat = (v: string) =>
    setCats(prev => prev.includes(v) ? prev.filter(x => x !== v) : [...prev, v])

  const isValid = nome.trim().length > 0

  async function handleSubmit() {
    if (!isValid) return
    setSaving(true)
    setCnpjError('')
    const data = {
      nome: nome.trim(),
      cnpj: cnpj.trim() || undefined,
      email: email.trim() || undefined,
      telefone: telefone.trim() || undefined,
      endereco: endereco.trim() || undefined,
      cidade: cidade.trim() || undefined,
      estado: estado || undefined,
      categorias: cats.length ? cats.join(',') : undefined,
      observacoes: observacoes.trim() || undefined,
    }
    try {
      const result = isEdit && fornecedor
        ? await updateFornecedor(fornecedor.id, data)
        : await createFornecedor(data)
      onSuccess(result)
    } catch (e: any) {
      if (e?.response?.status === 409) {
        setCnpjError('CNPJ já cadastrado.')
      } else {
        toast('Erro ao salvar fornecedor', 'error')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4 p-6 space-y-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">
            {isEdit ? 'Editar fornecedor' : 'Novo fornecedor'}
          </h2>
          <button onClick={onClose} aria-label="Fechar" className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>

        <div className="space-y-3">
          <div>
            <label htmlFor="forn-nome" className="block text-xs font-medium text-gray-700 mb-1">Nome / Razão Social *</label>
            <input id="forn-nome" type="text" value={nome} onChange={e => setNome(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div>
            <label htmlFor="forn-cnpj" className="block text-xs font-medium text-gray-700 mb-1">CNPJ</label>
            <input id="forn-cnpj" type="text" value={cnpj} onChange={e => { setCnpj(e.target.value); setCnpjError('') }}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${cnpjError ? 'border-red-400' : 'border-gray-300'}`} />
            {cnpjError && <p role="alert" className="text-xs text-red-500 mt-1">{cnpjError}</p>}
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="forn-email" className="block text-xs font-medium text-gray-700 mb-1">Email</label>
              <input id="forn-email" type="email" value={email} onChange={e => setEmail(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label htmlFor="forn-tel" className="block text-xs font-medium text-gray-700 mb-1">Telefone</label>
              <input id="forn-tel" type="tel" value={telefone} onChange={e => setTelefone(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>
          <div>
            <label htmlFor="forn-end" className="block text-xs font-medium text-gray-700 mb-1">Endereço</label>
            <input id="forn-end" type="text" value={endereco} onChange={e => setEndereco(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="forn-cidade" className="block text-xs font-medium text-gray-700 mb-1">Cidade</label>
              <input id="forn-cidade" type="text" value={cidade} onChange={e => setCidade(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label htmlFor="forn-uf" className="block text-xs font-medium text-gray-700 mb-1">UF</label>
              <select id="forn-uf" value={estado} onChange={e => setEstado(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">—</option>
                {UFS.map(uf => <option key={uf} value={uf}>{uf}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Categorias</label>
            <div className="flex flex-wrap gap-2">
              {CATEGORIAS.map(cat => (
                <label key={cat.value} className="flex items-center gap-1.5 text-sm cursor-pointer">
                  <input type="checkbox" checked={cats.includes(cat.value)} onChange={() => toggleCat(cat.value)} />
                  {cat.label}
                </label>
              ))}
            </div>
          </div>
          <div>
            <label htmlFor="forn-obs" className="block text-xs font-medium text-gray-700 mb-1">Observações</label>
            <textarea id="forn-obs" value={observacoes} onChange={e => setObservacoes(e.target.value)} rows={2}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none" />
          </div>
        </div>

        <div className="flex gap-2 justify-end pt-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancelar</button>
          <button
            onClick={handleSubmit}
            disabled={!isValid || saving}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
          >
            {saving ? 'Salvando…' : isEdit ? 'Salvar' : 'Criar'}
          </button>
        </div>
      </div>
    </div>
  )
}
