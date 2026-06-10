import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { gerarProposta, importarProposta } from '@/api/agente'
import { toast } from '@/hooks/useToast'
import type { PropostaGrupo, PropostaSugerida, PropostaItem } from '@/types'

interface Props {
  versaoId: number
  obraId: number
}

type Phase = 'idle' | 'streaming' | 'review' | 'done'

export default function AgenteTab({ versaoId, obraId }: Props) {
  const navigate = useNavigate()
  const [phase, setPhase] = useState<Phase>('idle')
  const [descricao, setDescricao] = useState('')
  const [progressMsgs, setProgressMsgs] = useState<string[]>([])
  const [grupos, setGrupos] = useState<PropostaGrupo[]>([])
  const [removidos, setRemovidosSet] = useState<Set<number>>(new Set())
  const [editando, setEditando] = useState<number | null>(null)
  const [editNome, setEditNome] = useState('')
  const [editItens, setEditItens] = useState<PropostaItem[]>([])
  const [expandidos, setExpandidos] = useState<Set<number>>(new Set())
  const [importResult, setImportResult] = useState<{ grupos_criados: number; itens_criados: number } | null>(null)
  const cancelRef = useRef<(() => void) | null>(null)

  function handleGerar() {
    if (!descricao.trim()) return
    setPhase('streaming')
    setProgressMsgs([])
    setRemovidosSet(new Set())
    setEditando(null)

    cancelRef.current = gerarProposta(
      versaoId,
      descricao,
      (msg) => setProgressMsgs(prev => [...prev, msg]),
      (proposta: PropostaSugerida) => {
        setGrupos(proposta.grupos)
        setExpandidos(new Set(proposta.grupos.map((_, i) => i)))
        setPhase('review')
      },
      (msg) => {
        toast(msg, 'error')
        setPhase('idle')
      },
    )
  }

  function handleCancelar() {
    cancelRef.current?.()
    setPhase('idle')
  }

  function handleToggleRemover(idx: number) {
    setRemovidosSet(prev => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }

  function handleToggleExpand(idx: number) {
    setExpandidos(prev => {
      const next = new Set(prev)
      if (next.has(idx)) next.delete(idx)
      else next.add(idx)
      return next
    })
  }

  function handleEditarIniciar(idx: number) {
    setEditando(idx)
    setEditNome(grupos[idx].nome)
    setEditItens(grupos[idx].itens.map(i => ({ ...i })))
  }

  function handleEditarConfirmar(idx: number) {
    setGrupos(prev => prev.map((g, i) =>
      i === idx ? { ...g, nome: editNome, itens: editItens } : g
    ))
    setEditando(null)
  }

  async function handleImportar() {
    const selecionados = grupos.filter((_, i) => !removidos.has(i))
    if (selecionados.length === 0) {
      toast('Selecione ao menos um grupo para importar', 'error')
      return
    }
    try {
      const result = await importarProposta(versaoId, selecionados)
      setImportResult(result)
      setPhase('done')
    } catch {
      toast('Erro ao importar proposta', 'error')
    }
  }

  if (phase === 'idle') {
    return (
      <div className="p-6 max-w-2xl space-y-4">
        <p className="text-sm text-gray-500">
          Descreva a obra e o agente irá sugerir uma estrutura de planilha buscando
          composições no banco local (SINAPI, SICRO e próprias).
        </p>
        <textarea
          rows={6}
          value={descricao}
          onChange={e => setDescricao(e.target.value)}
          placeholder="Ex: Rodovia estadual de 25km, 2 faixas, pavimento flexível com CBUQ, relevo ondulado, drenagem superficial, sinalização horizontal e vertical..."
          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 resize-y"
        />
        <button
          onClick={handleGerar}
          disabled={!descricao.trim()}
          className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
        >
          ✨ Gerar proposta
        </button>
      </div>
    )
  }

  if (phase === 'streaming') {
    return (
      <div className="p-6 max-w-2xl space-y-4">
        <div className="flex items-center gap-3">
          <span className="inline-block w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          <span className="text-sm font-medium text-gray-700">Gerando proposta…</span>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-3 space-y-1 max-h-48 overflow-y-auto">
          {progressMsgs.map((msg, i) => (
            <p key={i} className="text-xs text-gray-600">{msg}</p>
          ))}
        </div>
        <button
          onClick={handleCancelar}
          className="text-sm text-gray-500 hover:text-gray-700 underline"
        >
          Cancelar
        </button>
      </div>
    )
  }

  if (phase === 'done' && importResult) {
    return (
      <div className="p-6 max-w-2xl space-y-4">
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <p className="text-sm font-medium text-green-800">
            ✓ {importResult.grupos_criados} grupos e {importResult.itens_criados} itens adicionados à planilha
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => navigate(`/obras/${obraId}/versoes/${versaoId}`)}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700"
          >
            Abrir planilha →
          </button>
          <button
            onClick={() => { setPhase('idle'); setDescricao('') }}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Gerar nova proposta
          </button>
        </div>
      </div>
    )
  }

  const gruposSelecionados = grupos.filter((_, i) => !removidos.has(i)).length

  return (
    <div className="p-6 max-w-2xl space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-600">
          <span className="font-medium">{grupos.length} grupos</span> sugeridos — revise antes de importar
        </p>
        <button
          onClick={() => setPhase('idle')}
          className="text-xs text-gray-400 hover:text-gray-600 underline"
        >
          ← Refazer
        </button>
      </div>

      <div className="space-y-2">
        {grupos.map((grupo, idx) => {
          const removido = removidos.has(idx)
          const expandido = expandidos.has(idx)
          const emEdicao = editando === idx

          return (
            <div
              key={idx}
              className={`border rounded-lg overflow-hidden transition-opacity ${removido ? 'opacity-40' : ''} ${emEdicao ? 'border-blue-400' : 'border-gray-200'}`}
            >
              <div
                className={`flex items-center justify-between px-3 py-2.5 cursor-pointer select-none ${emEdicao ? 'bg-blue-50' : 'bg-gray-50 hover:bg-gray-100'}`}
                onClick={() => !emEdicao && handleToggleExpand(idx)}
              >
                <div className="flex items-center gap-2 min-w-0">
                  <span className="text-gray-400 text-xs">{expandido ? '▼' : '▶'}</span>
                  {emEdicao ? (
                    <input
                      value={editNome}
                      onChange={e => setEditNome(e.target.value)}
                      onClick={e => e.stopPropagation()}
                      className="border border-blue-300 rounded px-2 py-0.5 text-sm font-medium focus:outline-none focus:ring-1 focus:ring-blue-400"
                    />
                  ) : (
                    <span className="font-medium text-sm text-gray-800 truncate">{grupo.nome}</span>
                  )}
                  {!emEdicao && (
                    <span className="text-xs text-gray-400 shrink-0">{grupo.itens.length} itens</span>
                  )}
                </div>
                <div className="flex gap-1.5 shrink-0 ml-2" onClick={e => e.stopPropagation()}>
                  {emEdicao ? (
                    <button
                      onClick={() => handleEditarConfirmar(idx)}
                      className="bg-blue-600 text-white px-2 py-0.5 rounded text-xs font-medium"
                    >
                      ✓ Confirmar
                    </button>
                  ) : (
                    <>
                      <button
                        onClick={() => handleToggleRemover(idx)}
                        className={`px-2 py-0.5 rounded text-xs font-medium ${removido ? 'bg-gray-200 text-gray-600' : 'bg-red-50 text-red-700 hover:bg-red-100'}`}
                      >
                        {removido ? '+ Incluir' : '✕ Remover'}
                      </button>
                      <button
                        onClick={() => handleEditarIniciar(idx)}
                        className="bg-yellow-50 text-yellow-800 px-2 py-0.5 rounded text-xs font-medium hover:bg-yellow-100"
                      >
                        ✏ Editar
                      </button>
                    </>
                  )}
                </div>
              </div>

              {(expandido || emEdicao) && (
                <div className="px-3 py-2 bg-white border-t border-gray-100">
                  <div className="grid grid-cols-[1fr_auto_auto_auto] gap-x-3 text-xs text-gray-400 pb-1 border-b border-gray-100 mb-1">
                    <span>Descrição</span><span>Cód.</span><span>Un</span><span className="text-right">Qtd</span>
                  </div>
                  {(emEdicao ? editItens : grupo.itens).map((item, j) => (
                    <div key={j} className="grid grid-cols-[1fr_auto_auto_auto] gap-x-3 items-center py-0.5 text-xs text-gray-700">
                      <span className="truncate">{item.descricao}</span>
                      <span className="text-gray-400">{item.codigo}</span>
                      <span className="text-gray-400">{item.unidade}</span>
                      {emEdicao ? (
                        <input
                          type="number"
                          min={0}
                          value={editItens[j].quantidade}
                          onChange={e => {
                            const updated = [...editItens]
                            updated[j] = { ...updated[j], quantidade: Number(e.target.value) }
                            setEditItens(updated)
                          }}
                          className="w-20 text-right border border-gray-300 rounded px-1 py-0.5 focus:outline-none focus:ring-1 focus:ring-blue-400"
                        />
                      ) : (
                        <span className="text-right">{item.quantidade.toLocaleString('pt-BR')}</span>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )
        })}
      </div>

      <div className="flex items-center justify-between pt-1">
        <span className="text-xs text-gray-400">
          {gruposSelecionados} de {grupos.length} grupos selecionados
        </span>
        <button
          onClick={handleImportar}
          disabled={gruposSelecionados === 0}
          className="bg-blue-600 text-white px-5 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
        >
          Importar {gruposSelecionados} grupo{gruposSelecionados !== 1 ? 's' : ''} →
        </button>
      </div>
    </div>
  )
}
