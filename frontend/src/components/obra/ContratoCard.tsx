import { useRef, useState } from 'react'
import {
  deleteContrato, uploadContratoFile, downloadContratoUrl,
  deleteAditivo, uploadAditivoFile, downloadAditivoUrl,
} from '@/api/contratos'
import { toast } from '@/hooks/useToast'
import { fmtBRL } from '@/lib/utils'
import type { Contrato, Aditivo } from '@/types'
import ContratoModal from './ContratoModal'
import AditivoModal from './AditivoModal'

interface Props {
  contrato: Contrato
  obraId: number
  onUpdate: (c: Contrato) => void
  onDelete: (id: number) => void
}

function statusBadge(dataFimAtual: string | null) {
  if (!dataFimAtual) return null
  const hoje = new Date()
  const fim = new Date(dataFimAtual)
  const diff = (fim.getTime() - hoje.getTime()) / (1000 * 60 * 60 * 24)
  if (diff < 0) return <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700 font-medium">Vencido</span>
  if (diff <= 30) return <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700 font-medium">Vence em breve</span>
  return <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700 font-medium">Vigente</span>
}

function recomputeContrato(contrato: Contrato, aditivos: Aditivo[]): Contrato {
  const valor_atual = aditivos.reduce((s, a) => s + (a.delta_valor ?? 0), contrato.valor_original)
  const sorted = [...aditivos].sort((a, b) => a.id - b.id)
  const data_fim_atual = sorted.reduce<string | null>((d, a) => a.nova_data_fim ?? d, contrato.data_fim)
  return { ...contrato, aditivos, valor_atual, data_fim_atual }
}

function tipoLabel(tipo: string) {
  return tipo === 'valor' ? 'Valor' : tipo === 'prazo' ? 'Prazo' : 'Valor + Prazo'
}

export default function ContratoCard({ contrato, obraId, onUpdate, onDelete }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [editOpen, setEditOpen] = useState(false)
  const [aditivoModal, setAditivoModal] = useState<{ open: boolean; aditivo?: Aditivo }>({ open: false })
  const fileRef = useRef<HTMLInputElement>(null)
  const adFileRefs = useRef<Record<number, HTMLInputElement | null>>({})

  async function handleDelete() {
    if (!confirm('Remover este contrato e todos os seus aditivos?')) return
    try {
      await deleteContrato(contrato.id)
      onDelete(contrato.id)
      toast('Contrato removido')
    } catch {
      toast('Erro ao remover contrato', 'error')
    }
  }

  async function handleUpload(file: File) {
    try {
      const updated = await uploadContratoFile(contrato.id, file)
      onUpdate(updated)
      toast('PDF anexado')
    } catch {
      toast('Erro ao enviar PDF', 'error')
    }
  }

  async function handleDeleteAditivo(aditivoId: number) {
    if (!confirm('Remover este aditivo?')) return
    try {
      await deleteAditivo(aditivoId)
      const aditivos = contrato.aditivos.filter(a => a.id !== aditivoId)
      onUpdate(recomputeContrato(contrato, aditivos))
      toast('Aditivo removido')
    } catch {
      toast('Erro ao remover aditivo', 'error')
    }
  }

  async function handleUploadAditivo(aditivoId: number, file: File) {
    try {
      const updated = await uploadAditivoFile(aditivoId, file)
      onUpdate({
        ...contrato,
        aditivos: contrato.aditivos.map(a => a.id === updated.id ? updated : a),
      })
      toast('PDF do aditivo anexado')
    } catch {
      toast('Erro ao enviar PDF', 'error')
    }
  }

  return (
    <div className="border border-gray-200 rounded-xl bg-white overflow-hidden">
      {/* Header do card */}
      <button
        className="w-full text-left px-5 py-4 flex items-center gap-3 hover:bg-gray-50 transition-colors"
        onClick={() => setExpanded(v => !v)}
      >
        <svg className={`w-4 h-4 text-gray-400 transition-transform flex-shrink-0 ${expanded ? 'rotate-90' : ''}`}
          viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="9 18 15 12 9 6" />
        </svg>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-medium text-gray-900 text-sm">
              {contrato.numero ?? 'Sem número'}
            </span>
            {statusBadge(contrato.data_fim_atual)}
            {contrato.arquivo_path && (
              <span title="PDF anexado">
                <svg className="w-3.5 h-3.5 text-gray-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48" />
                </svg>
              </span>
            )}
          </div>
          <p className="text-xs text-gray-500 truncate mt-0.5">{contrato.objeto}</p>
        </div>
        <div className="text-right flex-shrink-0">
          <p className="text-sm font-semibold text-gray-900">{fmtBRL(String(contrato.valor_atual))}</p>
          {contrato.aditivos.length > 0 && (
            <p className="text-xs text-gray-400">{contrato.aditivos.length} aditivo{contrato.aditivos.length > 1 ? 's' : ''}</p>
          )}
        </div>
      </button>

      {/* Corpo expandido */}
      {expanded && (
        <div className="border-t border-gray-100 px-5 py-4 space-y-4">
          {/* Campos do contrato */}
          <div className="grid grid-cols-2 gap-x-6 gap-y-2 text-sm">
            {contrato.data_assinatura && (
              <div><span className="text-gray-500">Assinatura:</span> <span className="text-gray-900">{contrato.data_assinatura}</span></div>
            )}
            {contrato.data_inicio && (
              <div><span className="text-gray-500">Início:</span> <span className="text-gray-900">{contrato.data_inicio}</span></div>
            )}
            {contrato.data_fim && (
              <div><span className="text-gray-500">Prazo original:</span> <span className="text-gray-900">{contrato.data_fim}</span></div>
            )}
            {contrato.data_fim_atual && contrato.data_fim_atual !== contrato.data_fim && (
              <div><span className="text-gray-500">Prazo atual:</span> <span className="font-medium text-gray-900">{contrato.data_fim_atual}</span></div>
            )}
            {contrato.valor_atual !== contrato.valor_original && (
              <div><span className="text-gray-500">Valor original:</span> <span className="text-gray-900">{fmtBRL(String(contrato.valor_original))}</span></div>
            )}
            {contrato.contratante_nome && (
              <div><span className="text-gray-500">Contratante:</span> <span className="text-gray-900">{contrato.contratante_nome}{contrato.contratante_cnpj ? ` — ${contrato.contratante_cnpj}` : ''}</span></div>
            )}
            {contrato.contratado_nome && (
              <div><span className="text-gray-500">Contratada:</span> <span className="text-gray-900">{contrato.contratado_nome}{contrato.contratado_cnpj ? ` — ${contrato.contratado_cnpj}` : ''}</span></div>
            )}
          </div>

          {/* Aditivos */}
          {contrato.aditivos.length > 0 && (
            <div>
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-2">Aditivos</p>
              <div className="space-y-2">
                {contrato.aditivos.map(a => (
                  <div key={a.id} className="flex items-start gap-2 bg-gray-50 rounded-lg px-3 py-2">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 text-xs">
                        <span className="font-medium text-gray-800">{a.numero ?? tipoLabel(a.tipo)}</span>
                        <span className="text-gray-400">{tipoLabel(a.tipo)}</span>
                        {a.delta_valor != null && (
                          <span className={`font-medium ${a.delta_valor >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {a.delta_valor >= 0 ? '+' : ''}{fmtBRL(String(a.delta_valor))}
                          </span>
                        )}
                        {a.nova_data_fim && <span className="text-gray-500">→ {a.nova_data_fim}</span>}
                        {a.arquivo_path && (
                          <a
                            href={downloadAditivoUrl(a.id)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-500 hover:text-blue-700"
                            title="Baixar PDF"
                          >
                            PDF
                          </a>
                        )}
                      </div>
                      {a.justificativa && <p className="text-xs text-gray-400 mt-0.5 truncate">{a.justificativa}</p>}
                    </div>
                    <div className="flex items-center gap-1 flex-shrink-0">
                      <button
                        onClick={() => adFileRefs.current[a.id]?.click()}
                        className="text-xs text-gray-400 hover:text-gray-600 px-1"
                        title="Upload PDF"
                      >
                        <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/>
                        </svg>
                      </button>
                      <input
                        type="file"
                        accept=".pdf"
                        className="hidden"
                        ref={el => { adFileRefs.current[a.id] = el }}
                        onChange={e => { const f = e.target.files?.[0]; if (f) handleUploadAditivo(a.id, f) }}
                      />
                      <button
                        onClick={() => setAditivoModal({ open: true, aditivo: a })}
                        className="text-xs text-gray-400 hover:text-gray-600 px-1"
                        title="Editar"
                      >
                        <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                      </button>
                      <button
                        onClick={() => handleDeleteAditivo(a.id)}
                        className="text-xs text-red-300 hover:text-red-500 px-1"
                        title="Remover"
                      >
                        <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/>
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Ações */}
          <div className="flex flex-wrap gap-2 pt-1">
            <button
              onClick={() => setEditOpen(true)}
              className="flex items-center gap-1.5 text-xs border border-gray-300 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors text-gray-700"
            >
              Editar
            </button>
            <button
              onClick={() => fileRef.current?.click()}
              className="flex items-center gap-1.5 text-xs border border-gray-300 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors text-gray-700"
            >
              {contrato.arquivo_path ? 'Substituir PDF' : 'Anexar PDF'}
            </button>
            {contrato.arquivo_path && (
              <a
                href={downloadContratoUrl(contrato.id)}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 text-xs border border-gray-300 px-3 py-1.5 rounded-lg hover:bg-gray-50 transition-colors text-gray-700"
              >
                Baixar PDF
              </a>
            )}
            <button
              onClick={() => setAditivoModal({ open: true })}
              className="flex items-center gap-1.5 text-xs bg-blue-50 border border-blue-200 text-blue-700 px-3 py-1.5 rounded-lg hover:bg-blue-100 transition-colors"
            >
              + Aditivo
            </button>
            <button
              onClick={handleDelete}
              className="flex items-center gap-1.5 text-xs border border-red-200 text-red-500 px-3 py-1.5 rounded-lg hover:bg-red-50 transition-colors ml-auto"
            >
              Excluir
            </button>
          </div>

          <input
            type="file"
            accept=".pdf"
            className="hidden"
            ref={fileRef}
            onChange={e => { const f = e.target.files?.[0]; if (f) handleUpload(f) }}
          />
        </div>
      )}

      {editOpen && (
        <ContratoModal
          obraId={obraId}
          contrato={contrato}
          onClose={() => setEditOpen(false)}
          onSuccess={updated => { onUpdate(updated); setEditOpen(false) }}
        />
      )}

      {aditivoModal.open && (
        <AditivoModal
          contratoId={contrato.id}
          aditivo={aditivoModal.aditivo}
          onClose={() => setAditivoModal({ open: false })}
          onSuccess={a => {
            const aditivos = aditivoModal.aditivo
              ? contrato.aditivos.map(x => x.id === a.id ? a : x)
              : [...contrato.aditivos, a]
            onUpdate(recomputeContrato(contrato, aditivos))
            setAditivoModal({ open: false })
          }}
        />
      )}
    </div>
  )
}
