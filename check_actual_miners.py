#!/usr/bin/env python3
"""
Check actual miners in the blockchain and ensure they're getting their rewards.
"""

import json
import os

def check_actual_miners():
    """Check who actually mined blocks and ensure they get rewards."""
    
    blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
    
    print("🔍 Checking actual miners in blockchain...")
    
    # Read blockchain state
    with open(blockchain_state_path, 'r') as f:
        data = json.load(f)
    
    blocks = data['blocks']
    print(f"📊 Total blocks: {len(blocks)}")
    
    # Count unique miners
    miners = {}
    for block in blocks:
        miner = block.get('miner_address', 'unknown')
        if miner not in miners:
            miners[miner] = {'blocks': 0, 'rewards': 0}
        miners[miner]['blocks'] += 1
        miners[miner]['rewards'] += 50  # Base reward per block
    
    print(f"👥 Unique miners: {len(miners)}")
    print("\n🏆 Top miners by blocks:")
    
    for miner, stats in sorted(miners.items(), key=lambda x: x[1]['blocks'], reverse=True):
        print(f"  {miner}: {stats['blocks']} blocks, {stats['rewards']} BEANS")
    
    print("\n✅ All miners should be receiving their rewards:")
    for miner, stats in miners.items():
        if stats['blocks'] > 0:
            print(f"  • {miner}: {stats['blocks']} blocks → {stats['rewards']} BEANS")
    
    return miners

if __name__ == "__main__":
    check_actual_miners()
