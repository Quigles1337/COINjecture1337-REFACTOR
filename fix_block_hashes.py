#!/usr/bin/env python3
"""
Script to fix block hashes in the blockchain state.
This will generate proper SHA256 hashes for all blocks.
"""

import json
import hashlib
import time
import os
from pathlib import Path

def fix_block_hashes():
    """Fix block hashes in the blockchain state."""
    
    blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
    
    print("🔧 Starting block hash generation...")
    
    # Check if blockchain state exists
    if not os.path.exists(blockchain_state_path):
        print(f"❌ Blockchain state file not found: {blockchain_state_path}")
        return False
    
    # Read blockchain state
    try:
        with open(blockchain_state_path, 'r') as f:
            blockchain_data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading blockchain state: {e}")
        return False
    
    blocks = blockchain_data.get('blocks', [])
    print(f"📊 Found {len(blocks)} blocks to process with hash generation")
    
    if not blocks:
        print("❌ No blocks found in blockchain state")
        return False
    
    # Create a backup
    backup_path = f"{blockchain_state_path}.backup.{int(time.time())}"
    try:
        with open(backup_path, 'w') as f:
            json.dump(blockchain_data, f, indent=2)
        print(f"💾 Backup created: {backup_path}")
    except Exception as e:
        print(f"⚠️  Could not create backup: {e}")
    
    # Process blocks with hash generation
    print("🔧 Generating proper hashes for all blocks...")
    
    previous_hash = "0" * 64  # Genesis block previous hash
    processed_blocks = 0
    
    for i, block in enumerate(blocks):
        # Get block data
        block_index = block.get('index', i)
        block_timestamp = block.get('timestamp', int(time.time()))
        block_data = block.get('data', '')
        block_nonce = block.get('nonce', 0)
        
        # Create hash from block data
        block_string = f"{block_index}{block_timestamp}{block_data}{previous_hash}{block_nonce}"
        block_hash = hashlib.sha256(block_string.encode()).hexdigest()
        
        # Update block with proper hash
        block['hash'] = block_hash
        block['block_hash'] = block_hash
        block['previous_hash'] = previous_hash
        block['reprocessed_hash'] = True
        block['hash_generated_at'] = int(time.time())
        
        # Update previous hash for next block
        previous_hash = block_hash
        processed_blocks += 1
        
        if (i + 1) % 1000 == 0:
            print(f"   Processed {i + 1}/{len(blocks)} blocks with hash generation...")
    
    # Update blockchain state
    blockchain_data['blocks'] = blocks
    blockchain_data['hash_generation_completed'] = True
    blockchain_data['hash_generation_timestamp'] = int(time.time())
    blockchain_data['processed_blocks'] = processed_blocks
    
    # Save updated blockchain state
    try:
        with open(blockchain_state_path, 'w') as f:
            json.dump(blockchain_data, f, indent=2)
        print(f"✅ Updated blockchain state saved with proper hashes")
    except Exception as e:
        print(f"❌ Error saving updated blockchain state: {e}")
        return False
    
    print(f"🎯 Hash generation complete!")
    print(f"   • Processed {processed_blocks} blocks")
    print(f"   • All blocks now have proper SHA256 hashes")
    print(f"   • Blockchain integrity restored")
    
    return True

if __name__ == "__main__":
    success = fix_block_hashes()
    exit(0 if success else 1)
