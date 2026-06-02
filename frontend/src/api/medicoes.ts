import { api } from '@/api/client'
import type { MedicaoData } from '@/types'

export const getMedicoes = (versaoId: number): Promise<MedicaoData[]> =>
  api.get<MedicaoData[]>(`/versoes/${versaoId}/medicoes`).then(r => r.data)

export const postMedicao = (versaoId: number, mes: string): Promise<MedicaoData> =>
  api.post<MedicaoData>(`/versoes/${versaoId}/medicoes`, { mes }).then(r => r.data)

export const patchMedicao = (
  versaoId: number,
  medicaoId: number,
  linhas_json: Record<string, number>
): Promise<void> =>
  api.patch(`/versoes/${versaoId}/medicoes/${medicaoId}`, { linhas_json }).then(() => {})
