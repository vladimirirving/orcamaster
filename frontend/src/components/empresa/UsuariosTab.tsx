import { useState, useEffect } from 'react'
import { listUsuarios, createUsuario, updateUsuario } from '@/api/usuarios'
import { useAuth } from '@/hooks/useAuth'
import { toast } from '@/hooks/useToast'
import type { Usuario } from '@/types'

const PAPEL_LABELS: Record<string, string> = {
  admin: 'Administrador',
  orcamentista: 'Orçamentista',
  visualizador: 'Visualizador',
}

const PAPEL_BADGE: Record<string, string> = {
  admin: 'bg-purple-100 text-purple-700',
  orcamentista: 'bg-blue-100 text-blue-700',
  visualizador: 'bg-gray-100 text-gray-600',
}

export default function UsuariosTab() {
  const { userId } = useAuth()
  const [usuarios, setUsuarios] = useState<Usuario[]>([])
  const [loading, setLoading] = useState(true)
  const [modal, setModal] = useState<'criar' | 'editar' | null>(null)
  const [editTarget, setEditTarget] = useState<Usuario | null>(null)

  async function reload() {
    try {
      setUsuarios(await listUsuarios())
    } catch {
      toast('Erro ao carregar usuários', 'error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { reload() }, [])

  function openEditar(u: Usuario) {
    setEditTarget(u)
    setModal('editar')
  }

  if (loading) {
    return <div className="py-8 text-center text-gray-400 text-sm">Carregando...</div>
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500">
          {usuarios.length} membro{usuarios.length !== 1 ? 's' : ''}
        </p>
        <button
          onClick={() => setModal('criar')}
          className="bg-blue-600 text-white px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-blue-700"
        >
          + Adicionar membro
        </button>
      </div>

      <div className="divide-y divide-gray-100 border border-gray-200 rounded-xl overflow-hidden">
        {usuarios.map(u => (
          <div key={u.id} className="flex items-center gap-3 px-4 py-3 bg-white">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {u.nome}
                {u.id === userId && (
                  <span className="ml-2 text-xs text-gray-400">(você)</span>
                )}
              </p>
              <p className="text-xs text-gray-500 truncate">{u.email}</p>
            </div>
            <span
              className={`text-xs font-medium px-2 py-0.5 rounded-full ${PAPEL_BADGE[u.papel] ?? 'bg-gray-100 text-gray-600'}`}
            >
              {PAPEL_LABELS[u.papel] ?? u.papel}
            </span>
            <span
              className={`text-xs font-medium px-2 py-0.5 rounded-full ${u.ativo ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'}`}
            >
              {u.ativo ? 'Ativo' : 'Inativo'}
            </span>
            <button
              onClick={() => openEditar(u)}
              disabled={userId === null || u.id === userId}
              className="text-gray-400 hover:text-blue-600 disabled:opacity-30 disabled:cursor-not-allowed p-1 text-base leading-none"
              title={userId === null || u.id === userId ? 'Não é possível editar seu próprio perfil' : 'Editar'}
            >
              ✎
            </button>
          </div>
        ))}
      </div>

      {modal === 'criar' && (
        <CriarModal
          onClose={() => setModal(null)}
          onSuccess={() => { setModal(null); reload() }}
        />
      )}
      {modal === 'editar' && editTarget && (
        <EditarModal
          usuario={editTarget}
          onClose={() => { setModal(null); setEditTarget(null) }}
          onSuccess={() => { setModal(null); setEditTarget(null); reload() }}
        />
      )}
    </div>
  )
}

function CriarModal({
  onClose,
  onSuccess,
}: {
  onClose: () => void
  onSuccess: () => void
}) {
  const [nome, setNome] = useState('')
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [mostrarSenha, setMostrarSenha] = useState(false)
  const [papel, setPapel] = useState('orcamentista')
  const [saving, setSaving] = useState(false)
  const [emailError, setEmailError] = useState('')

  async function handleSubmit() {
    if (!nome || !email || senha.length < 8) return
    setSaving(true)
    setEmailError('')
    try {
      await createUsuario({ nome, email, senha, papel })
      onSuccess()
    } catch (e: any) {
      if (e?.response?.status === 400) {
        setEmailError('E-mail já cadastrado.')
      } else {
        toast('Erro ao criar usuário', 'error')
      }
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">Adicionar membro</h2>
          <button
            onClick={onClose}
            aria-label="Fechar"
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Nome</label>
            <input
              type="text"
              value={nome}
              onChange={e => setNome(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">E-mail</label>
            <input
              type="email"
              value={email}
              onChange={e => { setEmail(e.target.value); setEmailError('') }}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${emailError ? 'border-red-400' : 'border-gray-300'}`}
            />
            {emailError && <p className="text-xs text-red-500 mt-1">{emailError}</p>}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Senha</label>
            <div className="relative">
              <input
                type={mostrarSenha ? 'text' : 'password'}
                value={senha}
                onChange={e => setSenha(e.target.value)}
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
            {senha.length > 0 && senha.length < 8 && (
              <p className="text-xs text-red-500 mt-1">Mínimo 8 caracteres</p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Papel</label>
            <select
              value={papel}
              onChange={e => setPapel(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="orcamentista">Orçamentista</option>
              <option value="visualizador">Visualizador</option>
              <option value="admin">Administrador</option>
            </select>
          </div>
        </div>

        <div className="flex gap-2 justify-end pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={!nome || !email || senha.length < 8 || saving}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
          >
            {saving ? 'Salvando…' : 'Adicionar'}
          </button>
        </div>
      </div>
    </div>
  )
}

function EditarModal({
  usuario,
  onClose,
  onSuccess,
}: {
  usuario: Usuario
  onClose: () => void
  onSuccess: () => void
}) {
  const [papel, setPapel] = useState<Usuario['papel']>(usuario.papel)
  const [ativo, setAtivo] = useState(usuario.ativo)
  const [saving, setSaving] = useState(false)

  async function handleSubmit() {
    setSaving(true)
    try {
      await updateUsuario(usuario.id, { papel, ativo })
      onSuccess()
    } catch {
      toast('Erro ao atualizar usuário', 'error')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">Editar membro</h2>
          <button
            onClick={onClose}
            aria-label="Fechar"
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            ×
          </button>
        </div>

        <div className="space-y-3">
          <div>
            <p className="text-xs font-medium text-gray-500 mb-0.5">Nome</p>
            <p className="text-sm text-gray-900">{usuario.nome}</p>
          </div>
          <div>
            <p className="text-xs font-medium text-gray-500 mb-0.5">E-mail</p>
            <p className="text-sm text-gray-900">{usuario.email}</p>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Papel</label>
            <select
              value={papel}
              onChange={e => setPapel(e.target.value as Usuario['papel'])}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="orcamentista">Orçamentista</option>
              <option value="visualizador">Visualizador</option>
              <option value="admin">Administrador</option>
            </select>
          </div>
          <div className="flex items-center gap-3">
            <label className="text-xs font-medium text-gray-700">Ativo</label>
            <button
              type="button"
              onClick={() => setAtivo(v => !v)}
              className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${ativo ? 'bg-blue-600' : 'bg-gray-300'}`}
            >
              <span
                className={`inline-block h-3.5 w-3.5 transform rounded-full bg-white transition-transform ${ativo ? 'translate-x-4' : 'translate-x-1'}`}
              />
            </button>
          </div>
        </div>

        <div className="flex gap-2 justify-end pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800"
          >
            Cancelar
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
          >
            {saving ? 'Salvando…' : 'Salvar'}
          </button>
        </div>
      </div>
    </div>
  )
}
