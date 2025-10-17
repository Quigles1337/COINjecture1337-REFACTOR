"""
Cache Manager for COINjecture Faucet API

Handles file-based cache reading and validation for blockchain data.
"""

import json
import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any


class CacheManager:
    """
    Manages file-based cache for blockchain data.
    
    Reads from JSON cache files and provides validated data to the API.
    """
    
    def __init__(self, cache_dir: str = "data/cache"):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory containing cache files
        """
        self.cache_dir = Path(cache_dir)
        self.latest_block_file = self.cache_dir / "latest_block.json"
        self.blocks_history_file = self.cache_dir / "blocks_history.json"
        
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
        Get the latest block from cache.
        
        Returns:
            Latest block data
            
        Raises:
            ValueError: If cache data is invalid
            FileNotFoundError: If cache file doesn't exist
        """
        try:
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
        Get cache information.
        
        Returns:
            Cache metadata
        """
        try:
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
