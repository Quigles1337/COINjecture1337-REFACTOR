"""
Schemas and validators for faucet ingest payloads.

Avoid external dependencies by using dataclasses and simple validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class TelemetryEvent:
    event_id: str
    miner_id: str
    ts: float
    capacity: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    node: Dict[str, Any] = field(default_factory=dict)
    signature: str = ""

    @staticmethod
    def from_json(obj: Dict[str, Any]) -> "TelemetryEvent":
        required = ["event_id", "miner_id", "ts", "capacity", "metrics", "node", "signature"]
        missing = [k for k in required if k not in obj]
        if missing:
            raise ValueError(f"Missing fields: {', '.join(missing)}")
        if not isinstance(obj["ts"], (int, float)):
            raise ValueError("ts must be a number")
        if not isinstance(obj["metrics"], dict):
            raise ValueError("metrics must be an object")
        if not isinstance(obj["node"], dict):
            raise ValueError("node must be an object")
        return TelemetryEvent(
            event_id=str(obj["event_id"]),
            miner_id=str(obj["miner_id"]),
            ts=float(obj["ts"]),
            capacity=str(obj["capacity"]),
            metrics=obj["metrics"],
            node=obj["node"],
            signature=str(obj["signature"]),
        )


@dataclass
class BlockEvent:
    event_id: str
    block_index: int
    block_hash: str
    cid: str
    miner_address: str  # Changed from miner_id to miner_address
    capacity: str
    work_score: float
    ts: float
    signature: str = ""
    public_key: str = ""  # Added for signature verification

    @staticmethod
    def from_json(obj: Dict[str, Any]) -> "BlockEvent":
        required = [
            "event_id",
            "block_index",
            "block_hash",
            "cid",
            "miner_address",
            "capacity",
            "work_score",
            "ts",
            "signature",
        ]
        missing = [k for k in required if k not in obj]
        if missing:
            raise ValueError(f"Missing fields: {', '.join(missing)}")
        if not isinstance(obj["block_index"], int):
            raise ValueError("block_index must be an integer")
        if not isinstance(obj["work_score"], (int, float)):
            raise ValueError("work_score must be a number")
        if not isinstance(obj["ts"], (int, float)):
            raise ValueError("ts must be a number")
        return BlockEvent(
            event_id=str(obj["event_id"]),
            block_index=int(obj["block_index"]),
            block_hash=str(obj["block_hash"]),
            cid=str(obj["cid"]),
            miner_address=str(obj["miner_address"]),
            capacity=str(obj["capacity"]),
            work_score=float(obj["work_score"]),
            ts=float(obj["ts"]),
            signature=str(obj["signature"]),
            public_key=str(obj.get("public_key", "")),
        )


