
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
            base58btc_cid = base58.b58encode(raw_bytes, alphabet=base58.ALPHABET_BTC).decode('utf-8')
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
        
        print(f"\n📊 Summary:")
        print(f"  - Fixed files: {len(self.fixed_files)}")
        print(f"  - Errors: {len(self.errors)}")
        
        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"  - {error}")

# Usage:
# fixer = ComputationalDataFixer()
# fixer.fix_all_data_files("research_data")
