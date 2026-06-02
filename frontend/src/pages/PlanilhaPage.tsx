import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getVersoes } from '@/api/obras'
import { getGrupos } from '@/api/grupos'
import { getBdi } from '@/api/bdi'
import { useOrcamento } from '@/stores/orcamento'
import { fmtBRL, fmtPct } from '@/lib/utils'
import PlanilhaTabela from '@/components/planilha/PlanilhaTabela'
import PainelLateral from '@/components/planilha/PainelLateral'
import BDIModal from '@/components/planilha/BDIModal'

export default function PlanilhaPage() {
  const { obraId, versaoId } = useParams<{ obraId: string; versaoId: string }>()
  const numObraId = Number(obraId)
  const numVersaoId = Number(versaoId)
  const { versao, bdi, setVersao, setBdi, setGrupos } = useOrcamento()
  const [bdiModalOpen, setBdiModalOpen] = useState(false)

  useEffect(() => {
    async function load() {
      const [versoes, grupos] = await Promise.all([
        getVersoes(numObraId),
        getGrupos(numVersaoId),
      ])
      const v = versoes.find(x => x.id === numVersaoId)
      if (v) setVersao(v)
      setGrupos(grupos)

      getBdi(numVersaoId).then(setBdi).catch(() => setBdi(null))
    }
    load()
    // Clear store on unmount
    return () => {
      useOrcamento.setState({ versao: null, bdi: null, grupos: [], itens: {}, gruposAbertos: new Set(), painel: null })
    }
  }, [numVersaoId])

  const isReadOnly = versao?.bloqueada ?? false

  return (
    <div className="flex flex-col h-[calc(100vh-48px)]">
      {/* Toolbar */}
      <div className="flex items-center gap-4 px-4 py-2 bg-white border-b border-gray-200 shrink-0">
        <nav className="text-sm text-gray-500">
          <Link to="/obras" className="hover:text-blue-600">Obras</Link>
          <span className="mx-1">›</span>
          <Link to={`/obras/${obraId}`} className="hover:text-blue-600">Obra</Link>
          <span className="mx-1">›</span>
          <span className="text-gray-900 font-medium">Versão {versao?.numero}</span>
        </nav>

        {isReadOnly && (
          <span className="text-xs bg-yellow-100 text-yellow-700 px-2 py-0.5 rounded-full">Somente leitura</span>
        )}

        <div className="ml-auto flex items-center gap-3">
          <button
            onClick={() => setBdiModalOpen(true)}
            className="text-sm text-gray-600 hover:text-blue-600 border border-gray-200 px-3 py-1 rounded-lg"
          >
            BDI: {bdi ? fmtPct(bdi.bdi_composto) : 'Configurar BDI'}
          </button>
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden p-4 gap-4">
        <PlanilhaTabela versaoId={numVersaoId} isReadOnly={isReadOnly} />
        <PainelLateral isReadOnly={isReadOnly} />
      </div>

      {/* Footer totals */}
      <div className="flex items-center justify-end gap-6 px-6 py-2 bg-white border-t border-gray-200 text-sm shrink-0">
        <span className="text-gray-500">Total S/BDI: <span className="font-semibold text-gray-900">{fmtBRL(versao?.total_sem_bdi)}</span></span>
        <span className="text-gray-500">Total C/BDI: <span className="font-semibold text-blue-700">{fmtBRL(versao?.total_com_bdi)}</span></span>
      </div>
      <BDIModal
        open={bdiModalOpen}
        onOpenChange={setBdiModalOpen}
        versaoId={numVersaoId}
        obraId={numObraId}
      />
    </div>
  )
}
