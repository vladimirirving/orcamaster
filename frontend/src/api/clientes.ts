// frontend/src/api/clientes.ts
import { api } from '@/api/client'
import type { Cliente, Obra } from '@/types'

export const listClientes = (q?: string): Promise<Cliente[]> =>
  api.get<Cliente[]>('/clientes', { params: q ? { q } : {} }).then(r => r.data)

export const getCliente = (id: number): Promise<Cliente> =>
  api.get<Cliente>(`/clientes/${id}`).then(r => r.data)

export const createCliente = (data: {
  tipo: string
  nome: string
  cpf_cnpj?: string
  email?: string
  telefone?: string
  endereco?: string
  cidade?: string
  estado?: string
  observacoes?: string
}): Promise<Cliente> =>
  api.post<Cliente>('/clientes', data).then(r => r.data)

export const updateCliente = (
  id: number,
  data: Partial<{
    tipo: string
    nome: string
    cpf_cnpj: string
    email: string
    telefone: string
    endereco: string
    cidade: string
    estado: string
    observacoes: string
  }>,
): Promise<Cliente> =>
  api.patch<Cliente>(`/clientes/${id}`, data).then(r => r.data)

export const deleteCliente = (id: number): Promise<void> =>
  api.delete(`/clientes/${id}`)

export const getClienteObras = (id: number): Promise<Obra[]> =>
  api.get<Obra[]>(`/clientes/${id}/obras`).then(r => r.data)
