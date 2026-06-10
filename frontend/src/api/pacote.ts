import { api } from '@/api/client'
import type { PacoteJob } from '@/types'

export const createPacote = (versaoId: number): Promise<PacoteJob> =>
  api.post<PacoteJob>(`/versoes/${versaoId}/pacote`).then(r => r.data)

export const getPacote = (versaoId: number): Promise<PacoteJob> =>
  api.get<PacoteJob>(`/versoes/${versaoId}/pacote`).then(r => r.data)

export async function downloadPacote(versaoId: number): Promise<void> {
  const resp = await api.get<Blob>(`/versoes/${versaoId}/pacote/download`, {
    responseType: 'blob',
  })
  const url = URL.createObjectURL(resp.data)
  const a = document.createElement('a')
  a.href = url
  a.download = `pacote-v${versaoId}.zip`
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 100)
}
