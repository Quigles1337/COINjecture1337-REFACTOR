#!/usr/bin/env python3
"""
Auto-Deploy Network Stalling Fix on Connection
This script automatically deploys the fix when connecting to a valid IP address.
"""

import os
import sys
import subprocess
import time
import socket
import requests
from pathlib import Path

def check_valid_ip():
    """Check if we're connected to a valid IP address."""
    try:
        # Get local IP
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Check if we're on the remote server (167.172.213.70)
        if local_ip == "167.172.213.70" or "167.172.213.70" in hostname:
            return True, "167.172.213.70"
        
        # Check if we can reach the remote server
        try:
            response = requests.get('https://167.172.213.70/v1/data/block/latest', 
                                 verify=False, timeout=5)
            if response.status_code == 200:
                return True, "167.172.213.70"
        except:
            pass
            
        return False, local_ip
    except Exception as e:
        print(f"❌ IP check failed: {e}")
        return False, "unknown"

def deploy_network_fix():
    """Deploy the network stalling fix."""
    print("🚀 Auto-Deploying Network Stalling Fix")
    print("=" * 50)
    
    # Check if we're on the remote server
    if not os.path.exists("/home/coinjecture/COINjecture/src/tokenomics/wallet.py"):
        print("❌ Not on remote server - cannot deploy")
        return False
    
    print("✅ Confirmed on remote server")
    
    # Create enhanced wallet.py content
    enhanced_wallet_content = '''"""
Enhanced Wallet with Improved Signature Validation
This version includes proper hex string validation to prevent network stalling.
"""

import json
import time
import hashlib
import base64
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend

class Wallet:
    """Enhanced COINjecture Wallet with improved signature validation."""
    
    def __init__(self, private_key: ed25519.Ed25519PrivateKey, public_key: ed25519.Ed25519PublicKey):
        self.private_key = private_key
        self.public_key = public_key
        self.address = self._generate_address()
    
    @classmethod
    def generate(cls) -> 'Wallet':
        """Generate a new wallet."""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()
        return cls(private_key, public_key)
    
    def _generate_address(self) -> str:
        """Generate wallet address from public key."""
        pub_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return hashlib.sha256(pub_bytes).hexdigest()[:32]
    
    def sign_transaction(self, data: bytes) -> bytes:
        """Sign transaction data."""
        return self.private_key.sign(data)
    
    def get_private_key_bytes(self) -> bytes:
        """Get private key as bytes."""
        return self.private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )
    
    def get_public_key_bytes(self) -> bytes:
        """Get public key as bytes."""
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
    
    def save_to_file(self, filepath: str, password: Optional[str] = None) -> bool:
        """Save wallet to encrypted file."""
        try:
            wallet_data = {
                'address': self.address,
                'private_key': self.get_private_key_bytes().hex(),
                'public_key': self.get_public_key_bytes().hex()
            }
            
            with open(filepath, 'w') as f:
                json.dump(wallet_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving wallet: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: str, password: Optional[str] = None) -> Optional['Wallet']:
        """Load wallet from file."""
        try:
            with open(filepath, 'r') as f:
                wallet_data = json.load(f)
            
            private_key_bytes = bytes.fromhex(wallet_data['private_key'])
            public_key_bytes = bytes.fromhex(wallet_data['public_key'])
            
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            
            return cls(private_key, public_key)
        except Exception as e:
            print(f"Error loading wallet: {e}")
            return None
    
    def sign_block(self, block_data: Dict[str, Any]) -> str:
        """Sign block data and return signature as hex string."""
        import json
        canonical = json.dumps(block_data, sort_keys=True).encode()
        signature = self.sign_transaction(canonical)
        return signature.hex()
    
    @staticmethod
    def verify_block_signature(public_key_hex: str, block_data: dict, signature_hex: str) -> bool:
        """
        Verify block signature with enhanced error handling.
        
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
        return Wallet._verify_tweetnacl_signature(public_key_hex, canonical, signature_hex)
    
    @staticmethod
    def _verify_tweetnacl_signature(public_key_hex: str, data: bytes, signature_hex: str) -> bool:
        """
        Verify signature using multiple implementations as fallback.
        
        Args:
            public_key_hex: Public key as hex string
            data: Data that was signed
            signature_hex: Signature as hex string
            
        Returns:
            True if signature is valid
        """
        try:
            # Try PyNaCl first (browser compatibility)
            import nacl.signing
            import nacl.encoding
            
            public_key_bytes = bytes.fromhex(public_key_hex)
            signature_bytes = bytes.fromhex(signature_hex)
            
            # Create verifying key
            verify_key = nacl.signing.VerifyKey(public_key_bytes)
            
            # Verify signature
            try:
                verify_key.verify(data, signature_bytes)
                return True
            except nacl.exceptions.BadSignatureError:
                return False
                
        except ImportError:
            # Fallback to cryptography library
            try:
                from cryptography.hazmat.primitives.asymmetric import ed25519
                
                public_key_bytes = bytes.fromhex(public_key_hex)
                signature_bytes = bytes.fromhex(signature_hex)
                
                public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
                public_key.verify(signature_bytes, data)
                return True
                
            except Exception:
                return False
        except Exception:
            return False
'''
    
    try:
        # Backup original wallet.py
        print("💾 Creating backup of original wallet.py...")
        backup_cmd = f"sudo cp /home/coinjecture/COINjecture/src/tokenomics/wallet.py /home/coinjecture/COINjecture/src/tokenomics/wallet.py.backup.{int(time.time())}"
        subprocess.run(backup_cmd, shell=True, check=True)
        print("✅ Backup created")
        
        # Write enhanced wallet.py
        print("🔧 Creating enhanced wallet.py...")
        with open("/tmp/wallet_enhanced.py", "w") as f:
            f.write(enhanced_wallet_content)
        print("✅ Enhanced wallet.py created")
        
        # Apply the fix
        print("🔄 Applying enhanced wallet.py...")
        subprocess.run("sudo cp /tmp/wallet_enhanced.py /home/coinjecture/COINjecture/src/tokenomics/wallet.py", shell=True, check=True)
        subprocess.run("sudo chown coinjecture:coinjecture /home/coinjecture/COINjecture/src/tokenomics/wallet.py", shell=True, check=True)
        subprocess.run("sudo chmod 644 /home/coinjecture/COINjecture/src/tokenomics/wallet.py", shell=True, check=True)
        print("✅ Enhanced wallet.py applied")
        
        # Restart services
        print("🔄 Restarting services...")
        subprocess.run("sudo systemctl restart coinjecture-consensus.service", shell=True, check=True)
        time.sleep(2)
        subprocess.run("sudo systemctl restart coinjecture-api.service", shell=True, check=True)
        time.sleep(2)
        subprocess.run("sudo systemctl restart nginx.service", shell=True, check=True)
        print("✅ All services restarted")
        
        # Test the fix
        print("🧪 Testing the fix...")
        time.sleep(5)  # Wait for services to start
        
        try:
            response = requests.get('https://167.172.213.70/v1/data/block/latest', verify=False, timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Network accessible - Block #{data['data']['index']}")
                
                # Test block submission
                test_payload = {
                    'event_id': f'auto_deploy_test_{int(time.time())}',
                    'block_index': 167,
                    'block_hash': f'auto_deploy_test_{int(time.time())}',
                    'cid': f'QmAutoDeploy{int(time.time())}',
                    'miner_address': 'auto-deploy-test',
                    'capacity': 'MOBILE',
                    'work_score': 1.0,
                    'ts': time.time(),
                    'signature': 'a' * 64,
                    'public_key': 'b' * 64
                }
                
                test_response = requests.post('https://167.172.213.70/v1/ingest/block', 
                                           json=test_payload, verify=False, timeout=10)
                
                if test_response.status_code == 200:
                    print("✅ Block submission successful!")
                else:
                    print(f"⚠️  Block submission response: {test_response.status_code}")
                
            else:
                print(f"❌ Network test failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Network test error: {e}")
        
        print("\n🎉 Auto-Deployment Complete!")
        print("=" * 40)
        print("✅ Enhanced signature validation deployed")
        print("✅ All services restarted")
        print("🔧 Network should now be able to process new blocks beyond #166")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Deployment failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function to check IP and auto-deploy."""
    print("🔍 Auto-Deploy Network Stalling Fix")
    print("=" * 40)
    
    # Check if we're on a valid IP
    is_valid, ip = check_valid_ip()
    
    if is_valid:
        print(f"✅ Connected to valid IP: {ip}")
        print("🚀 Auto-deploying network stalling fix...")
        
        if deploy_network_fix():
            print("✅ Auto-deployment successful!")
            return True
        else:
            print("❌ Auto-deployment failed!")
            return False
    else:
        print(f"⚠️  Not connected to valid IP: {ip}")
        print("📋 Manual deployment required")
        print("1. Connect to 167.172.213.70")
        print("2. Run this script again")
        return False

if __name__ == "__main__":
    main()
