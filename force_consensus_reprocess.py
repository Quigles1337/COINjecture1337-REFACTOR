#!/usr/bin/env python3
"""
Force consensus service to reprocess all events
"""
import sqlite3
import json
import time
import os

def force_reprocess_events():
    """Force the consensus service to reprocess all events"""
    
    # Connect to ingest database
    ingest_conn = sqlite3.connect('/opt/coinjecture-consensus/data/faucet_ingest.db')
    ingest_cursor = ingest_conn.cursor()
    
    # Get all events
    ingest_cursor.execute('SELECT * FROM block_events ORDER BY block_index')
    events = ingest_cursor.fetchall()
    
    print(f"Found {len(events)} events to reprocess")
    
    # Load blockchain state
    blockchain_state_path = '/opt/coinjecture-consensus/data/blockchain_state.json'
    if os.path.exists(blockchain_state_path):
        with open(blockchain_state_path, 'r') as f:
            blockchain_state = json.load(f)
    else:
        blockchain_state = {"blocks": [], "latest_block": None}
    
    print(f"Current blockchain has {len(blockchain_state['blocks'])} blocks")
    
    # Process each event
    processed_count = 0
    for event in events:
        event_id, block_index, block_hash, cid, miner_address, capacity, work_score, ts, sig, created_at = event
        
        # Skip if already processed
        if block_index <= len(blockchain_state['blocks']):
            continue
            
        # Create block data
        block_data = {
            "index": block_index,
            "timestamp": ts,
            "previous_hash": blockchain_state['latest_block']['hash'] if blockchain_state['latest_block'] else '',
            "transactions": [],
            "merkle_root": '',
            "problem": {},
            "solution": [],
            "complexity": {},
            "mining_capacity": capacity or 'unknown',
            "cumulative_work_score": work_score,
            "block_hash": block_hash,
            "hash": block_hash,
            "miner_address": miner_address
        }
        
        # Add to blockchain state
        blockchain_state['blocks'].append(block_data)
        blockchain_state['latest_block'] = block_data
        
        processed_count += 1
        
        if processed_count % 100 == 0:
            print(f"Processed {processed_count} events...")
    
    # Save updated blockchain state
    with open(blockchain_state_path, 'w') as f:
        json.dump(blockchain_state, f, indent=2)
    
    print(f"✅ Reprocessed {processed_count} events")
    print(f"✅ Blockchain now has {len(blockchain_state['blocks'])} blocks")
    print(f"✅ Latest block: #{blockchain_state['latest_block']['index']}")
    
    ingest_conn.close()

if __name__ == "__main__":
    force_reprocess_events()
