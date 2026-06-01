# backend/app/scheduler.py — stub, replaced in Task 7
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import settings

AsyncSessionLocal = async_sessionmaker(
    create_async_engine(settings.database_url, echo=False),
    expire_on_commit=False,
)


async def purge_versoes_job() -> None:
    pass


async def expire_pacotes_job() -> None:
    pass


def start_scheduler() -> None:
    pass


def stop_scheduler() -> None:
    pass
