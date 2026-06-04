import { api } from '@/api/client'

export async function downloadTemplate(versaoId: number): Promise<void> {
  const resp = await api.get<Blob>(`/versoes/${versaoId}/planilha/template`, {
    responseType: 'blob',
  })
  const url = URL.createObjectURL(resp.data)
  const a = document.createElement('a')
  a.href = url
  a.download = `template-planilha-v${versaoId}.xlsx`
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 100)
}

export const importarPlanilha = (
  versaoId: number,
  file: File,
): Promise<{ grupos_criados: number; itens_criados: number; itens_sem_composicao: number }> => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/versoes/${versaoId}/planilha/importar`, form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }).then(r => r.data)
}
