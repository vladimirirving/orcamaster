# backend/app/scheduler.py — stub, replaced in Task 7
from app.database import AsyncSessionLocal  # noqa: F401


async def purge_versoes_job() -> None:
    pass


async def expire_pacotes_job() -> None:
    pass


def start_scheduler() -> None:
    pass


def stop_scheduler() -> None:
    pass
