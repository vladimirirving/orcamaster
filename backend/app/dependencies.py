from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models.usuario import Usuario
from app.services.auth_service import decode_access_token

_bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    try:
        payload = decode_access_token(credentials.credentials)
        if payload.get("type") == "refresh":
            raise ValueError("Refresh token não pode ser usado como access token")
        user_id = int(payload["sub"])
    except (ValueError, KeyError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    result = await db.execute(select(Usuario).where(Usuario.id == user_id, Usuario.ativo == True))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário não encontrado")
    return user


async def require_admin(current_user: Usuario = Depends(get_current_user)) -> Usuario:
    if current_user.papel != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Requer papel admin")
    return current_user
