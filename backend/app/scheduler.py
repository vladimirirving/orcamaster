import asyncio
import logging
from datetime import datetime, timedelta, timezone
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select, update, delete
from app.database import AsyncSessionLocal
from app.models.versao import Versao
from app.models.pacote_job import PacoteJob

logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler()


async def purge_versoes_job() -> None:
    """Hard-delete Versoes soft-deleted more than 90 days ago (CASCADE removes PacoteJobs)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Versao).where(Versao.deletada_em != None, Versao.deletada_em < cutoff)
        )
        versoes = result.scalars().all()
        for versao in versoes:
            await session.execute(
                update(PacoteJob)
                .where(PacoteJob.versao_id == versao.id, PacoteJob.status.in_(["pendente", "processando"]))
                .values(status="erro", erro_mensagem="Versão purgada")
            )
            await session.delete(versao)
        await session.commit()
        if versoes:
            logger.info("Purgadas %d versões soft-deleted", len(versoes))


async def expire_pacotes_job() -> None:
    """Mark PacoteJobs as expirado when their file is older than 7 days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(PacoteJob)
            .where(PacoteJob.status == "pronto", PacoteJob.gerado_em < cutoff)
            .values(status="expirado")
        )
        await session.commit()


def _run_async(coro):
    asyncio.run(coro)


def start_scheduler() -> None:
    _scheduler.add_job(_run_async, "cron", hour=3, minute=0, args=[purge_versoes_job()], id="purge_versoes")
    _scheduler.add_job(_run_async, "cron", hour=3, minute=30, args=[expire_pacotes_job()], id="expire_pacotes")
    _scheduler.start()
    logger.info("APScheduler started")


def stop_scheduler() -> None:
    _scheduler.shutdown(wait=False)
