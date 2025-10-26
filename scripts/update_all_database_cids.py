#!/usr/bin/env python3
"""
Update All Database CIDs
Converts ALL existing CIDs in the database from regular base58 to base58btc
"""

import sqlite3
import base58
import hashlib
import json
import time
from typing import Dict, Any, List, Optional

class DatabaseCIDUpdater:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.updated_count = 0
        self.error_count = 0
        self.conversion_log = []
        
    def convert_regular_base58_to_base58btc(self, cid: str) -> Optional[str]:
        """Convert regular base58 CID to base58btc CID"""
        try:
            if not cid or len(cid) != 46:
                return None
            
            # Use regular base58 alphabet (includes 0, O, I, l)
            regular_alphabet = base58.alphabet
            
            # Decode using regular base58
            raw_bytes = base58.b58decode(cid.encode('utf-8'), alphabet=regular_alphabet)
            
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
        
        # Check for characters that are invalid in base58btc (0, O, I, l)
        invalid_chars = ['0', 'O', 'I', 'l']
        return any(char in cid for char in invalid_chars)
    
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
    
    def migrate_all_cids(self) -> Dict[str, int]:
        """Migrate all CIDs in the database"""
        print("🚀 Starting comprehensive CID migration...")
        
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
                if not self.has_invalid_characters(old_cid):
                    results['already_correct'] += 1
                    print(f"✅ Block {block_index}: CID already correct")
                    continue
                
                # Convert CID
                new_cid = self.convert_regular_base58_to_base58btc(old_cid)
                if not new_cid:
                    results['conversion_errors'] += 1
                    print(f"❌ Block {block_index}: Conversion failed")
                    continue
                
                # Validate new CID
                if self.has_invalid_characters(new_cid):
                    results['conversion_errors'] += 1
                    print(f"❌ Block {block_index}: New CID validation failed")
                    continue
                
                # Update database
                if self.update_block_cid(block_index, old_cid, new_cid):
                    results['migrated'] += 1
                    self.updated_count += 1
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
        
        log_file = f"database_cid_migration_log_{int(time.time())}.json"
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        return log_file
    
    def run_migration(self) -> bool:
        """Run the complete CID migration"""
        print("🎯 COINjecture Database CID Migration")
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
        print("Usage: python update_all_database_cids.py <database_path>")
        print("Example: python update_all_database_cids.py data/blockchain.db")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    updater = DatabaseCIDUpdater(db_path)
    success = updater.run_migration()
    
    if success:
        print("\n✅ Database CID migration completed successfully!")
    else:
        print("\n❌ Database CID migration completed with errors.")
        print("Check the migration log for details.")

if __name__ == "__main__":
    main()
