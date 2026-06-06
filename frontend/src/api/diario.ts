import { api } from '@/api/client'
import type { DiarioEntrada, DiarioFoto } from '@/types'

export const listEntradas = (obraId: number): Promise<DiarioEntrada[]> =>
  api.get<DiarioEntrada[]>(`/obras/${obraId}/diario`).then(r => r.data)

export const getEntrada = (obraId: number, entryId: number): Promise<DiarioEntrada> =>
  api.get<DiarioEntrada>(`/obras/${obraId}/diario/${entryId}`).then(r => r.data)

export const createEntrada = (
  obraId: number,
  data: {
    data: string
    clima: string
    turnos?: string
    efetivo: number
    equipes?: string
    equipamentos?: string
    atividades: string
    ocorrencias?: string
  },
): Promise<DiarioEntrada> =>
  api.post<DiarioEntrada>(`/obras/${obraId}/diario`, data).then(r => r.data)

export const updateEntrada = (
  obraId: number,
  entryId: number,
  data: Partial<{
    clima: string
    turnos: string
    efetivo: number
    equipes: string
    equipamentos: string
    atividades: string
    ocorrencias: string
  }>,
): Promise<DiarioEntrada> =>
  api.patch<DiarioEntrada>(`/obras/${obraId}/diario/${entryId}`, data).then(r => r.data)

export const deleteEntrada = (obraId: number, entryId: number): Promise<void> =>
  api.delete(`/obras/${obraId}/diario/${entryId}`)

export const uploadFoto = (
  obraId: number,
  entryId: number,
  file: File,
): Promise<DiarioFoto> => {
  const form = new FormData()
  form.append('file', file)
  return api
    .post<DiarioFoto>(`/obras/${obraId}/diario/${entryId}/fotos`, form, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    .then(r => r.data)
}

export const deleteFoto = (
  obraId: number,
  entryId: number,
  fotoId: number,
): Promise<void> =>
  api.delete(`/obras/${obraId}/diario/${entryId}/fotos/${fotoId}`)

export const getFotoUrl = (obraId: number, entryId: number, fotoId: number): string =>
  `/obras/${obraId}/diario/${entryId}/fotos/${fotoId}`

export const getRdoUrl = (obraId: number, entryId: number): string =>
  `/obras/${obraId}/diario/${entryId}/rdo.pdf`
