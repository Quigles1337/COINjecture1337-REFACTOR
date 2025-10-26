
#!/usr/bin/env python3
"""
Database CID Update Script
Updates all CIDs in the database to use base58btc encoding
"""

import base58
import hashlib
import json
import time
from typing import Dict, Any

class DatabaseCIDUpdater:
    def __init__(self, db_connection):
        self.db = db_connection
        self.updated_count = 0
        self.error_count = 0
    
    def convert_cid_to_base58btc(self, cid: str) -> str:
        """Convert regular base58 CID to base58btc CID"""
        try:
            # Decode the base58 CID to get the raw bytes
            raw_bytes = base58.b58decode(cid)
            
            # Re-encode using base58btc (which excludes 0, O, I, l)
            base58btc_cid = base58.b58encode(raw_bytes, alphabet=base58.ALPHABET_BTC).decode('utf-8')
            
            return base58btc_cid
        except Exception as e:
            print(f"Error converting CID {cid}: {e}")
            return None
    
    def update_all_cids(self):
        """Update all CIDs in the database"""
        try:
            # Get all blocks with CIDs
            cursor = self.db.cursor()
            cursor.execute("SELECT index, cid FROM blocks WHERE cid IS NOT NULL")
            blocks = cursor.fetchall()
            
            print(f"Found {len(blocks)} blocks to update")
            
            for block_index, old_cid in blocks:
                try:
                    # Convert CID
                    new_cid = self.convert_cid_to_base58btc(old_cid)
                    if not new_cid:
                        self.error_count += 1
                        continue
                    
                    # Update database
                    cursor.execute(
                        "UPDATE blocks SET cid = %s WHERE index = %s",
                        (new_cid, block_index)
                    )
                    
                    self.updated_count += 1
                    print(f"Updated block {block_index}: {old_cid} → {new_cid}")
                    
                    # Commit every 100 updates
                    if self.updated_count % 100 == 0:
                        self.db.commit()
                        print(f"Committed {self.updated_count} updates")
                    
                except Exception as e:
                    print(f"Error updating block {block_index}: {e}")
                    self.error_count += 1
            
            # Final commit
            self.db.commit()
            
            print(f"\nUpdate complete:")
            print(f"  - Updated: {self.updated_count} CIDs")
            print(f"  - Errors: {self.error_count} errors")
            
        except Exception as e:
            print(f"Database error: {e}")
            self.db.rollback()

# Usage:
# import mysql.connector  # or your database connector
# db = mysql.connector.connect(host='localhost', user='user', password='pass', database='coinjecture')
# updater = DatabaseCIDUpdater(db)
# updater.update_all_cids()
# db.close()
