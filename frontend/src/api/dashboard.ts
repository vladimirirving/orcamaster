import { api } from '@/api/client'
import type { DashboardResumoItem, ObraDashboardData, DistribuicaoGruposOut } from '@/types'

export const getDashboard = (): Promise<DashboardResumoItem[]> =>
  api.get<DashboardResumoItem[]>('/dashboard').then(r => r.data)

export const getObraDashboard = (obraId: number): Promise<ObraDashboardData> =>
  api.get<ObraDashboardData>(`/obras/${obraId}/dashboard`).then(r => r.data)

export const getDistribuicaoGrupos = (obraId: number): Promise<DistribuicaoGruposOut> =>
  api.get<DistribuicaoGruposOut>(`/obras/${obraId}/distribuicao-grupos`).then(r => r.data)
