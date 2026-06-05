// frontend/src/api/fornecedores.ts
import { api } from '@/api/client'
import type { Fornecedor } from '@/types'

export const listFornecedores = (params?: { q?: string; categoria?: string }): Promise<Fornecedor[]> =>
  api.get<Fornecedor[]>('/fornecedores', { params }).then(r => r.data)

export const getFornecedor = (id: number): Promise<Fornecedor> =>
  api.get<Fornecedor>(`/fornecedores/${id}`).then(r => r.data)

export const createFornecedor = (data: {
  nome: string
  cnpj?: string
  email?: string
  telefone?: string
  endereco?: string
  cidade?: string
  estado?: string
  categorias?: string
  observacoes?: string
}): Promise<Fornecedor> =>
  api.post<Fornecedor>('/fornecedores', data).then(r => r.data)

export const updateFornecedor = (
  id: number,
  data: Partial<{
    nome: string
    cnpj: string
    email: string
    telefone: string
    endereco: string
    cidade: string
    estado: string
    categorias: string
    observacoes: string
  }>,
): Promise<Fornecedor> =>
  api.patch<Fornecedor>(`/fornecedores/${id}`, data).then(r => r.data)

export const deleteFornecedor = (id: number): Promise<void> =>
  api.delete(`/fornecedores/${id}`)
