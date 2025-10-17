"""
Cache Updater for COINjecture Faucet API

Updates cache files with real blockchain data from ConsensusEngine.
Handles IPFS integration for proof bundle storage.
"""

import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    from storage import StorageManager, StorageConfig, NodeRole, PruningMode
    from consensus import ConsensusEngine, ConsensusConfig
    from pow import ProblemRegistry
    from core.blockchain import Block
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)


class CacheUpdater:
    """
    Updates cache files with real blockchain data.
    
    Initializes ConsensusEngine to get genesis block with IPFS integration,
    then periodically updates cache files with the latest blockchain state.
    """
    
    def __init__(self, cache_dir: str = "data/cache", update_interval: int = 30):
        """
        Initialize cache updater.
        
        Args:
            cache_dir: Directory containing cache files
            update_interval: Seconds between cache updates
        """
        self.cache_dir = Path(cache_dir)
        self.latest_block_file = self.cache_dir / "latest_block.json"
        self.blocks_history_file = self.cache_dir / "blocks_history.json"
        self.update_interval = update_interval
        
        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize blockchain components
        self._initialize_blockchain()
        
        print("✅ CacheUpdater initialized")
    
    def _initialize_blockchain(self):
        """Initialize blockchain components with IPFS integration."""
        try:
            # Create storage config with IPFS
            storage_config = StorageConfig(
                data_dir="data",
                role=NodeRole.FULL,
                pruning_mode=PruningMode.FULL,
                ipfs_api_url="http://localhost:5001"
            )
            
            # Initialize components
            self.storage = StorageManager(storage_config)
            self.problem_registry = ProblemRegistry()
            
            # Create consensus config
            consensus_config = ConsensusConfig()
            
            # Initialize consensus engine (this triggers genesis creation with IPFS upload)
            self.consensus = ConsensusEngine(consensus_config, self.storage, self.problem_registry)
            
            print("✅ Blockchain components initialized")
            print(f"✅ Genesis block created with IPFS integration")
            
        except Exception as e:
            print(f"❌ Failed to initialize blockchain: {e}")
            raise
    
    def _check_ipfs_connectivity(self) -> bool:
        """
        Check if IPFS is available.
        
        Returns:
            True if IPFS is accessible
        """
        try:
            # Use the storage manager's IPFS client
            return self.storage.ipfs_client.health_check()
        except Exception as e:
            print(f"⚠️  IPFS connectivity check failed: {e}")
            return False
    
    def _block_to_cache_format(self, block: Block) -> Dict[str, Any]:
        """
        Convert Block object to cache format with proof summary.
        
        Args:
            block: Block object to convert
            
        Returns:
            Dictionary in cache format
        """
        # Extract proof data for summary
        proof_summary = {
            "problem_instance": block.problem,
            "solution": block.solution,
            "computational_metrics": {
                "problem_class": getattr(block.complexity, 'problem_class', 'unknown'),
                "problem_size": getattr(block.complexity, 'problem_size', 0),
                "solution_size": getattr(block.complexity, 'solution_size', 0),
                "measured_solve_time": getattr(block.complexity, 'measured_solve_time', 0.0),
                "measured_verify_time": getattr(block.complexity, 'measured_verify_time', 0.0),
                "time_solve_O": getattr(block.complexity, 'time_solve_O', 'unknown'),
                "time_verify_O": getattr(block.complexity, 'time_verify_O', 'unknown'),
                "space_solve_O": getattr(block.complexity, 'space_solve_O', 'unknown'),
                "space_verify_O": getattr(block.complexity, 'space_verify_O', 'unknown'),
            }
        }
        
        # Extract energy metrics if available
        try:
            if hasattr(block.complexity, 'energy_metrics') and block.complexity.energy_metrics:
                energy_metrics = block.complexity.energy_metrics
                proof_summary["energy_metrics"] = {
                    "solve_energy_joules": getattr(energy_metrics, 'solve_energy_joules', 0.0),
                    "verify_energy_joules": getattr(energy_metrics, 'verify_energy_joules', 0.0),
                    "solve_power_watts": getattr(energy_metrics, 'solve_power_watts', 0.0),
                    "cpu_utilization": getattr(energy_metrics, 'cpu_utilization', 0.0),
                    "memory_utilization": getattr(energy_metrics, 'memory_utilization', 0.0),
                    "gpu_utilization": getattr(energy_metrics, 'gpu_utilization', 0.0),
                }
        except Exception as e:
            print(f"⚠️  Could not extract energy metrics: {e}")
            proof_summary["energy_metrics"] = {"error": str(e)}
        
        # Convert to cache format
        cache_data = {
            "index": block.index,
            "timestamp": block.timestamp,
            "previous_hash": block.previous_hash,
            "transactions": getattr(block, 'transactions', []),
            "merkle_root": block.merkle_root,
            "mining_capacity": str(block.mining_capacity),
            "cumulative_work_score": block.cumulative_work_score,
            "block_hash": block.block_hash,
            "offchain_cid": getattr(block, 'offchain_cid', None),
            "proof_summary": proof_summary,
            "last_updated": time.time()
        }
        
        return cache_data
    
    def _update_cache(self):
        """Update cache files with current blockchain state."""
        try:
            # Get genesis block (which has IPFS integration)
            genesis_block = self.consensus.genesis_block
            
            # Convert to cache format
            latest_block_data = self._block_to_cache_format(genesis_block)
            
            # Write latest block
            with open(self.latest_block_file, 'w') as f:
                json.dump(latest_block_data, f, indent=2)
            
            # Update blocks history
            try:
                with open(self.blocks_history_file, 'r') as f:
                    blocks_history = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                blocks_history = []
            
            # Add or update genesis block in history
            block_found = False
            for i, block in enumerate(blocks_history):
                if block.get("index") == genesis_block.index:
                    blocks_history[i] = latest_block_data
                    block_found = True
                    break
            
            if not block_found:
                blocks_history.append(latest_block_data)
            
            # Write updated history
            with open(self.blocks_history_file, 'w') as f:
                json.dump(blocks_history, f, indent=2)
            
            # Log update
            ipfs_status = "✅ IPFS" if latest_block_data.get("offchain_cid") else "❌ No IPFS"
            print(f"📝 Cache updated: block {genesis_block.index}, {ipfs_status} CID: {latest_block_data.get('offchain_cid')}")
            
        except Exception as e:
            print(f"❌ Failed to update cache: {e}")
            import traceback
            traceback.print_exc()
    
    def run(self):
        """Run the cache updater loop."""
        print("🚀 Starting cache updater...")
        print(f"📁 Cache directory: {self.cache_dir}")
        print(f"⏱️  Update interval: {self.update_interval} seconds")
        
        # Check IPFS connectivity
        if self._check_ipfs_connectivity():
            print("✅ IPFS is available")
        else:
            print("⚠️  IPFS not available - blocks will have null offchain_cid")
        
        # Initial cache update
        self._update_cache()
        
        # Main update loop
        try:
            while True:
                time.sleep(self.update_interval)
                self._update_cache()
        except KeyboardInterrupt:
            print("\n🛑 Cache updater stopped by user")
        except Exception as e:
            print(f"❌ Cache updater error: {e}")
            import traceback
            traceback.print_exc()


def main():
    """Main entry point."""
    try:
        updater = CacheUpdater()
        updater.run()
    except Exception as e:
        print(f"❌ Failed to start cache updater: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
