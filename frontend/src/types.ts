export interface Obra {
  id: number
  nome: string
  tipo_obra: string
  estado: string
  data_criacao: string
  numero_processo: string | null
  data_prazo: string | null
  responsavel_id: number | null
  cliente: string | null
  cliente_id: number | null
  cliente_nome: string | null
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
  cronograma_inicio: string | null
  cronograma_fim: string | null
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
  empresa_id: number | null   // null = SINAPI/SICRO; number = própria da empresa
  origem: string
  codigo: string
  descricao: string
  unidade: string
  preco_unitario: string
}

export interface CronogramaLinhaData {
  item_id: number
  descricao: string
  unidade: string
  quantidade: string
  total_sem_bdi: string
  distribuicao_json: Record<string, number>
}

export interface CronogramaData {
  cronograma_inicio: string | null
  cronograma_fim: string | null
  linhas: CronogramaLinhaData[]
}

export interface MedicaoData {
  id: number
  periodo_inicio: string   // "2025-06-01"
  periodo_fim: string      // "2025-06-30"
  linhas_json: Record<string, number>  // {"42": 35.0}
  criada_por: number | null
}

export interface DashboardResumoItem {
  obra_id: number
  obra_nome: string
  versao_id: number | null
  total_sem_bdi: string | null
  total_com_bdi: string | null        // novo
  estado: string                       // novo
  tem_alertas: boolean                 // novo
  planejado_pct_hoje: number | null
  realizado_pct: number | null
  desvio: number | null
  status: 'adiantado' | 'no_prazo' | 'atrasado' | 'sem_dados'
}

export interface CurvaSPonto {
  mes: string
  planejado_acum: number
  realizado_acum: number | null
}

export interface ObraDashboardData {
  versao_id: number | null
  total_sem_bdi: string | null
  total_com_bdi: string | null        // novo
  planejado_pct_hoje: number | null
  realizado_pct: number | null
  desvio: number | null
  status: string
  curva_s: CurvaSPonto[]
}

export interface GrupoDistribuicao {
  grupo_id: number
  grupo_nome: string
  total: string
  participacao_pct: number
}

export interface DistribuicaoGruposOut {
  versao_id: number | null
  total_versao: string
  grupos: GrupoDistribuicao[]
}

export interface CurvaAbcItem {
  rank: number
  grupo_nome: string
  descricao: string
  unidade: string
  quantidade: string
  total: string
  participacao_pct: number
  acumulado_pct: number
  faixa: 'A' | 'B' | 'C'
}

export interface CurvaAbcData {
  total_versao: string
  itens: CurvaAbcItem[]
}

export interface PropostaConfig {
  id: number
  versao_id: number
  validade_dias: number
  data_proposta: string   // YYYY-MM-DD
  declaracoes: string | null
  criado_em: string
  atualizado_em: string
}

export interface EmpresaConfig {
  id: number
  nome: string
  cnpj: string
  representante_nome: string | null
  representante_cpf: string | null
  declaracoes_padrao: string | null
}

export interface PacoteJob {
  id: number
  versao_id: number
  status: 'pendente' | 'processando' | 'pronto' | 'erro' | 'expirado'
  criado_em: string
  atualizado_em: string
  url_download: string | null
  erro_mensagem: string | null
  gerado_em: string | null
}

export interface PropostaItem {
  composicao_id: number
  descricao: string
  codigo: string
  unidade: string
  quantidade: number
}

export interface PropostaGrupo {
  nome: string
  itens: PropostaItem[]
}

export interface PropostaSugerida {
  grupos: PropostaGrupo[]
}

export interface Usuario {
  id: number
  empresa_id: number
  nome: string
  email: string
  papel: 'admin' | 'orcamentista' | 'visualizador'
  ativo: boolean
}

export interface Cliente {
  id: number
  empresa_id: number
  tipo: 'pf' | 'pj'
  nome: string
  cpf_cnpj: string | null
  email: string | null
  telefone: string | null
  endereco: string | null
  cidade: string | null
  estado: string | null
  observacoes: string | null
  created_at: string
}

export interface Fornecedor {
  id: number
  empresa_id: number
  nome: string
  cnpj: string | null
  email: string | null
  telefone: string | null
  endereco: string | null
  cidade: string | null
  estado: string | null
  categorias: string | null
  observacoes: string | null
  created_at: string
}

export interface DiarioFoto {
  id: number
  diario_id: number
  nome_original: string
  tamanho_bytes: number
  criado_em: string
}

export interface DiarioEntrada {
  id: number
  obra_id: number
  data: string              // YYYY-MM-DD
  clima: 'ensolarado' | 'parcialmente_nublado' | 'nublado' | 'chuvoso'
  turnos: string | null     // CSV: 'manha,tarde,noite'
  efetivo: number
  equipes: string | null
  equipamentos: string | null
  atividades: string
  ocorrencias: string | null
  criado_por: number | null
  created_at: string
  fotos: DiarioFoto[]
  qtd_fotos?: number
}

export interface RelatorioMedicaoGrupo {
  grupo_id: number
  grupo_nome: string
  planejado_pct: number
  realizado_pct: number
  desvio_pct: number
  valor_medido: string
  valor_total: string
}

export interface RelatorioMedicaoOut {
  versao_id: number
  ultima_medicao_id: number | null
  periodo_fim: string | null
  grupos: RelatorioMedicaoGrupo[]
}

export interface ComparativoItem {
  status: 'novo' | 'removido' | 'alterado' | 'igual'
  grupo_nome: string
  descricao: string
  unidade: string
  v1_preco_unit: string | null
  v2_preco_unit: string | null
  v1_quantidade: string | null
  v2_quantidade: string | null
  v1_total: string | null
  v2_total: string | null
  delta_total: string
}

export interface ComparativoOut {
  obra_id: number
  v1_id: number
  v2_id: number
  v1_nome: string
  v2_nome: string
  v1_total: string
  v2_total: string
  delta_total: string
  delta_pct: number
  qtd_novos: number
  qtd_removidos: number
  qtd_alterados: number
  itens: ComparativoItem[]
}

export interface Aditivo {
  id: number
  contrato_id: number
  numero: string | null
  tipo: 'valor' | 'prazo' | 'valor_prazo'
  delta_valor: number | null
  nova_data_fim: string | null
  justificativa: string | null
  data_assinatura: string | null
  arquivo_path: string | null
  criado_em: string
}

export interface Contrato {
  id: number
  obra_id: number
  numero: string | null
  objeto: string
  valor_original: number
  valor_atual: number
  data_assinatura: string | null
  data_inicio: string | null
  data_fim: string | null
  data_fim_atual: string | null
  contratante_nome: string | null
  contratante_cnpj: string | null
  contratado_nome: string | null
  contratado_cnpj: string | null
  arquivo_path: string | null
  criado_em: string
  aditivos: Aditivo[]
}

export interface Alerta {
  tipo: 'contrato_vencido' | 'contrato_vencendo' | 'desvio_orcamento' | 'medicao_atrasada' | 'item_revisao'
  severidade: 'alta' | 'media' | 'baixa'
  obra_id: number
  obra_nome: string
  titulo: string
  detalhe: string | null
  link: string
}

export interface InsumoItem {
  id: number
  banco: string           // 'sinapi' | 'sicro' | 'propria'
  codigo: string
  descricao: string
  unidade: string
  tipo: string            // 'mao_obra' | 'material' | 'equipamento'
  preco_nao_desonerado: string
  preco_desonerado: string
  estado: string | null
  data_referencia: string // 'YYYY-MM-DD'
  empresa_id: number | null
}

export interface InsumoItemListOut {
  items: InsumoItem[]
  total: number
}
