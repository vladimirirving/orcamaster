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
    db.add(current_user)
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
    db.add(current_user)
    await db.commit()
    await db.refresh(current_user)
    return {"ok": True}
