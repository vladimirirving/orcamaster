import { create } from 'zustand'
import axios from 'axios'
import { api, setAccessToken } from '@/api/client'

interface AuthState {
  userId: number | null
  papel: string | null
  empresaId: number | null
  login: (email: string, senha: string) => Promise<void>
  logout: () => Promise<void>
  refresh: () => Promise<boolean>
}

function parseJwt(token: string) {
  try {
    return JSON.parse(atob(token.split('.')[1]))
  } catch {
    return null
  }
}

export const useAuth = create<AuthState>((set) => ({
  userId: null,
  papel: null,
  empresaId: null,

  login: async (email, senha) => {
    const { data } = await axios.post('/auth/login', { email, senha }, { withCredentials: true })
    setAccessToken(data.access_token)
    const payload = parseJwt(data.access_token)
    set({ userId: Number(payload.sub), papel: payload.papel, empresaId: payload.empresa_id })
  },

  logout: async () => {
    await api.post('/auth/logout')
    setAccessToken('')
    set({ userId: null, papel: null, empresaId: null })
  },

  refresh: async () => {
    try {
      const { data } = await axios.post('/auth/refresh', {}, { withCredentials: true })
      setAccessToken(data.access_token)
      const payload = parseJwt(data.access_token)
      set({ userId: Number(payload.sub), papel: payload.papel, empresaId: payload.empresa_id })
      return true
    } catch {
      return false
    }
  },
}))
