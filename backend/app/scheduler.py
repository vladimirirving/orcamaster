import asyncio
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select, update, delete
from app.database import AsyncSessionLocal
from app.models.versao import Versao
from app.models.pacote_job import PacoteJob
from app.models.grupo import Grupo
from app.models.item import Item
from app.models.bdi import BDI
from app.models.medicao import Medicao

logger = logging.getLogger(__name__)
_scheduler = BackgroundScheduler()


async def purge_versoes_job() -> None:
    """Hard-delete Versoes soft-deleted more than 90 days ago (CASCADE removes PacoteJobs)."""
    cutoff = datetime.utcnow() - timedelta(days=90)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Versao).where(Versao.deletada_em != None, Versao.deletada_em < cutoff)
        )
        versoes = result.scalars().all()
        for versao in versoes:
            # Cancel running jobs first (PacoteJob has ON DELETE CASCADE but we update status first)
            await session.execute(
                update(PacoteJob)
                .where(PacoteJob.versao_id == versao.id, PacoteJob.status.in_(["pendente", "processando"]))
                .values(status="erro", erro_mensagem="Versão purgada")
            )
            # Explicitly delete children that don't have ON DELETE CASCADE
            await session.execute(
                delete(Item).where(Item.grupo_id.in_(
                    select(Grupo.id).where(Grupo.versao_id == versao.id)
                ))
            )
            await session.execute(delete(Grupo).where(Grupo.versao_id == versao.id))
            await session.execute(delete(BDI).where(BDI.versao_id == versao.id))
            await session.execute(delete(Medicao).where(Medicao.versao_id == versao.id))
            await session.delete(versao)
        await session.commit()
        if versoes:
            logger.info("Purgadas %d versões soft-deleted", len(versoes))


async def expire_pacotes_job() -> None:
    """Mark PacoteJobs as expirado when their file is older than 7 days."""
    cutoff = datetime.utcnow() - timedelta(days=7)
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(PacoteJob)
            .where(PacoteJob.status == "pronto", PacoteJob.gerado_em < cutoff)
            .values(status="expirado")
        )
        await session.commit()


def _run_async(coro_fn):
    asyncio.run(coro_fn())


def start_scheduler() -> None:
    _scheduler.add_job(_run_async, "cron", hour=3, minute=0, args=[purge_versoes_job], id="purge_versoes")
    _scheduler.add_job(_run_async, "cron", hour=3, minute=30, args=[expire_pacotes_job], id="expire_pacotes")
    _scheduler.start()
    logger.info("APScheduler started")


def stop_scheduler() -> None:
    _scheduler.shutdown(wait=False)
