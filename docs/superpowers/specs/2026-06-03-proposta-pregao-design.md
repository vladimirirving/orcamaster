# Módulo 9 — Gerador de Proposta para Pregão: Design Spec

**Data:** 2026-06-03
**Status:** Aprovado

---

## 1. Objetivo

Gerar um documento PDF formatado para licitações por pregão eletrônico a partir dos dados da versão ativa de uma obra. O documento inclui: identificação da empresa e representante legal, dados da obra, planilha de preços unitários e totais por grupo, BDI, declarações e campo de assinatura.

Os dados específicos da proposta (validade, data, declarações) ficam persistidos por versão para que o Módulo 10 (Pacote de Licitação) possa regenerar o PDF em background sem intervenção do usuário.

---

## 2. Escopo

**Inclui:**
- Extensão do modelo `Empresa` com campos de representante legal e declarações padrão
- Novo modelo `PropostaConfig` associado a uma `Versao`
- Endpoints REST para configuração de empresa, CRUD de `PropostaConfig` e exportação PDF
- Template HTML/CSS estático renderizado via WeasyPrint + Jinja2
- Aba "Proposta" em `ObraDetailPage` com formulário + botão "Baixar PDF"
- Página `/configuracoes` (admin) para configurar representante e declarações padrão

**Fora do escopo:**
- Editor de template HTML pelo administrador
- Geração em background (isso é Módulo 10)
- Múltiplas propostas por versão
- Assinatura digital ou carimbo

---

## 3. Modelo de Dados

### 3.1 Extensão de `Empresa`

Três novos campos opcionais:

```sql
ALTER TABLE empresa ADD COLUMN representante_nome VARCHAR(200);
ALTER TABLE empresa ADD COLUMN representante_cpf  VARCHAR(14);
ALTER TABLE empresa ADD COLUMN declaracoes_padrao TEXT;
```

Correspondência em `app/models/empresa.py`:
```python
representante_nome: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
representante_cpf:  Mapped[Optional[str]] = mapped_column(String(14),  nullable=True)
declaracoes_padrao: Mapped[Optional[str]] = mapped_column(Text,         nullable=True)
```

### 3.2 Nova Tabela `proposta_config`

Uma linha por versão (UNIQUE em `versao_id`). Removida em cascata se a versão for deletada.

```sql
CREATE TABLE proposta_config (
    id            SERIAL PRIMARY KEY,
    versao_id     INT  NOT NULL REFERENCES versao(id) ON DELETE CASCADE,
    validade_dias INT  NOT NULL DEFAULT 60,
    data_proposta DATE NOT NULL,
    declaracoes   TEXT,
    criado_em     TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    UNIQUE (versao_id)
);
```

Correspondência em `app/models/proposta_config.py`:
```python
class PropostaConfig(Base):
    __tablename__ = "proposta_config"
    __table_args__ = (UniqueConstraint("versao_id"),)

    id:            Mapped[int]           = mapped_column(primary_key=True)
    versao_id:     Mapped[int]           = mapped_column(ForeignKey("versao.id", ondelete="CASCADE"))
    validade_dias: Mapped[int]           = mapped_column(Integer, default=60)
    data_proposta: Mapped[date]          = mapped_column(Date)
    declaracoes:   Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    criado_em:     Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow)
    atualizado_em: Mapped[datetime]      = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    versao: Mapped["Versao"] = relationship(back_populates="proposta_config")
```

`Versao` ganha:
```python
proposta_config: Mapped[Optional["PropostaConfig"]] = relationship(
    back_populates="versao", uselist=False
)
```

---

## 4. Backend

### 4.1 Arquivos

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `app/models/proposta_config.py` | Criar | Modelo SQLAlchemy `PropostaConfig` |
| `app/schemas/proposta.py` | Criar | Pydantic schemas (in/out) |
| `app/routers/proposta.py` | Criar | Endpoints da proposta |
| `app/routers/empresa.py` | Criar | `GET /empresa` e `PATCH /empresa` |
| `app/services/proposta_pdf.py` | Criar | Geração HTML + WeasyPrint |
| `app/templates/proposta.html.j2` | Criar | Template Jinja2 do PDF |
| `app/models/empresa.py` | Modificar | +3 campos opcionais |
| `app/models/versao.py` | Modificar | +relacionamento `proposta_config` |
| `app/main.py` | Modificar | Registrar `proposta.router` e `empresa.router` |

### 4.2 Schemas (`app/schemas/proposta.py`)

```python
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel

class PropostaConfigIn(BaseModel):
    validade_dias: int = 60
    data_proposta: date
    declaracoes: Optional[str] = None

class PropostaConfigOut(PropostaConfigIn):
    id: int
    versao_id: int
    criado_em: datetime
    atualizado_em: datetime
    model_config = {"from_attributes": True}

class EmpresaConfigIn(BaseModel):
    representante_nome: Optional[str] = None
    representante_cpf:  Optional[str] = None
    declaracoes_padrao: Optional[str] = None

class EmpresaConfigOut(EmpresaConfigIn):
    id: int
    nome: str
    cnpj: str
    model_config = {"from_attributes": True}
```

### 4.3 Endpoints

#### `app/routers/empresa.py`

```
GET  /empresa   → EmpresaConfigOut   (qualquer usuário autenticado)
PATCH /empresa  → EmpresaConfigOut   (admin only via require_admin)
```

#### `app/routers/proposta.py`

```
GET  /versoes/{versao_id}/proposta        → PropostaConfigOut | 404
PUT  /versoes/{versao_id}/proposta        → PropostaConfigOut (upsert)
GET  /versoes/{versao_id}/proposta/export → StreamingResponse (PDF)
```

**Isolamento:** todos os endpoints verificam `Versao → Obra.empresa_id == current_user.empresa_id` via `_get_versao` (mesmo padrão dos outros módulos).

**Upsert (`PUT`):** usa `INSERT ... ON CONFLICT (versao_id) DO UPDATE`. Ao inserir, se `declaracoes` não for fornecido, popula a partir de `empresa.declaracoes_padrao`. Ao atualizar, usa o valor fornecido (pode ser null para limpar).

**Export (`GET /export`):**
1. Carrega versão + empresa + proposta_config + BDI + grupos (com itens e composições via `selectinload`)
2. Retorna 404 se `proposta_config` não existir (usuário deve salvar primeiro)
3. Renderiza `proposta.html.j2` com Jinja2
4. Converte HTML para PDF com WeasyPrint
5. Retorna `StreamingResponse` com `Content-Disposition: attachment; filename="proposta-v{versao_id}.pdf"`

### 4.4 Serviço de PDF (`app/services/proposta_pdf.py`)

Interface pública usada pelo Módulo 10:
```python
async def gerar_pdf_bytes(versao_id: int, db: AsyncSession) -> bytes:
    """Carrega todos os dados e retorna o PDF em bytes. Levanta 404 se PropostaConfig não existe."""
```

O endpoint de export chama esta função e envolve o resultado em `StreamingResponse`.

### 4.5 Template PDF (`app/templates/proposta.html.j2`)

Seções do documento:
1. **Cabeçalho** — nome e CNPJ da empresa, logo placeholder
2. **Identificação** — representante legal (nome + CPF), cargo "Responsável Técnico"
3. **Dados da obra** — nome, número do processo, cliente, UF/município, tipo
4. **Validade e data** — "Esta proposta é válida por X dias a partir de {data_proposta}"
5. **Planilha de preços** — tabela: Grupo | Descrição | Un | Qtd | Preço Unit. | Total; agrupado por `Grupo.nome`; linha de BDI (alíquota + valor total com BDI); linha de TOTAL GERAL
6. **Declarações** — texto do campo `declaracoes` (preservar quebras de linha como `<br>`)
7. **Assinatura** — linha pontilhada + nome do representante + CPF + data

CSS: A4, margens 2 cm, fonte sans-serif 10pt, tabela com bordas finas, cabeçalho da tabela fundo cinza claro. Sem dependências externas de imagem.

---

## 5. Frontend

### 5.1 Arquivos

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `frontend/src/api/proposta.ts` | Criar | Funções de API |
| `frontend/src/components/obra/PropostaTab.tsx` | Criar | Formulário + botão PDF |
| `frontend/src/pages/EmpresaSettingsPage.tsx` | Criar | Config da empresa (admin) |
| `frontend/src/types.ts` | Modificar | +`PropostaConfig`, `EmpresaConfig` |
| `frontend/src/pages/ObraDetailPage.tsx` | Modificar | +aba `'proposta'` |
| `frontend/src/App.tsx` (ou router) | Modificar | +rota `/configuracoes` |
| Layout/nav | Modificar | +link "Configurações" visível apenas para admin |

### 5.2 Tipos (`types.ts`)

```ts
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
```

### 5.3 API (`api/proposta.ts`)

```ts
export const getPropostaConfig = (versaoId: number): Promise<PropostaConfig> =>
  api.get<PropostaConfig>(`/versoes/${versaoId}/proposta`).then(r => r.data)

export const savePropostaConfig = (versaoId: number, body: Partial<PropostaConfig>): Promise<PropostaConfig> =>
  api.put<PropostaConfig>(`/versoes/${versaoId}/proposta`, body).then(r => r.data)

export async function downloadPropostaPdf(versaoId: number): Promise<void> {
  const resp = await api.get<Blob>(`/versoes/${versaoId}/proposta/export`, { responseType: 'blob' })
  const url = URL.createObjectURL(resp.data)
  const a = document.createElement('a')
  a.href = url
  a.download = `proposta-v${versaoId}.pdf`
  a.click()
  setTimeout(() => URL.revokeObjectURL(url), 100)
}

export const getEmpresaConfig = (): Promise<EmpresaConfig> =>
  api.get<EmpresaConfig>('/empresa').then(r => r.data)

export const updateEmpresaConfig = (body: Partial<EmpresaConfig>): Promise<EmpresaConfig> =>
  api.patch<EmpresaConfig>('/empresa', body).then(r => r.data)
```

### 5.4 `PropostaTab.tsx`

Props: `{ versaoId: number }`

Comportamento:
- Monta com `useEffect([versaoId])`: tenta `getPropostaConfig`; se 404, inicia com estado vazio (hoje como `data_proposta`)
- Estados: `config` (PropostaConfig | null), `loading`, `saving`, `exporting`, `dirty`
- Campos controlados: `validade_dias` (select: 30/60/90/180), `data_proposta` (input date), `declaracoes` (textarea)
- **Salvar** (disabled se `!dirty` ou `saving`): chama `savePropostaConfig`, atualiza estado, `dirty = false`
- **Baixar PDF** (disabled se `exporting` ou `config == null`): chama `downloadPropostaPdf`; se config é null, mostra toast "Salve a proposta antes de gerar o PDF"
- Se não há versão ativa (prop não passada): mensagem estática igual ao padrão das outras abas

### 5.5 `EmpresaSettingsPage.tsx`

Rota `/configuracoes`, guard: redireciona não-admin para `/obras`.

- Monta com `useEffect`: `getEmpresaConfig()`
- Campos: `representante_nome`, `representante_cpf`, `declaracoes_padrao` (textarea)
- Botão Salvar: `updateEmpresaConfig`, toast de confirmação
- Exibe nome e CNPJ da empresa em modo somente-leitura (identificação)

---

## 6. Teste

### 6.1 Backend (`tests/backend/test_proposta.py`)

| Teste | Descrição |
|-------|-----------|
| `test_get_proposta_not_found` | 404 quando PropostaConfig não existe |
| `test_put_proposta_create` | Cria PropostaConfig; `declaracoes` herdada da empresa |
| `test_put_proposta_update` | Atualiza campos; `declaracoes` substituída |
| `test_put_proposta_clear_declaracoes` | `declaracoes: null` limpa o campo |
| `test_export_pdf_not_configured` | 404 ao exportar sem PropostaConfig |
| `test_export_pdf_ok` | Retorna bytes; Content-Type `application/pdf`; tamanho > 0 |
| `test_isolamento_empresa_b` | Empresa B não acessa PropostaConfig da empresa A |
| `test_empresa_get` | Retorna campos da empresa |
| `test_empresa_patch_admin` | Admin atualiza representante e declarações |
| `test_empresa_patch_nao_admin` | Orçamentista recebe 403 |

### 6.2 Frontend (manual)

- Acessar aba "Proposta" em obra com versão ativa → formulário vazio → preencher → Salvar → reload confirma persistência
- Baixar PDF → arquivo `proposta-v{id}.pdf` abre corretamente com todas as seções
- Acesso a `/configuracoes` como admin → salvar representante → abrir nova proposta → `declaracoes` pré-preenchidas
- Acesso a `/configuracoes` como orçamentista → redirecionado para `/obras`
- Aba "Proposta" sem versão ativa → mensagem estática

---

## 7. Dependências

- **WeasyPrint** — já previsto no design original (`PDF | WeasyPrint`); adicionar a `requirements.txt`
- **Jinja2** — já é dependência transitiva do FastAPI; confirmar está disponível

---

## 8. Módulo 10 — Interface de Integração

O Módulo 10 chama diretamente:
```python
from app.services.proposta_pdf import gerar_pdf_bytes
pdf_bytes = await gerar_pdf_bytes(versao_id, db)
```

Se `PropostaConfig` não existir para a versão, `gerar_pdf_bytes` levanta `HTTPException(404)`. O Módulo 10 deve tratar este caso omitindo a proposta do zip (ou marcando o job com aviso).
