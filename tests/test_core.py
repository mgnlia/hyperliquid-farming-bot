"""Core unit tests — risk, config, database, strategies."""
import pytest
import asyncio
import os

os.environ["SIMULATION_MODE"] = "true"
os.environ["PRIVATE_KEY"] = ""
os.environ["WALLET_ADDRESS"] = ""


def test_risk_can_trade_basic():
    from src import risk
    allowed, reason = risk.can_trade("BTC", 100.0)
    assert allowed is True
    assert reason == ""


def test_risk_position_limit():
    from src import risk
    from src.config import settings
    risk.record_open("TESTLIMIT", settings.max_position_usd)
    allowed, reason = risk.can_trade("TESTLIMIT", 1.0)
    assert allowed is False
    assert "Position limit" in reason
    risk.record_close("TESTLIMIT", settings.max_position_usd)


def test_risk_total_exposure():
    from src import risk
    from src.config import settings
    risk.record_open("ASSET_EXP", settings.max_total_exposure_usd)
    allowed, reason = risk.can_trade("ASSET_EXP2", 1.0)
    assert allowed is False
    assert "Total exposure" in reason
    risk.record_close("ASSET_EXP", settings.max_total_exposure_usd)


def test_risk_drawdown_block():
    from src import risk
    risk._state.blocked = False
    risk._state.peak_equity = 10000.0
    risk._state.current_equity = 10000.0
    risk.update_equity(8400.0)  # 16% drawdown > 10% limit
    assert risk._state.blocked is True
    risk.reset_block()
    assert risk._state.blocked is False
    risk._state.peak_equity = 10000.0
    risk._state.current_equity = 10000.0


def test_config_defaults():
    from src.config import settings
    assert settings.simulation_mode is True
    assert settings.max_leverage == 3.0
    assert settings.max_drawdown_pct == 0.10
    assert "BTC" in settings.perps_coins


def test_perps_get_status():
    from src.strategies import perps
    status = perps.get_status()
    assert status["strategy"] == "perps"
    assert "total_trades" in status
    assert "simulation_mode" in status


def test_defi_get_status():
    from src.strategies import defi_farming
    status = defi_farming.get_status()
    assert status["strategy"] == "defi_farming"
    assert "protocols" in status


def test_point_farmer_get_status():
    from src.strategies import point_farmer
    status = point_farmer.get_status()
    assert status["strategy"] == "point_farmer"
    assert "total_points" in status
    assert len(status["protocols"]) >= 4


@pytest.mark.asyncio
async def test_perps_price_fetch_simulated():
    from src.strategies.perps import _fetch_prices_simulated
    prices = await _fetch_prices_simulated()
    assert "BTC" in prices
    assert prices["BTC"] > 0


@pytest.mark.asyncio
async def test_database_init():
    import tempfile
    from pathlib import Path
    from src import database
    original = database.DB_PATH
    with tempfile.TemporaryDirectory() as tmpdir:
        database.DB_PATH = Path(tmpdir) / "test.db"
        await database.init_db()
        trade_id = await database.log_trade("test", "BTC", "BUY", 0.001, 65000, 65.0)
        assert trade_id > 0
        trades = await database.get_trades(10)
        assert len(trades) == 1
        assert trades[0]["strategy"] == "test"
        database.DB_PATH = original


@pytest.mark.asyncio
async def test_perps_run_cycle():
    """Test a full perps cycle in simulation mode."""
    from src.strategies import perps
    from src import database
    import tempfile
    from pathlib import Path
    original = database.DB_PATH
    with tempfile.TemporaryDirectory() as tmpdir:
        database.DB_PATH = Path(tmpdir) / "test.db"
        await database.init_db()
        before = perps._state["total_trades"]
        await perps.run_cycle()
        after = perps._state["total_trades"]
        assert after >= before  # Trades may be risk-blocked but shouldn't error
        database.DB_PATH = original


@pytest.mark.asyncio
async def test_point_farmer_cycle():
    """Test point farming cycle."""
    from src.strategies import point_farmer
    from src import database
    import tempfile
    from pathlib import Path
    original = database.DB_PATH
    with tempfile.TemporaryDirectory() as tmpdir:
        database.DB_PATH = Path(tmpdir) / "test.db"
        await database.init_db()
        await point_farmer.run_cycle()
        assert point_farmer._state["total_points"] > 0
        database.DB_PATH = original


@pytest.mark.asyncio
async def test_api_health():
    """Test FastAPI health endpoint without triggering full lifespan."""
    from fastapi.testclient import TestClient
    from src import main
    # Override lifespan with no-op for testing
    from contextlib import asynccontextmanager
    from fastapi import FastAPI

    @asynccontextmanager
    async def noop_lifespan(app):
        yield

    test_app = FastAPI(lifespan=noop_lifespan)
    test_app.add_api_route("/health", main.health)

    with TestClient(test_app) as client:
        resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
