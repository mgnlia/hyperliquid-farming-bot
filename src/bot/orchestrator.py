"""Bot orchestrator — manages all strategy tasks with asyncio."""
import asyncio
import structlog
from src.config import settings
from src.strategies import perps, defi_farming, point_farmer
from src import risk, database

log = structlog.get_logger(__name__)

_stop_event = asyncio.Event()
_tasks: list[asyncio.Task] = []
_running = False


async def start():
    global _running, _stop_event
    if _running:
        log.warning("orchestrator.already_running")
        return

    _stop_event = asyncio.Event()
    _running = True
    _tasks.clear()

    await database.init_db()
    log.info("orchestrator.start", simulation=settings.simulation_mode)

    if settings.enable_perps:
        _tasks.append(asyncio.create_task(perps.run(_stop_event), name="perps"))

    if settings.enable_defi:
        _tasks.append(asyncio.create_task(defi_farming.run(_stop_event), name="defi"))

    if settings.enable_points:
        _tasks.append(asyncio.create_task(point_farmer.run(_stop_event), name="points"))

    log.info("orchestrator.tasks_started", count=len(_tasks))


async def stop():
    global _running
    if not _running:
        return
    log.info("orchestrator.stopping")
    _stop_event.set()
    await asyncio.gather(*_tasks, return_exceptions=True)
    _tasks.clear()
    _running = False
    log.info("orchestrator.stopped")


def is_running() -> bool:
    return _running


def get_full_status() -> dict:
    return {
        "running": _running,
        "simulation_mode": settings.simulation_mode,
        "strategies": {
            "perps": perps.get_status(),
            "defi_farming": defi_farming.get_status(),
            "point_farmer": point_farmer.get_status(),
        },
        "risk": risk.get_risk_summary(),
    }
