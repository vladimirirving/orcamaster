import { create } from 'zustand'
import type { Versao, Grupo, Item, BDI } from '@/types'

type PainelItem =
  | { tipo: 'grupo'; data: Grupo }
  | { tipo: 'item'; data: Item }
  | null

interface OrcamentoState {
  versao: Versao | null
  bdi: BDI | null
  grupos: Grupo[]
  itens: Record<number, Item[]>
  gruposAbertos: Set<number>
  painel: PainelItem

  setVersao: (v: Versao) => void
  setBdi: (b: BDI | null) => void
  setGrupos: (gs: Grupo[]) => void
  setItens: (grupoId: number, is: Item[]) => void
  toggleGrupo: (id: number) => void
  abrirPainel: (p: PainelItem) => void
  fecharPainel: () => void
  updateItemNoStore: (item: Item) => void
  removeItemDoStore: (item: Item) => void
  updateGrupoNoStore: (grupo: Grupo) => void
  removeGrupoDoStore: (grupoId: number) => void
}

export const useOrcamento = create<OrcamentoState>((set) => ({
  versao: null,
  bdi: null,
  grupos: [],
  itens: {},
  gruposAbertos: new Set(),
  painel: null,

  setVersao: (v) => set({ versao: v }),
  setBdi: (b) => set({ bdi: b }),
  setGrupos: (gs) => set({ grupos: gs }),
  setItens: (grupoId, is) => set((s) => ({ itens: { ...s.itens, [grupoId]: is } })),
  toggleGrupo: (id) => set((s) => {
    const next = new Set(s.gruposAbertos)
    next.has(id) ? next.delete(id) : next.add(id)
    return { gruposAbertos: next }
  }),
  abrirPainel: (p) => set({ painel: p }),
  fecharPainel: () => set({ painel: null }),

  updateItemNoStore: (item) => set((s) => ({
    itens: {
      ...s.itens,
      [item.grupo_id]: (s.itens[item.grupo_id] ?? []).map(i => i.id === item.id ? item : i),
    },
    painel: s.painel?.tipo === 'item' && s.painel.data.id === item.id
      ? { tipo: 'item', data: item }
      : s.painel,
  })),

  removeItemDoStore: (item) => set((s) => ({
    itens: {
      ...s.itens,
      [item.grupo_id]: (s.itens[item.grupo_id] ?? []).filter(i => i.id !== item.id),
    },
    painel: s.painel?.tipo === 'item' && s.painel.data.id === item.id ? null : s.painel,
  })),

  updateGrupoNoStore: (grupo) => set((s) => ({
    grupos: updateGrupoInTree(s.grupos, grupo),
    painel: s.painel?.tipo === 'grupo' && s.painel.data.id === grupo.id
      ? { tipo: 'grupo', data: grupo }
      : s.painel,
  })),

  removeGrupoDoStore: (grupoId) => set((s) => ({
    grupos: removeGrupoFromTree(s.grupos, grupoId),
    painel: s.painel?.tipo === 'grupo' && s.painel.data.id === grupoId ? null : s.painel,
  })),
}))

function updateGrupoInTree(grupos: Grupo[], updated: Grupo): Grupo[] {
  return grupos.map(g => {
    if (g.id === updated.id) return { ...updated, filhos: g.filhos }
    return { ...g, filhos: updateGrupoInTree(g.filhos, updated) }
  })
}

function removeGrupoFromTree(grupos: Grupo[], id: number): Grupo[] {
  return grupos
    .filter(g => g.id !== id)
    .map(g => ({ ...g, filhos: removeGrupoFromTree(g.filhos, id) }))
}
