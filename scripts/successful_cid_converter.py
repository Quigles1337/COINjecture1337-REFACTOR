#!/usr/bin/env python3
"""
Successful CID Converter
Correctly converts CIDs from regular base58 to base58btc
"""

import base58
import hashlib
import json
import csv
import os
import time
from typing import Dict, Any, List, Optional

class SuccessfulCIDConverter:
    def __init__(self):
        self.converted_cids = []
        self.errors = []
        
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
    
    def fix_csv_file(self, file_path: str) -> int:
        """Fix CIDs in a CSV file"""
        try:
            print(f"🔧 Fixing CSV file: {file_path}")
            
            # Read CSV file
            rows = []
            fieldnames = None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                rows = list(reader)
            
            # Update CIDs
            cid_updates = 0
            for row in rows:
                if 'cid' in row and row['cid']:
                    old_cid = row['cid']
                    if self.has_invalid_characters(old_cid):
                        new_cid = self.convert_regular_base58_to_base58btc(old_cid)
                        if new_cid:
                            row['cid'] = new_cid
                            cid_updates += 1
                            self.converted_cids.append({
                                'file': file_path,
                                'old_cid': old_cid,
                                'new_cid': new_cid,
                                'timestamp': time.time()
                            })
                            print(f"  🔄 Updated CID: {old_cid} → {new_cid}")
            
            # Write updated CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            print(f"✅ Fixed {file_path} ({cid_updates} CIDs updated)")
            return cid_updates
            
        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
            self.errors.append(f"{file_path}: {e}")
            return 0
    
    def fix_json_file(self, file_path: str) -> int:
        """Fix CIDs in a JSON file"""
        try:
            print(f"🔧 Fixing JSON file: {file_path}")
            
            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Update CIDs recursively
            cid_updates = self._update_cids_in_data(data, file_path)
            
            # Write updated JSON
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Fixed {file_path} ({cid_updates} CIDs updated)")
            return cid_updates
            
        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
            self.errors.append(f"{file_path}: {e}")
            return 0
    
    def _update_cids_in_data(self, data, file_path: str) -> int:
        """Recursively update CIDs in data structure"""
        cid_updates = 0
        
        if isinstance(data, dict):
            for key, value in data.items():
                if key == 'cid' and isinstance(value, str):
                    if self.has_invalid_characters(value):
                        new_cid = self.convert_regular_base58_to_base58btc(value)
                        if new_cid:
                            data[key] = new_cid
                            cid_updates += 1
                            self.converted_cids.append({
                                'file': file_path,
                                'old_cid': value,
                                'new_cid': new_cid,
                                'timestamp': time.time()
                            })
                            print(f"  🔄 Updated CID: {value} → {new_cid}")
                else:
                    cid_updates += self._update_cids_in_data(data[key], file_path)
        elif isinstance(data, list):
            for item in data:
                cid_updates += self._update_cids_in_data(item, file_path)
        
        return cid_updates
    
    def fix_all_data_files(self, data_dir: str = "kaggle_data") -> Dict[str, int]:
        """Fix all computational data files"""
        print(f"🚀 Successful CID conversion in {data_dir}")
        
        results = {
            'total_files': 0,
            'fixed_files': 0,
            'total_cid_updates': 0,
            'csv_files': 0,
            'json_files': 0,
            'errors': 0
        }
        
        if not os.path.exists(data_dir):
            print(f"❌ Directory {data_dir} does not exist")
            return results
        
        # Process all files
        for file in os.listdir(data_dir):
            file_path = os.path.join(data_dir, file)
            
            if os.path.isfile(file_path):
                results['total_files'] += 1
                
                if file.endswith('.csv'):
                    results['csv_files'] += 1
                    cid_updates = self.fix_csv_file(file_path)
                    if cid_updates > 0:
                        results['fixed_files'] += 1
                        results['total_cid_updates'] += cid_updates
                    elif cid_updates == 0 and not self.errors:
                        results['fixed_files'] += 1
                    else:
                        results['errors'] += 1
                        
                elif file.endswith('.json'):
                    results['json_files'] += 1
                    cid_updates = self.fix_json_file(file_path)
                    if cid_updates > 0:
                        results['fixed_files'] += 1
                        results['total_cid_updates'] += cid_updates
                    elif cid_updates == 0 and not self.errors:
                        results['fixed_files'] += 1
                    else:
                        results['errors'] += 1
        
        return results
    
    def save_conversion_log(self, results: Dict[str, int]) -> str:
        """Save conversion log to file"""
        log_data = {
            'conversion_timestamp': time.time(),
            'results': results,
            'converted_cids': self.converted_cids,
            'errors': self.errors,
            'summary': {
                'total_files': results['total_files'],
                'fixed_files': results['fixed_files'],
                'total_cid_updates': results['total_cid_updates'],
                'errors': results['errors']
            }
        }
        
        log_file = f"successful_cid_conversion_log_{int(time.time())}.json"
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        return log_file
    
    def run_conversion(self, data_dir: str = "kaggle_data") -> bool:
        """Run the complete CID conversion"""
        print("🎯 COINjecture Successful CID Conversion")
        print("=" * 45)
        
        # Fix all files
        results = self.fix_all_data_files(data_dir)
        
        # Save log
        log_file = self.save_conversion_log(results)
        
        # Print summary
        print(f"\n📊 Conversion Summary:")
        print(f"  - Total files: {results['total_files']}")
        print(f"  - Fixed files: {results['fixed_files']}")
        print(f"  - CSV files: {results['csv_files']}")
        print(f"  - JSON files: {results['json_files']}")
        print(f"  - Total CID updates: {results['total_cid_updates']}")
        print(f"  - Errors: {results['errors']}")
        print(f"  - Log saved to: {log_file}")
        
        return results['errors'] == 0

def main():
    """Main function"""
    import sys
    
    data_dir = "kaggle_data"
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    
    converter = SuccessfulCIDConverter()
    success = converter.run_conversion(data_dir)
    
    if success:
        print("\n✅ Successful CID conversion completed successfully!")
    else:
        print("\n❌ Successful CID conversion completed with errors.")
        print("Check the conversion log for details.")

if __name__ == "__main__":
    main()
