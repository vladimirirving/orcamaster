import { api } from '@/api/client'
import type { Composicao } from '@/types'

export const searchComposicoes = (q: string) =>
  api.get<Composicao[]>('/composicoes', { params: { q, limit: 20 } }).then(r => r.data)

export async function importarComposicoes(
  origem: 'sinapi' | 'sicro',
  file: File,
): Promise<{ criadas: number; atualizadas: number; itens_marcados: number }> {
  const form = new FormData()
  form.append('origem', origem)
  form.append('file', file)
  return api.post('/composicoes/importar', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}

export const listComposicoesProprias = (q?: string): Promise<Composicao[]> =>
  api.get<Composicao[]>('/composicoes', {
    params: { origem: 'propria', q: q || undefined, limit: 200 },
  }).then(r => r.data)

export const createComposicao = (data: {
  codigo: string
  descricao: string
  unidade: string
  preco_unitario: string
}): Promise<Composicao> =>
  api.post<Composicao>('/composicoes', data).then(r => r.data)

export const updateComposicao = (
  id: number,
  data: { codigo?: string; descricao?: string; unidade?: string; preco_unitario?: string },
): Promise<Composicao> =>
  api.patch<Composicao>(`/composicoes/${id}`, data).then(r => r.data)

export const deleteComposicao = (id: number): Promise<void> =>
  api.delete(`/composicoes/${id}`)
