# Módulo 15 — Perfil do Usuário: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Permitir que qualquer usuário autenticado veja e edite seu próprio nome e troque sua senha via dropdown na TopBar.

**Architecture:** Backend ganha dois endpoints (`PATCH /auth/me` e `POST /auth/alterar-senha`) e passa a incluir `nome` no JWT. Frontend adiciona `nome` ao store Zustand, cria `PerfilModal` com dois formulários independentes, e converte a exibição de papel na TopBar num dropdown clicável.

**Tech Stack:** FastAPI · Pydantic v2 · SQLAlchemy async · python-jose · React 19 · TypeScript · Tailwind CSS · Zustand

---

## File Map

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `backend/app/schemas/auth.py` | Modificar | Adicionar `AlterarNomeRequest` e `AlterarSenhaRequest` |
| `backend/app/routers/auth.py` | Modificar | `nome` no JWT em `login`/`refresh` + 2 novos endpoints |
| `tests/backend/test_perfil.py` | Criar | 4 testes TDD |
| `frontend/src/hooks/useAuth.ts` | Modificar | Adicionar `nome: string \| null` e `setNome` |
| `frontend/src/api/perfil.ts` | Criar | `updateNome`, `alterarSenha` |
| `frontend/src/components/layout/PerfilModal.tsx` | Criar | Modal com form de nome + form de senha |
| `frontend/src/components/layout/TopBar.tsx` | Modificar | Nome clicável → dropdown (Meu Perfil + Sair) |

---

### Task 1: Backend — Schemas + Endpoints + Testes

**Files:**
- Modify: `backend/app/schemas/auth.py`
- Modify: `backend/app/routers/auth.py`
- Create: `tests/backend/test_perfil.py`

- [ ] **Step 1: Adicionar schemas em backend/app/schemas/auth.py**

Substituir o conteúdo completo do arquivo:

```python
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    senha: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class AlterarNomeRequest(BaseModel):
    nome: str = Field(min_length=1)


class AlterarSenhaRequest(BaseModel):
    senha_atual: str
    nova_senha: str = Field(min_length=8)
```

- [ ] **Step 2: Escrever os 4 testes em tests/backend/test_perfil.py**

```python
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuario import Usuario
from app.services.auth_service import verify_password


@pytest.mark.asyncio
async def test_alterar_nome_ok(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    admin_user: Usuario,
):
    resp = await client.patch(
        "/auth/me",
        json={"nome": "Novo Nome Teste"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    await db_session.refresh(admin_user)
    assert admin_user.nome == "Novo Nome Teste"


@pytest.mark.asyncio
async def test_alterar_senha_ok(
    client: AsyncClient,
    auth_headers: dict,
    db_session: AsyncSession,
    admin_user: Usuario,
):
    resp = await client.post(
        "/auth/alterar-senha",
        json={"senha_atual": "senha123", "nova_senha": "novaSenha456"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json() == {"ok": True}
    await db_session.refresh(admin_user)
    assert verify_password("novaSenha456", admin_user.senha_hash)


@pytest.mark.asyncio
async def test_alterar_senha_atual_errada(
    client: AsyncClient,
    auth_headers: dict,
):
    resp = await client.post(
        "/auth/alterar-senha",
        json={"senha_atual": "senhaErrada999", "nova_senha": "novaSenha456"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_alterar_senha_muito_curta(
    client: AsyncClient,
    auth_headers: dict,
):
    resp = await client.post(
        "/auth/alterar-senha",
        json={"senha_atual": "senha123", "nova_senha": "curta"},
        headers=auth_headers,
    )
    assert resp.status_code == 422
```

- [ ] **Step 3: Confirmar que os testes falham**

```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH" && docker compose exec backend pytest tests/backend/test_perfil.py -v 2>&1 | head -20
```

Expected: FAIL com 404 (endpoints não existem ainda)

- [ ] **Step 4: Implementar — substituir backend/app/routers/auth.py completo**

```python
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import get_current_user
from app.models.usuario import Usuario
from app.schemas.auth import (
    AlterarNomeRequest,
    AlterarSenhaRequest,
    LoginRequest,
    TokenResponse,
)
from app.services.auth_service import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _token_data(user: Usuario) -> dict:
    return {
        "sub": str(user.id),
        "papel": user.papel,
        "empresa_id": user.empresa_id,
        "nome": user.nome,
    }


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Usuario).where(Usuario.email == body.email, Usuario.ativo == True)
    )
    user = result.scalar_one_or_none()
    if user is None or not verify_password(body.senha, user.senha_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas")

    access_token = create_access_token(_token_data(user))
    refresh_token = create_refresh_token({"sub": str(user.id)})
    response.set_cookie("refresh_token", refresh_token, httponly=True, samesite="lax", max_age=7 * 86400)
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token ausente")
    try:
        payload = decode_access_token(token)
        if payload.get("type") != "refresh":
            raise ValueError("Não é refresh token")
        user_id = int(payload["sub"])
    except (ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")

    result = await db.execute(select(Usuario).where(Usuario.id == user_id, Usuario.ativo == True))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    access_token = create_access_token(_token_data(user))
    new_refresh = create_refresh_token({"sub": str(user.id)})
    response.set_cookie("refresh_token", new_refresh, httponly=True, samesite="lax", max_age=7 * 86400)
    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"ok": True}


@router.patch("/me", response_model=TokenResponse)
async def alterar_nome(
    body: AlterarNomeRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    current_user.nome = body.nome.strip()
    await db.commit()
    await db.refresh(current_user)
    return TokenResponse(access_token=create_access_token(_token_data(current_user)))


@router.post("/alterar-senha")
async def alterar_senha(
    body: AlterarSenhaRequest,
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not verify_password(body.senha_atual, current_user.senha_hash):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")
    current_user.senha_hash = hash_password(body.nova_senha)
    await db.commit()
    return {"ok": True}
```

- [ ] **Step 5: Confirmar que os 4 testes passam**

```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH" && docker compose exec backend pytest tests/backend/test_perfil.py -v 2>&1 | tail -15
```

Expected: 4 PASSED

- [ ] **Step 6: Rodar suíte completa**

```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH" && docker compose exec backend pytest tests/backend/ -q 2>&1 | tail -5
```

Expected: sem novas falhas (1 falha pré-existente em `test_proposta.py::test_export_pdf_ok` é esperada)

- [ ] **Step 7: Commit**

```bash
git add backend/app/schemas/auth.py \
        backend/app/routers/auth.py \
        tests/backend/test_perfil.py
git commit -m "feat: PATCH /auth/me + POST /auth/alterar-senha + nome no JWT — Módulo 15 backend"
```

---

### Task 2: Frontend — useAuth + API + PerfilModal + TopBar

**Files:**
- Modify: `frontend/src/hooks/useAuth.ts`
- Create: `frontend/src/api/perfil.ts`
- Create: `frontend/src/components/layout/PerfilModal.tsx`
- Modify: `frontend/src/components/layout/TopBar.tsx`

- [ ] **Step 1: Atualizar frontend/src/hooks/useAuth.ts**

Substituir o conteúdo completo:

```ts
import { create } from 'zustand'
import axios from 'axios'
import { api, setAccessToken } from '@/api/client'

interface AuthState {
  userId: number | null
  papel: string | null
  empresaId: number | null
  nome: string | null
  login: (email: string, senha: string) => Promise<void>
  logout: () => Promise<void>
  refresh: () => Promise<boolean>
  setNome: (nome: string) => void
}

function parseJwt(token: string) {
  try {
    return JSON.parse(atob(token.split('.')[1]))
  } catch {
    return null
  }
}

export const useAuth = create<AuthState>((set) => ({
  userId: null,
  papel: null,
  empresaId: null,
  nome: null,

  login: async (email, senha) => {
    const { data } = await axios.post('/auth/login', { email, senha }, { withCredentials: true })
    setAccessToken(data.access_token)
    const payload = parseJwt(data.access_token)
    set({
      userId: Number(payload.sub),
      papel: payload.papel,
      empresaId: payload.empresa_id,
      nome: payload.nome ?? null,
    })
  },

  logout: async () => {
    await api.post('/auth/logout')
    setAccessToken('')
    set({ userId: null, papel: null, empresaId: null, nome: null })
  },

  refresh: async () => {
    try {
      const { data } = await axios.post('/auth/refresh', {}, { withCredentials: true })
      setAccessToken(data.access_token)
      const payload = parseJwt(data.access_token)
      set({
        userId: Number(payload.sub),
        papel: payload.papel,
        empresaId: payload.empresa_id,
        nome: payload.nome ?? null,
      })
      return true
    } catch {
      return false
    }
  },

  setNome: (nome) => set({ nome }),
}))
```

- [ ] **Step 2: Criar frontend/src/api/perfil.ts**

```ts
import { api, setAccessToken } from '@/api/client'

export async function updateNome(nome: string): Promise<string> {
  const resp = await api.patch<{ access_token: string }>('/auth/me', { nome })
  setAccessToken(resp.data.access_token)
  return resp.data.access_token
}

export async function alterarSenha(
  senha_atual: string,
  nova_senha: string,
): Promise<void> {
  await api.post('/auth/alterar-senha', { senha_atual, nova_senha })
}
```

- [ ] **Step 3: Criar frontend/src/components/layout/PerfilModal.tsx**

```tsx
import { useState } from 'react'
import { updateNome, alterarSenha } from '@/api/perfil'
import { useAuth } from '@/hooks/useAuth'
import { toast } from '@/hooks/useToast'

interface Props {
  onClose: () => void
}

export default function PerfilModal({ onClose }: Props) {
  const { nome, papel, setNome } = useAuth()

  const [novoNome, setNovoNome] = useState(nome ?? '')
  const [savingNome, setSavingNome] = useState(false)

  const [senhaAtual, setSenhaAtual] = useState('')
  const [novaSenha, setNovaSenha] = useState('')
  const [confirmarSenha, setConfirmarSenha] = useState('')
  const [mostrarSenha, setMostrarSenha] = useState(false)
  const [savingSenha, setSavingSenha] = useState(false)
  const [senhaAtualErrada, setSenhaAtualErrada] = useState(false)

  async function handleSalvarNome() {
    if (!novoNome.trim()) return
    setSavingNome(true)
    try {
      await updateNome(novoNome.trim())
      setNome(novoNome.trim())
      toast('Nome atualizado')
    } catch {
      toast('Erro ao atualizar nome', 'error')
    } finally {
      setSavingNome(false)
    }
  }

  async function handleAlterarSenha() {
    if (!senhaAtual || novaSenha.length < 8 || novaSenha !== confirmarSenha) return
    setSavingSenha(true)
    setSenhaAtualErrada(false)
    try {
      await alterarSenha(senhaAtual, novaSenha)
      toast('Senha alterada com sucesso')
      setSenhaAtual('')
      setNovaSenha('')
      setConfirmarSenha('')
    } catch (e: any) {
      if (e?.response?.status === 400) {
        setSenhaAtualErrada(true)
      } else {
        toast('Erro ao alterar senha', 'error')
      }
    } finally {
      setSavingSenha(false)
    }
  }

  const senhaValida =
    senhaAtual.length > 0 &&
    novaSenha.length >= 8 &&
    novaSenha === confirmarSenha

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4 p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-base font-semibold text-gray-900">Meu Perfil</h2>
          <button
            onClick={onClose}
            aria-label="Fechar"
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            ×
          </button>
        </div>

        <p className="text-xs text-gray-500 -mt-4">
          Papel: <span className="font-medium capitalize text-gray-700">{papel}</span>
        </p>

        {/* Alterar nome */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-800">Alterar nome</h3>
          <input
            type="text"
            value={novoNome}
            onChange={e => setNovoNome(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            onClick={handleSalvarNome}
            disabled={!novoNome.trim() || savingNome}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
          >
            {savingNome ? 'Salvando…' : 'Salvar nome'}
          </button>
        </div>

        <hr className="border-gray-100" />

        {/* Alterar senha */}
        <div className="space-y-3">
          <h3 className="text-sm font-medium text-gray-800">Alterar senha</h3>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Senha atual</label>
            <input
              type={mostrarSenha ? 'text' : 'password'}
              value={senhaAtual}
              onChange={e => { setSenhaAtual(e.target.value); setSenhaAtualErrada(false) }}
              className={`w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 ${senhaAtualErrada ? 'border-red-400' : 'border-gray-300'}`}
            />
            {senhaAtualErrada && (
              <p className="text-xs text-red-500 mt-1">Senha atual incorreta</p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Nova senha</label>
            <div className="relative">
              <input
                type={mostrarSenha ? 'text' : 'password'}
                value={novaSenha}
                onChange={e => setNovaSenha(e.target.value)}
                className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 pr-16"
              />
              <button
                type="button"
                onClick={() => setMostrarSenha(v => !v)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-500 hover:text-gray-700"
              >
                {mostrarSenha ? 'Ocultar' : 'Mostrar'}
              </button>
            </div>
            {novaSenha.length > 0 && novaSenha.length < 8 && (
              <p className="text-xs text-red-500 mt-1">Mínimo 8 caracteres</p>
            )}
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-700 mb-1">Confirmar nova senha</label>
            <input
              type={mostrarSenha ? 'text' : 'password'}
              value={confirmarSenha}
              onChange={e => setConfirmarSenha(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {confirmarSenha.length > 0 && novaSenha !== confirmarSenha && (
              <p className="text-xs text-red-500 mt-1">As senhas não coincidem</p>
            )}
          </div>
          <button
            onClick={handleAlterarSenha}
            disabled={!senhaValida || savingSenha}
            className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 disabled:opacity-40"
          >
            {savingSenha ? 'Salvando…' : 'Alterar senha'}
          </button>
        </div>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Substituir frontend/src/components/layout/TopBar.tsx completo**

```tsx
import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import PerfilModal from '@/components/layout/PerfilModal'

const NAV_ITEMS = [
  { label: 'Dashboard', to: '/' },
  { label: 'Obras', to: '/obras' },
  { label: 'Orçamento', to: '/orcamento' },
  { label: 'BDI', to: '/bdi' },
  { label: 'Cronograma', to: '/cronograma' },
  { label: 'Medição', to: '/medicao' },
  { label: 'Relatórios', to: '/relatorios' },
  { label: 'Base de Comp.', to: '/composicoes' },
]

export default function TopBar() {
  const { logout, papel, nome } = useAuth()
  const navigate = useNavigate()
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const [perfilOpen, setPerfilOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  async function handleLogout() {
    setDropdownOpen(false)
    await logout()
    navigate('/login')
  }

  return (
    <header className="bg-gray-900 text-white px-4 h-12 flex items-center gap-6 shrink-0">
      <span className="font-bold text-blue-400">AVML</span>
      <nav className="flex gap-4 text-sm">
        {NAV_ITEMS.map(item => (
          <Link key={item.to} to={item.to} className="hover:text-blue-300 transition-colors">
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="ml-auto flex items-center gap-3 text-sm">
        {papel === 'admin' && (
          <Link to="/configuracoes" className="text-gray-400 hover:text-white transition-colors">
            Configurações
          </Link>
        )}
        <div className="relative" ref={dropdownRef}>
          <button
            onClick={() => setDropdownOpen(v => !v)}
            className="text-gray-300 hover:text-white transition-colors flex items-center gap-1"
          >
            {nome ?? papel}
            <span className="text-gray-500 text-xs">▾</span>
          </button>
          {dropdownOpen && (
            <div className="absolute right-0 top-8 bg-white text-gray-800 rounded-lg shadow-lg py-1 min-w-36 z-50">
              <button
                onClick={() => { setDropdownOpen(false); setPerfilOpen(true) }}
                className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50"
              >
                Meu Perfil
              </button>
              <hr className="border-gray-100 my-1" />
              <button
                onClick={handleLogout}
                className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
              >
                Sair
              </button>
            </div>
          )}
        </div>
      </div>
      {perfilOpen && <PerfilModal onClose={() => setPerfilOpen(false)} />}
    </header>
  )
}
```

- [ ] **Step 5: Confirmar que TypeScript compila**

```bash
cd /Users/vladimirirving/Desktop/orcaavml/frontend && npx tsc --noEmit 2>&1 | head -20
```

Expected: sem erros (saída vazia)

- [ ] **Step 6: Commit**

```bash
git add frontend/src/hooks/useAuth.ts \
        frontend/src/api/perfil.ts \
        frontend/src/components/layout/PerfilModal.tsx \
        frontend/src/components/layout/TopBar.tsx
git commit -m "feat: dropdown perfil na TopBar + PerfilModal (nome + senha) — Módulo 15 completo"
```
