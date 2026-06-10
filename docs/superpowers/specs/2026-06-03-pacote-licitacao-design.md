# Módulo 10 — Pacote de Licitação: Design Spec

**Data:** 2026-06-03
**Status:** Aprovado

---

## 1. Objetivo

Gerar um arquivo ZIP contendo os documentos necessários para um pregão eletrônico — Proposta (PDF), Planilha Orçamentária (XLSX) e Cronograma Físico-Financeiro (XLSX) — a partir dos dados da versão ativa de uma obra. A geração ocorre em background via FastAPI BackgroundTasks. O frontend acompanha o progresso por polling e oferece download direto quando o pacote está pronto.

---

## 2. Escopo

**Inclui:**
- Endpoint POST para criar e disparar o job de geração
- Endpoint GET para consultar status do job
- Endpoint GET `/download` para baixar o ZIP
- Serviço orquestrador `pacote_service.py` que gera os três documentos e compacta o ZIP
- Geração da Planilha Orçamentária XLSX (grupos → itens → preços) via openpyxl
- Geração do Cronograma XLSX (distribuição mensal por item) via openpyxl
- Reutilização de `gerar_pdf_bytes` do Módulo 9 para a Proposta
- Aba "Pacote" em `ObraDetailPage` com polling, botão "Gerar Pacote" e botão "Baixar ZIP"

**Fora do escopo:**
- Deleção física dos arquivos ZIP expirados (o scheduler já marca como `expirado`; purge de disco fica para módulo futuro)
- Geração em paralelo dos documentos
- Múltiplos jobs simultâneos por versão
- Notificação push/email ao concluir
- Armazenamento em nuvem (S3 etc.)

---

## 3. Modelo de Dados

`PacoteJob` já existe — nenhuma migração necessária.

```python
class PacoteJob(Base):
    __tablename__ = "pacote_job"

    id:            Mapped[int]           = mapped_column(primary_key=True)
    empresa_id:    Mapped[int]           = mapped_column(Integer)  # denormalized for concurrency check
    versao_id:     Mapped[int]           = mapped_column(ForeignKey("versao.id", ondelete="CASCADE"))
    status:        Mapped[str]           = mapped_column(String(20), default="pendente")
    criado_em:     Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    url_download:  Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    erro_mensagem: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    gerado_em:     Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    versao: Mapped["Versao"] = relationship(back_populates="pacote_jobs")
```

**Fluxo de status:** `pendente → processando → pronto | erro`
**Scheduler existente:** `expire_pacotes_job` marca como `expirado` após 7 dias (já implementado).

**Arquivo ZIP:** salvo em `settings.pacotes_dir / f"pacote-v{versao_id}-{job_id}.zip"`.
`url_download` armazena apenas o nome do arquivo (sem path completo).

---

## 4. Backend

### 4.1 Arquivos

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `app/schemas/pacote.py` | Criar | Schemas Pydantic (in/out) |
| `app/services/pacote_service.py` | Criar | Orquestrador + geração XLSX |
| `app/routers/pacote.py` | Criar | 3 endpoints REST |
| `app/main.py` | Modificar | Registrar `pacote.router` |

### 4.2 Schemas (`app/schemas/pacote.py`)

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class PacoteJobOut(BaseModel):
    id: int
    versao_id: int
    status: str          # pendente | processando | pronto | erro | expirado
    criado_em: datetime
    atualizado_em: datetime
    url_download: Optional[str] = None
    erro_mensagem: Optional[str] = None
    gerado_em: Optional[datetime] = None
    model_config = {"from_attributes": True}
```

### 4.3 Endpoints (`app/routers/pacote.py`)

```
POST /versoes/{versao_id}/pacote          → PacoteJobOut
GET  /versoes/{versao_id}/pacote          → PacoteJobOut | 404
GET  /versoes/{versao_id}/pacote/download → FileResponse (ZIP)
```

**Isolamento:** todos os endpoints verificam `Versao → Obra.empresa_id == current_user.empresa_id` via helper `_get_versao` (mesmo padrão dos outros módulos).

**POST `/pacote`:**
1. Verifica se já existe job com `status IN ("pendente", "processando")` para a versão → retorna 409 se sim
2. Cria `PacoteJob(versao_id=versao_id, empresa_id=current_user.empresa_id, status="pendente")`
3. Persiste e faz commit
4. Registra `background_tasks.add_task(processar_pacote, job.id, versao_id)`
5. Retorna o job criado

**GET `/pacote`:**
- Busca o job mais recente para a versão (`ORDER BY criado_em DESC LIMIT 1`)
- Retorna 404 se nenhum job existe

**GET `/pacote/download`:**
- Busca o job mais recente para a versão
- Retorna 404 se não existe ou `status != "pronto"`
- Retorna `FileResponse(path, media_type="application/zip", filename="pacote-v{versao_id}.zip")`

### 4.4 Serviço (`app/services/pacote_service.py`)

Interface pública:
```python
async def processar_pacote(job_id: int, versao_id: int) -> None:
    """Gera ZIP com proposta PDF + planilha XLSX + cronograma XLSX. Chamado via BackgroundTasks."""
```

Fluxo interno:
1. Abre `AsyncSessionLocal()` própria (não herda a sessão da requisição)
2. Carrega o job; seta `status = "processando"`, commit
3. Chama `gerar_pdf_bytes(versao_id, db)` → captura `HTTPException(404)` e omite `proposta.pdf` do ZIP sem erro
4. Chama `gerar_planilha_bytes(versao_id, db)` → retorna bytes XLSX da planilha orçamentária
5. Chama `gerar_cronograma_bytes(versao_id, db)` → retorna `None` se `cronograma_inicio` for null; retorna bytes XLSX do cronograma
6. Compacta ZIP em memória com `zipfile.ZipFile`
7. Salva em `settings.pacotes_dir / f"pacote-v{versao_id}-{job_id}.zip"` (cria dir se não existir)
8. Atualiza job: `status = "pronto"`, `url_download = filename`, `gerado_em = datetime.utcnow()`
9. Em qualquer exceção não tratada: `status = "erro"`, `erro_mensagem = str(e)[:1000]`, commit

### 4.5 Planilha Orçamentária XLSX (`gerar_planilha_bytes`)

- Carrega grupos ordenados por `Grupo.ordem` via `selectinload(Grupo.itens).selectinload(Item.composicao)`
- Inclui subgrupos (grupos com `pai_id != None`) como linhas de cabeçalho aninhadas com indentação
- Colunas: `Código | Descrição | Un | Qtd | Preço Unit. (R$) | Total (R$)`
- Linha de grupo: fundo cinza, negrito, colspan via merge de células
- Linha de item: dados do `Item` + `item.composicao.descricao` (ou "—" se sem composição)
- Linha de subtotal por grupo
- Linha de BDI (alíquota + valor) se existir
- Linha de TOTAL GERAL
- Retorna `bytes` via `BytesIO`

### 4.6 Cronograma XLSX (`gerar_cronograma_bytes`)

- Retorna `None` se `versao.cronograma_inicio` é null (sem dados de cronograma)
- Carrega `CronogramaLinha` com `selectinload(CronogramaLinha.item)` ordenado por `item.ordem`
- Colunas: `Item | Descrição | Un | Qtd | Total` + colunas mensais `MMM/AAAA` de `cronograma_inicio` até `cronograma_fim`
- Cada linha é um `CronogramaLinha` com `distribuicao_json` mapeando mês → percentual
- Valor mensal = `total_sem_bdi * percentual / 100`
- Linha de totais mensais no rodapé
- Retorna `bytes` via `BytesIO`

---

## 5. Frontend

### 5.1 Arquivos

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `frontend/src/types.ts` | Modificar | +`PacoteJob` interface |
| `frontend/src/api/pacote.ts` | Criar | `createPacote`, `getPacote`, `downloadPacote` |
| `frontend/src/components/obra/PacoteTab.tsx` | Criar | UI com polling + botões |
| `frontend/src/pages/ObraDetailPage.tsx` | Modificar | +aba "Pacote" |

### 5.2 Tipos (`types.ts`)

```ts
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
```

### 5.3 API (`api/pacote.ts`)

```ts
export const createPacote = (versaoId: number): Promise<PacoteJob> =>
  api.post<PacoteJob>(`/versoes/${versaoId}/pacote`).then(r => r.data)

export const getPacote = (versaoId: number): Promise<PacoteJob> =>
  api.get<PacoteJob>(`/versoes/${versaoId}/pacote`).then(r => r.data)

export async function downloadPacote(versaoId: number): Promise<void> {
  const resp = await api.get<Blob>(`/versoes/${versaoId}/pacote/download`, {
    responseType: 'blob',
  })
  const url = URL.createObjectURL(resp.data)
  const a = document.createElement('a')
  a.href = url
  a.download = `pacote-v${versaoId}.zip`
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 100)
}
```

### 5.4 `PacoteTab.tsx`

Props: `{ versaoId: number }`

Estados: `job` (PacoteJob | null), `loading`, `generating`, `downloading`

Comportamento:
- Monta com `useEffect([versaoId])`: chama `getPacote`; se 404, `job = null`
- Se `job.status` é `pendente` ou `processando`: inicia polling com `setInterval(3000)`; limpa interval ao desmontar ou quando status muda para terminal
- **"Gerar Pacote"** (habilitado se `job == null || status == "erro" || status == "expirado"`): chama `createPacote`, atualiza `job`, inicia polling
- **"Baixar ZIP"** (visível apenas se `status == "pronto"`): chama `downloadPacote`
- Indicador de progresso (spinner) quando `status == "pendente" || "processando"`
- Mensagem de erro em vermelho quando `status == "erro"` exibe `job.erro_mensagem`
- Mensagem "Pacote expirado — gere um novo" quando `status == "expirado"`
- Sem versão ativa: mensagem estática padrão

---

## 6. Testes

### 6.1 Backend (`tests/backend/test_pacote.py`)

| Teste | Descrição |
|-------|-----------|
| `test_post_pacote_cria_job` | POST cria job `pendente`, retorna 200 |
| `test_post_pacote_conflito` | POST com job `processando` ativo retorna 409 |
| `test_get_pacote_not_found` | GET sem job existente retorna 404 |
| `test_get_pacote_status` | GET retorna último job da versão |
| `test_download_not_ready` | GET /download com job `pendente` retorna 404 |
| `test_isolamento_empresa_b` | Empresa B não acessa pacote da empresa A |
| `test_processar_pacote_ok` | Chama `processar_pacote` diretamente; verifica `status == "pronto"` e arquivo ZIP criado com conteúdo válido |
| `test_processar_pacote_sem_proposta` | PropostaConfig ausente; pacote gerado sem `proposta.pdf`, `status == "pronto"` |
| `test_processar_pacote_sem_cronograma` | `cronograma_inicio == null`; pacote gerado sem `cronograma.xlsx`, `status == "pronto"` |
| `test_processar_pacote_erro` | Erro inesperado; `status == "erro"` e `erro_mensagem` preenchido |

### 6.2 Frontend (manual)

- Clicar "Gerar Pacote" → spinner aparece → status vira `pronto` → botão "Baixar ZIP" aparece
- Baixar ZIP → arquivo contém os documentos esperados
- Clicar "Gerar Pacote" com job em andamento → botão desabilitado (sem segundo job criado)
- Job `erro` exibe mensagem de erro + habilita "Gerar Pacote" para nova tentativa
- Obra sem versão ativa → mensagem estática

---

## 7. Dependências

- **`zipfile`** — stdlib Python, sem instalação adicional
- **`openpyxl`** — já em `pyproject.toml`
- **`pypdf`** — já em `pyproject.toml` (não usado neste módulo, mas disponível)
- **`gerar_pdf_bytes`** — `app.services.proposta_pdf` (Módulo 9)
- **`FileResponse`** — `fastapi.responses`, sem dependência extra

---

## 8. Interface para Módulos Futuros

```python
from app.services.pacote_service import processar_pacote
# Chamada direta (já usada pelo router via BackgroundTasks):
await processar_pacote(job_id=job.id, versao_id=versao_id)
```
