import { api } from '@/api/client'
import type { Item } from '@/types'

export const getItens = (grupoId: number) =>
  api.get<Item[]>(`/grupos/${grupoId}/itens`).then(r => r.data)
export const createItem = (grupoId: number, data: { ordem: number; quantidade: string; unidade: string }) =>
  api.post<Item>(`/grupos/${grupoId}/itens`, data).then(r => r.data)
export const updateItem = (itemId: number, data: Partial<{ ordem: number; quantidade: string; unidade: string }>) =>
  api.patch<Item>(`/itens/${itemId}`, data).then(r => r.data)
export const deleteItem = (itemId: number) =>
  api.delete(`/itens/${itemId}`)
export const vincularComposicao = (itemId: number, composicao_id: number) =>
  api.patch<Item>(`/itens/${itemId}/composicao`, { composicao_id }).then(r => r.data)
export const atualizarPreco = (itemId: number) =>
  api.post<Item>(`/itens/${itemId}/atualizar-preco`).then(r => r.data)
