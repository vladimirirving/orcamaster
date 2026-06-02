import { api } from '@/api/client'
import type { CronogramaData } from '@/types'

export const getCronograma = (versaoId: number) =>
  api.get<CronogramaData>(`/versoes/${versaoId}/cronograma`).then(r => r.data)

export const patchCronogramaConfig = (
  versaoId: number,
  data: { cronograma_inicio: string; cronograma_fim: string }
) => api.patch(`/versoes/${versaoId}/cronograma/config`, data)

export const patchCronogramaLinha = (
  versaoId: number,
  itemId: number,
  distribuicao_json: Record<string, number>
) => api.patch(`/versoes/${versaoId}/cronograma/linhas/${itemId}`, { distribuicao_json })
