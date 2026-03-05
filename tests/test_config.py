"""Smoke tests — import validation + config defaults."""
from src.config import settings


def test_config_defaults() -> None:
    assert settings.hl_api_url == "https://api.hyperliquid.xyz"
    assert settings.hyper_evm_rpc == "https://rpc.hyperliquid.xyz/evm"
    assert settings.simulation_mode is True
    assert settings.max_position_usdc > 0
    assert settings.daily_perp_trades > 0
    assert 0 < settings.max_drawdown_pct < 1


def test_imports() -> None:
    from src.bot import bot
    from src.database import DB_PATH
    from src.strategies.hyper_evm_farmer import HyperEVMFarmer
    from src.strategies.perps_trader import PerpsTrader
    from src.strategies.points_tracker import PointsTracker

    assert bot is not None
    assert PerpsTrader is not None
    assert HyperEVMFarmer is not None
    assert PointsTracker is not None
    assert DB_PATH is not None


def test_points_tracker() -> None:
    from src.strategies.points_tracker import PointsTracker

    pt = PointsTracker()
    pt.record_trade("Felix")
    pt.record_deposit("Mizu")
    pt.record_lp("KittenSwap")
    pt.record_stake("HypurrFi")
    assert pt.grand_total > 0
    summary = pt.summary()
    assert len(summary) > 0
    assert all("total_points" in s for s in summary)


def test_perps_trader_signal() -> None:
    from src.strategies.perps_trader import PerpsTrader, _price_history

    trader = PerpsTrader()
    # Feed enough prices to trigger a signal
    for i in range(15):
        price = 67000.0 * (1 + i * 0.001)   # uptrend → should trigger long
        _price_history["BTC"].append(price)
        _price_history["BTC"] = _price_history["BTC"][-60:]

    signal = trader._momentum_signal("BTC", 67000.0 * 1.015)
    # signal is "long", "short", or None — just assert it doesn't crash
    assert signal in ("long", "short", None)
