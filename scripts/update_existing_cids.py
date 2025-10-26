#!/usr/bin/env python3
"""
Update Existing CIDs Script

Updates all existing blocks in the database to use valid base58btc CIDs
instead of the old invalid format.
"""

import sqlite3
import json
import hashlib
import base58
import os
import sys
from datetime import datetime

class CIDUpdater:
    def __init__(self, db_path="data/blockchain.db"):
        self.db_path = db_path
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def generate_valid_cid(self, block_hash):
        """Generate a valid base58btc CID from block hash"""
        try:
            hash_bytes = hashlib.sha256(block_hash.encode()).digest()
            # IPFS CIDv0 uses multihash with sha256 (0x12) and length 32 (0x20)
            multihash = b'\x12\x20' + hash_bytes
            return base58.b58encode(multihash, alphabet=base58.BITCOIN_ALPHABET).decode('ascii')
        except Exception as e:
            self.log(f"⚠️  Error generating CID for {block_hash}: {e}")
            return None
    
    def is_old_cid_format(self, cid):
        """Check if CID is in the old invalid format"""
        if not cid or not cid.startswith('Qm'):
            return False
        
        # Old format: Qm + 44 hex characters
        if len(cid) == 46 and cid[2:].isalnum():
            try:
                # Try to decode as hex (old format)
                int(cid[2:], 16)
                return True
            except ValueError:
                return False
        
        return False
    
    def update_block_cid(self, block_bytes, new_cid):
        """Update the CID in block_bytes JSON"""
        try:
            block_data = json.loads(block_bytes.decode('utf-8'))
            block_data['cid'] = new_cid
            return json.dumps(block_data).encode('utf-8')
        except Exception as e:
            self.log(f"⚠️  Error updating block data: {e}")
            return block_bytes
    
    def update_existing_cids(self):
        """Update all existing blocks with valid CIDs"""
        self.log("🔄 Starting CID update for existing blocks...")
        
        if not os.path.exists(self.db_path):
            self.log(f"❌ Database not found: {self.db_path}")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all blocks
            cursor.execute("SELECT height, block_bytes FROM blocks ORDER BY height")
            blocks = cursor.fetchall()
            
            self.log(f"📊 Found {len(blocks)} blocks to process")
            
            updated_count = 0
            skipped_count = 0
            
            for height, block_bytes in blocks:
                try:
                    # Parse block data
                    block_data = json.loads(block_bytes.decode('utf-8'))
                    current_cid = block_data.get('cid', '')
                    block_hash = block_data.get('hash', '')
                    
                    # Check if CID needs updating
                    if self.is_old_cid_format(current_cid):
                        # Generate new valid CID
                        new_cid = self.generate_valid_cid(block_hash)
                        
                        if new_cid:
                            # Update block data
                            updated_block_bytes = self.update_block_cid(block_bytes, new_cid)
                            
                            # Update database
                            cursor.execute("""
                                UPDATE blocks 
                                SET block_bytes = ? 
                                WHERE height = ?
                            """, (updated_block_bytes, height))
                            
                            updated_count += 1
                            
                            if height % 100 == 0:
                                self.log(f"📊 Updated {height} blocks...")
                        else:
                            skipped_count += 1
                    else:
                        skipped_count += 1
                        
                except Exception as e:
                    self.log(f"⚠️  Error processing block {height}: {e}")
                    skipped_count += 1
                    continue
            
            # Commit changes
            conn.commit()
            conn.close()
            
            self.log("✅ CID update completed!")
            self.log(f"📊 Blocks updated: {updated_count}")
            self.log(f"📊 Blocks skipped: {skipped_count}")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error updating CIDs: {e}")
            return False
    
    def verify_cids(self):
        """Verify that CIDs are now valid"""
        self.log("🔍 Verifying updated CIDs...")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get sample of blocks to verify
            cursor.execute("SELECT height, block_bytes FROM blocks ORDER BY height LIMIT 10")
            blocks = cursor.fetchall()
            
            valid_count = 0
            invalid_count = 0
            
            for height, block_bytes in blocks:
                try:
                    block_data = json.loads(block_bytes.decode('utf-8'))
                    cid = block_data.get('cid', '')
                    
                    # Check if CID is valid base58btc
                    try:
                        decoded = base58.b58decode(cid)
                        if len(decoded) == 34 and decoded.startswith(b'\x12\x20'):
                            valid_count += 1
                        else:
                            invalid_count += 1
                            self.log(f"⚠️  Block {height}: Invalid CID format")
                    except Exception:
                        invalid_count += 1
                        self.log(f"⚠️  Block {height}: CID decode failed")
                        
                except Exception as e:
                    self.log(f"⚠️  Error verifying block {height}: {e}")
                    invalid_count += 1
            
            conn.close()
            
            self.log(f"✅ Verification complete: {valid_count} valid, {invalid_count} invalid")
            return valid_count > 0 and invalid_count == 0
            
        except Exception as e:
            self.log(f"❌ Error verifying CIDs: {e}")
            return False

def main():
    """Main function"""
    print("🔄 COINjecture CID Updater")
    print("=" * 40)
    
    # Check if database exists
    db_path = "data/blockchain.db"
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        print("Please run this script from the COINjecture project directory")
        sys.exit(1)
    
    # Create updater
    updater = CIDUpdater(db_path)
    
    # Update CIDs
    success = updater.update_existing_cids()
    
    if success:
        # Verify the update
        if updater.verify_cids():
            print("\n✅ CID update completed successfully!")
            print("🎯 All existing blocks now have valid base58btc CIDs")
            print("🚀 Ready for fresh Kaggle export!")
        else:
            print("\n⚠️  CID update completed but verification failed")
            print("🔍 Please check the database manually")
    else:
        print("\n❌ CID update failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
