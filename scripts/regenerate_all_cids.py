#!/usr/bin/env python3
"""
Regenerate All CIDs Script

Regenerates all CIDs in the database using proper base58btc encoding.
This ensures all CIDs are valid and consistent across the system.
"""

import sqlite3
import json
import hashlib
import base58
import os
import sys
from datetime import datetime

class CIDRegenerator:
    def __init__(self, db_path="data/blockchain.db"):
        # Try multiple possible database locations
        possible_paths = [
            "data/blockchain.db",
            "/root/coinjecture/data/blockchain.db", 
            "/root/data/blockchain.db",
            "/opt/coinjecture/data/blockchain.db",
            db_path
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                self.db_path = path
                break
        else:
            self.db_path = db_path
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def generate_proper_cid(self, block_hash):
        """Generate a proper base58btc CID from block hash"""
        try:
            hash_bytes = hashlib.sha256(block_hash.encode()).digest()
            # IPFS CIDv0 uses multihash with sha256 (0x12) and length 32 (0x20)
            multihash = b'\x12\x20' + hash_bytes
            return base58.b58encode(multihash, alphabet=base58.BITCOIN_ALPHABET).decode('ascii')
        except Exception as e:
            self.log(f"⚠️  Error generating CID for {block_hash}: {e}")
            return None
    
    def validate_cid(self, cid):
        """Validate that CID is proper base58btc format"""
        if not cid or len(cid) != 46:
            return False
        
        # Check for base58btc characters (excludes 0, O, I, l)
        base58btc_chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        return all(c in base58btc_chars for c in cid)
    
    def regenerate_all_cids(self):
        """Regenerate all CIDs in the database"""
        if not os.path.exists(self.db_path):
            self.log(f"❌ Database not found: {self.db_path}")
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all blocks
            cursor.execute("SELECT block_hash, block_bytes FROM blocks")
            blocks = cursor.fetchall()
            
            if not blocks:
                self.log("❌ No blocks found in database")
                return False
            
            self.log(f"📊 Found {len(blocks)} blocks to process")
            
            updated_count = 0
            error_count = 0
            
            for block_hash, block_bytes in blocks:
                try:
                    # Parse block data
                    block_data = json.loads(block_bytes.decode('utf-8'))
                    old_cid = block_data.get('cid', '')
                    
                    # Generate new CID
                    new_cid = self.generate_proper_cid(block_hash)
                    if not new_cid:
                        self.log(f"⚠️  Failed to generate CID for block {block_hash[:16]}...")
                        error_count += 1
                        continue
                    
                    # Validate new CID
                    if not self.validate_cid(new_cid):
                        self.log(f"⚠️  Generated invalid CID for block {block_hash[:16]}...")
                        error_count += 1
                        continue
                    
                    # Update block data
                    block_data['cid'] = new_cid
                    new_block_bytes = json.dumps(block_data).encode('utf-8')
                    
                    # Update database
                    cursor.execute(
                        "UPDATE blocks SET block_bytes = ? WHERE block_hash = ?",
                        (new_block_bytes, block_hash)
                    )
                    
                    updated_count += 1
                    
                    if updated_count % 100 == 0:
                        self.log(f"📈 Processed {updated_count} blocks...")
                    
                except Exception as e:
                    self.log(f"⚠️  Error processing block {block_hash[:16]}...: {e}")
                    error_count += 1
                    continue
            
            # Commit all changes
            conn.commit()
            conn.close()
            
            self.log(f"✅ Migration completed!")
            self.log(f"   📊 Total blocks: {len(blocks)}")
            self.log(f"   ✅ Updated: {updated_count}")
            self.log(f"   ❌ Errors: {error_count}")
            
            return error_count == 0
            
        except Exception as e:
            self.log(f"❌ Database error: {e}")
            return False
    
    def verify_migration(self):
        """Verify that all CIDs are now valid base58btc"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT block_hash, block_bytes FROM blocks")
            blocks = cursor.fetchall()
            
            valid_count = 0
            invalid_count = 0
            invalid_cids = []
            
            for block_hash, block_bytes in blocks:
                try:
                    block_data = json.loads(block_bytes.decode('utf-8'))
                    cid = block_data.get('cid', '')
                    
                    if self.validate_cid(cid):
                        valid_count += 1
                    else:
                        invalid_count += 1
                        invalid_cids.append(f"{block_hash[:16]}... -> {cid}")
                        
                except Exception as e:
                    invalid_count += 1
                    invalid_cids.append(f"{block_hash[:16]}... -> Error: {e}")
            
            conn.close()
            
            self.log(f"🔍 Verification Results:")
            self.log(f"   ✅ Valid CIDs: {valid_count}")
            self.log(f"   ❌ Invalid CIDs: {invalid_count}")
            
            if invalid_cids:
                self.log(f"   📋 Invalid CIDs:")
                for invalid in invalid_cids[:10]:  # Show first 10
                    self.log(f"      {invalid}")
                if len(invalid_cids) > 10:
                    self.log(f"      ... and {len(invalid_cids) - 10} more")
            
            return invalid_count == 0
            
        except Exception as e:
            self.log(f"❌ Verification error: {e}")
            return False

def main():
    """Main execution function"""
    print("🔄 COINjecture CID Regeneration Script")
    print("=" * 50)
    
    regenerator = CIDRegenerator()
    
    # Check if database exists
    if not os.path.exists(regenerator.db_path):
        print(f"❌ Database not found: {regenerator.db_path}")
        print("💡 Make sure you're running this from the project root directory")
        sys.exit(1)
    
    # Regenerate all CIDs
    print("\n🔄 Starting CID regeneration...")
    success = regenerator.regenerate_all_cids()
    
    if not success:
        print("\n❌ Migration failed!")
        sys.exit(1)
    
    # Verify migration
    print("\n🔍 Verifying migration...")
    verification_success = regenerator.verify_migration()
    
    if verification_success:
        print("\n✅ All CIDs are now valid base58btc format!")
        print("🎉 Migration completed successfully!")
    else:
        print("\n⚠️  Some CIDs are still invalid. Check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
