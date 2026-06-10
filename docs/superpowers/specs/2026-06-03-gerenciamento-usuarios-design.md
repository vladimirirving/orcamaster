# Módulo 14 — Gerenciamento de Usuários: Design Spec

**Data:** 2026-06-03
**Status:** Aprovado

---

## Objetivo

Permitir que o administrador da empresa liste, convide e gerencie os membros da equipe (papel e status ativo/inativo) diretamente em `/configuracoes`, sem sair da interface.

---

## Contexto

O backend já possui todos os endpoints necessários:

| Endpoint | Descrição |
|----------|-----------|
| `GET /usuarios` | Lista todos os usuários da empresa do admin |
| `POST /usuarios` | Cria usuário (requer `require_admin`) |
| `PATCH /usuarios/{id}` | Atualiza nome, papel e/ou ativo (requer `require_admin`) |

Papéis existentes: `admin` · `orcamentista` · `visualizador`

O frontend **não tem** nenhuma UI para estas operações. O `EmpresaSettingsPage` já é restrito a admins e possui abas de configuração da empresa e importação SINAPI/SICRO.

---

## Arquitetura

**Apenas frontend.** Nenhuma mudança de backend.

| Arquivo | Ação | Responsabilidade |
|---------|------|-----------------|
| `frontend/src/api/usuarios.ts` | Criar | `listUsuarios`, `createUsuario`, `updateUsuario` |
| `frontend/src/components/empresa/UsuariosTab.tsx` | Criar | Tabela de membros + modal criar + modal editar |
| `frontend/src/pages/EmpresaSettingsPage.tsx` | Modificar | Adicionar aba "Usuários" |

---

## Componente UsuariosTab

### Tabela de membros

Colunas: **Nome** · **E-mail** · **Papel** (badge colorido) · **Status** · **Ações**

Badges de papel:
- `admin` — roxo (`bg-purple-100 text-purple-700`)
- `orcamentista` — azul (`bg-blue-100 text-blue-700`)
- `visualizador` — cinza (`bg-gray-100 text-gray-600`)

Status: chip verde "Ativo" / vermelho "Inativo".

Ações por linha: ícone de lápis → abre modal de edição. O usuário logado vê sua própria linha marcada com "(você)" e não pode editar papel nem status de si mesmo.

Botão primário "Adicionar membro" no topo direito da aba.

### Modal de criação

Campos:
- **Nome** — texto obrigatório
- **E-mail** — email obrigatório
- **Senha** — password com toggle mostrar/ocultar, mínimo 8 caracteres
- **Papel** — select: Administrador / Orçamentista / Visualizador

Ação: `POST /usuarios`. Em caso de e-mail duplicado (400), exibe mensagem inline "E-mail já cadastrado."

### Modal de edição

Campos:
- **Nome** — read-only (exibido como texto, não input)
- **E-mail** — read-only
- **Papel** — select editável
- **Ativo** — toggle boolean

Ação: `PATCH /usuarios/{id}` com os campos `papel` e `ativo`.

---

## EmpresaSettingsPage

Adicionar aba `'usuarios'` ao tipo `Tab` e ao render de abas. A aba "Usuários" carrega `<UsuariosTab />` que faz o fetch ao montar.

A ordem das abas fica: **Empresa** · **Importação SINAPI/SICRO** · **Usuários**

---

## Comportamento de Erro e Loading

- Lista: skeleton de 3 linhas enquanto carrega; toast de erro se fetch falhar.
- Criar/Editar: botão de submit com estado de loading; erros exibidos inline no modal (e-mail duplicado) ou via toast (erros genéricos).
- Desativar o próprio usuário: botão "Salvar" desabilitado se `usuario.id === currentUser.id`.

---

## Testes

Nenhum teste de backend necessário (endpoints já cobertos pelos testes existentes de `usuarios`). Validação via TypeScript (`tsc --noEmit`) e teste manual no browser.

---

## Fora de Escopo

- Redefinição de senha por e-mail (sem serviço de e-mail no projeto)
- Exclusão permanente de usuário (backend não tem endpoint DELETE)
- Convite por link (sem serviço de e-mail)
- Paginação (times pequenos — sem necessidade imediata)
