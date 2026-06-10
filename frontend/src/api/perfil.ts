import { api, setAccessToken } from '@/api/client'

export async function updateNome(nome: string): Promise<string> {
  const resp = await api.patch<{ access_token: string }>('/auth/me', { nome })
  setAccessToken(resp.data.access_token)
  return resp.data.access_token
}

export async function alterarSenha(
  senha_atual: string,
  nova_senha: string,
): Promise<void> {
  await api.post('/auth/alterar-senha', { senha_atual, nova_senha })
}
