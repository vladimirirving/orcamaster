import { api } from '@/api/client'
import type { Usuario } from '@/types'

export const listUsuarios = () =>
  api.get<Usuario[]>('/usuarios').then(r => r.data)

export const createUsuario = (data: {
  nome: string
  email: string
  senha: string
  papel: string
}) => api.post<Usuario>('/usuarios', data).then(r => r.data)

export const updateUsuario = (
  id: number,
  data: { papel?: string; ativo?: boolean },
) => api.patch<Usuario>(`/usuarios/${id}`, data).then(r => r.data)
