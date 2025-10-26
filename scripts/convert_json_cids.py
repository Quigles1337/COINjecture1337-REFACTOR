#!/usr/bin/env python3
"""
Convert all CIDs in JSON data to base58btc format
This script processes all blocks in the database and converts CIDs from regular base58 to base58btc
"""

import sqlite3
import base58
import json
import time
from typing import Dict, Any, List, Optional
import os

class JSONCIDConverter:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.updated_count = 0
        self.already_correct_count = 0
        self.no_cid_count = 0
        self.conversion_error_count = 0
        self.update_error_count = 0
        self.conversion_log = []
        self.highest_block_processed = -1
        
    def convert_regular_base58_to_base58btc(self, cid: str) -> Optional[str]:
        """Convert regular base58 CID to base58btc CID"""
        try:
            if not cid or len(cid) != 46:
                return None
            
            # The CIDs are in regular base58 format (includes 0, O, I, l)
            # We need to decode them using regular base58 alphabet and re-encode with base58btc
            
            # Create regular base58 alphabet (includes 0, O, I, l)
            regular_alphabet = b'123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz0OIl'
            
            # Decode using regular base58 alphabet (includes 0, O, I, l)
            raw_bytes = base58.b58decode(cid, alphabet=regular_alphabet)
            
            # Re-encode using base58btc (which excludes 0, O, I, l)
            base58btc_cid = base58.b58encode(raw_bytes, alphabet=base58.BITCOIN_ALPHABET).decode('utf-8')
            
            return base58btc_cid
        except Exception as e:
            print(f"❌ Error converting CID {cid}: {e}")
            return None
    
    def has_invalid_characters(self, cid: str) -> bool:
        """Check if CID has characters that are invalid in base58btc"""
        if not cid or len(cid) != 46:
            return False
        
        invalid_chars = ['0', 'O', 'I', 'l']
        return any(char in cid for char in invalid_chars)

    def convert_cids_in_json_data(self):
        """Convert all CIDs in JSON data to base58btc format"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create a backup of the database
            backup_path = f"{self.db_path}.backup.json_cids.{int(time.time())}"
            with sqlite3.connect(backup_path) as backup_conn:
                conn.backup(backup_conn)
            print(f"✅ Database backup created: {backup_path}")

            print("🚀 Starting JSON CID conversion...")
            
            # Fetch all blocks
            cursor.execute("SELECT height, block_bytes FROM blocks ORDER BY height ASC")
            blocks = cursor.fetchall()
            
            print(f"📊 Found {len(blocks)} blocks with JSON data")

            for height, block_bytes_blob in blocks:
                self.highest_block_processed = max(self.highest_block_processed, height)
                try:
                    block_data = json.loads(block_bytes_blob.decode('utf-8') if isinstance(block_bytes_blob, bytes) else block_bytes_blob)
                    current_cid = block_data.get('cid')
                    
                    if current_cid:
                        if not self.has_invalid_characters(current_cid):
                            self.already_correct_count += 1
                            if height % 1000 == 0:
                                print(f"✅ Block {height}: CID already correct")
                            continue # CID is already base58btc compliant
                        
                        new_cid = self.convert_regular_base58_to_base58btc(current_cid)
                        if new_cid and new_cid != current_cid:
                            # Update the CID in the JSON data
                            block_data['cid'] = new_cid
                            
                            # Convert back to JSON and update the database
                            updated_block_bytes = json.dumps(block_data).encode('utf-8')
                            cursor.execute(
                                "UPDATE blocks SET block_bytes = ? WHERE height = ?",
                                (updated_block_bytes, height)
                            )
                            self.updated_count += 1
                            if height % 1000 == 0:
                                print(f"🔄 Block {height}: {current_cid} → {new_cid}")
                            self.conversion_log.append(f"Updated block {height}: {current_cid} -> {new_cid}")
                        elif not new_cid:
                            self.conversion_error_count += 1
                            self.conversion_log.append(f"❌ Block {height}: Conversion failed - CID {current_cid} could not be converted or was invalid.")
                    else:
                        self.no_cid_count += 1
                        self.conversion_log.append(f"Skipped block {height}: No CID found.")
                except json.JSONDecodeError:
                    self.conversion_error_count += 1
                    self.conversion_log.append(f"❌ Error decoding JSON for block at height {height}. Skipping.")
                except Exception as e:
                    self.update_error_count += 1
                    self.conversion_log.append(f"❌ Unexpected error processing block {height}: {e}")
            
            conn.commit()
            print("\n📊 JSON CID Conversion Summary:")
            print(f"  - Total blocks: {len(blocks)}")
            print(f"  - Converted: {self.updated_count}")
            print(f"  - Already correct: {self.already_correct_count}")
            print(f"  - No CID: {self.no_cid_count}")
            print(f"  - Conversion errors: {self.conversion_error_count}")
            print(f"  - Update errors: {self.update_error_count}")
            print(f"  - Log saved to: json_cid_conversion_log_{int(time.time())}.json")

            # Save detailed log to a file
            log_filename = f"json_cid_conversion_log_{int(time.time())}.json"
            with open(log_filename, 'w') as f:
                json.dump({
                    "timestamp": time.time(),
                    "db_path": self.db_path,
                    "total_blocks": len(blocks),
                    "converted_count": self.updated_count,
                    "already_correct_count": self.already_correct_count,
                    "no_cid_count": self.no_cid_count,
                    "conversion_error_count": self.conversion_error_count,
                    "update_error_count": self.update_error_count,
                    "highest_block_processed": self.highest_block_processed,
                    "log_entries": self.conversion_log
                }, f, indent=2)

            print("\n✅ JSON CID conversion completed successfully!")

        except sqlite3.Error as e:
            print(f"Database error: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
        finally:
            if conn:
                conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 convert_json_cids.py <database_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    print(f"🎯 COINjecture JSON CID Converter\n==================================================")
    converter = JSONCIDConverter(db_path)
    converter.convert_cids_in_json_data()
