import { api } from '@/api/client'
import type { RelatorioMedicaoOut, ComparativoOut } from '@/types'

export const getRelatorioMedicao = (versaoId: number): Promise<RelatorioMedicaoOut> =>
  api.get<RelatorioMedicaoOut>(`/versoes/${versaoId}/relatorio-medicao`).then(r => r.data)

export const getComparativo = (
  obraId: number,
  v1: number,
  v2: number,
): Promise<ComparativoOut> =>
  api
    .get<ComparativoOut>(`/obras/${obraId}/comparar`, { params: { v1, v2 } })
    .then(r => r.data)
