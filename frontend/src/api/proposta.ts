import { api } from '@/api/client'
import type { PropostaConfig, EmpresaConfig } from '@/types'

export const getPropostaConfig = (versaoId: number): Promise<PropostaConfig> =>
  api.get<PropostaConfig>(`/versoes/${versaoId}/proposta`).then(r => r.data)

export const savePropostaConfig = (
  versaoId: number,
  body: { validade_dias: number; data_proposta: string; declaracoes: string | null }
): Promise<PropostaConfig> =>
  api.put<PropostaConfig>(`/versoes/${versaoId}/proposta`, body).then(r => r.data)

export async function downloadPropostaPdf(versaoId: number): Promise<void> {
  const resp = await api.get<Blob>(`/versoes/${versaoId}/proposta/export`, {
    responseType: 'blob',
  })
  const url = URL.createObjectURL(resp.data)
  const a = document.createElement('a')
  a.href = url
  a.download = `proposta-v${versaoId}.pdf`
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  setTimeout(() => URL.revokeObjectURL(url), 30_000)
}

export const getEmpresaConfig = (): Promise<EmpresaConfig> =>
  api.get<EmpresaConfig>('/empresa').then(r => r.data)

export const updateEmpresaConfig = (
  body: Partial<Pick<EmpresaConfig, 'representante_nome' | 'representante_cpf' | 'declaracoes_padrao'>>
): Promise<EmpresaConfig> =>
  api.patch<EmpresaConfig>('/empresa', body).then(r => r.data)
