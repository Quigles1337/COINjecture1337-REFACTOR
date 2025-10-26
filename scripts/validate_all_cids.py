#!/usr/bin/env python3
"""
Validate All CIDs Script

Validates that all CIDs in the database are proper base58btc format.
Reports detailed statistics and any invalid CIDs found.
"""

import sqlite3
import json
import base58
import os
import sys
from datetime import datetime

class CIDValidator:
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
    
    def validate_cid_format(self, cid):
        """Validate that CID is proper base58btc format"""
        if not cid:
            return False, "Empty CID"
        
        if len(cid) != 46:
            return False, f"Wrong length: {len(cid)} (expected 46)"
        
        if not cid.startswith('Qm'):
            return False, f"Doesn't start with 'Qm': {cid[:5]}..."
        
        # Check for base58btc characters (excludes 0, O, I, l)
        base58btc_chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
        invalid_chars = [c for c in cid if c not in base58btc_chars]
        if invalid_chars:
            return False, f"Invalid characters: {invalid_chars}"
        
        # Try to decode with base58btc
        try:
            decoded = base58.b58decode(cid, alphabet=base58.BITCOIN_ALPHABET)
            if len(decoded) != 34:
                return False, f"Decoded length wrong: {len(decoded)} (expected 34)"
            if not decoded.startswith(b'\x12\x20'):
                return False, f"Doesn't start with multihash prefix: {decoded[:2]}"
        except Exception as e:
            return False, f"Decode error: {e}"
        
        return True, "Valid"
    
    def validate_all_cids(self):
        """Validate all CIDs in the database"""
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
            
            self.log(f"📊 Validating {len(blocks)} blocks...")
            
            valid_count = 0
            invalid_count = 0
            invalid_details = []
            
            for i, (block_hash, block_bytes) in enumerate(blocks):
                try:
                    block_data = json.loads(block_bytes.decode('utf-8'))
                    cid = block_data.get('cid', '')
                    
                    is_valid, reason = self.validate_cid_format(cid)
                    
                    if is_valid:
                        valid_count += 1
                    else:
                        invalid_count += 1
                        invalid_details.append({
                            'block_hash': block_hash,
                            'cid': cid,
                            'reason': reason,
                            'index': i
                        })
                    
                    # Progress indicator
                    if (i + 1) % 100 == 0:
                        self.log(f"📈 Processed {i + 1}/{len(blocks)} blocks...")
                        
                except Exception as e:
                    invalid_count += 1
                    invalid_details.append({
                        'block_hash': block_hash,
                        'cid': 'ERROR',
                        'reason': f"JSON parse error: {e}",
                        'index': i
                    })
            
            conn.close()
            
            # Report results
            self.log(f"\n📊 Validation Results:")
            self.log(f"   📈 Total blocks: {len(blocks)}")
            self.log(f"   ✅ Valid CIDs: {valid_count}")
            self.log(f"   ❌ Invalid CIDs: {invalid_count}")
            self.log(f"   📊 Success rate: {(valid_count/len(blocks)*100):.1f}%")
            
            if invalid_details:
                self.log(f"\n❌ Invalid CIDs Details:")
                for detail in invalid_details[:20]:  # Show first 20
                    self.log(f"   Block {detail['index']}: {detail['block_hash'][:16]}...")
                    self.log(f"      CID: {detail['cid']}")
                    self.log(f"      Reason: {detail['reason']}")
                    self.log("")
                
                if len(invalid_details) > 20:
                    self.log(f"   ... and {len(invalid_details) - 20} more invalid CIDs")
            
            return invalid_count == 0
            
        except Exception as e:
            self.log(f"❌ Validation error: {e}")
            return False
    
    def generate_report(self):
        """Generate a detailed validation report"""
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
            
            # Analyze CIDs
            cid_lengths = {}
            cid_prefixes = {}
            invalid_chars_count = {}
            
            valid_count = 0
            invalid_count = 0
            
            for block_hash, block_bytes in blocks:
                try:
                    block_data = json.loads(block_bytes.decode('utf-8'))
                    cid = block_data.get('cid', '')
                    
                    # Length analysis
                    length = len(cid)
                    cid_lengths[length] = cid_lengths.get(length, 0) + 1
                    
                    # Prefix analysis
                    prefix = cid[:2] if len(cid) >= 2 else cid
                    cid_prefixes[prefix] = cid_prefixes.get(prefix, 0) + 1
                    
                    # Invalid character analysis
                    base58btc_chars = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
                    invalid_chars = [c for c in cid if c not in base58btc_chars]
                    for char in invalid_chars:
                        invalid_chars_count[char] = invalid_chars_count.get(char, 0) + 1
                    
                    is_valid, _ = self.validate_cid_format(cid)
                    if is_valid:
                        valid_count += 1
                    else:
                        invalid_count += 1
                        
                except Exception:
                    invalid_count += 1
            
            conn.close()
            
            # Generate report
            self.log(f"\n📋 Detailed CID Analysis Report:")
            self.log(f"   📊 Total blocks: {len(blocks)}")
            self.log(f"   ✅ Valid CIDs: {valid_count}")
            self.log(f"   ❌ Invalid CIDs: {invalid_count}")
            self.log(f"   📈 Success rate: {(valid_count/len(blocks)*100):.1f}%")
            
            self.log(f"\n📏 CID Length Distribution:")
            for length, count in sorted(cid_lengths.items()):
                self.log(f"   Length {length}: {count} CIDs")
            
            self.log(f"\n🔤 CID Prefix Distribution:")
            for prefix, count in sorted(cid_prefixes.items()):
                self.log(f"   '{prefix}': {count} CIDs")
            
            if invalid_chars_count:
                self.log(f"\n❌ Invalid Characters Found:")
                for char, count in sorted(invalid_chars_count.items()):
                    self.log(f"   '{char}': {count} occurrences")
            
            return invalid_count == 0
            
        except Exception as e:
            self.log(f"❌ Report generation error: {e}")
            return False

def main():
    """Main execution function"""
    print("🔍 COINjecture CID Validation Script")
    print("=" * 50)
    
    validator = CIDValidator()
    
    # Check if database exists
    if not os.path.exists(validator.db_path):
        print(f"❌ Database not found: {validator.db_path}")
        print("💡 Make sure you're running this from the project root directory")
        sys.exit(1)
    
    # Validate all CIDs
    print("\n🔍 Starting CID validation...")
    success = validator.validate_all_cids()
    
    # Generate detailed report
    print("\n📋 Generating detailed report...")
    validator.generate_report()
    
    if success:
        print("\n✅ All CIDs are valid base58btc format!")
        print("🎉 Validation passed!")
        sys.exit(0)
    else:
        print("\n❌ Some CIDs are invalid. Check the details above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
