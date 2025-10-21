#!/usr/bin/env python3
"""
Check current blockchain status.
"""

import json

def check_blockchain_status():
    """Check current blockchain status."""
    
    blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
    
    print("🔍 Checking blockchain status...")
    
    # Read blockchain state
    with open(blockchain_state_path, 'r') as f:
        data = json.load(f)
    
    blocks = data['blocks']
    print(f"📊 Total blocks: {len(blocks)}")
    
    if blocks:
        last_block = blocks[-1]
        print(f"📈 Latest block: #{last_block.get('index', 'N/A')}")
        print(f"👤 Latest miner: {last_block.get('miner_address', 'N/A')}")
        print(f"🔗 Latest hash: {last_block.get('hash', 'N/A')[:16]}...")
        print(f"⏰ Timestamp: {last_block.get('timestamp', 'N/A')}")
    
    return len(blocks)

if __name__ == "__main__":
    check_blockchain_status()
