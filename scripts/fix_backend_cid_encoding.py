#!/usr/bin/env python3
"""
Fix Backend CID Encoding
Updates CID generation to use proper base58btc encoding and fixes existing CIDs
"""

import base58
import hashlib
import json
import time
from typing import Dict, Any, List

class BackendCIDFixer:
    def __init__(self):
        self.fixed_cids = []
        self.errors = []
        
    def convert_to_base58btc(self, cid: str) -> str:
        """Convert regular base58 CID to base58btc CID"""
        try:
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
    
    def generate_proper_cid(self, data: str) -> str:
        """Generate a proper base58btc CID from data"""
        try:
            # Create SHA-256 hash of the data
            hash_bytes = hashlib.sha256(data.encode('utf-8')).digest()
            
            # Create CIDv0 format (multihash with SHA-256)
            # CIDv0 format: 0x12 (SHA-256) + 0x20 (32 bytes) + hash
            cid_bytes = b'\x12\x20' + hash_bytes
            
            # Encode using base58btc
            cid = base58.b58encode(cid_bytes, alphabet=base58.BITCOIN_ALPHABET).decode('utf-8')
            
            return cid
        except Exception as e:
            print(f"❌ Error generating CID: {e}")
            return None
    
    def create_backend_migration_script(self) -> str:
        """Create a database migration script for the backend"""
        migration_script = '''
-- COINjecture CID Encoding Migration Script
-- Converts all CIDs from base58 to base58btc encoding

-- Step 1: Add new column for base58btc CIDs
ALTER TABLE blocks ADD COLUMN cid_base58btc VARCHAR(46);

-- Step 2: Update all existing CIDs
-- This would need to be run with a Python script that converts each CID
UPDATE blocks SET cid_base58btc = convert_to_base58btc(cid);

-- Step 3: Drop old column and rename new one
ALTER TABLE blocks DROP COLUMN cid;
ALTER TABLE blocks RENAME COLUMN cid_base58btc TO cid;

-- Step 4: Add index for performance
CREATE INDEX idx_blocks_cid ON blocks(cid);

-- Step 5: Update any other tables that reference CIDs
-- (This would depend on your database schema)
'''
        return migration_script
    
    def create_backend_cid_generator(self) -> str:
        """Create updated CID generation code for the backend"""
        cid_generator_code = '''
# Updated CID Generation for COINjecture Backend
# This should replace the existing CID generation code

import base58
import hashlib
from typing import Dict, Any

def generate_block_cid(block_data: Dict[Any, Any]) -> str:
    """
    Generate a proper base58btc CID for a block
    """
    try:
        # Create a deterministic string from block data
        block_string = f"{block_data['index']}_{block_data['block_hash']}_{block_data['timestamp']}"
        
        # Create SHA-256 hash
        hash_bytes = hashlib.sha256(block_string.encode('utf-8')).digest()
        
        # Create CIDv0 format (multihash with SHA-256)
        # CIDv0 format: 0x12 (SHA-256) + 0x20 (32 bytes) + hash
        cid_bytes = b'\\x12\\x20' + hash_bytes
        
        # Encode using base58btc (excludes 0, O, I, l)
        cid = base58.b58encode(cid_bytes, alphabet=base58.BITCOIN_ALPHABET).decode('utf-8')
        
        return cid
    except Exception as e:
        print(f"Error generating CID: {e}")
        return None

def validate_cid_format(cid: str) -> bool:
    """
    Validate that CID uses proper base58btc encoding
    """
    if not cid or len(cid) != 46:
        return False
    
    # Check for base58btc characters (excludes 0, O, I, l)
    import re
    base58btc_pattern = r'^[1-9A-HJ-NP-Za-km-z]+$'
    return bool(re.match(base58btc_pattern, cid))

# Example usage:
# block_data = {
#     'index': 11473,
#     'block_hash': 'ea67892b21f971d636625994774a7a56262a955b0df0bdecca69e0af4fd2a0a7',
#     'timestamp': 1761442499.7123244
# }
# cid = generate_block_cid(block_data)
# print(f"Generated CID: {cid}")
# print(f"Valid format: {validate_cid_format(cid)}")
'''
        return cid_generator_code
    
    def create_database_update_script(self) -> str:
        """Create a Python script to update the database"""
        update_script = '''
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
            base58btc_cid = base58.b58encode(raw_bytes, alphabet=base58.BITCOIN_ALPHABET).decode('utf-8')
            
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
            
            print(f"\\nUpdate complete:")
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
'''
        return update_script
    
    def create_computational_data_fix(self) -> str:
        """Create a script to fix computational data with proper CIDs"""
        computational_fix = '''
#!/usr/bin/env python3
"""
Computational Data CID Fix
Updates computational data files with proper base58btc CIDs
"""

import base58
import json
import csv
import os
from typing import Dict, Any, List

class ComputationalDataFixer:
    def __init__(self):
        self.fixed_files = []
        self.errors = []
    
    def convert_cid_to_base58btc(self, cid: str) -> str:
        """Convert regular base58 CID to base58btc CID"""
        try:
            raw_bytes = base58.b58decode(cid)
            base58btc_cid = base58.b58encode(raw_bytes, alphabet=base58.BITCOIN_ALPHABET).decode('utf-8')
            return base58btc_cid
        except Exception as e:
            print(f"Error converting CID {cid}: {e}")
            return None
    
    def fix_csv_file(self, file_path: str):
        """Fix CIDs in a CSV file"""
        try:
            # Read CSV file
            with open(file_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Update CIDs
            for row in rows:
                if 'cid' in row and row['cid']:
                    old_cid = row['cid']
                    new_cid = self.convert_cid_to_base58btc(old_cid)
                    if new_cid:
                        row['cid'] = new_cid
                        print(f"Updated CID: {old_cid} → {new_cid}")
            
            # Write updated CSV
            with open(file_path, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=reader.fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            self.fixed_files.append(file_path)
            print(f"✅ Fixed {file_path}")
            
        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
            self.errors.append(f"{file_path}: {e}")
    
    def fix_json_file(self, file_path: str):
        """Fix CIDs in a JSON file"""
        try:
            # Read JSON file
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Update CIDs recursively
            self._update_cids_in_data(data)
            
            # Write updated JSON
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.fixed_files.append(file_path)
            print(f"✅ Fixed {file_path}")
            
        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
            self.errors.append(f"{file_path}: {e}")
    
    def _update_cids_in_data(self, data):
        """Recursively update CIDs in data structure"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key == 'cid' and isinstance(value, str):
                    new_cid = self.convert_cid_to_base58btc(value)
                    if new_cid:
                        data[key] = new_cid
                else:
                    self._update_cids_in_data(value)
        elif isinstance(data, list):
            for item in data:
                self._update_cids_in_data(item)
    
    def fix_all_data_files(self, data_dir: str = "research_data"):
        """Fix all computational data files"""
        print(f"🔧 Fixing computational data files in {data_dir}")
        
        # Fix CSV files
        for file in os.listdir(data_dir):
            if file.endswith('.csv'):
                self.fix_csv_file(os.path.join(data_dir, file))
        
        # Fix JSON files
        for file in os.listdir(data_dir):
            if file.endswith('.json'):
                self.fix_json_file(os.path.join(data_dir, file))
        
        print(f"\\n📊 Summary:")
        print(f"  - Fixed files: {len(self.fixed_files)}")
        print(f"  - Errors: {len(self.errors)}")
        
        if self.errors:
            print("\\n❌ Errors:")
            for error in self.errors:
                print(f"  - {error}")

# Usage:
# fixer = ComputationalDataFixer()
# fixer.fix_all_data_files("research_data")
'''
        return computational_fix
    
    def generate_fix_report(self) -> str:
        """Generate a comprehensive fix report"""
        report = f"""
🎯 COINjecture CID Encoding Fix Report
=====================================

✅ ISSUE IDENTIFIED:
   - Backend uses regular base58 encoding (includes 0, O, I, l)
   - Should use base58btc encoding (excludes 0, O, I, l)
   - All existing CIDs need to be converted
   - New CID generation needs to be updated

🔧 FILES CREATED:
   1. backend_migration.sql - Database migration script
   2. cid_generator.py - Updated CID generation code
   3. database_update.py - Database update script
   4. computational_data_fix.py - Computational data fix script

📋 BACKEND CHANGES NEEDED:
   1. Update CID generation code to use base58btc
   2. Run database migration to convert existing CIDs
   3. Update computational data files
   4. Test with IPFS integration
   5. Verify academic data export

🌐 COMPUTATIONAL DATA IMPACT:
   - All research data files need CID updates
   - Academic publication requires proper encoding
   - IPFS integration needs valid CIDs
   - Research dataset export needs fixing

💡 NEXT STEPS:
   1. Deploy updated CID generation code
   2. Run database migration
   3. Update computational data files
   4. Test proof bundle downloads
   5. Verify IPFS compatibility

🔧 IMMEDIATE ACTIONS:
   - Update backend CID generation
   - Run database migration script
   - Fix computational data files
   - Test with frontend
   - Verify academic export
"""
        return report
    
    def run_fix(self):
        """Run the complete CID encoding fix"""
        print("🚀 COINjecture CID Encoding Fix")
        print("=" * 40)
        
        # Create all necessary files
        migration_script = self.create_backend_migration_script()
        cid_generator = self.create_backend_cid_generator()
        database_update = self.create_database_update_script()
        computational_fix = self.create_computational_data_fix()
        
        # Save files
        with open('backend_migration.sql', 'w') as f:
            f.write(migration_script)
        
        with open('cid_generator.py', 'w') as f:
            f.write(cid_generator)
        
        with open('database_update.py', 'w') as f:
            f.write(database_update)
        
        with open('computational_data_fix.py', 'w') as f:
            f.write(computational_fix)
        
        # Generate report
        report = self.generate_fix_report()
        print(report)
        
        # Save report
        with open('cid_encoding_fix_report.txt', 'w') as f:
            f.write(report)
        
        print("📄 All fix files created:")
        print("  - backend_migration.sql")
        print("  - cid_generator.py")
        print("  - database_update.py")
        print("  - computational_data_fix.py")
        print("  - cid_encoding_fix_report.txt")
        
        return True

def main():
    """Main function"""
    fixer = BackendCIDFixer()
    fixer.run_fix()

if __name__ == "__main__":
    main()
