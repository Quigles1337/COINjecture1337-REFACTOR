#!/usr/bin/env python3
"""
Update Server CIDs Script

Updates all existing blocks on the server to use valid base58btc CIDs
by connecting to the API and updating blocks.
"""

import requests
import json
import hashlib
import base58
import time
from datetime import datetime

class ServerCIDUpdater:
    def __init__(self, api_url="http://167.172.213.70:12346"):
        self.api_url = api_url
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def generate_valid_cid(self, block_hash):
        """Generate a valid base58btc CID from block hash"""
        try:
            hash_bytes = hashlib.sha256(block_hash.encode()).digest()
            # IPFS CIDv0 uses multihash with sha256 (0x12) and length 32 (0x20)
            multihash = b'\x12\x20' + hash_bytes
            return base58.b58encode(multihash, alphabet=base58.BITCOIN_ALPHABET).decode('ascii')
        except Exception as e:
            self.log(f"⚠️  Error generating CID for {block_hash}: {e}")
            return None
    
    def is_old_cid_format(self, cid):
        """Check if CID is in the old invalid format"""
        if not cid or not cid.startswith('Qm'):
            return False
        
        # Old format: Qm + 44 hex characters
        if len(cid) == 46 and cid[2:].isalnum():
            try:
                # Try to decode as hex (old format)
                int(cid[2:], 16)
                return True
            except ValueError:
                return False
        
        return False
    
    def get_latest_block_height(self):
        """Get the latest block height from the server"""
        try:
            response = requests.get(f"{self.api_url}/v1/data/block/latest", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {}).get('index', 0)
            else:
                self.log(f"❌ Error getting latest block: {response.status_code}")
                return 0
        except Exception as e:
            self.log(f"❌ Error connecting to server: {e}")
            return 0
    
    def get_block_data(self, height):
        """Get block data from server"""
        try:
            response = requests.get(f"{self.api_url}/v1/data/block/{height}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get('data', {})
            else:
                return None
        except Exception as e:
            self.log(f"⚠️  Error getting block {height}: {e}")
            return None
    
    def update_server_cids(self, max_blocks=1000):
        """Update CIDs on the server by re-ingesting blocks with new CIDs"""
        self.log("🔄 Starting server CID update...")
        
        # Get latest block height
        latest_height = self.get_latest_block_height()
        if latest_height == 0:
            self.log("❌ Could not get latest block height")
            return False
        
        self.log(f"📊 Latest block height: {latest_height}")
        
        # Process blocks in batches
        start_height = max(1, latest_height - max_blocks + 1)
        self.log(f"📊 Processing blocks {start_height} to {latest_height}")
        
        updated_count = 0
        skipped_count = 0
        
        for height in range(start_height, latest_height + 1):
            try:
                block_data = self.get_block_data(height)
                if not block_data:
                    continue
                
                current_cid = block_data.get('cid', '')
                block_hash = block_data.get('hash', '')
                
                # Check if CID needs updating
                if self.is_old_cid_format(current_cid):
                    # Generate new valid CID
                    new_cid = self.generate_valid_cid(block_hash)
                    
                    if new_cid:
                        # Create updated block data for re-ingestion
                        updated_block_data = block_data.copy()
                        updated_block_data['cid'] = new_cid
                        
                        # Re-ingest the block with new CID
                        try:
                            response = requests.post(
                                f"{self.api_url}/v1/ingest/block",
                                json=updated_block_data,
                                timeout=10
                            )
                            
                            if response.status_code == 200:
                                updated_count += 1
                                self.log(f"✅ Updated block {height}: {current_cid} → {new_cid}")
                            else:
                                self.log(f"⚠️  Failed to update block {height}: HTTP {response.status_code}")
                                skipped_count += 1
                        except Exception as e:
                            self.log(f"⚠️  Error re-ingesting block {height}: {e}")
                            skipped_count += 1
                    else:
                        skipped_count += 1
                else:
                    skipped_count += 1
                
                # Progress indicator
                if height % 100 == 0:
                    self.log(f"📊 Processed {height - start_height + 1} blocks...")
                
                # Small delay to avoid overwhelming the server
                time.sleep(0.1)
                
            except Exception as e:
                self.log(f"⚠️  Error processing block {height}: {e}")
                skipped_count += 1
                continue
        
        self.log("✅ Server CID update completed!")
        self.log(f"📊 Blocks updated: {updated_count}")
        self.log(f"📊 Blocks skipped: {skipped_count}")
        
        return True

def main():
    """Main function"""
    print("🔄 COINjecture Server CID Updater")
    print("=" * 50)
    
    # Create updater
    updater = ServerCIDUpdater()
    
    # Update CIDs
    success = updater.update_server_cids(max_blocks=1000)
    
    if success:
        print("\n✅ Server CID update completed successfully!")
        print("🎯 All updated blocks now have valid base58btc CIDs")
        print("🚀 Ready for fresh Kaggle export!")
    else:
        print("\n❌ Server CID update failed!")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
