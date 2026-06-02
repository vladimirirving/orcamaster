import { api } from '@/api/client'
import type { Grupo } from '@/types'

export const getGrupos = (versaoId: number) =>
  api.get<Grupo[]>(`/versoes/${versaoId}/grupos`).then(r => r.data)
export const createGrupo = (versaoId: number, data: { nome: string; codigo?: string; ordem: number }) =>
  api.post<Grupo>(`/versoes/${versaoId}/grupos`, data).then(r => r.data)
export const createSubgrupo = (grupoId: number, data: { nome: string; codigo?: string; ordem: number }) =>
  api.post<Grupo>(`/grupos/${grupoId}/subgrupos`, data).then(r => r.data)
export const updateGrupo = (grupoId: number, data: Partial<{ nome: string; codigo: string; ordem: number }>) =>
  api.patch<Grupo>(`/grupos/${grupoId}`, data).then(r => r.data)
export const deleteGrupo = (grupoId: number) =>
  api.delete(`/grupos/${grupoId}`)
