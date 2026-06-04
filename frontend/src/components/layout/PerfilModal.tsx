import { useState, useEffect } from 'react'
import { updateNome, alterarSenha } from '@/api/perfil'
import { useAuth } from '@/hooks/useAuth'
import { toast } from '@/hooks/useToast'

interface Props {
  onClose: () => void
}

export default function PerfilModal({ onClose }: Props) {
  const { nome, papel, setNome } = useAuth()

  const [novoNome, setNovoNome] = useState(nome ?? '')
  const [savingNome, setSavingNome] = useState(false)

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  useEffect(() => {
    if (!savingNome) {
      setNovoNome(nome ?? '')
    }
  }, [nome, savingNome])

  const [senhaAtual, setSenhaAtual] = useState('')
  const [novaSenha, setNovaSenha] = useState('')
  const [confirmarSenha, setConfirmarSenha] = useState('')
  const [mostrarSenha, setMostrarSenha] = useState(false)
  const [savingSenha, setSavingSenha] = useState(false)
  const [senhaAtualErrada, setSenhaAtualErrada] = useState(false)

  async function handleSalvarNome() {
    if (!novoNome.trim()) return
    setSavingNome(true)
    try {
      await updateNome(novoNome.trim())
      setNome(novoNome.trim())
      toast('Nome atualizado')
    } catch {
      toast('Erro ao atualizar nome', 'error')
    } finally {
      setSavingNome(false)
    }
  }

  async function handleAlterarSenha() {
    if (!senhaAtual || novaSenha.length < 8 || novaSenha !== confirmarSenha) return
    setSavingSenha(true)
    setSenhaAtualErrada(false)
    try {
      await alterarSenha(senhaAtual, novaSenha)
      toast('Senha alterada com sucesso')
      setSenhaAtual('')
      setNovaSenha('')
      setConfirmarSenha('')
    } catch (e: any) {
      if (e?.response?.status === 400) {
        setSenhaAtualErrada(true)
      } else {
        toast('Erro ao alterar senha', 'error')
      }
    } finally {
      setSavingSenha(false)
    }
  }

  const senhaValida =
    senhaAtual.length > 0 &&
    novaSenha.length >= 8 &&
    novaSenha === confirmarSenha

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">Meu Perfil</h2>
          <button
            onClick={onClose}
            aria-label="Fechar"
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            ×
          </button>
        </div>

        <p className="text-xs text-gray-500 -mt-4">
          Papel: <span className="font-medium capitalize text-gray-700">{papel}</span>
        </p>

        {/* Alterar nome */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-800">Alterar nome</h3>
          <input
            type="text"
            value={novoNome}
            onChange={e => setNovoNome(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSalvarNome}
            disabled={!novoNome.trim() || savingNome}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
          >
            {savingNome ? 'Salvando…' : 'Salvar nome'}
          </button>
        </div>

        <hr className="border-gray-100" />

        {/* Alterar senha */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-800">Alterar senha</h3>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Senha atual</label>
            <input
              type={mostrarSenha ? 'text' : 'password'}
              value={senhaAtual}
              onChange={e => { setSenhaAtual(e.target.value); setSenhaAtualErrada(false) }}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${senhaAtualErrada ? 'border-red-400' : 'border-gray-300'}`}
            />
            {senhaAtualErrada && (
              <p className="text-xs text-red-500 mt-1">Senha atual incorreta</p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Nova senha</label>
            <div className="relative">
              <input
                type={mostrarSenha ? 'text' : 'password'}
                value={novaSenha}
                onChange={e => setNovaSenha(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 pr-16"
              />
              <button
                type="button"
                onClick={() => setMostrarSenha(v => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-500 hover:text-gray-700"
              >
                {mostrarSenha ? 'Ocultar' : 'Mostrar'}
              </button>
            </div>
            {novaSenha.length > 0 && novaSenha.length < 8 && (
              <p className="text-xs text-red-500 mt-1">Mínimo 8 caracteres</p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Confirmar nova senha</label>
            <input
              type={mostrarSenha ? 'text' : 'password'}
              value={confirmarSenha}
              onChange={e => setConfirmarSenha(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {confirmarSenha.length > 0 && novaSenha !== confirmarSenha && (
              <p className="text-xs text-red-500 mt-1">As senhas não coincidem</p>
            )}
          </div>
          <button
            onClick={handleAlterarSenha}
            disabled={!senhaValida || savingSenha}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
          >
            {savingSenha ? 'Salvando…' : 'Alterar senha'}
          </button>
        </div>
      </div>
    </div>
  )
}
