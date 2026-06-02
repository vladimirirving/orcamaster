import { useState, useEffect } from 'react'
import * as Dialog from '@radix-ui/react-dialog'
import { X } from 'lucide-react'
import { upsertBdi, deleteBdi } from '@/api/bdi'
import { getVersoes } from '@/api/obras'
import { calcBdiComposto } from '@/utils/bdi'
import { useOrcamento } from '@/stores/orcamento'
import { toast } from '@/hooks/useToast'

const CAMPOS = [
  { key: 'ac', label: 'Administração Central (AC)' },
  { key: 'sg', label: 'Seguros e Garantias (SG)' },
  { key: 'r', label: 'Riscos (R)' },
  { key: 'df', label: 'Despesas Financeiras (DF)' },
  { key: 'lucro', label: 'Lucro' },
  { key: 'iss', label: 'ISS' },
  { key: 'pis', label: 'PIS' },
  { key: 'cofins', label: 'COFINS' },
] as const

type BDIKey = typeof CAMPOS[number]['key']

const emptyForm = () => Object.fromEntries(CAMPOS.map(c => [c.key, ''])) as Record<BDIKey, string>

interface Props {
  open: boolean
  onOpenChange: (o: boolean) => void
  versaoId: number
  obraId: number
}

export default function BDIModal({ open, onOpenChange, versaoId, obraId }: Props) {
  const { bdi, setBdi, setVersao } = useOrcamento()
  const [form, setForm] = useState<Record<BDIKey, string>>(emptyForm())
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  useEffect(() => {
    if (bdi) {
      setForm({
        ac: (parseFloat(bdi.ac) * 100).toFixed(4),
        sg: (parseFloat(bdi.sg) * 100).toFixed(4),
        r: (parseFloat(bdi.r) * 100).toFixed(4),
        df: (parseFloat(bdi.df) * 100).toFixed(4),
        lucro: (parseFloat(bdi.lucro) * 100).toFixed(4),
        iss: (parseFloat(bdi.iss) * 100).toFixed(4),
        pis: (parseFloat(bdi.pis) * 100).toFixed(4),
        cofins: (parseFloat(bdi.cofins) * 100).toFixed(4),
      })
    } else {
      setForm(emptyForm())
    }
  }, [bdi, open])

  function toDecimal(val: string) {
    return (parseFloat(val || '0') / 100).toFixed(6)
  }

  function getPreview(): string {
    try {
      const v = (k: BDIKey) => parseFloat(form[k] || '0') / 100
      const result = calcBdiComposto(v('ac'), v('sg'), v('r'), v('df'), v('lucro'), v('iss'), v('pis'), v('cofins'))
      return (result * 100).toFixed(2) + '%'
    } catch {
      return 'Inválido (ISS+PIS+COFINS ≥ 100%)'
    }
  }

  async function handleSave(e: React.FormEvent) {
    e.preventDefault()
    try {
      const v = (k: BDIKey) => parseFloat(form[k] || '0') / 100
      calcBdiComposto(v('ac'), v('sg'), v('r'), v('df'), v('lucro'), v('iss'), v('pis'), v('cofins'))
    } catch {
      toast('ISS + PIS + COFINS deve ser menor que 100%', 'error')
      return
    }

    setSaving(true)
    try {
      const payload = Object.fromEntries(
        CAMPOS.map(c => [c.key, toDecimal(form[c.key])])
      ) as Record<BDIKey, string>
      const saved = await upsertBdi(versaoId, payload)
      setBdi(saved)
      useOrcamento.setState({ itens: {} }) // invalidate item price cache — BDI recalculated server-side
      const versoes = await getVersoes(obraId)
      const v = versoes.find(x => x.id === versaoId)
      if (v) setVersao(v)
      onOpenChange(false)
      toast('BDI aplicado a todos os itens')
    } catch (e: any) {
      toast(e?.response?.data?.detail ?? 'Erro ao salvar BDI', 'error')
    } finally {
      setSaving(false)
    }
  }

  async function handleDelete() {
    try {
      await deleteBdi(versaoId)
      setBdi(null)
      useOrcamento.setState({ itens: {} }) // invalidate item price cache — BDI zeroed server-side
      const versoes = await getVersoes(obraId)
      const v = versoes.find(x => x.id === versaoId)
      if (v) setVersao(v)
      onOpenChange(false)
      toast('BDI removido')
    } catch {
      toast('Erro ao remover BDI', 'error')
    }
  }

  const preview = getPreview()

  return (
    <Dialog.Root open={open} onOpenChange={onOpenChange}>
      <Dialog.Portal>
        <Dialog.Overlay className="fixed inset-0 bg-black/50 z-40" />
        <Dialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-xl shadow-2xl p-6 z-50 w-full max-w-md max-h-[90vh] overflow-y-auto">
          <div className="flex items-center justify-between mb-5">
            <Dialog.Title className="text-lg font-bold">Configurar BDI</Dialog.Title>
            <Dialog.Close asChild>
              <button className="text-gray-400 hover:text-gray-600"><X size={18} /></button>
            </Dialog.Close>
          </div>

          <form onSubmit={handleSave} className="flex flex-col gap-3">
            {CAMPOS.map(c => (
              <div key={c.key}>
                <label className="block text-xs font-medium text-gray-500 mb-1">{c.label} (%)</label>
                <input
                  type="number"
                  step="0.0001"
                  min="0"
                  value={form[c.key]}
                  onChange={e => setForm(f => ({ ...f, [c.key]: e.target.value }))}
                  placeholder="0.0000"
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            ))}

            <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 mt-1">
              <p className="text-xs text-blue-600 font-medium">BDI Composto (preview)</p>
              <p className="text-2xl font-bold text-blue-700 mt-1">{preview}</p>
            </div>

            <div className="flex gap-2 pt-2">
              <button
                type="submit"
                disabled={saving}
                className="flex-1 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-50"
              >
                {saving ? 'Aplicando...' : 'Salvar e Aplicar'}
              </button>
              {bdi && (
                <button
                  type="button"
                  onClick={() => {
                    if (confirmDelete) handleDelete()
                    else { setConfirmDelete(true); setTimeout(() => setConfirmDelete(false), 3000) }
                  }}
                  className={`px-3 py-2 rounded-lg text-sm transition-colors ${confirmDelete ? 'bg-red-100 text-red-600' : 'text-gray-400 hover:bg-gray-100'}`}
                  title={confirmDelete ? 'Confirmar remoção' : 'Remover BDI'}
                >
                  {confirmDelete ? 'Confirmar?' : 'Remover'}
                </button>
              )}
            </div>
          </form>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog.Root>
  )
}
