#!/usr/bin/env python3
"""
Database CID Migration Script
Converts all existing CIDs from base58 to base58btc encoding
"""

import sqlite3
import base58
import hashlib
import json
import time
from typing import Dict, Any, List, Optional

class DatabaseCIDMigrator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.migrated_count = 0
        self.error_count = 0
        self.conversion_log = []
        
    def convert_cid_to_base58btc(self, cid: str) -> Optional[str]:
        """Convert regular base58 CID to base58btc CID"""
        try:
            if not cid or len(cid) != 46:
                return None
                
            # Decode the base58 CID to get the raw bytes
            raw_bytes = base58.b58decode(cid)
            
            # Re-encode using base58btc (which excludes 0, O, I, l)
            base58btc_cid = base58.b58encode(raw_bytes, alphabet=base58.BITCOIN_ALPHABET).decode('utf-8')
            
            return base58btc_cid
        except Exception as e:
            print(f"❌ Error converting CID {cid}: {e}")
            return None
    
    def validate_base58btc_cid(self, cid: str) -> bool:
        """Validate that CID uses proper base58btc encoding"""
        if not cid or len(cid) != 46:
            return False
        
        # Check for base58btc characters (excludes 0, O, I, l)
        import re
        base58btc_pattern = r'^[1-9A-HJ-NP-Za-km-z]+$'
        return bool(re.match(base58btc_pattern, cid))
    
    def get_all_blocks_with_cids(self) -> List[Dict[str, Any]]:
        """Get all blocks that have CIDs"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all blocks with CIDs
            cursor.execute("""
                SELECT index, block_hash, block_bytes, offchain_cid 
                FROM blocks 
                WHERE offchain_cid IS NOT NULL AND offchain_cid != ''
                ORDER BY index
            """)
            
            blocks = []
            for row in cursor.fetchall():
                blocks.append({
                    'index': row[0],
                    'block_hash': row[1],
                    'block_bytes': row[2],
                    'offchain_cid': row[3]
                })
            
            conn.close()
            return blocks
        except Exception as e:
            print(f"❌ Error getting blocks: {e}")
            return []
    
    def update_block_cid(self, block_index: int, old_cid: str, new_cid: str) -> bool:
        """Update a block's CID in the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Update the CID
            cursor.execute("""
                UPDATE blocks 
                SET offchain_cid = ? 
                WHERE index = ?
            """, (new_cid, block_index))
            
            conn.commit()
            conn.close()
            
            # Log the conversion
            self.conversion_log.append({
                'block_index': block_index,
                'old_cid': old_cid,
                'new_cid': new_cid,
                'timestamp': time.time()
            })
            
            return True
        except Exception as e:
            print(f"❌ Error updating block {block_index}: {e}")
            return False
    
    def migrate_all_cids(self) -> Dict[str, int]:
        """Migrate all CIDs in the database"""
        print("🚀 Starting CID migration...")
        
        # Get all blocks with CIDs
        blocks = self.get_all_blocks_with_cids()
        print(f"📊 Found {len(blocks)} blocks with CIDs")
        
        results = {
            'total_blocks': len(blocks),
            'migrated': 0,
            'already_correct': 0,
            'conversion_errors': 0,
            'update_errors': 0
        }
        
        for block in blocks:
            try:
                old_cid = block['offchain_cid']
                block_index = block['index']
                
                # Check if CID is already base58btc
                if self.validate_base58btc_cid(old_cid):
                    results['already_correct'] += 1
                    print(f"✅ Block {block_index}: CID already correct")
                    continue
                
                # Convert CID
                new_cid = self.convert_cid_to_base58btc(old_cid)
                if not new_cid:
                    results['conversion_errors'] += 1
                    print(f"❌ Block {block_index}: Conversion failed")
                    continue
                
                # Validate new CID
                if not self.validate_base58btc_cid(new_cid):
                    results['conversion_errors'] += 1
                    print(f"❌ Block {block_index}: New CID validation failed")
                    continue
                
                # Update database
                if self.update_block_cid(block_index, old_cid, new_cid):
                    results['migrated'] += 1
                    self.migrated_count += 1
                    print(f"🔄 Block {block_index}: {old_cid} → {new_cid}")
                else:
                    results['update_errors'] += 1
                    print(f"❌ Block {block_index}: Database update failed")
                
                # Rate limiting
                time.sleep(0.01)
                
            except Exception as e:
                print(f"❌ Error processing block {block['index']}: {e}")
                results['update_errors'] += 1
        
        return results
    
    def create_backup(self) -> bool:
        """Create a backup of the database before migration"""
        try:
            import shutil
            backup_path = f"{self.db_path}.backup.{int(time.time())}"
            shutil.copy2(self.db_path, backup_path)
            print(f"✅ Database backup created: {backup_path}")
            return True
        except Exception as e:
            print(f"❌ Error creating backup: {e}")
            return False
    
    def save_migration_log(self, results: Dict[str, int]) -> str:
        """Save migration log to file"""
        log_data = {
            'migration_timestamp': time.time(),
            'results': results,
            'conversion_log': self.conversion_log,
            'summary': {
                'total_processed': results['total_blocks'],
                'migrated': results['migrated'],
                'already_correct': results['already_correct'],
                'errors': results['conversion_errors'] + results['update_errors']
            }
        }
        
        log_file = f"cid_migration_log_{int(time.time())}.json"
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        return log_file
    
    def run_migration(self) -> bool:
        """Run the complete CID migration"""
        print("🎯 COINjecture CID Database Migration")
        print("=" * 40)
        
        # Create backup
        if not self.create_backup():
            print("❌ Failed to create backup. Aborting migration.")
            return False
        
        # Run migration
        results = self.migrate_all_cids()
        
        # Save log
        log_file = self.save_migration_log(results)
        
        # Print summary
        print(f"\n📊 Migration Summary:")
        print(f"  - Total blocks: {results['total_blocks']}")
        print(f"  - Migrated: {results['migrated']}")
        print(f"  - Already correct: {results['already_correct']}")
        print(f"  - Conversion errors: {results['conversion_errors']}")
        print(f"  - Update errors: {results['update_errors']}")
        print(f"  - Log saved to: {log_file}")
        
        return results['update_errors'] == 0

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python migrate_cid_database.py <database_path>")
        print("Example: python migrate_cid_database.py data/blockchain.db")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    migrator = DatabaseCIDMigrator(db_path)
    success = migrator.run_migration()
    
    if success:
        print("\n✅ CID migration completed successfully!")
    else:
        print("\n❌ CID migration completed with errors.")
        print("Check the migration log for details.")

if __name__ == "__main__":
    main()
