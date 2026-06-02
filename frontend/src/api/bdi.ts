import { api } from '@/api/client'
import type { BDI } from '@/types'

export const getBdi = (versaoId: number) =>
  api.get<BDI>(`/versoes/${versaoId}/bdi`).then(r => r.data)
export const upsertBdi = (versaoId: number, data: {
  ac: string; sg: string; r: string; df: string; lucro: string
  iss: string; pis: string; cofins: string
}) => api.put<BDI>(`/versoes/${versaoId}/bdi`, data).then(r => r.data)
export const deleteBdi = (versaoId: number) =>
  api.delete(`/versoes/${versaoId}/bdi`)
