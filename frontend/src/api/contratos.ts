import { api } from '@/api/client'
import type { Contrato, Aditivo } from '@/types'

export const getContratos = (obraId: number) =>
  api.get<Contrato[]>(`/obras/${obraId}/contratos`).then(r => r.data)

export const createContrato = (obraId: number, data: {
  objeto: string
  valor_original: number
  numero?: string | null
  data_assinatura?: string | null
  data_inicio?: string | null
  data_fim?: string | null
  contratante_nome?: string | null
  contratante_cnpj?: string | null
  contratado_nome?: string | null
  contratado_cnpj?: string | null
}) => api.post<Contrato>(`/obras/${obraId}/contratos`, data).then(r => r.data)

export const updateContrato = (id: number, data: Partial<{
  objeto: string
  valor_original: number
  numero: string | null
  data_assinatura: string | null
  data_inicio: string | null
  data_fim: string | null
  contratante_nome: string | null
  contratante_cnpj: string | null
  contratado_nome: string | null
  contratado_cnpj: string | null
}>) => api.patch<Contrato>(`/contratos/${id}`, data).then(r => r.data)

export const deleteContrato = (id: number) =>
  api.delete(`/contratos/${id}`)

export const uploadContratoFile = (id: number, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post<Contrato>(`/contratos/${id}/upload`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}

export const downloadContratoFile = async (id: number) => {
  const resp = await api.get(`/contratos/${id}/download`, { responseType: 'blob' })
  const url = URL.createObjectURL(resp.data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `contrato-${id}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}

export const createAditivo = (contratoId: number, data: {
  tipo: 'valor' | 'prazo' | 'valor_prazo'
  numero?: string | null
  delta_valor?: number | null
  nova_data_fim?: string | null
  justificativa?: string | null
  data_assinatura?: string | null
}) => api.post<Aditivo>(`/contratos/${contratoId}/aditivos`, data).then(r => r.data)

export const updateAditivo = (id: number, data: Partial<{
  numero: string | null
  tipo: 'valor' | 'prazo' | 'valor_prazo'
  delta_valor: number | null
  nova_data_fim: string | null
  justificativa: string | null
  data_assinatura: string | null
}>) => api.patch<Aditivo>(`/aditivos/${id}`, data).then(r => r.data)

export const deleteAditivo = (id: number) =>
  api.delete(`/aditivos/${id}`)

export const uploadAditivoFile = (id: number, file: File) => {
  const form = new FormData()
  form.append('file', file)
  return api.post<Aditivo>(`/aditivos/${id}/upload`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}

export const downloadAditivoFile = async (id: number) => {
  const resp = await api.get(`/aditivos/${id}/download`, { responseType: 'blob' })
  const url = URL.createObjectURL(resp.data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `aditivo-${id}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}
