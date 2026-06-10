import { useState } from 'react'
import { downloadTemplate, importarPlanilha } from '@/api/planilhaImport'
import { toast } from '@/hooks/useToast'

interface Props {
  versaoId: number
  onClose: () => void
  onSuccess: () => void
}

type Phase = 'form' | 'importing' | 'done'

export default function ImportarPlanilhaModal({ versaoId, onClose, onSuccess }: Props) {
  const [phase, setPhase] = useState<Phase>('form')
  const [file, setFile] = useState<File | null>(null)
  const [result, setResult] = useState<{
    grupos_criados: number
    itens_criados: number
    itens_sem_composicao: number
  } | null>(null)

  async function handleDownloadTemplate() {
    try {
      await downloadTemplate(versaoId)
    } catch {
      toast('Erro ao baixar template', 'error')
    }
  }

  async function handleImportar() {
    if (!file) return
    setPhase('importing')
    try {
      const r = await importarPlanilha(versaoId, file)
      setResult(r)
      setPhase('done')
    } catch {
      toast('Erro ao importar planilha', 'error')
      setPhase('form')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6 space-y-5">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">Importar planilha Excel</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            ×
          </button>
        </div>

        {phase === 'form' && (
          <>
            <p className="text-sm text-gray-500">
              Baixe o template, preencha com seus grupos e itens, e faça o upload.
            </p>
            <button
              onClick={handleDownloadTemplate}
              className="text-sm text-blue-600 hover:underline"
            >
              ↓ Baixar template (.xlsx)
            </button>
            <div className="space-y-3">
              <label className="block">
                <span className="text-xs font-medium text-gray-700 mb-1 block">Arquivo preenchido</span>
                <input
                  type="file"
                  accept=".xlsx"
                  onChange={e => setFile(e.target.files?.[0] ?? null)}
                  className="block w-full text-sm text-gray-500 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
              </label>
              <button
                onClick={handleImportar}
                disabled={!file}
                className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
              >
                Importar
              </button>
            </div>
          </>
        )}

        {phase === 'importing' && (
          <div className="flex items-center gap-3 py-4">
            <span className="inline-block w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm text-gray-600">Importando…</span>
          </div>
        )}

        {phase === 'done' && result && (
          <>
            <div className="bg-green-50 border border-green-200 rounded-lg px-4 py-3 text-sm text-green-800">
              ✓ {result.grupos_criados} grupos e {result.itens_criados} itens adicionados
            </div>
            {result.itens_sem_composicao > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-4 py-3 text-sm text-yellow-800">
                ⚠ {result.itens_sem_composicao} {result.itens_sem_composicao === 1 ? 'item' : 'itens'} sem composição vinculada — verifique os itens marcados para revisão
              </div>
            )}
            <button
              onClick={onSuccess}
              className="w-full bg-blue-600 text-white py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
            >
              Fechar e atualizar planilha
            </button>
          </>
        )}
      </div>
    </div>
  )
}
