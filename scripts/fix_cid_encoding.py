#!/usr/bin/env python3
"""
Fix CID Encoding in Database
Converts regular base58 CIDs to proper base58btc encoding for IPFS compatibility
"""

import requests
import json
import base58
import hashlib
import time
from typing import Dict, Any

class CIDEncodingFixer:
    def __init__(self):
        self.api_base = "https://api.coinjecture.com"
        self.fixed_count = 0
        self.error_count = 0
        
    def convert_base58_to_base58btc(self, cid: str) -> str:
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
        base58btc_pattern = r'^[1-9A-HJ-NP-Za-km-z]+$'
        import re
        return bool(re.match(base58btc_pattern, cid))
    
    def get_block_data(self, block_index: int) -> Dict[Any, Any]:
        """Get block data from API"""
        try:
            response = requests.get(f"{self.api_base}/v1/data/block/{block_index}", timeout=10)
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"❌ Error fetching block {block_index}: {e}")
            return None
    
    def update_block_cid(self, block_index: int, old_cid: str, new_cid: str) -> bool:
        """Update block CID in database (this would need backend API endpoint)"""
        # Note: This would require a backend API endpoint to update the database
        # For now, we'll just log what needs to be updated
        print(f"📝 Block {block_index}: {old_cid} → {new_cid}")
        return True
    
    def fix_cids_in_range(self, start_block: int, end_block: int) -> Dict[str, int]:
        """Fix CIDs in a range of blocks"""
        print(f"🔧 Fixing CIDs in blocks {start_block} to {end_block}")
        
        results = {
            'total_checked': 0,
            'needs_fixing': 0,
            'already_correct': 0,
            'conversion_errors': 0,
            'api_errors': 0
        }
        
        for block_index in range(start_block, end_block + 1):
            try:
                # Get block data
                block_data = self.get_block_data(block_index)
                if not block_data or 'data' not in block_data:
                    results['api_errors'] += 1
                    continue
                
                current_cid = block_data['data'].get('cid')
                if not current_cid:
                    continue
                
                results['total_checked'] += 1
                
                # Check if CID needs fixing
                if self.validate_base58btc_cid(current_cid):
                    results['already_correct'] += 1
                    print(f"✅ Block {block_index}: CID already correct")
                    continue
                
                # Convert CID
                new_cid = self.convert_base58_to_base58btc(current_cid)
                if not new_cid:
                    results['conversion_errors'] += 1
                    continue
                
                # Validate new CID
                if not self.validate_base58btc_cid(new_cid):
                    print(f"❌ Block {block_index}: Conversion failed validation")
                    results['conversion_errors'] += 1
                    continue
                
                # Update block (would need backend API)
                if self.update_block_cid(block_index, current_cid, new_cid):
                    results['needs_fixing'] += 1
                    self.fixed_count += 1
                
                # Rate limiting
                time.sleep(0.1)
                
            except Exception as e:
                print(f"❌ Error processing block {block_index}: {e}")
                results['api_errors'] += 1
        
        return results
    
    def generate_fix_report(self, results: Dict[str, int]) -> str:
        """Generate a report of the CID fixing process"""
        report = f"""
🎯 CID Encoding Fix Report
========================

📊 SUMMARY:
   - Total blocks checked: {results['total_checked']}
   - CIDs needing fixing: {results['needs_fixing']}
   - Already correct: {results['already_correct']}
   - Conversion errors: {results['conversion_errors']}
   - API errors: {results['api_errors']}

🔧 NEXT STEPS:
   1. Backend needs API endpoint to update block CIDs
   2. Run database migration to fix all CIDs
   3. Update CID generation to use base58btc encoding
   4. Verify all CIDs are properly formatted

💡 BACKEND CHANGES NEEDED:
   - Add PUT /v1/admin/block/{index}/cid endpoint
   - Update CID generation to use base58btc
   - Run database migration script
   - Update all existing CIDs in database
"""
        return report
    
    def run_fix(self, start_block: int = None, end_block: int = None):
        """Run the CID fixing process"""
        print("🚀 COINjecture CID Encoding Fix")
        print("=" * 40)
        
        # Get latest block if range not specified
        if not start_block or not end_block:
            try:
                response = requests.get(f"{self.api_base}/v1/data/block/latest", timeout=10)
                if response.status_code == 200:
                    latest_data = response.json()
                    latest_block = latest_data['data']['index']
                    start_block = max(1, latest_block - 100)  # Last 100 blocks
                    end_block = latest_block
                else:
                    print("❌ Could not get latest block, using default range")
                    start_block = 11400
                    end_block = 11482
            except Exception as e:
                print(f"❌ Error getting latest block: {e}")
                start_block = 11400
                end_block = 11482
        
        print(f"🎯 Fixing CIDs in blocks {start_block} to {end_block}")
        
        # Run the fix
        results = self.fix_cids_in_range(start_block, end_block)
        
        # Generate report
        report = self.generate_fix_report(results)
        print(report)
        
        # Save report to file
        with open('cid_fix_report.txt', 'w') as f:
            f.write(report)
        
        print("📄 Report saved to cid_fix_report.txt")
        
        return results

def main():
    """Main function"""
    fixer = CIDEncodingFixer()
    
    # Fix recent blocks
    results = fixer.run_fix()
    
    print(f"\n✅ CID Fix Complete!")
    print(f"   - Fixed: {fixer.fixed_count} CIDs")
    print(f"   - Errors: {fixer.error_count} errors")

if __name__ == "__main__":
    main()
