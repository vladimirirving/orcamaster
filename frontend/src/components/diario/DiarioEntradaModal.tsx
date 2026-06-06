import { useState } from 'react'
import { createEntrada, updateEntrada, uploadFoto, deleteFoto, getFotoUrl } from '@/api/diario'
import { toast } from '@/hooks/useToast'
import type { DiarioEntrada, DiarioFoto } from '@/types'

const CLIMAS = [
  { value: 'ensolarado' as const, label: '☀️ Ensolarado' },
  { value: 'parcialmente_nublado' as const, label: '⛅ Parcialmente Nublado' },
  { value: 'nublado' as const, label: '☁️ Nublado' },
  { value: 'chuvoso' as const, label: '🌧️ Chuvoso' },
]

const TURNOS = [
  { value: 'manha', label: 'Manhã' },
  { value: 'tarde', label: 'Tarde' },
  { value: 'noite', label: 'Noite' },
]

interface Props {
  obraId: number
  entrada?: DiarioEntrada
  onClose: () => void
  onSuccess: (e: DiarioEntrada) => void
}

export default function DiarioEntradaModal({ obraId, entrada, onClose, onSuccess }: Props) {
  const isEdit = !!entrada
  const today = new Date().toISOString().split('T')[0]

  const [data, setData] = useState(entrada?.data ?? today)
  const [clima, setClima] = useState(entrada?.clima ?? 'ensolarado')
  const [turnos, setTurnos] = useState<string[]>(
    entrada?.turnos ? entrada.turnos.split(',') : []
  )
  const [efetivo, setEfetivo] = useState(entrada?.efetivo ?? 0)
  const [equipes, setEquipes] = useState(entrada?.equipes ?? '')
  const [equipamentos, setEquipamentos] = useState(entrada?.equipamentos ?? '')
  const [atividades, setAtividades] = useState(entrada?.atividades ?? '')
  const [ocorrencias, setOcorrencias] = useState(entrada?.ocorrencias ?? '')
  const [saving, setSaving] = useState(false)
  const [dataError, setDataError] = useState('')

  const [fotos, setFotos] = useState<DiarioFoto[]>(entrada?.fotos ?? [])
  const [uploadingFoto, setUploadingFoto] = useState(false)

  const toggleTurno = (v: string) =>
    setTurnos(prev => prev.includes(v) ? prev.filter(t => t !== v) : [...prev, v])

  const isValid = atividades.trim().length > 0 && data.length > 0

  async function handleSubmit() {
    if (!isValid) return
    setSaving(true)
    setDataError('')
    const payload = {
      data,
      clima,
      turnos: turnos.length ? turnos.join(',') : undefined,
      efetivo,
      equipes: equipes.trim() || undefined,
      equipamentos: equipamentos.trim() || undefined,
      atividades: atividades.trim(),
      ocorrencias: ocorrencias.trim() || undefined,
    }
    try {
      const result = isEdit && entrada
        ? await updateEntrada(obraId, entrada.id, payload)
        : await createEntrada(obraId, payload)
      onSuccess(result)
    } catch (e: any) {
      if (e?.response?.status === 409) {
        setDataError('Já existe uma entrada para esta data.')
      } else {
        toast('Erro ao salvar entrada', 'error')
      }
    } finally {
      setSaving(false)
    }
  }

  async function handleUploadFoto(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file || !entrada) return
    if (fotos.length >= 5) {
      toast('Limite de 5 fotos atingido', 'error')
      return
    }
    setUploadingFoto(true)
    try {
      const foto = await uploadFoto(obraId, entrada.id, file)
      setFotos(prev => [...prev, foto])
    } catch (e: any) {
      toast(e?.response?.data?.detail ?? 'Erro ao fazer upload', 'error')
    } finally {
      setUploadingFoto(false)
      e.target.value = ''
    }
  }

  async function handleDeleteFoto(fotoId: number) {
    if (!entrada) return
    try {
      await deleteFoto(obraId, entrada.id, fotoId)
      setFotos(prev => prev.filter(f => f.id !== fotoId))
    } catch {
      toast('Erro ao remover foto', 'error')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl mx-4 p-6 space-y-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">
            {isEdit ? 'Editar entrada' : 'Nova entrada'}
          </h2>
          <button onClick={onClose} aria-label="Fechar" className="text-gray-400 hover:text-gray-600 text-xl leading-none">×</button>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="diario-data" className="block text-xs font-medium text-gray-700 mb-1">Data *</label>
            <input
              id="diario-data"
              type="date"
              value={data}
              onChange={e => { setData(e.target.value); setDataError('') }}
              disabled={isEdit}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${dataError ? 'border-red-400' : 'border-gray-300'} ${isEdit ? 'bg-gray-50 text-gray-500' : ''}`}
            />
            {dataError && <p role="alert" className="text-xs text-red-500 mt-1">{dataError}</p>}
          </div>

          <div>
            <label htmlFor="diario-efetivo" className="block text-xs font-medium text-gray-700 mb-1">Efetivo (trabalhadores)</label>
            <input
              id="diario-efetivo"
              type="number"
              min={0}
              value={efetivo}
              onChange={e => setEfetivo(Number(e.target.value))}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Clima</label>
          <div className="flex gap-2 flex-wrap">
            {CLIMAS.map(c => (
              <label key={c.value} className={`flex items-center gap-1.5 text-sm cursor-pointer px-3 py-1.5 rounded-lg border transition-colors ${clima === c.value ? 'border-blue-500 bg-blue-50 text-blue-700' : 'border-gray-200 hover:border-gray-300'}`}>
                <input type="radio" name="clima" value={c.value} checked={clima === c.value} onChange={() => setClima(c.value)} className="sr-only" />
                {c.label}
              </label>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700 mb-1">Turnos trabalhados</label>
          <div className="flex gap-3">
            {TURNOS.map(t => (
              <label key={t.value} className="flex items-center gap-1.5 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={turnos.includes(t.value)}
                  onChange={() => toggleTurno(t.value)}
                />
                {t.label}
              </label>
            ))}
          </div>
        </div>

        <div>
          <label htmlFor="diario-ativ" className="block text-xs font-medium text-gray-700 mb-1">Atividades Executadas *</label>
          <textarea
            id="diario-ativ"
            value={atividades}
            onChange={e => setAtividades(e.target.value)}
            rows={3}
            placeholder="Descreva as atividades executadas no dia..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>

        <div>
          <label htmlFor="diario-equipes" className="block text-xs font-medium text-gray-700 mb-1">Equipes por serviço</label>
          <textarea
            id="diario-equipes"
            value={equipes}
            onChange={e => setEquipes(e.target.value)}
            rows={2}
            placeholder="Ex: Equipe A (Concreto): 5 pessoas; Equipe B (Armação): 3 pessoas"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>

        <div>
          <label htmlFor="diario-equip" className="block text-xs font-medium text-gray-700 mb-1">Equipamentos utilizados</label>
          <textarea
            id="diario-equip"
            value={equipamentos}
            onChange={e => setEquipamentos(e.target.value)}
            rows={2}
            placeholder="Ex: Betoneira 400L, Vibrador de concreto"
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>

        <div>
          <label htmlFor="diario-ocorr" className="block text-xs font-medium text-gray-700 mb-1">Ocorrências</label>
          <textarea
            id="diario-ocorr"
            value={ocorrencias}
            onChange={e => setOcorrencias(e.target.value)}
            rows={2}
            placeholder="Incidentes, paralisações, observações importantes..."
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
          />
        </div>

        {isEdit && (
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-2">
              Fotos ({fotos.length}/5)
            </label>
            <div className="grid grid-cols-3 gap-2">
              {fotos.map(foto => (
                <div key={foto.id} className="relative group aspect-square bg-gray-100 rounded-lg overflow-hidden border border-gray-200">
                  <img
                    src={getFotoUrl(obraId, entrada!.id, foto.id)}
                    alt={foto.nome_original}
                    className="w-full h-full object-cover"
                  />
                  <button
                    onClick={() => handleDeleteFoto(foto.id)}
                    className="absolute top-1 right-1 bg-red-600 text-white rounded-full w-5 h-5 text-xs flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity"
                    aria-label={`Remover ${foto.nome_original}`}
                  >
                    ×
                  </button>
                </div>
              ))}
              {fotos.length < 5 && (
                <label className="aspect-square bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 flex flex-col items-center justify-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-colors">
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/webp"
                    onChange={handleUploadFoto}
                    disabled={uploadingFoto}
                    className="sr-only"
                  />
                  {uploadingFoto ? (
                    <span className="text-xs text-gray-400">Enviando…</span>
                  ) : (
                    <>
                      <span className="text-2xl text-gray-400">+</span>
                      <span className="text-xs text-gray-400 mt-1">Adicionar</span>
                    </>
                  )}
                </label>
              )}
            </div>
            <p className="text-xs text-gray-400 mt-1">JPEG, PNG ou WebP · máx. 5 MB cada</p>
          </div>
        )}
        {!isEdit && (
          <p className="text-xs text-gray-400">Fotos podem ser adicionadas após salvar a entrada.</p>
        )}

        <div className="flex gap-2 justify-end pt-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Cancelar</button>
          <button
            onClick={handleSubmit}
            disabled={!isValid || saving}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
          >
            {saving ? 'Salvando…' : isEdit ? 'Salvar' : 'Criar'}
          </button>
        </div>
      </div>
    </div>
  )
}
