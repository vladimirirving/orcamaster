import { api } from '@/api/client'
import type { Composicao } from '@/types'

export const searchComposicoes = (q: string) =>
  api.get<Composicao[]>('/composicoes', { params: { q, limit: 20 } }).then(r => r.data)
