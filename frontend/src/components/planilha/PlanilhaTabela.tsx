import { useOrcamento } from '@/stores/orcamento'
import { getItens, createItem } from '@/api/itens'
import { createGrupo, createSubgrupo } from '@/api/grupos'
import { toast } from '@/hooks/useToast'
import PlanilhaLinha from './PlanilhaLinha'
import type { Grupo } from '@/types'

interface Props {
  versaoId: number
  isReadOnly: boolean
}

export default function PlanilhaTabela({ versaoId, isReadOnly }: Props) {
  const { grupos, itens, gruposAbertos, painel, toggleGrupo, abrirPainel, setItens, setGrupos } = useOrcamento()

  async function loadItens(grupoId: number) {
    if (itens[grupoId] !== undefined) return
    const items = await getItens(grupoId)
    setItens(grupoId, items)
  }

  function handleToggle(grupo: Grupo) {
    toggleGrupo(grupo.id)
    if (!gruposAbertos.has(grupo.id)) {
      loadItens(grupo.id)
    }
  }

  async function handleAddGrupo() {
    try {
      const ordem = grupos.length
      const g = await createGrupo(versaoId, { nome: 'Novo grupo', ordem })
      setGrupos([...grupos, { ...g, filhos: [] }])
      abrirPainel({ tipo: 'grupo', data: { ...g, filhos: [] } })
      toast('Grupo adicionado')
    } catch {
      toast('Erro ao adicionar grupo', 'error')
    }
  }

  async function handleAddSubgrupo(pai: Grupo) {
    try {
      const ordem = pai.filhos.length
      const sg = await createSubgrupo(pai.id, { nome: 'Novo subgrupo', ordem })
      const updated = { ...pai, filhos: [...pai.filhos, { ...sg, filhos: [] }] }
      useOrcamento.getState().updateGrupoNoStore(updated)
      abrirPainel({ tipo: 'grupo', data: { ...sg, filhos: [] } })
      toast('Subgrupo adicionado')
    } catch {
      toast('Erro ao adicionar subgrupo', 'error')
    }
  }

  async function handleAddItem(grupoId: number) {
    try {
      await loadItens(grupoId)
      const existentes = useOrcamento.getState().itens[grupoId] ?? []
      const item = await createItem(grupoId, { ordem: existentes.length, quantidade: '1.000000', unidade: 'un' })
      setItens(grupoId, [...existentes, item])
      abrirPainel({ tipo: 'item', data: item })
      if (!gruposAbertos.has(grupoId)) toggleGrupo(grupoId)
      toast('Item adicionado')
    } catch {
      toast('Erro ao adicionar item', 'error')
    }
  }

  const colHeader = (
    <div className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 border-b border-gray-200 text-xs text-gray-500 font-medium sticky top-0">
      <span className="w-4" />
      <span className="w-16">Cód.</span>
      <span className="flex-1">Descrição</span>
      <span className="w-8 text-right">Un</span>
      <span className="w-20 text-right">Qtde</span>
      <span className="w-24 text-right">Unit S/BDI</span>
      <span className="w-28 text-right">Total</span>
      <span className="w-16" />
    </div>
  )

  function renderGrupo(grupo: Grupo, tipo: 'grupo-raiz' | 'subgrupo') {
    const aberto = gruposAbertos.has(grupo.id)
    const selectedGrupo = painel?.tipo === 'grupo' && painel.data.id === grupo.id

    return (
      <div key={grupo.id}>
        <PlanilhaLinha
          tipo={tipo}
          grupo={grupo}
          aberto={aberto}
          selecionado={selectedGrupo}
          isReadOnly={isReadOnly}
          onToggle={() => handleToggle(grupo)}
          onSelect={() => abrirPainel({ tipo: 'grupo', data: grupo })}
          onAddSubgrupo={tipo === 'grupo-raiz' ? () => handleAddSubgrupo(grupo) : undefined}
          onAddItem={() => handleAddItem(grupo.id)}
        />

        {aberto && (
          <>
            {/* Subgrupos */}
            {tipo === 'grupo-raiz' && grupo.filhos.map(filho => renderGrupo(filho, 'subgrupo'))}

            {/* Itens do grupo */}
            {(itens[grupo.id] ?? []).map(item => (
              <PlanilhaLinha
                key={item.id}
                tipo="item"
                item={item}
                selecionado={painel?.tipo === 'item' && painel.data.id === item.id}
                isReadOnly={isReadOnly}
                onSelect={() => abrirPainel({ tipo: 'item', data: item })}
              />
            ))}
          </>
        )}
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-auto border border-gray-200 rounded-lg bg-white">
      {colHeader}
      {grupos.map(g => renderGrupo(g, 'grupo-raiz'))}

      {!isReadOnly && (
        <button
          onClick={handleAddGrupo}
          className="w-full py-3 text-sm text-blue-600 hover:bg-blue-50 border-t border-gray-100"
        >
          + Adicionar grupo
        </button>
      )}

      {grupos.length === 0 && (
        <p className="text-center py-12 text-gray-400 text-sm">
          {isReadOnly ? 'Sem grupos nesta versão' : 'Clique em "+ Adicionar grupo" para começar'}
        </p>
      )}
    </div>
  )
}
