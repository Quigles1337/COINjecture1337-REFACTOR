#!/usr/bin/env python3
"""
Check Database CIDs
Simple script to check what CIDs are actually in the database
"""

import sqlite3
import json
import sys

def check_database_cids(db_path):
    """Check what CIDs are in the database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get the latest block from database
        cursor.execute('SELECT height, block_bytes FROM blocks ORDER BY height DESC LIMIT 1')
        result = cursor.fetchone()
        
        if result:
            height, block_bytes = result
            block_data = json.loads(block_bytes.decode('utf-8') if isinstance(block_bytes, bytes) else block_bytes)
            cid = block_data.get('cid', '')
            print(f'Latest block in database: {height}')
            print(f'CID: {cid}')
            print(f'Length: {len(cid)}')
            print(f'Starts with 9D: {cid.startswith("9D")}')
            print(f'Starts with Qm: {cid.startswith("Qm")}')
            print(f'Contains 0: {"0" in cid}')
            print(f'Contains O: {"O" in cid}')
            print(f'Contains I: {"I" in cid}')
            print(f'Contains l: {"l" in cid}')
        else:
            print('No blocks found in database')
        
        conn.close()
        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 check_database_cids.py <database_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    check_database_cids(db_path)
