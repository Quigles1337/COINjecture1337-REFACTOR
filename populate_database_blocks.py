#!/usr/bin/env python3
"""
Script to populate the database with all blocks from the cache.
This will sync the database with the 10,561+ blocks in the cache.
"""

import json
import sqlite3
import time
from pathlib import Path

def populate_database():
    """Populate database with blocks from cache."""
    
    # Database path
    db_path = "/opt/coinjecture-consensus/data/faucet_ingest.db"
    
    # Cache path
    cache_path = "/home/coinjecture/COINjecture/data/cache/blocks_history.json"
    
    print("🔄 Loading blocks from cache...")
    
    # Load blocks from cache
    try:
        with open(cache_path, 'r') as f:
            blocks = json.load(f)
        print(f"📦 Loaded {len(blocks)} blocks from cache")
    except Exception as e:
        print(f"❌ Error loading cache: {e}")
        return False
    
    # Connect to database
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Clear existing blocks to avoid duplicates
        print("🗑️  Clearing existing blocks...")
        cursor.execute("DELETE FROM block_events")
        conn.commit()
        
        # Insert blocks into database
        print("📝 Inserting blocks into database...")
        
        for i, block in enumerate(blocks):
            if i % 1000 == 0:
                print(f"   Processed {i}/{len(blocks)} blocks...")
            
            # Extract block data
            event_id = f"block_{block['index']}_{int(block['timestamp'])}"
            block_index = block['index']
            block_hash = block['block_hash']
            cid = block.get('offchain_cid', '')
            miner_address = block.get('miner_address', 'unknown')
            capacity = block.get('mining_capacity', '')
            work_score = block.get('cumulative_work_score', 0.0)
            ts = block['timestamp']
            
            # Insert into database
            cursor.execute("""
                INSERT OR REPLACE INTO block_events 
                (event_id, block_index, block_hash, cid, miner_address, capacity, work_score, ts, sig, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id,
                block_index,
                block_hash,
                cid,
                miner_address,
                capacity,
                work_score,
                ts,
                '',  # sig
                time.time()  # created_at
            ))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Successfully populated database with {len(blocks)} blocks")
        return True
        
    except Exception as e:
        print(f"❌ Error populating database: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting database population...")
    success = populate_database()
    if success:
        print("🎉 Database population completed successfully!")
    else:
        print("💥 Database population failed!")
