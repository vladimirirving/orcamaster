# Módulo 15 — Perfil do Usuário: Design Spec

**Data:** 2026-06-03
**Status:** Aprovado

---

## Objetivo

Permitir que qualquer usuário autenticado veja e edite seu próprio nome e troque sua senha, acessando o perfil via dropdown na TopBar.

---

## Contexto

O JWT atual carrega `sub` (user ID), `papel` e `empresa_id` — mas não `nome`. A TopBar exibe apenas `papel`. Não existe endpoint que permita ao usuário editar seu próprio perfil (`PATCH /usuarios/{id}` exige `require_admin`).

---

## Arquitetura

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `backend/app/routers/auth.py` | Modificar | `PATCH /auth/me` (alterar nome) + `POST /auth/alterar-senha` |
| `backend/app/services/auth_service.py` | Modificar | Adicionar `nome` ao payload do JWT em `create_access_token` |
| `tests/backend/test_perfil.py` | Criar | 4 testes cobrindo os dois endpoints |
| `frontend/src/hooks/useAuth.ts` | Modificar | Adicionar `nome: string \| null`, parsear do JWT |
| `frontend/src/api/perfil.ts` | Criar | `updateNome(nome)`, `alterarSenha(senha_atual, nova_senha)` |
| `frontend/src/components/layout/PerfilModal.tsx` | Criar | Modal com form de nome + form de senha |
| `frontend/src/components/layout/TopBar.tsx` | Modificar | Nome clicável → dropdown (Meu Perfil + Sair) |

---

## Backend

### JWT com `nome`

`create_access_token` em `auth_service.py` não muda de assinatura — os callers (`login` e `refresh` em `auth.py`) passam `nome` no dicionário `data`:

```python
create_access_token({
    "sub": str(user.id),
    "papel": user.papel,
    "empresa_id": user.empresa_id,
    "nome": user.nome,   # novo
})
```

O `useAuth` no frontend parseia `payload.nome` do JWT. Tokens mais antigos (sem `nome`) terão `nome = null` até o próximo login/refresh — comportamento aceitável (TopBar mostra papel como fallback).

### `PATCH /auth/me`

- **Auth:** `get_current_user` (qualquer usuário ativo)
- **Body:** `{ nome: str }` — mínimo 1 char, strip de espaços
- **Ação:** atualiza `current_user.nome` no banco, commita, retorna novo `access_token` (com `nome` atualizado) via `TokenResponse`
- **Frontend** chama `setAccessToken(novo_token)` e atualiza `nome` no store

### `POST /auth/alterar-senha`

- **Auth:** `get_current_user`
- **Body:** `{ senha_atual: str, nova_senha: str }`
- **Validações:**
  - `verify_password(senha_atual, user.senha_hash)` → 400 "Senha atual incorreta" se falhar
  - `len(nova_senha) < 8` → 422 (via Pydantic `min_length=8`)
- **Ação:** atualiza `user.senha_hash = hash_password(nova_senha)`, commita
- **Retorno:** `{ "ok": true }`

### Schemas novos (`backend/app/schemas/auth.py`)

```python
class AlterarNomeRequest(BaseModel):
    nome: str

class AlterarSenhaRequest(BaseModel):
    senha_atual: str
    nova_senha: str = Field(min_length=8)
```

---

## Testes (`tests/backend/test_perfil.py`)

| Teste | Endpoint | Cenário | Esperado |
|-------|----------|---------|----------|
| `test_alterar_nome_ok` | `PATCH /auth/me` | nome válido | 200, token com novo nome |
| `test_alterar_senha_ok` | `POST /auth/alterar-senha` | senha atual correta, nova ≥ 8 | 200, `{"ok": true}`, novo hash válido |
| `test_alterar_senha_atual_errada` | `POST /auth/alterar-senha` | senha atual incorreta | 400 |
| `test_alterar_senha_muito_curta` | `POST /auth/alterar-senha` | nova senha com 5 chars | 422 |

---

## Frontend

### `useAuth.ts`

Adicionar `nome: string | null` ao estado inicial e ao `parseJwt`. O `login` e o `refresh` já chamam `set({...})` — adicionar `nome: payload.nome ?? null`. Adicionar `setNome(nome: string)` para o modal atualizar o store após `PATCH /auth/me` sem precisar fazer novo refresh.

### `frontend/src/api/perfil.ts`

```ts
updateNome(nome: string) → POST PATCH /auth/me → { access_token }
alterarSenha(senha_atual, nova_senha) → POST /auth/alterar-senha → { ok }
```

### `PerfilModal.tsx`

Modal dividido em duas seções independentes:

**Alterar nome:**
- Input pré-preenchido com `nome` atual
- Botão "Salvar" → `updateNome()` → `setAccessToken(token)` + `setNome(nome)` + toast

**Alterar senha:**
- Campos: senha atual · nova senha · confirmar nova senha
- Validação client-side: nova === confirmação, nova ≥ 8 chars
- Erro inline se senha atual incorreta (400)
- Toast de sucesso, campos limpos após sucesso

### `TopBar.tsx`

- Substituir `<span className="text-gray-400 capitalize">{papel}</span>` por botão clicável mostrando `nome ?? papel`
- Click toggle estado `dropdownOpen`
- Dropdown (posição `absolute right-0 top-8`): "Meu Perfil" (abre modal) + divisor + "Sair"
- Clicar fora fecha o dropdown (listener `mousedown` no `document`)
- `<button onClick={handleLogout}>` movido para dentro do dropdown

---

## Fora de Escopo

- Alteração de e-mail (requer verificação de unicidade e fluxo extra)
- Upload de avatar
- Redefinição de senha por e-mail (sem serviço de e-mail)
- Alteração de papel (só admin via UsuariosTab)
