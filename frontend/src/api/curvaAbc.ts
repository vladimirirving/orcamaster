import { api } from '@/api/client'
import type { CurvaAbcData } from '@/types'

export const getCurvaAbc = (versaoId: number): Promise<CurvaAbcData> =>
  api.get<CurvaAbcData>(`/versoes/${versaoId}/curva-abc`).then(r => r.data)

export async function downloadCurvaAbcExcel(versaoId: number): Promise<void> {
  const resp = await api.get(`/versoes/${versaoId}/curva-abc/export`, {
    responseType: 'blob',
  })
  const url = URL.createObjectURL(resp.data as Blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `curva-abc-v${versaoId}.xlsx`
  a.click()
  URL.revokeObjectURL(url)
}
