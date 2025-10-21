#!/usr/bin/env python3
"""
Sync databases with updated blockchain state.
"""

import json
import sqlite3
import os
import time
from datetime import datetime

def sync_databases():
    """Sync all databases with the updated blockchain state."""
    
    print("🔄 Starting database synchronization...")
    
    # Read updated blockchain state
    blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
    if not os.path.exists(blockchain_state_path):
        print(f"❌ Blockchain state file not found: {blockchain_state_path}")
        return False
    
    with open(blockchain_state_path, 'r') as f:
        blockchain_data = json.load(f)
    
    blocks = blockchain_data.get('blocks', [])
    print(f"📊 Found {len(blocks)} blocks to sync to databases")
    
    if not blocks:
        print("❌ No blocks found in blockchain state")
        return False
    
    # Sync blockchain.db
    blockchain_db_path = "/opt/coinjecture-consensus/data/blockchain.db"
    try:
        # Backup existing database
        if os.path.exists(blockchain_db_path):
            backup_path = f"{blockchain_db_path}.backup.{int(time.time())}"
            os.rename(blockchain_db_path, backup_path)
            print(f"💾 Backed up existing blockchain.db to {backup_path}")
        
        # Create new database with updated data
        conn = sqlite3.connect(blockchain_db_path)
        cursor = conn.cursor()
        
        # Create blocks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blocks (
                id INTEGER PRIMARY KEY,
                block_index INTEGER UNIQUE,
                hash TEXT,
                previous_hash TEXT,
                timestamp REAL,
                data TEXT,
                nonce INTEGER,
                work_score REAL
            )
        ''')
        
        # Insert all blocks
        for block in blocks:
            cursor.execute('''
                INSERT OR REPLACE INTO blocks 
                (block_index, hash, previous_hash, timestamp, data, nonce, work_score)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                block.get('index', 0),
                block.get('hash', ''),
                block.get('previous_hash', ''),
                block.get('timestamp', 0),
                block.get('data', ''),
                block.get('nonce', 0),
                block.get('work_score', 0)
            ))
        
        conn.commit()
        conn.close()
        print(f"✅ Synced {len(blocks)} blocks to blockchain.db")
        
    except Exception as e:
        print(f"❌ Error syncing blockchain.db: {e}")
        return False
    
    # Sync faucet_ingest.db
    faucet_db_path = "/opt/coinjecture-consensus/data/faucet_ingest.db"
    try:
        conn = sqlite3.connect(faucet_db_path)
        cursor = conn.cursor()
        
        # Insert block events using existing schema
        for block in blocks:
            event_id = f"block_{block.get('index', 0)}_{int(time.time())}"
            cursor.execute('''
                INSERT OR REPLACE INTO block_events 
                (event_id, block_index, block_hash, cid, miner_address, capacity, work_score, ts, sig, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event_id,
                block.get('index', 0),
                block.get('hash', ''),
                block.get('hash', ''),  # Use hash as CID
                block.get('miner_address', ''),
                block.get('capacity', ''),
                block.get('work_score', 0),
                block.get('timestamp', 0),
                block.get('signature', ''),
                time.time()
            ))
        
        conn.commit()
        conn.close()
        print(f"✅ Synced {len(blocks)} block events to faucet_ingest.db")
        
    except Exception as e:
        print(f"❌ Error syncing faucet_ingest.db: {e}")
        return False
    
    print(f"🎯 Database synchronization complete!")
    print(f"   • All databases now synchronized with blockchain state")
    print(f"   • API should now read updated data")
    print(f"   • Blockchain hashes are now available")
    
    return True

if __name__ == "__main__":
    success = sync_databases()
    exit(0 if success else 1)
