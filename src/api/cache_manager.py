"""
Cache Manager for COINjecture Faucet API

Handles file-based cache reading and validation for blockchain data.
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from .coupling_config import ETA, CACHE_READ_INTERVAL, CouplingState


class CacheManager:
    """
    Manages file-based cache for blockchain data.
    
    Reads from JSON cache files and provides validated data to the API.
    """
    
    def __init__(self, cache_dir: str = "data/cache", blockchain_state_path: str = "data/blockchain_state.json"):
        """
        Initialize cache manager with η-damped polling.
        
        Args:
            cache_dir: Directory containing cache files (legacy)
            blockchain_state_path: Path to shared blockchain state from consensus
        """
        self.cache_dir = Path(cache_dir)
        self.blockchain_state_path = blockchain_state_path
        self.latest_block_file = self.cache_dir / "latest_block.json"
        self.blocks_history_file = self.cache_dir / "blocks_history.json"
        
        # η-damped polling state
        self.coupling_state = CouplingState()
        self.cached_blocks = {}
        self.last_poll_time = 0.0
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize cache files if they don't exist
        self._initialize_cache_files()
    
    def _initialize_cache_files(self):
        """Initialize cache files with default data if they don't exist."""
        if not self.latest_block_file.exists():
            default_block = {
                "index": 0,
                "timestamp": 1609459200.0,  # 2021-01-01 00:00:00 UTC
                "previous_hash": "0" * 64,
                "merkle_root": "0" * 64,
                "mining_capacity": "TIER_1_MOBILE",
                "cumulative_work_score": 0.0,
                "block_hash": "0" * 64,
                "offchain_cid": None,
                "last_updated": time.time()
            }
            self._write_json(self.latest_block_file, default_block)
        
        if not self.blocks_history_file.exists():
            self._write_json(self.blocks_history_file, [])
    
    def _read_json(self, file_path: Path) -> Any:
        """
        Read JSON from file.
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Parsed JSON data
            
        Raises:
            ValueError: If JSON is invalid
            FileNotFoundError: If file doesn't exist
        """
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {file_path}: {e}")
        except FileNotFoundError:
            raise FileNotFoundError(f"Cache file not found: {file_path}")
    
    def _write_json(self, file_path: Path, data: Any):
        """
        Write JSON to file.
        
        Args:
            file_path: Path to JSON file
            data: Data to write
        """
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_latest_block(self) -> Dict[str, Any]:
        """
        Get the latest block from cache with η-damped polling.
        
        Returns:
            Latest block data
            
        Raises:
            ValueError: If cache data is invalid
            FileNotFoundError: If cache file doesn't exist
        """
        try:
            # Check η-damped timing
            if self.coupling_state.can_read():
                self._poll_blockchain_state()
                self.coupling_state.record_read()
            
            # Return cached data
            if 'latest_block' in self.cached_blocks:
                return self.cached_blocks['latest_block']
            
            # Fallback to legacy cache
            block_data = self._read_json(self.latest_block_file)
            self._validate_block_data(block_data)
            return block_data
        except Exception as e:
            raise ValueError(f"Failed to get latest block: {e}")
    
    def get_block_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """
        Get block by index from history cache.
        
        Args:
            index: Block index to retrieve
            
        Returns:
            Block data if found, None otherwise
            
        Raises:
            ValueError: If cache data is invalid
        """
        try:
            blocks_history = self._read_json(self.blocks_history_file)
            
            # Search for block with matching index
            for block in blocks_history:
                if block.get("index") == index:
                    self._validate_block_data(block)
                    return block
            
            return None
        except Exception as e:
            raise ValueError(f"Failed to get block by index {index}: {e}")
    
    def get_blocks_range(self, start: int, end: int) -> List[Dict[str, Any]]:
        """
        Get range of blocks from history cache.
        
        Args:
            start: Starting block index (inclusive)
            end: Ending block index (inclusive)
            
        Returns:
            List of block data in range
            
        Raises:
            ValueError: If cache data is invalid
        """
        try:
            blocks_history = self._read_json(self.blocks_history_file)
            
            # Filter blocks in range
            blocks_in_range = []
            for block in blocks_history:
                block_index = block.get("index")
                if start <= block_index <= end:
                    self._validate_block_data(block)
                    blocks_in_range.append(block)
            
            # Sort by index
            blocks_in_range.sort(key=lambda x: x.get("index", 0))
            return blocks_in_range
        except Exception as e:
            raise ValueError(f"Failed to get blocks range {start}-{end}: {e}")
    
    def _validate_block_data(self, block_data: Dict[str, Any]):
        """
        Validate block data structure.
        
        Args:
            block_data: Block data to validate
            
        Raises:
            ValueError: If block data is invalid
        """
        required_fields = [
            "index", "timestamp", "previous_hash", "merkle_root",
            "mining_capacity", "cumulative_work_score", "block_hash"
        ]
        
        for field in required_fields:
            if field not in block_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate data types
        if not isinstance(block_data["index"], int):
            raise ValueError("Block index must be integer")
        
        if not isinstance(block_data["timestamp"], (int, float)):
            raise ValueError("Block timestamp must be number")
        
        if not isinstance(block_data["cumulative_work_score"], (int, float)):
            raise ValueError("Cumulative work score must be number")
        
        # Validate hash lengths
        for hash_field in ["previous_hash", "merkle_root", "block_hash"]:
            if len(block_data[hash_field]) != 64:
                raise ValueError(f"{hash_field} must be 64 characters")
    
    def is_cache_available(self) -> bool:
        """
        Check if cache is available and valid.
        
        Returns:
            True if cache is available and valid
        """
        try:
            self.get_latest_block()
            return True
        except Exception:
            return False
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get cache information from database (real blockchain data).
        
        Returns:
            Cache metadata
        """
        try:
            # Read from database instead of outdated JSON files
            import sqlite3
            
            # Connect to the database
            db_path = "/opt/coinjecture-consensus/data/faucet_ingest.db"
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get total blocks count from block_events
                cursor.execute("SELECT COUNT(*) FROM block_events")
                total_blocks = cursor.fetchone()[0]
                
                # Get latest block info
                cursor.execute("""
                    SELECT block_index, block_hash, created_at 
                    FROM block_events 
                    ORDER BY block_index DESC 
                    LIMIT 1
                """)
                latest = cursor.fetchone()
                
                conn.close()
                
                # Get the real block count from consensus service API
                try:
                    import requests
                    consensus_response = requests.get('http://localhost:5000/v1/consensus/status', timeout=5)
                    if consensus_response.status_code == 200:
                        consensus_data = consensus_response.json()
                        real_block_count = consensus_data.get('data', {}).get('total_blocks', 0)
                        if real_block_count > total_blocks:
                            total_blocks = real_block_count
                            if latest:
                                latest = (real_block_count - 1, latest[1], latest[2])
                except:
                    # Fallback to blockchain_state.json if consensus API not available
                    blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
                    if os.path.exists(blockchain_state_path):
                        with open(blockchain_state_path, 'r') as f:
                            blockchain_data = json.load(f)
                            real_block_count = blockchain_data.get('latest_block_index', 0) + 1
                            if real_block_count > total_blocks:
                                total_blocks = real_block_count
                                if latest:
                                    latest = (real_block_count - 1, latest[1], latest[2])
                
                if latest:
                    return {
                        "latest_block_index": latest[0],
                        "latest_block_hash": latest[1],
                        "last_updated": latest[2],
                        "history_blocks_count": total_blocks,
                        "cache_available": True
                    }
                else:
                    return {
                        "cache_available": False,
                        "error": "No blocks found in database"
                    }
            else:
                # Fallback to JSON if database not available
                latest_block = self.get_latest_block()
                blocks_history = self._read_json(self.blocks_history_file)
                
                return {
                    "latest_block_index": latest_block.get("index"),
                    "latest_block_hash": latest_block.get("block_hash"),
                    "last_updated": latest_block.get("last_updated"),
                    "history_blocks_count": len(blocks_history),
                    "cache_available": True
                }
        except Exception as e:
            return {
                "cache_available": False,
                "error": str(e)
            }
    
    def get_all_blocks(self) -> List[Dict[str, Any]]:
        """
        Get all blocks in the blockchain from database.
        
        Returns:
            List of all blocks
        """
        try:
            # Read from database instead of outdated JSON files
            import sqlite3
            
            # Connect to the database
            db_path = "/opt/coinjecture-consensus/data/faucet_ingest.db"
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get all blocks from database
                cursor.execute("""
                    SELECT block_index, block_hash, created_at, miner_address, work_score, 
                           capacity, cid, previous_hash, merkle_root
                    FROM block_events 
                    ORDER BY block_index ASC
                """)
                rows = cursor.fetchall()
                
                print(f"DEBUG: Found {len(rows)} rows in database")
                
                all_blocks = []
                for row in rows:
                    block = {
                        "index": row[0],
                        "block_hash": row[1],
                        "timestamp": row[2],
                        "miner_address": row[3],
                        "work_score": row[4],
                        "capacity": row[5],
                        "offchain_cid": row[6],
                        "previous_hash": row[7],
                        "merkle_root": row[8]
                    }
                    all_blocks.append(block)
                
                print(f"DEBUG: Returning {len(all_blocks)} blocks")
                conn.close()
                return all_blocks
            else:
                # Fallback to JSON if database not available
                if os.path.exists(self.blockchain_state_path):
                    with open(self.blockchain_state_path, 'r') as f:
                        blockchain_state = json.load(f)
                    
                    # Get all blocks from blockchain state
                    all_blocks = []
                    if 'blocks' in blockchain_state:
                        all_blocks = blockchain_state['blocks']
                    elif 'block_history' in blockchain_state:
                        all_blocks = blockchain_state['block_history']
                    
                    return all_blocks
                else:
                    # Fallback to cache files
                    blocks_history = self._read_json(self.blocks_history_file)
                    return blocks_history if blocks_history else []
        except Exception as e:
            print(f"Error getting all blocks: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_ipfs_data(self, cid: str) -> Optional[Dict[str, Any]]:
        """
        Get IPFS data by CID.
        
        Args:
            cid: IPFS content identifier
            
        Returns:
            IPFS data or None if not found
        """
        try:
            # Read from blockchain state
            if os.path.exists(self.blockchain_state_path):
                with open(self.blockchain_state_path, 'r') as f:
                    blockchain_state = json.load(f)
                
                # Look for IPFS data in blockchain state
                if 'ipfs_data' in blockchain_state:
                    ipfs_data = blockchain_state['ipfs_data']
                    if cid in ipfs_data:
                        return ipfs_data[cid]
                
                # Look in blocks for IPFS references
                if 'blocks' in blockchain_state:
                    for block in blockchain_state['blocks']:
                        if block.get('cid') == cid:
                            return {
                                'cid': cid,
                                'block_index': block.get('index'),
                                'block_hash': block.get('block_hash'),
                                'data': block.get('data', {}),
                                'timestamp': block.get('timestamp')
                            }
            
            return None
        except Exception as e:
            print(f"Error getting IPFS data for CID {cid}: {e}")
            return None
    
    def list_ipfs_cids(self) -> List[str]:
        """
        List all available IPFS CIDs.
        
        Returns:
            List of CIDs
        """
        try:
            cids = []
            
            # Read from blockchain state
            if os.path.exists(self.blockchain_state_path):
                with open(self.blockchain_state_path, 'r') as f:
                    blockchain_state = json.load(f)
                
                # Get CIDs from IPFS data
                if 'ipfs_data' in blockchain_state:
                    cids.extend(blockchain_state['ipfs_data'].keys())
                
                # Get CIDs from blocks
                if 'blocks' in blockchain_state:
                    for block in blockchain_state['blocks']:
                        if 'cid' in block:
                            cids.append(block['cid'])
            
            return list(set(cids))  # Remove duplicates
        except Exception as e:
            print(f"Error listing IPFS CIDs: {e}")
            return []
    
    def search_ipfs_data(self, query: str) -> List[Dict[str, Any]]:
        """
        Search IPFS data by content or metadata.
        
        Args:
            query: Search query
            
        Returns:
            List of matching IPFS data
        """
        try:
            results = []
            query_lower = query.lower()
            
            # Read from blockchain state
            if os.path.exists(self.blockchain_state_path):
                with open(self.blockchain_state_path, 'r') as f:
                    blockchain_state = json.load(f)
                
                # Search in IPFS data
                if 'ipfs_data' in blockchain_state:
                    for cid, data in blockchain_state['ipfs_data'].items():
                        if self._matches_query(data, query_lower):
                            results.append({
                                'cid': cid,
                                'data': data,
                                'type': 'ipfs_data'
                            })
                
                # Search in blocks
                if 'blocks' in blockchain_state:
                    for block in blockchain_state['blocks']:
                        if 'cid' in block and self._matches_query(block, query_lower):
                            results.append({
                                'cid': block['cid'],
                                'block_index': block.get('index'),
                                'block_hash': block.get('block_hash'),
                                'data': block.get('data', {}),
                                'timestamp': block.get('timestamp'),
                                'type': 'block_data'
                            })
            
            return results
        except Exception as e:
            print(f"Error searching IPFS data: {e}")
            return []
    
    def _matches_query(self, data: Dict[str, Any], query: str) -> bool:
        """
        Check if data matches search query.
        
        Args:
            data: Data to search in
            query: Search query (lowercase)
            
        Returns:
            True if data matches query
        """
        try:
            # Convert data to string for searching
            data_str = json.dumps(data, default=str).lower()
            return query in data_str
        except Exception:
            return False
    
    def _poll_blockchain_state(self):
        """
        Poll blockchain state from database directly with η-damped timing.
        Read from database instead of outdated JSON files.
        """
        try:
            # Read from database instead of outdated JSON files
            import sqlite3
            
            # Connect to the database
            db_path = "/opt/coinjecture-consensus/data/faucet_ingest.db"
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Get the latest block from database
                cursor.execute("""
                    SELECT block_index, block_hash, created_at, miner_address, work_score, 
                           capacity, cid, previous_hash, merkle_root
                    FROM block_events 
                    ORDER BY block_index DESC 
                    LIMIT 1
                """)
                latest = cursor.fetchone()
                
                if latest:
                    # Create latest block data from database
                    latest_block = {
                        "index": latest[0],
                        "block_hash": latest[1],
                        "timestamp": latest[2],
                        "miner_address": latest[3],
                        "work_score": latest[4],
                        "capacity": latest[5],
                        "offchain_cid": latest[6],
                        "previous_hash": latest[7],
                        "merkle_root": latest[8],
                        "last_updated": time.time()
                    }
                    
                    self.cached_blocks['latest_block'] = latest_block
                
                # Get total blocks count
                cursor.execute("SELECT COUNT(*) FROM block_events")
                total_blocks = cursor.fetchone()[0]
                
                conn.close()
                
                # Update last poll time
                self.last_poll_time = time.time()
            else:
                # Fallback to JSON if database not available
                if not os.path.exists(self.blockchain_state_path):
                    return  # No blockchain state yet
                
                with open(self.blockchain_state_path, 'r') as f:
                    blockchain_state = json.load(f)
                
                # Lightweight validation (trust consensus)
                if 'latest_block' in blockchain_state:
                    self.cached_blocks['latest_block'] = blockchain_state['latest_block']
                
                if 'blocks' in blockchain_state:
                    self.cached_blocks['blocks'] = blockchain_state['blocks']
                
                # Update last poll time
                self.last_poll_time = time.time()
            
        except Exception as e:
            # Silent fail - fallback to legacy cache
            pass


if __name__ == "__main__":
    # Test CacheManager
    print("Testing CacheManager...")
    
    cache = CacheManager()
    print("✅ CacheManager initialized")
    
    # Test latest block
    latest = cache.get_latest_block()
    print(f"✅ Latest block retrieved: index={latest['index']}")
    
    # Test cache info
    info = cache.get_cache_info()
    print(f"✅ Cache info: {info}")
    
    # Test availability
    available = cache.is_cache_available()
    print(f"✅ Cache available: {available}")
    
    print("✅ All cache manager tests passed!")
