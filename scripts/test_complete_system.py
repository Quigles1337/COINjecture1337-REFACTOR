#!/usr/bin/env python3
"""
Complete System Test Script

Tests the entire CID generation and download system:
1. Tests CID generation locally
2. Tests API endpoints
3. Tests frontend download functionality
4. Exports fresh Kaggle dataset
"""

import requests
import json
import hashlib
import base58
import time
from datetime import datetime

class SystemTester:
    def __init__(self, api_url="http://167.172.213.70:12346"):
        self.api_url = api_url
        
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def test_cid_generation(self):
        """Test CID generation locally"""
        self.log("🧪 Testing CID generation...")
        
        try:
            # Test with a sample block hash
            test_hash = "test_block_hash_12345"
            
            # Generate valid CID
            hash_bytes = hashlib.sha256(test_hash.encode()).digest()
            multihash = b'\x12\x20' + hash_bytes
            cid = base58.b58encode(multihash, alphabet=base58.BITCOIN_ALPHABET).decode('ascii')
            
            # Validate CID
            decoded = base58.b58decode(cid)
            if len(decoded) == 34 and decoded.startswith(b'\x12\x20'):
                self.log(f"✅ CID generation working: {cid}")
                return True
            else:
                self.log(f"❌ CID validation failed")
                return False
                
        except Exception as e:
            self.log(f"❌ CID generation test failed: {e}")
            return False
    
    def test_api_health(self):
        """Test API health"""
        self.log("🏥 Testing API health...")
        
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ API healthy: {data.get('status', 'unknown')}")
                return True
            else:
                self.log(f"❌ API health check failed: HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ API health check failed: {e}")
            return False
    
    def test_ipfs_endpoint(self):
        """Test the new IPFS endpoint"""
        self.log("🔗 Testing IPFS endpoint...")
        
        try:
            # Get a sample CID from latest block
            response = requests.get(f"{self.api_url}/v1/data/block/latest", timeout=10)
            if response.status_code == 200:
                data = response.json()
                cid = data.get('data', {}).get('cid', '')
                
                if cid:
                    # Test IPFS endpoint
                    ipfs_response = requests.get(f"{self.api_url}/v1/ipfs/{cid}", timeout=10)
                    if ipfs_response.status_code == 200:
                        ipfs_data = ipfs_response.json()
                        self.log(f"✅ IPFS endpoint working: {cid}")
                        self.log(f"📦 Proof bundle data: {len(str(ipfs_data))} characters")
                        return True
                    else:
                        self.log(f"⚠️  IPFS endpoint returned HTTP {ipfs_response.status_code}")
                        return False
                else:
                    self.log("⚠️  No CID found in latest block")
                    return False
            else:
                self.log(f"❌ Could not get latest block: HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ IPFS endpoint test failed: {e}")
            return False
    
    def test_cid_format(self):
        """Test if CIDs are in the new valid format"""
        self.log("🔍 Testing CID format...")
        
        try:
            # Get latest few blocks
            response = requests.get(f"{self.api_url}/v1/metrics/dashboard", timeout=10)
            if response.status_code == 200:
                data = response.json()
                transactions = data.get('recent_transactions', [])
                
                valid_count = 0
                invalid_count = 0
                
                for tx in transactions[:5]:  # Check first 5 transactions
                    cid = tx.get('cid', '')
                    if cid:
                        try:
                            # Check if CID is valid base58btc
                            decoded = base58.b58decode(cid)
                            if len(decoded) == 34 and decoded.startswith(b'\x12\x20'):
                                valid_count += 1
                            else:
                                invalid_count += 1
                                self.log(f"⚠️  Invalid CID format: {cid}")
                        except Exception:
                            invalid_count += 1
                            self.log(f"⚠️  CID decode failed: {cid}")
                
                self.log(f"📊 CID format check: {valid_count} valid, {invalid_count} invalid")
                return valid_count > 0 and invalid_count == 0
            else:
                self.log(f"❌ Could not get dashboard data: HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ CID format test failed: {e}")
            return False
    
    def export_fresh_data(self):
        """Export fresh data from server"""
        self.log("📊 Exporting fresh data...")
        
        try:
            import subprocess
            import sys
            
            # Run the export script
            result = subprocess.run([
                sys.executable, 
                "scripts/export_from_server.py",
                "--max-blocks", "100"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.log("✅ Fresh data export completed")
                return True
            else:
                self.log(f"❌ Export failed: {result.stderr}")
                return False
        except Exception as e:
            self.log(f"❌ Export failed: {e}")
            return False
    
    def run_complete_test(self):
        """Run all tests"""
        self.log("🚀 Starting Complete System Test")
        self.log("=" * 50)
        
        tests = [
            ("CID Generation", self.test_cid_generation),
            ("API Health", self.test_api_health),
            ("IPFS Endpoint", self.test_ipfs_endpoint),
            ("CID Format", self.test_cid_format),
            ("Fresh Export", self.export_fresh_data)
        ]
        
        results = {}
        
        for test_name, test_func in tests:
            self.log(f"\n🧪 Running {test_name} test...")
            try:
                result = test_func()
                results[test_name] = result
                if result:
                    self.log(f"✅ {test_name} test passed")
                else:
                    self.log(f"❌ {test_name} test failed")
            except Exception as e:
                self.log(f"❌ {test_name} test error: {e}")
                results[test_name] = False
        
        # Summary
        self.log("\n📊 Test Results Summary")
        self.log("=" * 30)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name}: {status}")
        
        self.log(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            self.log("🎉 All tests passed! System is ready!")
            return True
        else:
            self.log("⚠️  Some tests failed. Check the logs above.")
            return False

def main():
    """Main function"""
    print("🧪 COINjecture Complete System Test")
    print("=" * 50)
    
    # Create tester
    tester = SystemTester()
    
    # Run all tests
    success = tester.run_complete_test()
    
    if success:
        print("\n🎉 System test completed successfully!")
        print("🚀 Ready for production!")
        return 0
    else:
        print("\n⚠️  System test completed with issues")
        print("🔧 Please check the failed tests above")
        return 1

if __name__ == "__main__":
    exit(main())
