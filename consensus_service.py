#!/usr/bin/env python3
"""
COINjecture Consensus Service
Processes block events into actual blockchain blocks
"""

import sys
import os
import time
import json
import logging
import signal
import threading
from pathlib import Path
from typing import Optional, Dict, Any

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

class ConsensusService:
    """Consensus service that processes block events into blockchain blocks."""
    
    def __init__(self):
        self.running = False
        self.consensus_engine = None
        self.ingest_store = None
        self.processed_events = set()
        self.coupling_state = CouplingState()
        self.blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
        
    def initialize(self):
        """Initialize consensus engine and storage."""
        try:
            # Create consensus configuration
            consensus_config = ConsensusConfig(
                network_id="coinjecture-mainnet",
                confirmation_depth=6,
                max_reorg_depth=100
            )
            
            # Create storage configuration
            storage_config = StorageConfig(
                data_dir="./data",
                role=NodeRole.FULL,
                pruning_mode=PruningMode.FULL
            )
            storage_manager = StorageManager(storage_config)
            
            # Create problem registry
            problem_registry = ProblemRegistry()
            
            # Initialize consensus engine
            self.consensus_engine = ConsensusEngine(
                consensus_config,
                storage_manager,
                problem_registry
            )
            
            # Initialize ingest store (use API server's database)
            self.ingest_store = IngestStore("/opt/coinjecture-consensus/data/faucet_ingest.db")
            
            # Bootstrap from existing blockchain state
            if not self.bootstrap_from_cache():
                logger.warning("Bootstrap failed, starting fresh")
            
            logger.info("✅ Consensus service initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize consensus service: {e}")
            return False
    
    def bootstrap_from_cache(self):
        """Bootstrap consensus engine with existing blockchain state."""
        try:
            # Check if blockchain state file exists
            if os.path.exists(self.blockchain_state_path):
                with open(self.blockchain_state_path, 'r') as f:
                    blockchain_state = json.load(f)
                
                blocks = blockchain_state.get('blocks', [])
                logger.info(f"📊 Found {len(blocks)} blocks in blockchain state")
                
                if not blocks:
                    logger.info("No blocks found in blockchain state, starting from genesis")
                    return True
                
                # Sort blocks by index to ensure proper sequence
                blocks.sort(key=lambda x: x.get('index', 0))
                
                # Add each block to consensus engine in sequence
                for i, block_data in enumerate(blocks):
                    block = self._convert_cache_block_to_block(block_data)
                    if block:
                        # Add to block tree without validation
                        self.consensus_engine._add_block_to_tree(block, receipt_time=block.timestamp)
                        if i % 100 == 0 or i == len(blocks) - 1:
                            logger.info(f"📦 Bootstrapped block #{block.index} ({i+1}/{len(blocks)})")
                
                logger.info(f"✅ Successfully bootstrapped {len(blocks)} blocks")
                return True
            else:
                logger.info("No blockchain state found, starting from genesis")
                return True
        except Exception as e:
            logger.error(f"❌ Failed to bootstrap from cache: {e}")
            return False
    
    def _convert_cache_block_to_block(self, block_data: Dict[str, Any]) -> Optional[Any]:
        """Convert cached block data to Block object."""
        try:
            from core.blockchain import Block, ProblemTier, ComputationalComplexity, EnergyMetrics
            
            # Extract block data
            block_index = block_data.get('index', 0)
            timestamp = block_data.get('timestamp', time.time())
            previous_hash = block_data.get('previous_hash', "0" * 64)
            merkle_root = block_data.get('merkle_root', "0" * 64)
            mining_capacity_str = block_data.get('mining_capacity', 'TIER_1_MOBILE')
            cumulative_work_score = block_data.get('cumulative_work_score', 0.0)
            block_hash = block_data.get('block_hash', '')
            offchain_cid = block_data.get('offchain_cid', '')
            
            # Convert capacity string to ProblemTier with support for lowercase
            mining_capacity = ProblemTier.TIER_1_MOBILE  # Default
            capacity_upper = str(mining_capacity_str).upper()
            if "DESKTOP" in capacity_upper or "TIER_2" in capacity_upper:
                mining_capacity = ProblemTier.TIER_2_DESKTOP
            elif "SERVER" in capacity_upper or "TIER_3" in capacity_upper:
                mining_capacity = ProblemTier.TIER_3_SERVER
            elif "MOBILE" in capacity_upper or "TIER_1" in capacity_upper:
                mining_capacity = ProblemTier.TIER_1_MOBILE
            
            # Create basic problem and solution (placeholder for cached blocks)
            problem = {
                'type': 'subset_sum',
                'numbers': [1, 2, 3, 4, 5],
                'target': 10,
                'size': 5
            }
            solution = [1, 2, 3, 4]
            
            # Create computational complexity with all required parameters
            complexity = ComputationalComplexity(
                "O(2^n)",  # time_solve_O
                "O(2^n)",  # time_solve_Omega
                None,       # time_solve_Theta
                "O(n)",     # time_verify_O
                "O(n)",     # time_verify_Omega
                None,       # time_verify_Theta
                "O(n * target)",  # space_solve_O
                "O(n * target)",  # space_solve_Omega
                None,       # space_solve_Theta
                "O(n)",     # space_verify_O
                "O(n)",     # space_verify_Omega
                None,       # space_verify_Theta
                "NP-Complete",  # problem_class
                5,          # problem_size
                4,          # solution_size
                None,       # epsilon_approximation
                2.0,        # asymmetry_time
                1.0,        # asymmetry_space
                cumulative_work_score / 1000,  # measured_solve_time
                0.001,      # measured_verify_time
                0,          # measured_solve_space
                0,          # measured_verify_space
                EnergyMetrics(
                    solve_energy_joules=cumulative_work_score * 0.1,
                    verify_energy_joules=0.001,
                    solve_power_watts=100,
                    verify_power_watts=1,
                    solve_time_seconds=cumulative_work_score / 1000,
                    verify_time_seconds=0.001,
                    cpu_utilization=80.0,
                    memory_utilization=50.0,
                    gpu_utilization=0.0
                ),  # energy_metrics
                problem,    # problem
                1.0         # solution_quality
            )
            
            # Create Block object
            block = Block(
                index=block_index,
                timestamp=timestamp,
                previous_hash=previous_hash,
                transactions=[f"Cached block {block_index}"],
                merkle_root=merkle_root,
                problem=problem,
                solution=solution,
                complexity=complexity,
                mining_capacity=mining_capacity,
                cumulative_work_score=cumulative_work_score,
                block_hash=block_hash,
                offchain_cid=offchain_cid
            )
            
            return block
            
        except Exception as e:
            logger.error(f"❌ Failed to convert cache block to block: {e}")
            return None
    
    def process_block_events(self):
        """Process stored block events into blockchain blocks with λ-coupled timing."""
        try:
            # Always check for new events, but only write at λ-coupled intervals
            # This allows continuous processing while respecting λ-coupling for writes
            
            # Get current chain length
            current_chain = self.consensus_engine.get_chain_from_genesis()
            current_tip_index = current_chain[-1].index if current_chain else -1
            
            # Get latest block events
            block_events = self.ingest_store.latest_blocks(limit=50)
            
            processed_count = 0
            for event in block_events:
                event_id = event.get('event_id', '')
                event_block_index = event.get('block_index', 0)
                
                # Skip if already processed
                if event_id in self.processed_events:
                    continue
                
                # Skip events for blocks that are already in the chain
                if event_block_index <= current_tip_index:
                    continue
                
                # Convert block event to Block object
                block = self._convert_event_to_block(event)
                if not block:
                    continue
                
                # Validate and add to consensus
                try:
                    # Validate header
                    self.consensus_engine.validate_header(block)
                    
                    # Store block in consensus engine
                    self.consensus_engine.storage.store_block(block)
                    self.consensus_engine.storage.store_header(block)
                    
                    # Mark as processed
                    self.processed_events.add(event_id)
                    processed_count += 1
                    
                    logger.info(f"✅ Processed block event: {event_id}")
                    logger.info(f"📊 Block #{block.index}: {block.block_hash[:16]}...")
                    logger.info(f"⛏️  Work score: {block.cumulative_work_score}")
                    
                    # Automatically distribute mining rewards
                    self._distribute_mining_rewards(event, block)
                    
                except Exception as e:
                    logger.warning(f"⚠️  Failed to process block event {event_id}: {e}")
                    continue
            
            if processed_count > 0:
                logger.info(f"🔄 Processed {processed_count} new block events")
                
                # Only write blockchain state at λ-coupled intervals
                if self.coupling_state.can_write():
                    # Update blockchain state
                    self._write_blockchain_state()
                    
                    # Record λ-coupled write
                    self.coupling_state.record_write()
                    
                    # Log coupling metrics
                    metrics = self.coupling_state.get_coupling_metrics()
                    logger.info(f"🔗 λ-coupling: {metrics['write_count']} writes, interval: {metrics['consensus_write_interval']:.2f}s")
                else:
                    logger.info("⏳ Block events processed, waiting for λ-coupling interval to write state")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing block events: {e}")
            return False
    
    def _convert_event_to_block(self, event: Dict[str, Any]) -> Optional[Any]:
        """Convert block event to Block object."""
        try:
            from core.blockchain import Block, ProblemTier, ComputationalComplexity, EnergyMetrics
            
            # Extract event data - use the event's own block_index
            block_index = event.get('block_index', 0)
            
            block_hash = event.get('block_hash', '')
            cid = event.get('cid', '')
            miner_address = event.get('miner_address', '')
            capacity = event.get('capacity', 'TIER_1_MOBILE')
            work_score = event.get('work_score', 0.0)
            timestamp = event.get('ts', time.time())
            
            # Convert capacity string to ProblemTier with support for lowercase
            mining_capacity = ProblemTier.TIER_1_MOBILE  # Default
            capacity_upper = str(capacity).upper()
            if "DESKTOP" in capacity_upper or "TIER_2" in capacity_upper:
                mining_capacity = ProblemTier.TIER_2_DESKTOP
            elif "SERVER" in capacity_upper or "TIER_3" in capacity_upper:
                mining_capacity = ProblemTier.TIER_3_SERVER
            elif "MOBILE" in capacity_upper or "TIER_1" in capacity_upper:
                mining_capacity = ProblemTier.TIER_1_MOBILE
            
            # Create basic problem and solution (placeholder for now)
            problem = {
                'type': 'subset_sum',
                'numbers': [1, 2, 3, 4, 5],
                'target': 10,
                'size': 5
            }
            solution = [1, 2, 3, 4]
            
            # Create computational complexity with all required parameters
            complexity = ComputationalComplexity(
                "O(2^n)",  # time_solve_O
                "O(2^n)",  # time_solve_Omega
                None,       # time_solve_Theta
                "O(n)",     # time_verify_O
                "O(n)",     # time_verify_Omega
                None,       # time_verify_Theta
                "O(n * target)",  # space_solve_O
                "O(n * target)",  # space_solve_Omega
                None,       # space_solve_Theta
                "O(n)",     # space_verify_O
                "O(n)",     # space_verify_Omega
                None,       # space_verify_Theta
                "NP-Complete",  # problem_class
                5,          # problem_size
                4,          # solution_size
                None,       # epsilon_approximation
                2.0,        # asymmetry_time
                1.0,        # asymmetry_space
                work_score / 1000,  # measured_solve_time
                0.001,      # measured_verify_time
                0,          # measured_solve_space
                0,          # measured_verify_space
                EnergyMetrics(
                    solve_energy_joules=work_score * 0.1,
                    verify_energy_joules=0.001,
                    solve_power_watts=100,
                    verify_power_watts=1,
                    solve_time_seconds=work_score / 1000,
                    verify_time_seconds=0.001,
                    cpu_utilization=80.0,
                    memory_utilization=50.0,
                    gpu_utilization=0.0
                ),  # energy_metrics
                problem,    # problem
                1.0         # solution_quality
            )
            
            # Use the previous hash from the event data
            previous_hash = event.get('previous_hash', "0" * 64)
            
            # Create Block object
            block = Block(
                index=block_index,
                timestamp=timestamp,
                previous_hash=previous_hash,
                transactions=[f"Mined by {miner_address}"],
                merkle_root="0" * 64,  # Simplified for now
                problem=problem,
                solution=solution,
                complexity=complexity,
                mining_capacity=mining_capacity,
                cumulative_work_score=work_score,
                block_hash=block_hash,
                offchain_cid=cid
            )
            
            return block
            
        except Exception as e:
            logger.error(f"❌ Failed to convert event to block: {e}")
            return None
    
    def _write_blockchain_state(self):
        """Write blockchain state to shared storage for cache manager."""
        try:
            # Get current blockchain state
            best_tip = self.consensus_engine.get_best_tip()
            if not best_tip:
                return
            
            # Get chain from genesis
            chain = self.consensus_engine.get_chain_from_genesis()
            
            # Create blockchain state structure
            blockchain_state = {
                "latest_block": {
                    "index": best_tip.index,
                    "timestamp": best_tip.timestamp,
                    "previous_hash": best_tip.previous_hash,
                    "merkle_root": best_tip.merkle_root,
                    "mining_capacity": best_tip.mining_capacity.value if hasattr(best_tip.mining_capacity, 'value') else str(best_tip.mining_capacity),
                    "cumulative_work_score": best_tip.cumulative_work_score,
                    "block_hash": best_tip.block_hash,
                    "offchain_cid": best_tip.offchain_cid,
                    "last_updated": time.time()
                },
                "blocks": [
                    {
                        "index": block.index,
                        "timestamp": block.timestamp,
                        "previous_hash": block.previous_hash,
                        "merkle_root": block.merkle_root,
                        "mining_capacity": block.mining_capacity.value if hasattr(block.mining_capacity, 'value') else str(block.mining_capacity),
                        "cumulative_work_score": block.cumulative_work_score,
                        "block_hash": block.block_hash,
                        "offchain_cid": block.offchain_cid
                    }
                    for block in chain
                ],
                "last_updated": time.time(),
                "consensus_version": "3.9.0-alpha.2",
                "lambda_coupling": LAMBDA,
                "processed_events_count": len(self.processed_events)
            }
            
            # Ensure data directory exists
            os.makedirs(os.path.dirname(self.blockchain_state_path), exist_ok=True)
            
            # Write to shared blockchain state file
            with open(self.blockchain_state_path, 'w') as f:
                json.dump(blockchain_state, f, indent=2)
            
            logger.info(f"📝 Blockchain state written: {len(chain)} blocks, tip: #{best_tip.index}")
            
        except Exception as e:
            logger.error(f"❌ Failed to write blockchain state: {e}")
    
    def _distribute_mining_rewards(self, event: Dict[str, Any], block: Any):
        """Automatically distribute mining rewards to the miner."""
        try:
            miner_address = event.get('miner_address', '')
            work_score = event.get('work_score', 0.0)
            
            if not miner_address:
                logger.warning("⚠️  No miner address found for reward distribution")
                return
            
            # Calculate rewards (same as API: 50 COIN base + 0.1 COIN per work score)
            base_reward = 50.0
            work_bonus = work_score * 0.1
            total_reward = base_reward + work_bonus
            
            # Log reward distribution
            logger.info(f"💰 Distributing mining rewards to {miner_address}")
            logger.info(f"   Base reward: {base_reward} COIN")
            logger.info(f"   Work bonus: {work_bonus:.2f} COIN (work score: {work_score})")
            logger.info(f"   Total reward: {total_reward:.2f} COIN")
            
            # TODO: Implement actual token transfer to miner's wallet
            # This would involve:
            # 1. Creating a transaction from network to miner
            # 2. Adding it to the blockchain state
            # 3. Updating miner's balance
            
            # For now, just log the reward calculation
            logger.info(f"🎉 Mining rewards calculated for {miner_address}: {total_reward:.2f} COIN")
            
        except Exception as e:
            logger.error(f"❌ Failed to distribute mining rewards: {e}")
    
    def run(self):
        """Main consensus service loop with λ-coupled timing."""
        self.running = True
        logger.info("🚀 Consensus service started")
        logger.info(f"🔗 λ-coupling enabled: {CONSENSUS_WRITE_INTERVAL:.2f}s intervals")
        
        while self.running:
            try:
                # Process block events with λ-coupled timing
                self.process_block_events()
                
                # Wait for λ-coupled interval
                time.sleep(1)  # Check every second, but write only at λ intervals
                
            except KeyboardInterrupt:
                logger.info("🛑 Consensus service stopping...")
                break
            except Exception as e:
                logger.error(f"❌ Consensus service error: {e}")
                time.sleep(5)  # Wait before retry
        
        self.running = False
        logger.info("✅ Consensus service stopped")

def main():
    """Main entry point."""
    service = ConsensusService()
    
    # Initialize service
    if not service.initialize():
        logger.error("❌ Failed to initialize consensus service")
        return 1
    
    # Set up signal handlers
    def signal_handler(signum, frame):
        logger.info("🛑 Received shutdown signal")
        service.running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run service
    try:
        service.run()
    except Exception as e:
        logger.error(f"❌ Consensus service failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
