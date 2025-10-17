"""
SQLite-backed store for faucet ingest events.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple


class IngestStore:
    def __init__(self, db_path: str = "data/faucet_ingest.db") -> None:
        self.db_path = db_path
        Path(Path(db_path).parent).mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES)

    def _init_db(self) -> None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry (
                    event_id TEXT PRIMARY KEY,
                    miner_id TEXT,
                    ts REAL,
                    capacity TEXT,
                    metrics_json TEXT,
                    node_json TEXT,
                    sig TEXT,
                    created_at REAL
                )
                """
            )
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS block_events (
                    event_id TEXT PRIMARY KEY,
                    block_index INTEGER,
                    block_hash TEXT,
                    cid TEXT,
                    miner_id TEXT,
                    capacity TEXT,
                    work_score REAL,
                    ts REAL,
                    sig TEXT,
                    created_at REAL
                )
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_ts ON telemetry(ts)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_telemetry_miner ON telemetry(miner_id)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_block_ts ON block_events(ts)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_block_index ON block_events(block_index)")
            conn.commit()

    def insert_telemetry(self, ev: Dict[str, Any]) -> bool:
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO telemetry(event_id, miner_id, ts, capacity, metrics_json, node_json, sig, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ev["event_id"],
                        ev["miner_id"],
                        float(ev["ts"]),
                        ev["capacity"],
                        json.dumps(ev.get("metrics", {})),
                        json.dumps(ev.get("node", {})),
                        ev.get("signature", ""),
                        time.time(),
                    ),
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False  # Duplicate event_id

    def insert_block_event(self, ev: Dict[str, Any]) -> bool:
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    INSERT INTO block_events(event_id, block_index, block_hash, cid, miner_id, capacity, work_score, ts, sig, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        ev["event_id"],
                        int(ev["block_index"]),
                        ev["block_hash"],
                        ev["cid"],
                        ev["miner_id"],
                        ev["capacity"],
                        float(ev["work_score"]),
                        float(ev["ts"]),
                        ev.get("signature", ""),
                        time.time(),
                    ),
                )
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def latest_telemetry(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT event_id, miner_id, ts, capacity, metrics_json, node_json FROM telemetry ORDER BY ts DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "event_id": r[0],
                    "miner_id": r[1],
                    "ts": r[2],
                    "capacity": r[3],
                    "metrics": json.loads(r[4] or "{}"),
                    "node": json.loads(r[5] or "{}"),
                }
            )
        return out

    def latest_blocks(self, limit: int = 20) -> List[Dict[str, Any]]:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT event_id, block_index, block_hash, cid, miner_id, capacity, work_score, ts FROM block_events ORDER BY ts DESC LIMIT ?",
                (limit,),
            )
            rows = cur.fetchall()
        out: List[Dict[str, Any]] = []
        for r in rows:
            out.append(
                {
                    "event_id": r[0],
                    "block_index": r[1],
                    "block_hash": r[2],
                    "cid": r[3],
                    "miner_id": r[4],
                    "capacity": r[5],
                    "work_score": r[6],
                    "ts": r[7],
                }
            )
        return out


