export interface Obra {
  id: number
  nome: string
  tipo_obra: string
  estado: string
  data_criacao: string
  cliente: string | null
  municipio: string | null
  uf: string | null
}

export interface Versao {
  id: number
  obra_id: number
  numero: number
  nome: string | null
  bloqueada: boolean
  deletada_em: string | null
  total_sem_bdi: string
  total_com_bdi: string
}

export interface Grupo {
  id: number
  versao_id: number
  pai_id: number | null
  nome: string
  codigo: string | null
  ordem: number
  filhos: Grupo[]
}

export interface Item {
  id: number
  grupo_id: number
  ordem: number
  composicao_id: number | null
  quantidade: string
  unidade: string | null
  preco_unitario_sem_bdi: string | null
  preco_unitario_com_bdi: string | null
  total: string
  requer_revisao: boolean
  etiqueta_revisao: string | null
}

export interface BDI {
  id: number
  versao_id: number
  ac: string; sg: string; r: string; df: string; lucro: string
  iss: string; pis: string; cofins: string
  bdi_composto: string
}

export interface Composicao {
  id: number
  origem: string
  codigo: string
  descricao: string
  unidade: string
  preco_unitario: string
}
