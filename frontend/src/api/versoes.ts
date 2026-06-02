import { api } from '@/api/client'
import type { Versao } from '@/types'

export const duplicarVersao = (versaoId: number) =>
  api.post<Versao>(`/versoes/${versaoId}/duplicar`).then(r => r.data)
export const softDeleteVersao = (versaoId: number) =>
  api.delete(`/versoes/${versaoId}`)
export const restoreVersao = (versaoId: number) =>
  api.post<Versao>(`/versoes/${versaoId}/restore`).then(r => r.data)
