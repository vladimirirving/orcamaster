import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'

export default function LoginPage() {
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  const [erro, setErro] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErro('')
    try {
      await login(email, senha)
      navigate('/')
    } catch {
      setErro('Email ou senha inválidos')
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-md w-full max-w-sm space-y-4">
        <h1 className="text-2xl font-bold text-gray-900">OrçaAVML</h1>
        <div>
          <label className="block text-sm font-medium text-gray-700">Email</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)}
            className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm" required />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700">Senha</label>
          <input type="password" value={senha} onChange={e => setSenha(e.target.value)}
            className="mt-1 block w-full border border-gray-300 rounded-md px-3 py-2 text-sm" required />
        </div>
        {erro && <p className="text-red-600 text-sm">{erro}</p>}
        <button type="submit"
          className="w-full bg-blue-600 text-white py-2 px-4 rounded-md text-sm font-medium hover:bg-blue-700">
          Entrar
        </button>
      </form>
    </div>
  )
}
