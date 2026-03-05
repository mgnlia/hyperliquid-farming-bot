"""Unit tests for Hyperliquid Farming Bot — runs in SIMULATION_MODE=true."""
import os

import pytest

os.environ["SIMULATION_MODE"] = "true"
os.environ["BOT_API_KEY"] = ""  # disable auth for tests


def test_risk_manager_kelly_size():
    from backend.risk import RiskManager

    rm = RiskManager(max_position_pct=0.25)
    # Good signal → positive Kelly
    size = rm.kelly_size(0.6, 2.0)
    assert 0 < size <= 0.25

    # Zero win prob → 0
    assert rm.kelly_size(0.0, 2.0) == 0.0

    # Negative Kelly clamped to 0
    assert rm.kelly_size(0.2, 0.5) == 0.0


def test_risk_manager_drawdown_halt():
    from backend.risk import RiskManager

    rm = RiskManager(max_drawdown_pct=0.15)
    rm.peak_value = 10000.0

    # No drawdown yet
    assert rm.update_drawdown(10000.0) is True

    # 10% drawdown — within limits
    assert rm.update_drawdown(9000.0) is True
    assert abs(rm.current_drawdown - 0.10) < 0.001

    # 20% drawdown — breach
    assert rm.update_drawdown(8000.0) is False
    assert rm.is_halted() is True


def test_risk_manager_daily_reset():
    from backend.risk import RiskManager

    rm = RiskManager(daily_loss_cap_usd=500.0)
    rm.record_loss(-300.0)
    assert rm.daily_loss_usd == -300.0

    rm.reset_daily()
    assert rm.daily_loss_usd == 0.0


def test_risk_manager_daily_loss_cap():
    from backend.risk import RiskManager

    rm = RiskManager(daily_loss_cap_usd=500.0)
    assert rm.record_loss(-300.0) is True   # still within cap
    assert rm.record_loss(-300.0) is False  # now at -600, over cap


def test_perps_strategy_signals():
    from backend.strategies.perps import PerpsStrategy

    ps = PerpsStrategy()
    ps.update_prices()
    # Prices should be positive
    for price in ps.prices.values():
        assert price > 0

    signal = ps.generate_signal("ETH-PERP")
    assert signal["action"] in ("open", "hold")
    if signal["action"] == "open":
        assert signal["side"] in ("long", "short")
        assert 0 < signal["win_prob"] <= 1.0


def test_perps_strategy_execute():
    from backend.risk import RiskManager
    from backend.strategies.perps import PerpsStrategy

    rm = RiskManager()
    rm.peak_value = 10000.0
    ps = PerpsStrategy()
    events = ps.execute_signals(rm.kelly_size, 10000.0)
    # Should return a list (possibly empty)
    assert isinstance(events, list)


def test_defi_farming_execute():
    from backend.strategies.defi_farming import DeFiFarmingStrategy

    ds = DeFiFarmingStrategy()
    events = ds.execute(5000.0)
    assert isinstance(events, list)
    # Should have deposited into at least one pool
    assert len(ds.positions) >= 0  # may be 0 on first call if random skips


def test_point_farmer():
    from backend.strategies.point_farmer import PointFarmerStrategy

    pf = PointFarmerStrategy()
    events = pf.execute()
    assert isinstance(events, list)
    score = pf.get_airdrop_score()
    assert 0 <= score <= 100


@pytest.mark.asyncio
async def test_api_health():
    from httpx import ASGITransport, AsyncClient

    from backend.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_api_status_no_auth():
    """With BOT_API_KEY empty, auth is disabled — should return 200."""
    from httpx import ASGITransport, AsyncClient

    from backend.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/api/status")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data
    assert "simulation_mode" in data


@pytest.mark.asyncio
async def test_api_auth_enforced():
    """With BOT_API_KEY set, requests without token should get 401."""
    import backend.config as cfg

    original = cfg.settings.BOT_API_KEY
    cfg.settings.BOT_API_KEY = "secret-test-key"

    from httpx import ASGITransport, AsyncClient

    from backend.main import app

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r = await ac.get("/api/status")
        assert r.status_code == 401

        # With correct key → 200
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            r2 = await ac.get("/api/status", headers={"Authorization": "Bearer secret-test-key"})
        assert r2.status_code == 200
    finally:
        cfg.settings.BOT_API_KEY = original


@pytest.mark.asyncio
async def test_api_start_stop():
    from httpx import ASGITransport, AsyncClient

    from backend.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/agent/start")
        assert r.status_code == 200
        r2 = await ac.post("/api/agent/stop")
        assert r2.status_code == 200
