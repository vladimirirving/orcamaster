// frontend/src/components/clientes/ClienteModal.tsx
import { useState } from 'react'
import { createCliente, updateCliente } from '@/api/clientes'
import { toast } from '@/hooks/useToast'
import type { Cliente } from '@/types'

const UFS = ['AC','AL','AP','AM','BA','CE','DF','ES','GO','MA','MT','MS','MG','PA','PB','PR','PE','PI','RJ','RN','RS','RO','RR','SC','SP','SE','TO']

interface Props {
  cliente?: Cliente
  onClose: () => void
  onSuccess: (c: Cliente) => void
}

export default function ClienteModal({ cliente, onClose, onSuccess }: Props) {
  const isEdit = !!cliente
  const [tipo, setTipo] = useState(cliente?.tipo ?? 'pj')
  const [nome, setNome] = useState(cliente?.nome ?? '')
  const [cpfCnpj, setCpfCnpj] = useState(cliente?.cpf_cnpj ?? '')
  const [email, setEmail] = useState(cliente?.email ?? '')
  const [telefone, setTelefone] = useState(cliente?.telefone ?? '')
  const [endereco, setEndereco] = useState(cliente?.endereco ?? '')
  const [cidade, setCidade] = useState(cliente?.cidade ?? '')
  const [estado, setEstado] = useState(cliente?.estado ?? '')
  const [observacoes, setObservacoes] = useState(cliente?.observacoes ?? '')
  const [saving, setSaving] = useState(false)
  const [cpfError, setCpfError] = useState('')

  const isValid = nome.trim().length > 0

  async function handleSubmit() {
    if (!isValid) return
    setSaving(true)
    setCpfError('')
    const data = {
      tipo,
      nome: nome.trim(),
      cpf_cnpj: cpfCnpj.trim() || undefined,
      email: email.trim() || undefined,
      telefone: telefone.trim() || undefined,
      endereco: endereco.trim() || undefined,
      cidade: cidade.trim() || undefined,
      estado: estado || undefined,
      observacoes: observacoes.trim() || undefined,
    }
    try {
      const result = isEdit && cliente
        ? await updateCliente(cliente.id, data)
        : await createCliente(data)
      onSuccess(result)
    } catch (e: any) {
      if (e?.response?.status === 409) {
        setCpfError('CPF/CNPJ já cadastrado.')
      } else {
        toast('Erro ao salvar cliente', 'error')
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
            {isEdit ? 'Editar cliente' : 'Novo cliente'}
          </h2>
          <button onClick={onClose} aria-label="Fechar" className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Tipo</label>
            <div className="flex gap-3">
              {(['pj', 'pf'] as const).map(t => (
                <label key={t} className="flex items-center gap-1.5 text-sm cursor-pointer">
                  <input type="radio" name="tipo" value={t} checked={tipo === t} onChange={() => setTipo(t)} />
                  {t === 'pj' ? 'Pessoa Jurídica' : 'Pessoa Física'}
                </label>
              ))}
            </div>
          </div>

          <div>
            <label htmlFor="cliente-nome" className="block text-xs font-medium text-gray-700 mb-1">
              {tipo === 'pj' ? 'Razão Social' : 'Nome'} *
            </label>
            <input
              id="cliente-nome"
              type="text"
              value={nome}
              onChange={e => setNome(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label htmlFor="cliente-cpfcnpj" className="block text-xs font-medium text-gray-700 mb-1">
              {tipo === 'pj' ? 'CNPJ' : 'CPF'}
            </label>
            <input
              id="cliente-cpfcnpj"
              type="text"
              value={cpfCnpj}
              onChange={e => { setCpfCnpj(e.target.value); setCpfError('') }}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${cpfError ? 'border-red-400' : 'border-gray-300'}`}
            />
            {cpfError && <p role="alert" className="text-xs text-red-500 mt-1">{cpfError}</p>}
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="cliente-email" className="block text-xs font-medium text-gray-700 mb-1">Email</label>
              <input id="cliente-email" type="email" value={email} onChange={e => setEmail(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label htmlFor="cliente-tel" className="block text-xs font-medium text-gray-700 mb-1">Telefone</label>
              <input id="cliente-tel" type="tel" value={telefone} onChange={e => setTelefone(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
          </div>

          <div>
            <label htmlFor="cliente-end" className="block text-xs font-medium text-gray-700 mb-1">Endereço</label>
            <input id="cliente-end" type="text" value={endereco} onChange={e => setEndereco(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="cliente-cidade" className="block text-xs font-medium text-gray-700 mb-1">Cidade</label>
              <input id="cliente-cidade" type="text" value={cidade} onChange={e => setCidade(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
            </div>
            <div>
              <label htmlFor="cliente-uf" className="block text-xs font-medium text-gray-700 mb-1">UF</label>
              <select id="cliente-uf" value={estado} onChange={e => setEstado(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">—</option>
                {UFS.map(uf => <option key={uf} value={uf}>{uf}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label htmlFor="cliente-obs" className="block text-xs font-medium text-gray-700 mb-1">Observações</label>
            <textarea id="cliente-obs" value={observacoes} onChange={e => setObservacoes(e.target.value)} rows={2}
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
