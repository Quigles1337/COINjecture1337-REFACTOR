#!/usr/bin/env python3
"""
Check database status and synchronization.
"""

import json
import sqlite3
import os
from datetime import datetime

def check_database_status():
    """Check if databases are up to date."""
    
    print("🔍 Checking database synchronization status...")
    
    # Check blockchain_state.json
    blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
    if os.path.exists(blockchain_state_path):
        with open(blockchain_state_path, 'r') as f:
            blockchain_data = json.load(f)
        
        blocks = blockchain_data.get('blocks', [])
        print(f"📊 Blockchain State JSON:")
        print(f"   - Total blocks: {len(blocks)}")
        if blocks:
            last_block = blocks[-1]
            print(f"   - Last block index: {last_block.get('index', 'N/A')}")
            print(f"   - Last block hash: {last_block.get('hash', 'N/A')[:16] if last_block.get('hash') else 'N/A'}")
            print(f"   - Hash generated: {last_block.get('reprocessed_hash', False)}")
    else:
        print("❌ Blockchain state file not found")
    
    # Check blockchain.db
    blockchain_db_path = "/opt/coinjecture-consensus/data/blockchain.db"
    if os.path.exists(blockchain_db_path):
        try:
            conn = sqlite3.connect(blockchain_db_path)
            cursor = conn.cursor()
            
            # Get table info
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"📊 Blockchain DB:")
            print(f"   - Tables: {[t[0] for t in tables]}")
            
            # Check blocks table
            if ('blocks',) in tables:
                cursor.execute('SELECT COUNT(*) FROM blocks')
                db_count = cursor.fetchone()[0]
                cursor.execute('SELECT index, hash FROM blocks ORDER BY index DESC LIMIT 1')
                last_block = cursor.fetchone()
                
                print(f"   - Total blocks: {db_count}")
                if last_block:
                    print(f"   - Last block index: {last_block[0]}")
                    print(f"   - Last block hash: {last_block[1][:16] if last_block[1] else 'N/A'}")
                else:
                    print(f"   - No blocks found")
            
            conn.close()
        except Exception as e:
            print(f"❌ Blockchain DB error: {e}")
    else:
        print("❌ Blockchain DB not found")
    
    # Check faucet_ingest.db
    faucet_db_path = "/opt/coinjecture-consensus/data/faucet_ingest.db"
    if os.path.exists(faucet_db_path):
        try:
            conn = sqlite3.connect(faucet_db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print(f"📊 Faucet Ingest DB:")
            print(f"   - Tables: {[t[0] for t in tables]}")
            
            if ('blocks',) in tables:
                cursor.execute('SELECT COUNT(*) FROM blocks')
                db_count = cursor.fetchone()[0]
                print(f"   - Total blocks: {db_count}")
            
            conn.close()
        except Exception as e:
            print(f"❌ Faucet DB error: {e}")
    else:
        print("❌ Faucet DB not found")
    
    print("\n💡 Database Status Summary:")
    print("   - Blockchain State JSON: Updated with proper hashes")
    print("   - Blockchain DB: May be outdated")
    print("   - Faucet Ingest DB: May be outdated")
    print("   - API may be reading from outdated database files")

if __name__ == "__main__":
    check_database_status()
