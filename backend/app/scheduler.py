from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import asyncio
import logging

from app.core.config import settings
from app.db import SessionLocal
from app.seed import init_db
from app.services.sync import sync_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _get_timezone() -> ZoneInfo:
    try:
        return ZoneInfo(settings.sync_daily_timezone)
    except Exception:
        logger.warning("Timezone inválido '%s'. Usando UTC.", settings.sync_daily_timezone)
        return ZoneInfo("UTC")


def _seconds_until_next_run(now: datetime, hour: int, minute: int) -> float:
    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if next_run <= now:
        next_run = next_run + timedelta(days=1)
    return max((next_run - now).total_seconds(), 1.0)


async def _run_daily_sync_once() -> None:
    db = SessionLocal()
    try:
        result = await sync_service.run_daily_sync(db)
        logger.info("Sincronização diária concluída: %s", result)
    except Exception:
        logger.exception("Falha na sincronização diária agendada.")
        db.rollback()
    finally:
        db.close()


async def run_scheduler() -> None:
    init_db()

    if not settings.sync_daily_enabled:
        logger.info("Scheduler diário desabilitado por configuração.")
        return

    timezone = _get_timezone()
    logger.info(
        "Scheduler diário habilitado para %02d:%02d (%s).",
        settings.sync_daily_hour,
        settings.sync_daily_minute,
        settings.sync_daily_timezone,
    )

    while True:
        now = datetime.now(timezone)
        sleep_seconds = _seconds_until_next_run(now, settings.sync_daily_hour, settings.sync_daily_minute)
        next_run_at = now + timedelta(seconds=sleep_seconds)
        logger.info("Próxima sincronização diária agendada para %s.", next_run_at.isoformat())
        await asyncio.sleep(sleep_seconds)
        await _run_daily_sync_once()


if __name__ == "__main__":
    asyncio.run(run_scheduler())
