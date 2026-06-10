import { api } from '@/api/client'
import type { InsumoItem, InsumoItemListOut } from '@/types'

export interface InsumosFiltros {
  q?: string
  banco?: string
  estado?: string
  tipo?: string
  data_ref?: string   // 'YYYY-MM'
  order_by?: string
  page?: number
}

export const listInsumos = (params: InsumosFiltros = {}) =>
  api.get<InsumoItemListOut>('/insumos', { params }).then(r => r.data)

export const createInsumo = (data: Omit<InsumoItem, 'id' | 'banco' | 'empresa_id'>) =>
  api.post<InsumoItem>('/insumos', data).then(r => r.data)

export const updateInsumo = (
  id: number,
  data: Partial<Omit<InsumoItem, 'id' | 'banco' | 'empresa_id'>>
) => api.patch<InsumoItem>(`/insumos/${id}`, data).then(r => r.data)

export const deleteInsumo = (id: number) =>
  api.delete(`/insumos/${id}`)
