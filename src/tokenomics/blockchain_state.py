"""
Blockchain State Management for COINjecture

Manages balances, transaction pool, and transaction history for the blockchain.
"""

import time
import hashlib
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class Transaction:
    """
    Enhanced Transaction class with cryptographic signatures.
    """
    sender: str
    recipient: str
    amount: float
    timestamp: float
    transaction_id: str = ""
    signature: str = ""
    public_key: str = ""
    
    def __post_init__(self):
        """Calculate transaction ID after initialization."""
        if not self.transaction_id:
            self.transaction_id = self.calculate_transaction_id()
    
    def calculate_transaction_id(self) -> str:
        """Calculate unique transaction ID from transaction data."""
        # Create hash of transaction data (excluding signature and public_key)
        data = f"{self.sender}{self.recipient}{self.amount}{self.timestamp}".encode()
        return hashlib.sha256(data).hexdigest()
    
    def sign(self, private_key_bytes: bytes) -> str:
        """
        Sign transaction with private key.
        
        Args:
            private_key_bytes: Private key as bytes
            
        Returns:
            Signature as hex string
        """
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            from cryptography.hazmat.primitives import serialization
            
            # Load private key
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
            
            # Get public key for storage
            public_key = private_key.public_key()
            self.public_key = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            ).hex()
            
            # Sign transaction data
            transaction_data = f"{self.sender}{self.recipient}{self.amount}{self.timestamp}".encode()
            signature = private_key.sign(transaction_data)
            self.signature = signature.hex()
            
            return self.signature
        except Exception as e:
            print(f"Error signing transaction: {e}")
            return ""
    
    def verify_signature(self) -> bool:
        """
        Verify transaction signature.
        
        Returns:
            True if signature is valid
        """
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            from cryptography.hazmat.primitives import serialization
            
            if not self.signature or not self.public_key:
                return False
            
            # Load public key
            public_key_bytes = bytes.fromhex(self.public_key)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            
            # Verify signature
            transaction_data = f"{self.sender}{self.recipient}{self.amount}{self.timestamp}".encode()
            signature_bytes = bytes.fromhex(self.signature)
            
            public_key.verify(signature_bytes, transaction_data)
            return True
        except Exception:
            return False
    
    def to_dict(self) -> Dict:
        """Convert transaction to dictionary for serialization."""
        return {
            'transaction_id': self.transaction_id,
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp,
            'signature': self.signature,
            'public_key': self.public_key
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Transaction':
        """Create transaction from dictionary."""
        tx = cls(
            sender=data['sender'],
            recipient=data['recipient'],
            amount=data['amount'],
            timestamp=data['timestamp'],
            transaction_id=data.get('transaction_id', ''),
            signature=data.get('signature', ''),
            public_key=data.get('public_key', '')
        )
        return tx
    
    def __str__(self):
        return f"Transaction {self.transaction_id[:8]}...: {self.sender} -> {self.recipient} ({self.amount})"


class BlockchainState:
    """
    Manages blockchain state including balances, transaction pool, and history.
    """
    
    def __init__(self):
        """Initialize blockchain state."""
        # Address balances
        self.balances: Dict[str, float] = defaultdict(float)
        
        # Transaction pool (pending transactions)
        self.pending_transactions: List[Transaction] = []
        
        # Transaction history by address
        self.transaction_history: Dict[str, List[Transaction]] = defaultdict(list)
        
        # Set of processed transaction IDs to prevent double-spending
        self.processed_transactions: Set[str] = set()
        
        # Genesis block reward address (if any)
        self.genesis_address: Optional[str] = None
    
    def update_balance(self, address: str, amount: float) -> bool:
        """
        Update address balance.
        
        Args:
            address: Wallet address
            amount: Amount to add (positive) or subtract (negative)
            
        Returns:
            True if successful
        """
        try:
            self.balances[address] += amount
            return True
        except Exception as e:
            print(f"Error updating balance: {e}")
            return False
    
    def get_balance(self, address: str) -> float:
        """
        Get current balance for address.
        
        Args:
            address: Wallet address
            
        Returns:
            Current balance
        """
        return self.balances.get(address, 0.0)
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """
        Add transaction to pending pool.
        
        Args:
            transaction: Transaction to add
            
        Returns:
            True if added successfully
        """
        try:
            # Validate transaction
            if not self.validate_transaction(transaction):
                return False
            
            # Check if already in pool
            if any(tx.transaction_id == transaction.transaction_id for tx in self.pending_transactions):
                return False
            
            # Add to pending pool
            self.pending_transactions.append(transaction)
            return True
        except Exception as e:
            print(f"Error adding transaction: {e}")
            return False
    
    def validate_transaction(self, transaction: Transaction) -> bool:
        """
        Validate transaction.
        
        Args:
            transaction: Transaction to validate
            
        Returns:
            True if valid
        """
        try:
            # Check if already processed
            if transaction.transaction_id in self.processed_transactions:
                return False
            
            # Verify signature (skip for coinbase transactions)
            if transaction.sender != "COINBASE" and not transaction.verify_signature():
                return False
            
            # Check sender has sufficient balance (skip for coinbase)
            if transaction.sender != "COINBASE":
                sender_balance = self.get_balance(transaction.sender)
                if sender_balance < transaction.amount:
                    return False
            
            # Check amount is positive
            if transaction.amount <= 0:
                return False
            
            # Check addresses are valid format
            if transaction.sender != "COINBASE" and not self._is_valid_address(transaction.sender):
                return False
            if not self._is_valid_address(transaction.recipient):
                return False
            
            return True
        except Exception as e:
            print(f"Error validating transaction: {e}")
            return False
    
    def _is_valid_address(self, address: str) -> bool:
        """Check if address format is valid."""
        return (address.startswith('CJ') or address.startswith('BEANS')) and len(address) in [42, 45]
    
    def get_pending_transactions(self, max_count: int = 100) -> List[Transaction]:
        """
        Get pending transactions for block inclusion.
        
        Args:
            max_count: Maximum number of transactions to return
            
        Returns:
            List of pending transactions
        """
        # Sort by timestamp (oldest first)
        sorted_transactions = sorted(self.pending_transactions, key=lambda tx: tx.timestamp)
        return sorted_transactions[:max_count]
    
    def process_transactions(self, transactions: List[Transaction]) -> bool:
        """
        Process transactions and update balances.
        
        Args:
            transactions: List of transactions to process
            
        Returns:
            True if all processed successfully
        """
        try:
            for transaction in transactions:
                # Update balances
                if transaction.sender != "COINBASE":
                    self.update_balance(transaction.sender, -transaction.amount)
                self.update_balance(transaction.recipient, transaction.amount)
                
                # Add to history
                self.transaction_history[transaction.sender].append(transaction)
                self.transaction_history[transaction.recipient].append(transaction)
                
                # Mark as processed
                self.processed_transactions.add(transaction.transaction_id)
            
            return True
        except Exception as e:
            print(f"Error processing transactions: {e}")
            return False
    
    def clear_pending_transactions(self, processed_transactions: List[Transaction]):
        """
        Remove processed transactions from pending pool.
        
        Args:
            processed_transactions: Transactions that were included in a block
        """
        processed_ids = {tx.transaction_id for tx in processed_transactions}
        self.pending_transactions = [
            tx for tx in self.pending_transactions 
            if tx.transaction_id not in processed_ids
        ]
    
    def get_transaction_history(self, address: str, limit: int = 100) -> List[Transaction]:
        """
        Get transaction history for address.
        
        Args:
            address: Wallet address
            limit: Maximum number of transactions to return
            
        Returns:
            List of transactions involving the address
        """
        history = self.transaction_history.get(address, [])
        # Sort by timestamp (newest first)
        sorted_history = sorted(history, key=lambda tx: tx.timestamp, reverse=True)
        return sorted_history[:limit]
    
    def get_transaction_by_id(self, transaction_id: str) -> Optional[Transaction]:
        """
        Get transaction by ID.
        
        Args:
            transaction_id: Transaction ID to search for
            
        Returns:
            Transaction if found, None otherwise
        """
        # Search in pending transactions
        for tx in self.pending_transactions:
            if tx.transaction_id == transaction_id:
                return tx
        
        # Search in history
        for address_history in self.transaction_history.values():
            for tx in address_history:
                if tx.transaction_id == transaction_id:
                    return tx
        
        return None
    
    def create_coinbase_transaction(self, recipient: str, amount: float, timestamp: float = None) -> Transaction:
        """
        Create coinbase transaction for block rewards.
        
        Args:
            recipient: Miner's address
            amount: Reward amount
            timestamp: Transaction timestamp (defaults to current time)
            
        Returns:
            Coinbase transaction
        """
        if timestamp is None:
            timestamp = time.time()
        
        return Transaction(
            sender="COINBASE",
            recipient=recipient,
            amount=amount,
            timestamp=timestamp
        )
    
    def get_total_supply(self) -> float:
        """Get total coin supply."""
        return sum(self.balances.values())
    
    def get_network_stats(self) -> Dict:
        """Get network statistics."""
        return {
            'total_addresses': len(self.balances),
            'total_supply': self.get_total_supply(),
            'pending_transactions': len(self.pending_transactions),
            'processed_transactions': len(self.processed_transactions),
            'top_balances': dict(sorted(self.balances.items(), key=lambda x: x[1], reverse=True)[:10])
        }
    
    def to_dict(self) -> Dict:
        """Convert blockchain state to dictionary for serialization."""
        return {
            'balances': dict(self.balances),
            'pending_transactions': [tx.to_dict() for tx in self.pending_transactions],
            'transaction_history': {
                addr: [tx.to_dict() for tx in txs] 
                for addr, txs in self.transaction_history.items()
            },
            'processed_transactions': list(self.processed_transactions)
        }
    
    def from_dict(self, data: Dict):
        """Load blockchain state from dictionary."""
        self.balances = defaultdict(float, data.get('balances', {}))
        self.pending_transactions = [
            Transaction.from_dict(tx_data) 
            for tx_data in data.get('pending_transactions', [])
        ]
        self.transaction_history = defaultdict(list, {
            addr: [Transaction.from_dict(tx_data) for tx_data in txs]
            for addr, txs in data.get('transaction_history', {}).items()
        })
        self.processed_transactions = set(data.get('processed_transactions', []))
    
    def save_state(self, filepath: str = "data/blockchain_state.json") -> bool:
        """Save blockchain state to file."""
        try:
            import json
            import os
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Get state as dictionary
            state_data = self.to_dict()
            
            with open(filepath, 'w') as f:
                json.dump(state_data, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Error saving blockchain state: {e}")
            return False
    
    def load_state(self, filepath: str = "data/blockchain_state.json") -> bool:
        """Load blockchain state from file."""
        try:
            import json
            import os
            
            if not os.path.exists(filepath):
                # File doesn't exist, start with empty state
                return True
            
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Load state from dictionary
            self.from_dict(data)
            
            return True
        except Exception as e:
            print(f"Error loading blockchain state: {e}")
            return False


if __name__ == "__main__":
    # Test blockchain state functionality
    print("Testing COINjecture Blockchain State...")
    
    # Create blockchain state
    state = BlockchainState()
    
    # Test address creation
    test_address1 = "CJ1234567890abcdef1234567890abcdef12345678"
    test_address2 = "CJabcdef1234567890abcdef1234567890abcdef12"
    
    # Test balance operations
    state.update_balance(test_address1, 100.0)
    state.update_balance(test_address2, 50.0)
    
    print(f"✅ Balance {test_address1}: {state.get_balance(test_address1)}")
    print(f"✅ Balance {test_address2}: {state.get_balance(test_address2)}")
    
    # Test coinbase transaction
    coinbase_tx = state.create_coinbase_transaction(test_address1, 10.0)
    print(f"✅ Created coinbase transaction: {coinbase_tx}")
    
    # Test transaction processing
    state.process_transactions([coinbase_tx])
    print(f"✅ Balance after coinbase: {state.get_balance(test_address1)}")
    
    # Test network stats
    stats = state.get_network_stats()
    print(f"✅ Network stats: {stats}")
    
    print("✅ Blockchain state tests completed")
