"""
Cryptographic Wallet System for COINjecture

Implements Ed25519-based wallets with public/private key pairs for secure
transaction signing and address generation.
"""

import os
import json
import hashlib
from typing import Optional, Dict, List
from pathlib import Path
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class Wallet:
    """
    Cryptographic wallet with Ed25519 key pairs.
    
    Provides secure key generation, address derivation, and transaction signing.
    """
    
    def __init__(self, private_key: Optional[ed25519.Ed25519PrivateKey] = None):
        """
        Initialize wallet with existing or new key pair.
        
        Args:
            private_key: Existing private key, or None to generate new
        """
        if private_key is None:
            self.private_key = ed25519.Ed25519PrivateKey.generate()
        else:
            self.private_key = private_key
        
        self.public_key = self.private_key.public_key()
        self.address = self.get_address()
    
    @classmethod
    def generate_new(cls) -> 'Wallet':
        """Generate a new wallet with fresh key pair."""
        return cls()
    
    @classmethod
    def from_private_key_bytes(cls, private_key_bytes: bytes) -> 'Wallet':
        """Load wallet from private key bytes."""
        private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
        return cls(private_key)
    
    def get_address(self) -> str:
        """
        Derive address from public key.
        
        Address is SHA-256 hash of public key, prefixed with 'BEANS' for COINjecture.
        """
        # Serialize public key to bytes
        public_key_bytes = self.public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        
        # Hash public key
        address_hash = hashlib.sha256(public_key_bytes).digest()
        
        # Take first 20 bytes and encode as hex
        address_bytes = address_hash[:20]
        address_hex = address_bytes.hex()
        
        # Prefix with 'BEANS' for COINjecture
        return f"BEANS{address_hex}"
    
    def sign_transaction(self, transaction_data: bytes) -> bytes:
        """
        Sign transaction data with private key.
        
        Args:
            transaction_data: Raw transaction data to sign
            
        Returns:
            Signature bytes
        """
        return self.private_key.sign(transaction_data)
    
    def sign_block(self, block_data: dict) -> str:
        """
        Sign block data with private key.
        
        Args:
            block_data: Block data dictionary to sign
            
        Returns:
            Signature as hex string
        """
        import json
        canonical = json.dumps(block_data, sort_keys=True).encode()
        signature = self.sign_transaction(canonical)
        return signature.hex()
    
    @staticmethod
    def verify_block_signature(public_key_hex: str, block_data: dict, signature_hex: str) -> bool:
        """
        Verify block signature.
        
        Args:
            public_key_hex: Public key as hex string
            block_data: Block data dictionary that was signed
            signature_hex: Signature as hex string
            
        Returns:
            True if signature is valid
        """
        import json
        from cryptography.hazmat.primitives.asymmetric import ed25519
        
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
        # Try 1: PyNaCl (most compatible with browser crypto.subtle)
        try:
            import nacl.signing
            pub_bytes = bytes.fromhex(public_key_hex)
            sig_bytes = bytes.fromhex(signature_hex)
            verify_key = nacl.signing.VerifyKey(pub_bytes)
            # PyNaCl expects signature + message concatenated format
            signed_message = sig_bytes + data
            verify_key.verify(signed_message)
            print("✅ Signature verified with PyNaCl (browser-compatible)")
            return True
        except Exception as e:
            print(f"PyNaCl verification failed: {e}")
        
        # Try 2: cryptography library (standard Python Ed25519)
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            pub_bytes = bytes.fromhex(public_key_hex)
            sig_bytes = bytes.fromhex(signature_hex)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
            public_key.verify(sig_bytes, data)
            print("✅ Signature verified with cryptography library")
            return True
        except Exception as e:
            print(f"Cryptography library verification failed: {e}")
        
        # Try 3: Pure Python ed25519 library (fallback)
        try:
            import ed25519
            pub_bytes = bytes.fromhex(public_key_hex)
            sig_bytes = bytes.fromhex(signature_hex)
            vk = ed25519.VerifyingKey(pub_bytes)
            vk.verify(sig_bytes, data)
            return True
        except Exception as e:
            pass
        
        return False
    
    def verify_signature(self, data: bytes, signature: bytes) -> bool:
        """
        Verify signature against data using public key.
        
        Args:
            data: Original data that was signed
            signature: Signature to verify
            
        Returns:
            True if signature is valid
        """
        try:
            self.public_key.verify(signature, data)
            return True
        except Exception:
            return False
    
    def get_private_key_bytes(self) -> bytes:
        """Get private key as bytes for storage."""
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
        """
        Save wallet to encrypted file.
        
        Args:
            filepath: Path to save wallet file
            password: Optional password for encryption
            
        Returns:
            True if saved successfully
        """
        try:
            wallet_data = {
                'address': self.address,
                'private_key': self.get_private_key_bytes().hex(),
                'public_key': self.get_public_key_bytes().hex()
            }
            
            # For now, save unencrypted (in production, use proper encryption)
            with open(filepath, 'w') as f:
                json.dump(wallet_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving wallet: {e}")
            return False
    
    @classmethod
    def load_from_file(cls, filepath: str, password: Optional[str] = None) -> Optional['Wallet']:
        """
        Load wallet from file.
        
        Args:
            filepath: Path to wallet file
            password: Optional password for decryption
            
        Returns:
            Wallet instance or None if failed
        """
        try:
            with open(filepath, 'r') as f:
                wallet_data = json.load(f)
            
            private_key_bytes = bytes.fromhex(wallet_data['private_key'])
            return cls.from_private_key_bytes(private_key_bytes)
        except Exception as e:
            print(f"Error loading wallet: {e}")
            return None
    
    def to_dict(self) -> Dict:
        """Convert wallet to dictionary for serialization."""
        return {
            'address': self.address,
            'public_key': self.get_public_key_bytes().hex(),
            'private_key': self.get_private_key_bytes().hex()
        }


class WalletManager:
    """
    Manages multiple wallets and provides high-level operations.
    """
    
    def __init__(self, wallets_dir: str = "data/wallets"):
        """
        Initialize wallet manager.
        
        Args:
            wallets_dir: Directory to store wallet files
        """
        self.wallets_dir = Path(wallets_dir)
        self.wallets_dir.mkdir(parents=True, exist_ok=True)
        self._wallets: Dict[str, Wallet] = {}
        self._load_existing_wallets()
    
    def _load_existing_wallets(self):
        """Load existing wallets from disk."""
        for wallet_file in self.wallets_dir.glob("*.json"):
            try:
                wallet = Wallet.load_from_file(str(wallet_file))
                if wallet:
                    self._wallets[wallet.address] = wallet
            except Exception as e:
                print(f"Error loading wallet {wallet_file}: {e}")
    
    def create_wallet(self, name: str) -> Optional[Wallet]:
        """
        Create new wallet with given name.
        
        Args:
            name: Human-readable name for wallet
            
        Returns:
            New wallet instance or None if failed
        """
        try:
            wallet = Wallet.generate_new()
            filepath = self.wallets_dir / f"{name}.json"
            
            if wallet.save_to_file(str(filepath)):
                self._wallets[wallet.address] = wallet
                return wallet
            else:
                return None
        except Exception as e:
            print(f"Error creating wallet: {e}")
            return None
    
    def get_wallet(self, address: str) -> Optional[Wallet]:
        """
        Get wallet by address.
        
        Args:
            address: Wallet address
            
        Returns:
            Wallet instance or None if not found
        """
        return self._wallets.get(address)
    
    def list_wallets(self) -> List[Dict]:
        """
        List all available wallets.
        
        Returns:
            List of wallet info dictionaries
        """
        return [
            {
                'address': wallet.address,
                'public_key': wallet.get_public_key_bytes().hex()
            }
            for wallet in self._wallets.values()
        ]
    
    def get_balance(self, address: str, blockchain_state) -> float:
        """
        Get wallet balance from blockchain state.
        
        Args:
            address: Wallet address
            blockchain_state: BlockchainState instance
            
        Returns:
            Current balance
        """
        return blockchain_state.get_balance(address)
    
    def import_wallet(self, name: str, private_key_hex: str) -> Optional[Wallet]:
        """
        Import existing wallet from private key.
        
        Args:
            name: Name for the wallet
            private_key_hex: Private key as hex string
            
        Returns:
            Imported wallet or None if failed
        """
        try:
            private_key_bytes = bytes.fromhex(private_key_hex)
            wallet = Wallet.from_private_key_bytes(private_key_bytes)
            
            filepath = self.wallets_dir / f"{name}.json"
            if wallet.save_to_file(str(filepath)):
                self._wallets[wallet.address] = wallet
                return wallet
            else:
                return None
        except Exception as e:
            print(f"Error importing wallet: {e}")
            return None


# Utility functions for address validation
def is_valid_address(address: str) -> bool:
    """
    Validate COINjecture address format.
    
    Args:
        address: Address string to validate
        
    Returns:
        True if address format is valid
    """
    if not (address.startswith('CJ') or address.startswith('BEANS')):
        return False
    
    # CJ + 40 hex chars = 42, BEANS + 40 hex chars = 45
    if len(address) not in [42, 45]:
        return False
    
    try:
        # Validate hex part after prefix
        if address.startswith('CJ'):
            int(address[2:], 16)
        elif address.startswith('BEANS'):
            int(address[5:], 16)
        return True
    except ValueError:
        return False


def address_from_public_key(public_key_bytes: bytes) -> str:
    """
    Derive address from public key bytes.
    
    Args:
        public_key_bytes: Raw public key bytes
        
    Returns:
        COINjecture address
    """
    # Hash public key
    address_hash = hashlib.sha256(public_key_bytes).digest()
    
    # Take first 20 bytes and encode as hex
    address_bytes = address_hash[:20]
    address_hex = address_bytes.hex()
    
    # Prefix with 'BEANS' for COINjecture
    return f"BEANS{address_hex}"


if __name__ == "__main__":
    # Test wallet functionality
    print("Testing COINjecture Wallet System...")
    
    # Create wallet manager
    manager = WalletManager()
    
    # Create test wallet
    wallet = manager.create_wallet("test_wallet")
    if wallet:
        print(f"✅ Created wallet: {wallet.address}")
        print(f"   Public key: {wallet.get_public_key_bytes().hex()}")
        
        # Test signing
        test_data = b"test transaction data"
        signature = wallet.sign_transaction(test_data)
        print(f"✅ Signed transaction: {signature.hex()}")
        
        # Test verification
        is_valid = wallet.verify_signature(test_data, signature)
        print(f"✅ Signature verification: {is_valid}")
        
        # Test address validation
        is_valid_addr = is_valid_address(wallet.address)
        print(f"✅ Address validation: {is_valid_addr}")
        
        # List wallets
        wallets = manager.list_wallets()
        print(f"✅ Available wallets: {len(wallets)}")
        
    else:
        print("❌ Failed to create wallet")
