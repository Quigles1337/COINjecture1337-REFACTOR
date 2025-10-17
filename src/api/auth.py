"""
Simple HMAC signature verification and replay protection helpers.
"""

from __future__ import annotations

import hashlib
import hmac
import time
from typing import Dict


class HMACAuth:
    def __init__(self, secret: str, max_drift_sec: int = 300) -> None:
        self.secret = secret.encode("utf-8")
        self.max_drift = max_drift_sec

    def _canonical_body(self, body: Dict) -> bytes:
        # Minimal canonicalization: stable key order
        import json

        return json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")

    def verify(self, body: Dict, provided_sig: str, ts_header: str) -> bool:
        try:
            ts = float(ts_header)
        except Exception:
            return False
        now = time.time()
        if abs(now - ts) > self.max_drift:
            return False
        mac = hmac.new(self.secret, self._canonical_body(body), hashlib.sha256).hexdigest()
        return hmac.compare_digest(mac, provided_sig)


