#!/usr/bin/env python3
"""
Fix hash field mapping - copy block_hash to hash field for API compatibility.
"""

import json
import os
import time

def fix_hash_field_mapping():
    """Copy block_hash to hash field for API compatibility."""
    
    blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
    
    print("🔧 Fixing hash field mapping...")
    
    # Read blockchain state
    with open(blockchain_state_path, 'r') as f:
        blockchain_data = json.load(f)
    
    blocks = blockchain_data.get('blocks', [])
    print(f"📊 Found {len(blocks)} blocks to fix hash field mapping")
    
    # Fix hash field mapping
    fixed_blocks = 0
    for block in blocks:
        # Copy block_hash to hash field if hash is None or empty
        if not block.get('hash') and block.get('block_hash'):
            block['hash'] = block['block_hash']
            block['hash_fixed'] = True
            fixed_blocks += 1
    
    # Update blockchain state
    blockchain_data['blocks'] = blocks
    blockchain_data['hash_field_fixed'] = True
    blockchain_data['hash_field_fixed_at'] = int(time.time())
    blockchain_data['fixed_blocks'] = fixed_blocks
    
    # Save updated blockchain state
    with open(blockchain_state_path, 'w') as f:
        json.dump(blockchain_data, f, indent=2)
    
    print(f"✅ Fixed hash field mapping for {fixed_blocks} blocks")
    print(f"   • Copied block_hash to hash field")
    print(f"   • API should now read proper hashes")
    
    return True

if __name__ == "__main__":
    fix_hash_field_mapping()
