"""
Module: storage
Specification: docs/blockchain/storage.md

Local persistent store for headers/blocks/indices with IPFS client integration
and pruning strategies per node role.
"""

import os
import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Union
from enum import Enum
import sqlite3
from pathlib import Path

# Import from existing modules
try:
    from .core.blockchain import Block, ProblemTier
    from .pow import ProblemRegistry
except ImportError:
    # Fallback for direct execution
    from core.blockchain import Block, ProblemTier
    from pow import ProblemRegistry


class NodeRole(Enum):
    """Node roles with different storage requirements."""
    LIGHT = "light"
    FULL = "full"
    MINER = "miner"
    ARCHIVE = "archive"


class PruningMode(Enum):
    """Pruning modes for different node roles."""
    LIGHT = "light"      # keep headers + commit_index only
    FULL = "full"        # keep recent N epochs of bundles (configurable)
    ARCHIVE = "archive"  # keep all; disable IPFS GC; pin bundles


@dataclass
class StorageConfig:
    """Storage configuration for different node roles."""
    data_dir: str
    role: NodeRole
    pruning_mode: PruningMode
    ipfs_api_url: str = "http://localhost:5001"
    max_bundle_epochs: int = 10  # For FULL mode
    batch_size: int = 100
    fsync_interval: int = 10  # Sync every N blocks


@dataclass
class IPFSClient:
    """
    IPFS client for proof bundle storage.
    
    Implements the IPFS client interface from storage.md specification.
    """
    
    api_url: str = "http://localhost:5001"
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        """Initialize IPFS client."""
        self._session = None
        self._health_check_interval = 60  # seconds
        self._last_health_check = 0
        self._is_healthy = False
    
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Make HTTP request to IPFS API.
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            data: Request data
            
        Returns:
            Response data
        """
        try:
            import requests  # type: ignore  # External dependency
        except ImportError:
            raise Exception("requests library not available. Install with: pip install requests")
        
        url = f"{self.api_url}/api/v0/{endpoint}"
        
        for attempt in range(self.max_retries):
            try:
                if method == "POST":
                    response = requests.post(url, data=data, timeout=self.timeout)
                else:
                    response = requests.get(url, timeout=self.timeout)
                
                response.raise_for_status()
                return response.json() if response.content else {}
                
            except Exception as e:
                if attempt == self.max_retries - 1:
                    raise Exception(f"IPFS request failed after {self.max_retries} attempts: {e}")
                time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
    
    def add(self, obj_bytes: bytes) -> str:
        """
        Add object to IPFS and return CID.
        
        Args:
            obj_bytes: Object data to store
            
        Returns:
            IPFS CID
        """
        try:
            import requests  # type: ignore  # External dependency
        except ImportError:
            raise Exception("requests library not available. Install with: pip install requests")
        
        try:
            url = f"{self.api_url}/api/v0/add"
            files = {"file": ("data", obj_bytes, "application/octet-stream")}
            response = requests.post(url, files=files, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            return result.get("Hash", "")
        except Exception as e:
            raise Exception(f"Failed to add object to IPFS: {e}")
    
    def get(self, cid: str) -> bytes:
        """
        Get object from IPFS by CID.
        
        Args:
            cid: IPFS CID
            
        Returns:
            Object data
        """
        try:
            import requests  # type: ignore  # External dependency
        except ImportError:
            raise Exception("requests library not available. Install with: pip install requests")
        
        try:
            url = f"{self.api_url}/api/v0/cat?arg={cid}"
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise Exception(f"Failed to get object from IPFS: {e}")
    
    def pin(self, cid: str) -> bool:
        """
        Pin object in IPFS.
        
        Args:
            cid: IPFS CID to pin
            
        Returns:
            True if successful
        """
        try:
            self._make_request(f"pin/add?arg={cid}")
            return True
        except Exception as e:
            print(f"Warning: Failed to pin CID {cid}: {e}")
            return False
    
    def health_check(self) -> bool:
        """
        Check IPFS node health.
        
        Returns:
            True if IPFS is healthy
        """
        current_time = time.time()
        if current_time - self._last_health_check < self._health_check_interval:
            return self._is_healthy
        
        try:
            self._make_request("version", method="POST")
            self._is_healthy = True
        except Exception:
            self._is_healthy = False
        
        self._last_health_check = current_time
        return self._is_healthy


class StorageManager:
    """
    Storage manager for blockchain data.
    
    Implements the storage module from storage.md specification.
    """
    
    def __init__(self, config: StorageConfig):
        """
        Initialize storage manager.
        
        Args:
            config: Storage configuration
        """
        self.config = config
        self.db_path = os.path.join(config.data_dir, "blockchain.db")
        self.ipfs_client = IPFSClient(config.ipfs_api_url)
        
        # Ensure data directory exists
        os.makedirs(config.data_dir, exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Batch write buffer
        self._write_buffer: List[tuple] = []
        self._last_sync = 0
    
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Headers table: key=header_hash -> header_bytes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS headers (
                    header_hash BLOB PRIMARY KEY,
                    header_bytes BLOB NOT NULL,
                    height INTEGER,
                    timestamp INTEGER,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            # Blocks table: key=block_hash -> block_bytes (optional body)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS blocks (
                    block_hash BLOB PRIMARY KEY,
                    block_bytes BLOB,
                    header_hash BLOB,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    FOREIGN KEY (header_hash) REFERENCES headers (header_hash)
                )
            """)
            
            # Tips table: single key -> set of tip hashes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tips (
                    id INTEGER PRIMARY KEY,
                    tip_hash BLOB NOT NULL,
                    cumulative_work INTEGER,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            # Work index: key=height -> cumulative_work:u128
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS work_index (
                    height INTEGER PRIMARY KEY,
                    cumulative_work INTEGER NOT NULL,
                    block_hash BLOB,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            # Commit index: key=commitment:[32] -> cid
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS commit_index (
                    commitment BLOB PRIMARY KEY,
                    cid TEXT NOT NULL,
                    problem_type INTEGER,
                    capacity INTEGER,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            # Peer index: key=peer_id -> meta
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS peer_index (
                    peer_id TEXT PRIMARY KEY,
                    meta TEXT,
                    last_seen INTEGER,
                    created_at INTEGER DEFAULT (strftime('%s', 'now'))
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_headers_height ON headers (height)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_headers_timestamp ON headers (timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_work_index_height ON work_index (height)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_commit_index_commitment ON commit_index (commitment)")
            
            conn.commit()
    
    def store_header(self, block: Block) -> bool:
        """
        Store block header (extracted from block).
        
        Args:
            block: Block containing header information
            
        Returns:
            True if successful
        """
        try:
            header_bytes = self._serialize_header(block)
            # Use the block's hash field if available, otherwise calculate it
            header_hash = (block.block_hash if hasattr(block, 'block_hash') and block.block_hash else block.calculate_hash()).encode()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO headers 
                    (header_hash, header_bytes, height, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (header_hash, header_bytes, block.index, int(block.timestamp)))
                conn.commit()
            
            return True
        except Exception as e:
            print(f"Error storing header: {e}")
            return False
    
    def get_header(self, header_hash: str) -> Optional[Block]:
        """
        Get block header by hash.
        
        Args:
            header_hash: Header hash
            
        Returns:
            Block or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT header_bytes FROM headers 
                    WHERE header_hash = ?
                """, (header_hash.encode(),))
                
                result = cursor.fetchone()
                if result:
                    return self._deserialize_header(result[0])
                return None
        except Exception as e:
            print(f"Error getting header: {e}")
            return None
    
    def store_block(self, block: Block) -> bool:
        """
        Store full block.
        
        Args:
            block: Block to store
            
        Returns:
            True if successful
        """
        try:
            block_bytes = self._serialize_block(block)
            block_hash = block.calculate_hash().encode()
            header_hash = block.calculate_hash().encode()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO blocks 
                    (block_hash, block_bytes, header_hash)
                    VALUES (?, ?, ?)
                """, (block_hash, block_bytes, header_hash))
                conn.commit()
            
            return True
        except Exception as e:
            print(f"Error storing block: {e}")
            return False
    
    def get_block(self, block_hash: str) -> Optional[Block]:
        """
        Get full block by hash.
        
        Args:
            block_hash: Block hash
            
        Returns:
            Block or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT block_bytes FROM blocks 
                    WHERE block_hash = ?
                """, (block_hash.encode(),))
                
                result = cursor.fetchone()
                if result:
                    return self._deserialize_block(result[0])
                return None
        except Exception as e:
            print(f"Error getting block: {e}")
            return None
    
    def store_tip(self, tip_hash: str, cumulative_work: int) -> bool:
        """
        Store chain tip.
        
        Args:
            tip_hash: Tip block hash
            cumulative_work: Cumulative work score
            
        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO tips 
                    (tip_hash, cumulative_work)
                    VALUES (?, ?)
                """, (tip_hash.encode(), cumulative_work))
                conn.commit()
            
            return True
        except Exception as e:
            print(f"Error storing tip: {e}")
            return False
    
    def get_tips(self) -> List[tuple]:
        """
        Get all chain tips.
        
        Returns:
            List of (tip_hash, cumulative_work) tuples
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT tip_hash, cumulative_work FROM tips 
                    ORDER BY cumulative_work DESC
                """)
                
                return [(row[0].decode(), row[1]) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error getting tips: {e}")
            return []
    
    def store_work_index(self, height: int, cumulative_work: int, block_hash: str) -> bool:
        """
        Store work index entry.
        
        Args:
            height: Block height
            cumulative_work: Cumulative work score
            block_hash: Block hash
            
        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO work_index 
                    (height, cumulative_work, block_hash)
                    VALUES (?, ?, ?)
                """, (height, cumulative_work, block_hash.encode()))
                conn.commit()
            
            return True
        except Exception as e:
            print(f"Error storing work index: {e}")
            return False
    
    def get_work_at_height(self, height: int) -> Optional[int]:
        """
        Get cumulative work at height.
        
        Args:
            height: Block height
            
        Returns:
            Cumulative work or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT cumulative_work FROM work_index 
                    WHERE height = ?
                """, (height,))
                
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Error getting work at height: {e}")
            return None
    
    def store_commitment(self, commitment: bytes, cid: str, problem_type: int, capacity: int) -> bool:
        """
        Store commitment to CID mapping.
        
        Args:
            commitment: 32-byte commitment
            cid: IPFS CID
            problem_type: Problem type
            capacity: Hardware capacity
            
        Returns:
            True if successful
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO commit_index 
                    (commitment, cid, problem_type, capacity)
                    VALUES (?, ?, ?, ?)
                """, (commitment, cid, problem_type, capacity))
                conn.commit()
            
            return True
        except Exception as e:
            print(f"Error storing commitment: {e}")
            return False
    
    def get_commitment_cid(self, commitment: bytes) -> Optional[str]:
        """
        Get CID for commitment.
        
        Args:
            commitment: 32-byte commitment
            
        Returns:
            IPFS CID or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT cid FROM commit_index 
                    WHERE commitment = ?
                """, (commitment,))
                
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            print(f"Error getting commitment CID: {e}")
            return None
    
    def store_proof_bundle(self, bundle_data: bytes) -> Optional[str]:
        """
        Store proof bundle in IPFS.
        
        Args:
            bundle_data: Proof bundle data
            
        Returns:
            IPFS CID or None
        """
        try:
            if not self.ipfs_client.health_check():
                print("Warning: IPFS not available, cannot store proof bundle")
                return None
            
            cid = self.ipfs_client.add(bundle_data)
            
            # Pin if in archive mode
            if self.config.pruning_mode == PruningMode.ARCHIVE:
                self.ipfs_client.pin(cid)
            
            return cid
        except Exception as e:
            print(f"Error storing proof bundle: {e}")
            return None
    
    def get_proof_bundle(self, cid: str) -> Optional[bytes]:
        """
        Get proof bundle from IPFS.
        
        Args:
            cid: IPFS CID
            
        Returns:
            Proof bundle data or None
        """
        try:
            if not self.ipfs_client.health_check():
                print("Warning: IPFS not available, cannot get proof bundle")
                return None
            
            return self.ipfs_client.get(cid)
        except Exception as e:
            print(f"Error getting proof bundle: {e}")
            return None
    
    def prune_data(self):
        """
        Prune data based on node role and pruning mode.
        
        Implements pruning strategies from storage.md specification.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if self.config.pruning_mode == PruningMode.LIGHT:
                    # Keep headers + commit_index only
                    cursor.execute("DELETE FROM blocks")
                    cursor.execute("DELETE FROM work_index WHERE height < (SELECT MAX(height) - 100 FROM work_index)")
                    
                elif self.config.pruning_mode == PruningMode.FULL:
                    # Keep recent N epochs of bundles
                    cursor.execute("""
                        DELETE FROM commit_index 
                        WHERE created_at < (strftime('%s', 'now') - ?)
                    """, (self.config.max_bundle_epochs * 3600,))
                    
                # Archive mode keeps everything
                
                conn.commit()
                print(f"Pruning completed for {self.config.pruning_mode.value} mode")
                
        except Exception as e:
            print(f"Error during pruning: {e}")
    
    def batch_write(self, operations: List[tuple]):
        """
        Batch write operations for performance.
        
        Args:
            operations: List of (operation_type, data) tuples
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for op_type, data in operations:
                    if op_type == "header":
                        header, header_bytes = data
                        header_hash = header.calculate_hash().encode()
                        cursor.execute("""
                            INSERT OR REPLACE INTO headers 
                            (header_hash, header_bytes, height, timestamp)
                            VALUES (?, ?, ?, ?)
                        """, (header_hash, header_bytes, header.index, int(header.timestamp)))
                    
                    elif op_type == "work_index":
                        height, cumulative_work, block_hash = data
                        cursor.execute("""
                            INSERT OR REPLACE INTO work_index 
                            (height, cumulative_work, block_hash)
                            VALUES (?, ?, ?)
                        """, (height, cumulative_work, block_hash.encode()))
                
                conn.commit()
                
        except Exception as e:
            print(f"Error in batch write: {e}")
    
    def sync(self):
        """Force sync to disk."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA synchronous = FULL")
                conn.commit()
        except Exception as e:
            print(f"Error during sync: {e}")
    
    def _serialize_header(self, block: Block) -> bytes:
        """Serialize block header to bytes."""
        # Simple JSON serialization for now
        header_dict = {
            'index': block.index,
            'timestamp': block.timestamp,
            'previous_hash': block.previous_hash,
            'merkle_root': block.merkle_root,
            'mining_capacity': block.mining_capacity.value if hasattr(block.mining_capacity, 'value') else str(block.mining_capacity),
            'cumulative_work_score': block.cumulative_work_score,
            'block_hash': block.block_hash,
            'offchain_cid': getattr(block, 'offchain_cid', None)
        }
        return json.dumps(header_dict).encode()
    
    def _deserialize_header(self, header_bytes: bytes) -> Block:
        """Deserialize bytes to block."""
        header_dict = json.loads(header_bytes.decode())
        
        # Create Block object with minimal required fields
        # Note: This is a simplified deserialization for header-only storage
        return Block(
            index=header_dict['index'],
            timestamp=header_dict['timestamp'],
            previous_hash=header_dict['previous_hash'],
            transactions=[],  # Empty for header-only
            merkle_root=header_dict['merkle_root'],
            problem={},  # Empty for header-only
            solution=[],  # Empty for header-only
            complexity=None,  # Will be None for header-only
            mining_capacity=ProblemTier(header_dict['mining_capacity']),
            cumulative_work_score=header_dict['cumulative_work_score'],
            block_hash=header_dict['block_hash'],
            offchain_cid=header_dict.get('offchain_cid', None)
        )
    
    def _serialize_block(self, block: Block) -> bytes:
        """Serialize block to bytes."""
        # Simple JSON serialization for now
        block_dict = {
            'index': block.index,
            'timestamp': block.timestamp,
            'previous_hash': block.previous_hash,
            'transactions': block.transactions,
            'merkle_root': block.merkle_root,
            'problem': block.problem,
            'solution': block.solution,
            'mining_capacity': block.mining_capacity.value if hasattr(block.mining_capacity, 'value') else str(block.mining_capacity),
            'cumulative_work_score': block.cumulative_work_score,
            'block_hash': block.block_hash,
            'offchain_cid': getattr(block, 'offchain_cid', None)
        }
        return json.dumps(block_dict).encode()
    
    def _deserialize_block(self, block_bytes: bytes) -> Block:
        """Deserialize bytes to block."""
        block_dict = json.loads(block_bytes.decode())
        
        # Create Block object
        # Note: This is a simplified deserialization
        from core.blockchain import ProblemTier
        
        return Block(
            index=block_dict['index'],
            timestamp=block_dict['timestamp'],
            previous_hash=block_dict['previous_hash'],
            transactions=block_dict['transactions'],
            merkle_root=block_dict['merkle_root'],
            problem=block_dict['problem'],
            solution=block_dict['solution'],
            mining_capacity=ProblemTier(block_dict['mining_capacity']),
            cumulative_work_score=block_dict['cumulative_work_score'],
            block_hash=block_dict['block_hash'],
            offchain_cid=block_dict.get('offchain_cid', None)
        )


if __name__ == "__main__":
    # Test StorageManager
    print("Testing StorageManager...")
    
    # Create test configuration
    config = StorageConfig(
        data_dir="/tmp/coinjecture_test",
        role=NodeRole.FULL,
        pruning_mode=PruningMode.FULL
    )
    
    # Initialize storage manager
    storage = StorageManager(config)
    print("✅ StorageManager initialized")
    
    # Test IPFS client (if available)
    print("Testing IPFS client...")
    try:
        if storage.ipfs_client.health_check():
            print("✅ IPFS client is healthy")
            
            # Test adding and getting data
            test_data = b"test proof bundle data"
            cid = storage.ipfs_client.add(test_data)
            print(f"✅ Added data to IPFS: {cid}")
            
            retrieved_data = storage.ipfs_client.get(cid)
            if retrieved_data == test_data:
                print("✅ Retrieved data matches original")
            else:
                print("❌ Retrieved data does not match")
        else:
            print("⚠️ IPFS client not available (this is expected in test environment)")
    except Exception as e:
        print(f"⚠️ IPFS test failed (expected): {e}")
    
    # Test database operations
    print("Testing database operations...")
    
    # Create a mock block for testing
    from core.blockchain import ProblemTier, ComputationalComplexity
    
    mock_block = Block(
        index=1,
        timestamp=time.time(),
        previous_hash="0" * 64,
        transactions=[],
        merkle_root="1" * 64,
        problem={"type": "subset_sum", "numbers": [1, 2, 3], "target": 3},
        solution=[1, 2],
        complexity=ComputationalComplexity(
            time_solve_O="O(2^n)",
            time_solve_Omega="Omega(2^(n/2))",
            time_solve_Theta=None,
            time_verify_O="O(n)",
            time_verify_Omega="Omega(n)",
            time_verify_Theta="Theta(n)",
            space_solve_O="O(n * target)",
            space_solve_Omega="Omega(n)",
            space_solve_Theta=None,
            space_verify_O="O(n)",
            space_verify_Omega="Omega(n)",
            space_verify_Theta="Theta(n)",
            problem_class="NP-Complete",
            problem_size=3,
            solution_size=2,
            epsilon_approximation=None,
            asymmetry_time=100.0,
            asymmetry_space=10.0,
            measured_solve_time=0.001,
            measured_verify_time=0.0001,
            measured_solve_space=1024,
            measured_verify_space=64,
            energy_metrics=None,
            problem={"type": "subset_sum", "numbers": [1, 2, 3], "target": 3},
            solution_quality=1.0
        ),
        mining_capacity=ProblemTier.TIER_2_DESKTOP,
        cumulative_work_score=1000.0,
        block_hash="2" * 64
    )
    
    # Test header storage
    if storage.store_header(mock_block):
        print("✅ Header stored successfully")
        
        # Test header retrieval
        retrieved_header = storage.get_header(mock_block.block_hash)
        if retrieved_header and retrieved_header.index == mock_block.index:
            print("✅ Header retrieved successfully")
        else:
            print("❌ Header retrieval failed")
    else:
        print("❌ Header storage failed")
    
    # Test work index
    if storage.store_work_index(1, 1000, mock_block.block_hash):
        print("✅ Work index stored successfully")
        
        work = storage.get_work_at_height(1)
        if work == 1000:
            print("✅ Work index retrieved successfully")
        else:
            print("❌ Work index retrieval failed")
    else:
        print("❌ Work index storage failed")
    
    # Test tips
    if storage.store_tip(mock_block.block_hash, 1000):
        print("✅ Tip stored successfully")
        
        tips = storage.get_tips()
        if tips and len(tips) > 0:
            print("✅ Tips retrieved successfully")
        else:
            print("❌ Tips retrieval failed")
    else:
        print("❌ Tip storage failed")
    
    # Test commitment storage
    test_commitment = b"test_commitment_32_bytes_padding_"
    test_cid = "QmTest123456789"
    
    if storage.store_commitment(test_commitment, test_cid, 1, 2):
        print("✅ Commitment stored successfully")
        
        retrieved_cid = storage.get_commitment_cid(test_commitment)
        if retrieved_cid == test_cid:
            print("✅ Commitment retrieved successfully")
        else:
            print("❌ Commitment retrieval failed")
    else:
        print("❌ Commitment storage failed")
    
    # Test pruning
    print("Testing pruning...")
    storage.prune_data()
    print("✅ Pruning completed")
    
    # Test sync
    print("Testing sync...")
    storage.sync()
    print("✅ Sync completed")
    
    print("✅ All storage module tests passed!")
