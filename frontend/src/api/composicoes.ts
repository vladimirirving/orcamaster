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
