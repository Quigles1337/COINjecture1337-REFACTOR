#!/usr/bin/env python3
"""
Computational Data CID Fix
Updates all research data files with proper base58btc CIDs
"""

import base58
import json
import csv
import os
import time
import zipfile
from typing import Dict, Any, List, Optional

class ComputationalDataCIDFixer:
    def __init__(self):
        self.fixed_files = []
        self.errors = []
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
    
    def fix_csv_file(self, file_path: str) -> bool:
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
                    if not self.validate_base58btc_cid(old_cid):
                        new_cid = self.convert_cid_to_base58btc(old_cid)
                        if new_cid:
                            row['cid'] = new_cid
                            cid_updates += 1
                            self.conversion_log.append({
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
            
            self.fixed_files.append(file_path)
            print(f"✅ Fixed {file_path} ({cid_updates} CIDs updated)")
            return True
            
        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
            self.errors.append(f"{file_path}: {e}")
            return False
    
    def fix_json_file(self, file_path: str) -> bool:
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
            
            self.fixed_files.append(file_path)
            print(f"✅ Fixed {file_path} ({cid_updates} CIDs updated)")
            return True
            
        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
            self.errors.append(f"{file_path}: {e}")
            return False
    
    def _update_cids_in_data(self, data, file_path: str) -> int:
        """Recursively update CIDs in data structure"""
        cid_updates = 0
        
        if isinstance(data, dict):
            for key, value in data.items():
                if key == 'cid' and isinstance(value, str):
                    if not self.validate_base58btc_cid(value):
                        new_cid = self.convert_cid_to_base58btc(value)
                        if new_cid:
                            data[key] = new_cid
                            cid_updates += 1
                            self.conversion_log.append({
                                'file': file_path,
                                'old_cid': value,
                                'new_cid': new_cid,
                                'timestamp': time.time()
                            })
                            print(f"  🔄 Updated CID: {value} → {new_cid}")
                else:
                    cid_updates += self._update_cids_in_data(value, file_path)
        elif isinstance(data, list):
            for item in data:
                cid_updates += self._update_cids_in_data(item, file_path)
        
        return cid_updates
    
    def fix_zip_file(self, file_path: str) -> bool:
        """Fix CIDs in a ZIP file by extracting, fixing, and re-zipping"""
        try:
            print(f"🔧 Fixing ZIP file: {file_path}")
            
            # Create temporary directory
            temp_dir = f"temp_{int(time.time())}"
            os.makedirs(temp_dir, exist_ok=True)
            
            # Extract ZIP file
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Fix all files in the extracted directory
            fixed_files = 0
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    file_path_full = os.path.join(root, file)
                    if file.endswith('.csv'):
                        if self.fix_csv_file(file_path_full):
                            fixed_files += 1
                    elif file.endswith('.json'):
                        if self.fix_json_file(file_path_full):
                            fixed_files += 1
            
            # Re-create ZIP file
            with zipfile.ZipFile(file_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path_full = os.path.join(root, file)
                        arcname = os.path.relpath(file_path_full, temp_dir)
                        zip_ref.write(file_path_full, arcname)
            
            # Clean up temporary directory
            import shutil
            shutil.rmtree(temp_dir)
            
            self.fixed_files.append(file_path)
            print(f"✅ Fixed {file_path} ({fixed_files} files updated)")
            return True
            
        except Exception as e:
            print(f"❌ Error fixing {file_path}: {e}")
            self.errors.append(f"{file_path}: {e}")
            return False
    
    def fix_all_data_files(self, data_dir: str = "kaggle_data") -> Dict[str, int]:
        """Fix all computational data files"""
        print(f"🚀 Fixing computational data files in {data_dir}")
        
        results = {
            'total_files': 0,
            'fixed_files': 0,
            'csv_files': 0,
            'json_files': 0,
            'zip_files': 0,
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
                    if self.fix_csv_file(file_path):
                        results['fixed_files'] += 1
                    else:
                        results['errors'] += 1
                        
                elif file.endswith('.json'):
                    results['json_files'] += 1
                    if self.fix_json_file(file_path):
                        results['fixed_files'] += 1
                    else:
                        results['errors'] += 1
                        
                elif file.endswith('.zip'):
                    results['zip_files'] += 1
                    if self.fix_zip_file(file_path):
                        results['fixed_files'] += 1
                    else:
                        results['errors'] += 1
        
        return results
    
    def save_fix_log(self, results: Dict[str, int]) -> str:
        """Save fix log to file"""
        log_data = {
            'fix_timestamp': time.time(),
            'results': results,
            'conversion_log': self.conversion_log,
            'fixed_files': self.fixed_files,
            'errors': self.errors,
            'summary': {
                'total_files': results['total_files'],
                'fixed_files': results['fixed_files'],
                'errors': results['errors'],
                'cid_conversions': len(self.conversion_log)
            }
        }
        
        log_file = f"computational_data_cid_fix_log_{int(time.time())}.json"
        with open(log_file, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        return log_file
    
    def run_fix(self, data_dir: str = "kaggle_data") -> bool:
        """Run the complete computational data CID fix"""
        print("🎯 COINjecture Computational Data CID Fix")
        print("=" * 45)
        
        # Fix all files
        results = self.fix_all_data_files(data_dir)
        
        # Save log
        log_file = self.save_fix_log(results)
        
        # Print summary
        print(f"\n📊 Fix Summary:")
        print(f"  - Total files: {results['total_files']}")
        print(f"  - Fixed files: {results['fixed_files']}")
        print(f"  - CSV files: {results['csv_files']}")
        print(f"  - JSON files: {results['json_files']}")
        print(f"  - ZIP files: {results['zip_files']}")
        print(f"  - Errors: {results['errors']}")
        print(f"  - CID conversions: {len(self.conversion_log)}")
        print(f"  - Log saved to: {log_file}")
        
        return results['errors'] == 0

def main():
    """Main function"""
    import sys
    
    data_dir = "kaggle_data"
    if len(sys.argv) > 1:
        data_dir = sys.argv[1]
    
    fixer = ComputationalDataCIDFixer()
    success = fixer.run_fix(data_dir)
    
    if success:
        print("\n✅ Computational data CID fix completed successfully!")
    else:
        print("\n❌ Computational data CID fix completed with errors.")
        print("Check the fix log for details.")

if __name__ == "__main__":
    main()
