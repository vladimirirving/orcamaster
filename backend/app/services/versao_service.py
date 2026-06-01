from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession


async def clone_versao(obra_id: int, criada_por: int, db: AsyncSession):
    """Stub: full implementation in Task 4."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Clone de versão ainda não implementado",
    )
