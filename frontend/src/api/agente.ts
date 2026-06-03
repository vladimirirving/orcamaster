import { api, getAccessToken } from '@/api/client'
import type { PropostaGrupo, PropostaSugerida } from '@/types'

export function gerarProposta(
  versaoId: number,
  descricao: string,
  onProgress: (msg: string) => void,
  onProposta: (proposta: PropostaSugerida) => void,
  onError: (msg: string) => void,
): () => void {
  const controller = new AbortController()

  ;(async () => {
    try {
      const resp = await fetch(`/versoes/${versaoId}/agente/gerar`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${getAccessToken()}`,
        },
        body: JSON.stringify({ descricao }),
        signal: controller.signal,
      })

      if (!resp.ok || !resp.body) {
        onError(`Erro ${resp.status}`)
        return
      }

      const reader = resp.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const event = JSON.parse(line.slice(6))
          if (event.type === 'progress') onProgress(event.msg)
          else if (event.type === 'proposta') onProposta(event.data)
          else if (event.type === 'error') onError(event.msg)
        }
      }
    } catch (e: any) {
      if (e?.name !== 'AbortError') onError('Erro ao conectar ao agente')
    }
  })()

  return () => controller.abort()
}

export const importarProposta = (
  versaoId: number,
  grupos: PropostaGrupo[],
): Promise<{ grupos_criados: number; itens_criados: number }> =>
  api.post(`/versoes/${versaoId}/agente/importar`, { grupos }).then(r => r.data)
