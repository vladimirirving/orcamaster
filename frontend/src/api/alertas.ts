import { api } from '@/api/client'
import type { Alerta } from '@/types'

export const getAlertas = () =>
  api.get<Alerta[]>('/alertas').then(r => r.data)
