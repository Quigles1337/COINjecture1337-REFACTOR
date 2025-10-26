#!/usr/bin/env python3
"""
Working CID Migration
Properly converts CIDs from regular base58 to base58btc by using the correct alphabets
"""

import sqlite3
import base58
import json
import time
from typing import Dict, Any, List, Optional

class WorkingCIDMigrator:
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
        
        # Check for characters that are invalid in base58btc (0, O, I, l)
        invalid_chars = ['0', 'O', 'I', 'l']
        return any(char in cid for char in invalid_chars)
    
    def get_all_blocks_with_json_data(self) -> List[Dict[str, Any]]:
        """Get all blocks that have JSON data in block_bytes"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all blocks with block_bytes
            cursor.execute("""
                SELECT block_hash, height, block_bytes 
                FROM blocks 
                WHERE block_bytes IS NOT NULL AND block_bytes != ''
                ORDER BY height
            """)
            
            blocks = []
            for row in cursor.fetchall():
                try:
                    # Parse JSON data
                    json_data = json.loads(row[2])
                    blocks.append({
                        'block_hash': row[0],
                        'height': row[1],
                        'json_data': json_data
                    })
                except json.JSONDecodeError:
                    print(f"⚠️ Block {row[1]} has invalid JSON data")
                    continue
            
            conn.close()
            return blocks
        except Exception as e:
            print(f"❌ Error getting blocks: {e}")
            return []
    
    def update_block_json_cid(self, block_hash: str, height: int, old_cid: str, new_cid: str, json_data: dict) -> bool:
        """Update a block's CID in the JSON data and save back to database"""
        try:
            # Update the CID in the JSON data
            json_data['cid'] = new_cid
            
            # Convert back to JSON
            updated_json = json.dumps(json_data, separators=(',', ':'))
            
            # Update the database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE blocks 
                SET block_bytes = ? 
                WHERE block_hash = ?
            """, (updated_json, block_hash))
            
            conn.commit()
            conn.close()
            
            # Log the conversion
            self.conversion_log.append({
                'block_hash': block_hash,
                'height': height,
                'old_cid': old_cid,
                'new_cid': new_cid,
                'timestamp': time.time()
            })
            
            return True
        except Exception as e:
            print(f"❌ Error updating block {height} ({block_hash}): {e}")
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
    
    def migrate_all_json_cids(self) -> Dict[str, int]:
        """Migrate all CIDs in JSON block data"""
        print("🚀 Starting working CID migration...")
        
        # Get all blocks with JSON data
        blocks = self.get_all_blocks_with_json_data()
        print(f"📊 Found {len(blocks)} blocks with JSON data")
        
        results = {
            'total_blocks': len(blocks),
            'migrated': 0,
            'already_correct': 0,
            'conversion_errors': 0,
            'update_errors': 0,
            'no_cid': 0
        }
        
        for block in blocks:
            try:
                json_data = block['json_data']
                block_hash = block['block_hash']
                height = block['height']
                
                # Check if block has CID
                if 'cid' not in json_data:
                    results['no_cid'] += 1
                    if height % 1000 == 0:  # Only print every 1000 blocks
                        print(f"⚠️ Block {height}: No CID found")
                    continue
                
                old_cid = json_data['cid']
                
                # Check if CID is already base58btc
                if not self.has_invalid_characters(old_cid):
                    results['already_correct'] += 1
                    if height % 1000 == 0:  # Only print every 1000 blocks
                        print(f"✅ Block {height}: CID already correct")
                    continue
                
                # Convert CID
                new_cid = self.convert_regular_base58_to_base58btc(old_cid)
                if not new_cid:
                    results['conversion_errors'] += 1
                    if height % 1000 == 0:  # Only print every 1000 blocks
                        print(f"❌ Block {height}: Conversion failed")
                    continue
                
                # Validate new CID
                if self.has_invalid_characters(new_cid):
                    results['conversion_errors'] += 1
                    if height % 1000 == 0:  # Only print every 1000 blocks
                        print(f"❌ Block {height}: New CID validation failed")
                    continue
                
                # Update database
                if self.update_block_json_cid(block_hash, height, old_cid, new_cid, json_data):
                    results['migrated'] += 1
                    self.updated_count += 1
                    if height % 1000 == 0:  # Only print every 1000 blocks
                        print(f"🔄 Block {height}: {old_cid} → {new_cid}")
                else:
                    results['update_errors'] += 1
                    if height % 1000 == 0:  # Only print every 1000 blocks
                        print(f"❌ Block {height}: Database update failed")
                
                # Rate limiting
                time.sleep(0.001)
                
            except Exception as e:
                print(f"❌ Error processing block {block['height']}: {e}")
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
        
        log_file = f"working_cid_migration_log_{int(time.time())}.json"
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        return log_file
    
    def run_migration(self) -> bool:
        """Run the complete CID migration"""
        print("🎯 COINjecture Working CID Migration")
        print("=" * 50)
        
        # Create backup
        if not self.create_backup():
            print("❌ Failed to create backup. Aborting migration.")
            return False
        
        # Run migration
        results = self.migrate_all_json_cids()
        
        # Save log
        log_file = self.save_migration_log(results)
        
        # Print summary
        print(f"\n📊 Migration Summary:")
        print(f"  - Total blocks: {results['total_blocks']}")
        print(f"  - Migrated: {results['migrated']}")
        print(f"  - Already correct: {results['already_correct']}")
        print(f"  - No CID: {results['no_cid']}")
        print(f"  - Conversion errors: {results['conversion_errors']}")
        print(f"  - Update errors: {results['update_errors']}")
        print(f"  - Log saved to: {log_file}")
        
        return results['update_errors'] == 0

def main():
    """Main function"""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python working_cid_migration.py <database_path>")
        print("Example: python working_cid_migration.py /opt/coinjecture/data/blockchain.db")
        sys.exit(1)
    
    db_path = sys.argv[1]
    
    migrator = WorkingCIDMigrator(db_path)
    success = migrator.run_migration()
    
    if success:
        print("\n✅ Working CID migration completed successfully!")
    else:
        print("\n❌ Working CID migration completed with errors.")
        print("Check the migration log for details.")

if __name__ == "__main__":
    main()
