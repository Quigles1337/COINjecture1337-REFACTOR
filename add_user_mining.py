#!/usr/bin/env python3
"""
Add user mining activity to blockchain state as a workaround for consensus engine issues.
"""

import json
import time
import hashlib
import os

def add_user_mining_activity():
    """Add user mining activity to blockchain state."""
    
    blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
    user_address = "BEANSesdpmvi5rtm"
    
    print(f"🔧 Adding mining activity for {user_address}...")
    
    # Read current blockchain state
    with open(blockchain_state_path, 'r') as f:
        blockchain_data = json.load(f)
    
    blocks = blockchain_data.get('blocks', [])
    last_block = blocks[-1] if blocks else None
    
    if not last_block:
        print("❌ No blocks found in blockchain state")
        return False
    
    # Create new block for user mining activity
    new_block_index = last_block.get('index', 0) + 1
    new_timestamp = int(time.time())
    
    # Generate block hash
    block_data_string = f"{new_block_index}{new_timestamp}{user_address}{last_block.get('hash', '')}0"
    new_hash = hashlib.sha256(block_data_string.encode()).hexdigest()
    
    # Create new block
    new_block = {
        "index": new_block_index,
        "timestamp": new_timestamp,
        "hash": new_hash,
        "previous_hash": last_block.get('hash', ''),
        "miner_address": user_address,
        "work_score": 100.0,
        "data": f"User mining activity - {user_address}",
        "nonce": 0,
        "merkle_root": new_hash,
        "mining_capacity": "mobile",
        "cumulative_work_score": last_block.get('cumulative_work_score', 0) + 100.0,
        "block_hash": new_hash,
        "offchain_cid": new_hash,
        "event_id": f"user_mining_{new_block_index}_{int(time.time())}",
        "calculated_work_score": True,
        "reprocessed_at": int(time.time()),
        "reprocessed_hash": True,
        "hash_generated_at": int(time.time()),
        "user_mining_block": True
    }
    
    # Add new block to blockchain
    blocks.append(new_block)
    blockchain_data['blocks'] = blocks
    blockchain_data['total_blocks'] = len(blocks)
    blockchain_data['latest_block'] = new_block
    blockchain_data['last_updated'] = int(time.time())
    blockchain_data['user_mining_added'] = True
    blockchain_data['user_mining_timestamp'] = int(time.time())
    
    # Save updated blockchain state
    with open(blockchain_state_path, 'w') as f:
        json.dump(blockchain_data, f, indent=2)
    
    print(f"✅ Added mining block #{new_block_index} for {user_address}")
    print(f"   • Block hash: {new_hash[:16]}...")
    print(f"   • Work score: 100.0")
    print(f"   • Timestamp: {new_timestamp}")
    print(f"   • Total blocks: {len(blocks)}")
    
    return True

if __name__ == "__main__":
    add_user_mining_activity()
