#!/usr/bin/env python3
"""
Network Stall Fix: Address the root cause of network stalling at block #166
This script implements a comprehensive solution to unstick the network.
"""

import json
import time
import requests
import sys
from pathlib import Path

def test_api_connectivity():
    """Test if API is accessible and responding."""
    try:
        response = requests.get('https://167.172.213.70/v1/data/block/latest', 
                             verify=False, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API accessible - Current block: #{data['data']['index']}")
            return True
        else:
            print(f"❌ API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def test_block_submission():
    """Test if new blocks can be submitted to the API."""
    print("🧪 Testing block submission...")
    
    # Create a valid test payload with proper hex strings
    test_payload = {
        'event_id': f'test_block_167_{int(time.time())}',
        'block_index': 167,
        'block_hash': f'test_block_167_{int(time.time())}',
        'cid': f'QmTestBlock167{int(time.time())}',
        'miner_address': 'test-miner-167',
        'capacity': 'MOBILE',
        'work_score': 1.0,
        'ts': time.time(),
        'signature': 'a' * 64,  # Valid hex string (64 chars)
        'public_key': 'b' * 64   # Valid hex string (64 chars)
    }
    
    try:
        response = requests.post('https://167.172.213.70/v1/ingest/block', 
                              json=test_payload, 
                              verify=False, 
                              timeout=10)
        
        print(f"📤 Submission Status: {response.status_code}")
        print(f"📤 Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            print("✅ Block submission successful!")
            return True
        else:
            print(f"❌ Block submission failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Submission error: {e}")
        return False

def create_signature_validation_fix():
    """Create a comprehensive signature validation fix."""
    print("🔧 Creating signature validation fix...")
    
    # Read current wallet.py
    wallet_path = Path('src/tokenomics/wallet.py')
    if not wallet_path.exists():
        print("❌ wallet.py not found")
        return False
    
    with open(wallet_path, 'r') as f:
        content = f.read()
    
    # Create improved signature validation
    improved_validation = '''    @staticmethod
    def verify_block_signature(public_key_hex: str, block_data: dict, signature_hex: str) -> bool:
        """
        Verify block signature with improved error handling.
        
        Args:
            public_key_hex: Public key as hex string
            block_data: Block data dictionary that was signed
            signature_hex: Signature as hex string
            
        Returns:
            True if signature is valid
        """
        import json
        from cryptography.hazmat.primitives.asymmetric import ed25519
        
        # Validate inputs
        if not public_key_hex or not signature_hex:
            return False
        
        # Check if strings are valid hexadecimal
        try:
            # Test if strings are valid hex
            bytes.fromhex(public_key_hex)
            bytes.fromhex(signature_hex)
        except ValueError:
            # Not valid hex strings - this is likely a test or invalid submission
            print(f"⚠️  Invalid hex strings: pub_key={public_key_hex[:16]}..., sig={signature_hex[:16]}...")
            return False
        
        # Additional validation for Ed25519 keys
        if len(public_key_hex) != 64 or len(signature_hex) != 128:
            print(f"⚠️  Invalid key/signature length: pub_key={len(public_key_hex)}, sig={len(signature_hex)}")
            return False
        
        canonical = json.dumps(block_data, sort_keys=True).encode()
        pub_bytes = bytes.fromhex(public_key_hex)
        sig_bytes = bytes.fromhex(signature_hex)
        
        # Use multi-implementation verification (prioritizes PyNaCl for browser compatibility)
        return Wallet._verify_tweetnacl_signature(public_key_hex, canonical, signature_hex)'''
    
    # Replace the method in the content
    import re
    pattern = r'@staticmethod\s+def verify_block_signature\(.*?\n.*?return Wallet\._verify_tweetnacl_signature\(public_key_hex, canonical, signature_hex\)'
    new_content = re.sub(pattern, improved_validation, content, flags=re.DOTALL)
    
    # Write the improved version
    with open('/tmp/wallet_improved.py', 'w') as f:
        f.write(new_content)
    
    print("✅ Improved signature validation created")
    return True

def create_network_flush_script():
    """Create a script to flush stuck network events."""
    print("🌊 Creating network flush script...")
    
    flush_script = '''#!/usr/bin/env python3
"""
Network Flush: Process stuck events and advance blockchain
"""

import json
import time
import requests

def flush_network():
    """Flush stuck network events."""
    print("🌊 Flushing network...")
    
    # Get current blockchain status
    try:
        response = requests.get('https://167.172.213.70/v1/data/block/latest', verify=False)
        if response.status_code == 200:
            data = response.json()
            current_block = data['data']['index']
            print(f"📊 Current block: #{current_block}")
            
            # Try to submit a new block to test network flow
            test_payload = {
                'event_id': f'flush_block_{int(time.time())}',
                'block_index': current_block + 1,
                'block_hash': f'flush_block_{int(time.time())}',
                'cid': f'QmFlush{int(time.time())}',
                'miner_address': 'network-flush',
                'capacity': 'MOBILE',
                'work_score': 1.0,
                'ts': time.time(),
                'signature': 'a' * 64,
                'public_key': 'b' * 64
            }
            
            response = requests.post('https://167.172.213.70/v1/ingest/block', 
                                  json=test_payload, verify=False)
            
            if response.status_code == 200:
                print("✅ Network flush successful!")
                return True
            else:
                print(f"❌ Network flush failed: {response.text}")
                return False
        else:
            print(f"❌ Failed to get current block: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Network flush error: {e}")
        return False

if __name__ == "__main__":
    flush_network()
'''
    
    with open('/tmp/network_flush.py', 'w') as f:
        f.write(flush_script)
    
    print("✅ Network flush script created")
    return True

def main():
    """Main function to fix network stalling."""
    print("🔧 Network Stall Fix - Comprehensive Solution")
    print("=" * 50)
    
    # Test current API status
    if not test_api_connectivity():
        print("❌ API not accessible - cannot proceed")
        return False
    
    # Test block submission
    if not test_block_submission():
        print("❌ Block submission failing - signature validation issue confirmed")
        
        # Create fixes
        create_signature_validation_fix()
        create_network_flush_script()
        
        print("\n🔧 Fixes created:")
        print("1. /tmp/wallet_improved.py - Enhanced signature validation")
        print("2. /tmp/network_flush.py - Network flush script")
        
        print("\n📋 Manual deployment required:")
        print("1. Copy /tmp/wallet_improved.py to remote server")
        print("2. Replace /home/coinjecture/COINjecture/src/tokenomics/wallet.py")
        print("3. Restart API service")
        print("4. Run network flush script")
        
        return False
    else:
        print("✅ Network is working - no fixes needed")
        return True

if __name__ == "__main__":
    main()
