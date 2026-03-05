"""Async SQLite database — trades + points tables."""
from __future__ import annotations

import aiosqlite
from pathlib import Path

DB_PATH = Path("data/farming.db")


async def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT    NOT NULL,
                strategy  TEXT    NOT NULL,
                market    TEXT    NOT NULL,
                side      TEXT    NOT NULL,
                size      REAL    NOT NULL,
                price     REAL    NOT NULL,
                pnl       REAL    DEFAULT 0.0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS points (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp  TEXT    NOT NULL,
                protocol   TEXT    NOT NULL,
                points_earned REAL NOT NULL,
                cumulative REAL    NOT NULL
            )
        """)
        await db.commit()


async def insert_trade(timestamp: str, strategy: str, market: str,
                       side: str, size: float, price: float, pnl: float = 0.0) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO trades (timestamp,strategy,market,side,size,price,pnl) VALUES (?,?,?,?,?,?,?)",
            (timestamp, strategy, market, side, size, price, pnl),
        )
        await db.commit()


async def insert_points(timestamp: str, protocol: str, points_earned: float, cumulative: float) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO points (timestamp,protocol,points_earned,cumulative) VALUES (?,?,?,?)",
            (timestamp, protocol, points_earned, cumulative),
        )
        await db.commit()


async def get_trades(limit: int = 50) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT * FROM trades ORDER BY id DESC LIMIT ?", (limit,)
        ) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]


async def get_points_summary() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT protocol, MAX(cumulative) as total_points, COUNT(*) as events
            FROM points GROUP BY protocol ORDER BY total_points DESC
        """) as cur:
            rows = await cur.fetchall()
    return [dict(r) for r in rows]
