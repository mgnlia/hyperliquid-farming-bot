import aiosqlite
import os
from datetime import datetime
from app.config import settings


async def get_db():
    os.makedirs(os.path.dirname(settings.db_path), exist_ok=True)
    return await aiosqlite.connect(settings.db_path)


async def init_db():
    os.makedirs(os.path.dirname(settings.db_path), exist_ok=True)
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy TEXT NOT NULL,
                symbol TEXT NOT NULL,
                side TEXT NOT NULL,
                size_usd REAL NOT NULL,
                entry_price REAL,
                exit_price REAL,
                pnl REAL DEFAULT 0,
                fee REAL DEFAULT 0,
                status TEXT DEFAULT 'open',
                simulated INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                closed_at TEXT
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS farm_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                protocol TEXT NOT NULL,
                action TEXT NOT NULL,
                amount_usd REAL,
                points_earned REAL DEFAULT 0,
                tx_hash TEXT,
                simulated INTEGER DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS airdrop_score (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT UNIQUE,
                trading_volume_usd REAL DEFAULT 0,
                defi_volume_usd REAL DEFAULT 0,
                protocols_used INTEGER DEFAULT 0,
                estimated_points REAL DEFAULT 0,
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.commit()


async def get_daily_pnl() -> float:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    async with aiosqlite.connect(settings.db_path) as db:
        async with db.execute(
            "SELECT COALESCE(SUM(pnl), 0) FROM trades WHERE date(created_at) = ? AND status = 'closed'",
            (today,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0.0


async def record_trade(strategy: str, symbol: str, side: str, size_usd: float,
                        entry_price: float = 0, simulated: bool = True) -> int:
    async with aiosqlite.connect(settings.db_path) as db:
        cursor = await db.execute(
            "INSERT INTO trades (strategy, symbol, side, size_usd, entry_price, simulated) VALUES (?,?,?,?,?,?)",
            (strategy, symbol, side, size_usd, entry_price, int(simulated))
        )
        await db.commit()
        return cursor.lastrowid


async def record_farm_event(protocol: str, action: str, amount_usd: float,
                             points: float = 0, tx_hash: str = None, simulated: bool = True):
    async with aiosqlite.connect(settings.db_path) as db:
        await db.execute(
            "INSERT INTO farm_events (protocol, action, amount_usd, points_earned, tx_hash, simulated) VALUES (?,?,?,?,?,?)",
            (protocol, action, amount_usd, points, tx_hash, int(simulated))
        )
        await db.commit()


async def get_stats():
    async with aiosqlite.connect(settings.db_path) as db:
        async with db.execute("SELECT COUNT(*), COALESCE(SUM(size_usd), 0), COALESCE(SUM(pnl), 0) FROM trades") as c:
            trades_row = await c.fetchone()
        async with db.execute("SELECT COUNT(*), COALESCE(SUM(amount_usd), 0), COALESCE(SUM(points_earned), 0) FROM farm_events") as c:
            farm_row = await c.fetchone()
    return {
        "total_trades": trades_row[0],
        "total_volume_usd": trades_row[1],
        "total_pnl": trades_row[2],
        "farm_events": farm_row[0],
        "farm_volume_usd": farm_row[1],
        "total_points": farm_row[2],
    }
