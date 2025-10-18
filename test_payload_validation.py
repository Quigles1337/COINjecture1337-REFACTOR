#!/usr/bin/env python3
"""
Test script to validate the exact payload from the browser
"""

import sys
import os
sys.path.append('src')

from api.schema import BlockEvent

# Test payload from browser debug logs
test_payload = {
    'event_id': 'web-mining-1760758427056-mobile',
    'block_index': 4,
    'block_hash': '0x37316366326534383037376133663365366232616430366436353335373566396666613834353634656262326139623433393666383439643334366437373966',
    'cid': 'QmeyJwcm9ibGVtIjp7Im51bWJlcnMiOls0NSwzLDMxLDk5',
    'miner_address': 'web-61764d0b2f53e1ef',
    'capacity': 'MOBILE',
    'work_score': 25600,
    'ts': 1760758427.056,
    'signature': 'ab720e571dc662ee0ed8f017c149903e11b93eba4c2f793529e163311f3c0384',
    'public_key': 'e1cb40c5d789e3ff3f7487e6a9a5befd7fed4f5bf29d572b3db76ababb2d6d46731994c2d29764733d07a3653858375205043ab0f8359e9400a4e5104d749e05'
}

print("=== TESTING BLOCK EVENT VALIDATION ===")
print(f"Payload keys: {list(test_payload.keys())}")
print(f"Payload types: {[(k, type(v).__name__) for k, v in test_payload.items()]}")
print()

try:
    event = BlockEvent.from_json(test_payload)
    print("✅ Validation passed locally")
    print(f"Event: {event}")
except Exception as e:
    print(f"❌ Validation failed: {e}")
    print(f"Error type: {type(e).__name__}")
    import traceback
    traceback.print_exc()

