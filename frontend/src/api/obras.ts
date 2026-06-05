import { api } from '@/api/client'
import type { Obra, Versao } from '@/types'

export const getObras = () => api.get<Obra[]>('/obras').then(r => r.data)
export const getObra = (id: number) => api.get<Obra>(`/obras/${id}`).then(r => r.data)
export const createObra = (data: { nome: string; tipo_obra: string; cliente_id?: number }) =>
  api.post<Obra>('/obras', data).then(r => r.data)

export const updateObra = (id: number, data: Partial<{ cliente_id: number | null }>) =>
  api.patch<Obra>(`/obras/${id}`, data).then(r => r.data)

export const getVersoes = (obraId: number) =>
  api.get<Versao[]>(`/obras/${obraId}/versoes`).then(r => r.data)
export const createVersao = (obraId: number) =>
  api.post<Versao>(`/obras/${obraId}/versoes`).then(r => r.data)
