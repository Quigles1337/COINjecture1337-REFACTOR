#!/usr/bin/env python3
"""
Memory-Efficient Consensus Service
Applies conjecture about balancing memory and processing
"""

import os
import sys
import json
import time
import gc
import psutil
import logging
from pathlib import Path

# Add src to path
sys.path.append('src')

# Import consensus and storage modules
from consensus import ConsensusEngine, ConsensusConfig
from storage import StorageManager, StorageConfig, NodeRole, PruningMode
from pow import ProblemRegistry
from api.ingest_store import IngestStore
from api.coupling_config import LAMBDA, CONSENSUS_WRITE_INTERVAL, CouplingState

# Set up logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/consensus_service.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('coinjecture-consensus-service')

class MemoryEfficientConsensusService:
    def __init__(self):
        self.blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
        self.max_memory_mb = 256  # 256MB limit
        self.chunk_size = 10  # Process 10 blocks at a time
        self.memory_check_interval = 5  # Check memory every 5 seconds
        self.last_memory_check = 0
        
        # Initialize components
        self.consensus_engine = None
        self.ingest_store = None
        self.running = False
        
    def check_memory_usage(self):
        """Check current memory usage and trigger cleanup if needed"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > self.max_memory_mb:
                logger.warning(f"Memory usage {memory_mb:.1f}MB exceeds limit {self.max_memory_mb}MB")
                self.cleanup_memory()
                return False
            return True
        except Exception as e:
            logger.error(f"Error checking memory usage: {e}")
            return True
    
    def cleanup_memory(self):
        """Clean up memory by forcing garbage collection"""
        try:
            gc.collect()
            logger.info("Performed memory cleanup")
        except Exception as e:
            logger.error(f"Error during memory cleanup: {e}")
    
    def initialize(self):
        """Initialize the consensus service with memory management"""
        try:
            logger.info("🚀 Initializing memory-efficient consensus service")
            
            # Check memory before initialization
            if not self.check_memory_usage():
                logger.error("Memory usage too high, cannot initialize")
                return False
            
            # Initialize consensus engine with memory limits
            consensus_config = ConsensusConfig(
                
                
            )
            
            storage_config = StorageConfig("/opt/coinjecture-consensus/data", 
                role=NodeRole.FULL,
                pruning_mode=PruningMode.FULL
            )
            
            storage_manager = StorageManager(storage_config)
            problem_registry = ProblemRegistry()
            
            self.consensus_engine = ConsensusEngine(
                consensus_config,
                storage_manager,
                problem_registry
            )
            
            # Initialize ingest store
            self.ingest_store = IngestStore("/opt/coinjecture-consensus/data/faucet_ingest.db")
            
            # Bootstrap from existing blockchain state with memory management
            if not self.bootstrap_from_cache_memory_efficient():
                logger.warning("Bootstrap failed, starting fresh")
            
            logger.info("✅ Memory-efficient consensus service initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize consensus service: {e}")
            return False
    
    def bootstrap_from_cache_memory_efficient(self):
        """Bootstrap from cache with memory management"""
        try:
            if not os.path.exists(self.blockchain_state_path):
                logger.warning("Blockchain state file not found")
                return False
            
            with open(self.blockchain_state_path, 'r') as f:
                blockchain_data = json.load(f)
            
            blocks = blockchain_data.get('blocks', [])
            logger.info(f"📊 Found {len(blocks)} blocks in blockchain state")
            
            # Process blocks in memory-efficient chunks
            for i in range(0, len(blocks), self.chunk_size):
                chunk = blocks[i:i + self.chunk_size]
                
                # Check memory before processing chunk
                if not self.check_memory_usage():
                    logger.warning("Memory limit reached, pausing bootstrap")
                    time.sleep(1)
                    continue
                
                # Process chunk
                for block in chunk:
                    try:
                        self.consensus_engine._add_block_to_tree(self._dict_to_block(block), time.time())
                        if block['index'] % 100 == 0:
                            logger.info(f"📦 Bootstrapped block #{block['index']} ({i + chunk.index(block) + 1}/{len(blocks)})")
                    except Exception as e:
                        logger.error(f"Error processing block {block.get('index', 'unknown')}: {e}")
                        continue
                
                # Small delay between chunks
                time.sleep(0.1)
            
            logger.info(f"✅ Successfully bootstrapped {len(blocks)} blocks")
            return True
            
        except Exception as e:
            logger.error(f"Error during bootstrap: {e}")
            return False
    
    def run(self):
        """Run the consensus service with memory management"""
        if not self.initialize():
            return False
        
        self.running = True
        logger.info("🔄 Starting consensus service main loop")
        
        try:
            while self.running:
                # Check memory usage periodically
                current_time = time.time()
                if current_time - self.last_memory_check > self.memory_check_interval:
                    self.check_memory_usage()
                    self.last_memory_check = current_time
                
                # Process events with memory management
                self.process_events_memory_efficient()
                
                # Small delay to prevent excessive CPU usage
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Consensus service stopped by user")
        except Exception as e:
            logger.error(f"❌ Consensus service error: {e}")
        finally:
            self.running = False
        
        return True
    
    def _dict_to_block(self, block_dict):
        """Convert dictionary to Block object."""
        from core.blockchain import Block
        
        # Create Block object with required fields
        block = Block(
            index=block_dict.get("index", 0),
            timestamp=block_dict.get("timestamp", 0),
            previous_hash=block_dict.get("previous_hash", ""),
            transactions=block_dict.get("transactions", []),
            merkle_root=block_dict.get("merkle_root", ""),
            problem=block_dict.get("problem", {}),
            solution=block_dict.get("solution", []),
            complexity={},  # Empty dict to avoid 'str' object has no attribute errors
            mining_capacity=block_dict.get("mining_capacity", "mobile"),
            cumulative_work_score=block_dict.get("cumulative_work_score", 0),
            block_hash=block_dict.get("block_hash", "")
        )
        block.index = block_dict.get("index", 0)
        block.timestamp = block_dict.get("timestamp", 0)
        block.previous_hash = block_dict.get("previous_hash", "")
        block.merkle_root = block_dict.get("merkle_root", "")
        block.transactions = block_dict.get("transactions", [])
        block.problem = block_dict.get("problem", {})
        block.solution = block_dict.get("solution", [])
        
        return block
    def process_events_memory_efficient(self):
        """Process events with memory management"""
        try:
            # Get events from ingest store
            events = self.ingest_store.latest_blocks(limit=100)
            
            if not events:
                return
            
            # Process events in small chunks
            for i in range(0, len(events), self.chunk_size):
                chunk = events[i:i + self.chunk_size]
                
                # Check memory before processing chunk
                if not self.check_memory_usage():
                    logger.warning("Memory limit reached, pausing event processing")
                    break
                
                # Process chunk
                for event in chunk:
                    try:
                        self.consensus_engine._add_block_to_tree(self._dict_to_block(event), time.time()) if isinstance(event, dict) else None
                    except Exception as e:
                        logger.error(f"Error processing event: {e}")
                        continue
                
                # Small delay between chunks
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error processing events: {e}")

def main():
    """Main function"""
    service = MemoryEfficientConsensusService()
    
    try:
        success = service.run()
        if success:
            logger.info("Consensus service completed successfully")
            sys.exit(0)
        else:
            logger.error("Consensus service failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

