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
        self.blockchain_state_path = "data/blockchain_state.json"
        
        # NEW: Initialize P2P discovery
        from p2p_discovery import P2PDiscoveryService, DiscoveryConfig
        
        discovery_config = DiscoveryConfig(
            listen_port=12346,
            bootstrap_nodes=[
                "167.172.213.70:12346",
                "167.172.213.70:12345",
                "167.172.213.70:5000"
            ],
            max_peers=100,
            discovery_interval=10.0
        )
        
        self.p2p_discovery = P2PDiscoveryService(discovery_config)
        
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
            self.ingest_store = IngestStore("/home/coinjecture/COINjecture/data/faucet_ingest.db")
            
            # Bootstrap from existing blockchain state
            if not self.bootstrap_from_cache():
                logger.warning("Bootstrap failed, starting fresh")
            
            # Start P2P discovery to find ALL network peers
            if self.p2p_discovery.start():
                logger.info("✅ P2P Discovery started - discovering ALL network peers")
                time.sleep(5)  # Wait for initial discovery
                
                stats = self.p2p_discovery.get_peer_statistics()
                logger.info(f"📊 Discovered {stats['total_discovered']} peers")
            else:
                logger.warning("⚠️  P2P Discovery failed to start")
            
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
                logger.info(f"Found {len(blocks)} blocks in blockchain state")
                
                # Add each block to consensus engine
                for block_data in blocks:
                    block = self._convert_cache_block_to_block(block_data)
                    if block:
                        # Add to block tree without validation
                        self.consensus_engine._add_block_to_tree(block, receipt_time=block.timestamp)
                        logger.info(f"Bootstrapped block #{block.index}")
                
                return True
            else:
                logger.info("No blockchain state found, starting from genesis")
                return True
        except Exception as e:
            logger.error(f"Failed to bootstrap from cache: {e}")
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
            
            # Convert capacity string to ProblemTier
            mining_capacity = ProblemTier.TIER_1_MOBILE
            if "TIER_2_DESKTOP" in mining_capacity_str:
                mining_capacity = ProblemTier.TIER_2_DESKTOP
            elif "TIER_3_SERVER" in mining_capacity_str:
                mining_capacity = ProblemTier.TIER_3_SERVER
            
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
    
    def process_all_peer_submissions(self):
        """Process submissions from ALL discovered peers."""
        try:
            peer_stats = self.p2p_discovery.get_peer_statistics()
            logger.info(f"🔍 Checking {peer_stats['total_discovered']} peers for submissions")
            
            # Get ALL events (increase limit to catch all)
            all_events = self.ingest_store.latest_blocks(limit=1000)
            pending = [e for e in all_events if e.get('event_id') not in self.processed_events]
            
            logger.info(f"📊 Found {len(pending)} pending submissions")
            
            # Sort by timestamp for ordering
            pending.sort(key=lambda e: e.get('ts', 0))
            
            processed = 0
            for event in pending:
                if not self._validate_event(event):
                    continue
                
                block = self._convert_event_to_block(event)
                if not block or self._is_duplicate(block):
                    self.processed_events.add(event.get('event_id'))
                    continue
                
                try:
                    self.consensus_engine.validate_header(block)
                    self.consensus_engine.storage.store_block(block)
                    self.consensus_engine.storage.store_header(block)
                    
                    self.processed_events.add(event.get('event_id'))
                    processed += 1
                    
                    logger.info(f"✅ Processed block #{block.index}")
                    self._distribute_mining_rewards(event, block)
                except Exception as e:
                    logger.warning(f"⚠️  Failed to process: {e}")
            
            if processed > 0:
                logger.info(f"🎉 Processed {processed} blocks from network peers")
                if self.coupling_state.can_write():
                    self._write_blockchain_state()
                    self.coupling_state.record_write()
            
            return True
        except Exception as e:
            logger.error(f"❌ Error processing peer submissions: {e}")
            return False
    
    def _convert_event_to_block(self, event: Dict[str, Any]) -> Optional[Any]:
        """Convert block event to Block object with η-damping for web mining events."""
        try:
            from core.blockchain import Block, ProblemTier, ComputationalComplexity, EnergyMetrics
            
            # η-damping: Use current chain tip + 1 instead of event's block_index
            current_chain = self.consensus_engine.get_chain_from_genesis()
            current_tip_index = current_chain[-1].index if current_chain else -1
            block_index = current_tip_index + 1
            
            # Extract event data with η-damping (graceful defaults)
            block_hash = event.get('block_hash', f'web_mined_{int(time.time())}')
            cid = event.get('cid', f'QmWebMined{int(time.time())}')
            miner_address = event.get('miner_address', 'web-miner')
            capacity = event.get('capacity', 'MOBILE')
            work_score = event.get('work_score', 1.0)
            timestamp = event.get('ts', time.time())
            
            # Convert capacity string to ProblemTier with η-damping
            mining_capacity = ProblemTier.TIER_1_MOBILE
            if "DESKTOP" in capacity.upper():
                mining_capacity = ProblemTier.TIER_2_DESKTOP
            elif "SERVER" in capacity.upper():
                mining_capacity = ProblemTier.TIER_3_SERVER
            
            # η-damping: Create minimal problem/solution for web-mined blocks
            problem = {
                'type': 'subset_sum',
                'numbers': [1, 2, 3, 4, 5],
                'target': 10,
                'size': 5
            }
            solution = [1, 2, 3, 4]
            
            # η-damping: Simplified complexity for web mining
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
            
            # η-damping: Use previous block hash from chain tip
            previous_hash = current_chain[-1].block_hash if current_chain else "0" * 64
            
            # Create Block object with η-damped validation
            block = Block(
                index=block_index,
                timestamp=timestamp,
                previous_hash=previous_hash,
                transactions=[f"Web-mined by {miner_address}"],
                merkle_root="0" * 64,  # Simplified for web mining
                problem=problem,
                solution=solution,
                complexity=complexity,
                mining_capacity=mining_capacity,
                cumulative_work_score=work_score,
                block_hash=block_hash,
                offchain_cid=cid
            )
            
            logger.info(f"✅ η-damped block conversion: #{block_index} by {miner_address}")
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
    
    def _validate_event(self, event):
        """Validate event has required fields."""
        required = ['event_id', 'block_hash', 'miner_address', 'work_score', 'ts']
        return all(field in event for field in required) and event.get('work_score', 0) > 0

    def _is_duplicate(self, block):
        """Check if block is duplicate."""
        try:
            chain = self.consensus_engine.get_chain_from_genesis()
            for existing in chain:
                if existing.index == block.index:
                    return True
            return False
        except:
            return False
    
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
            
            # Implement actual token transfer to miner's wallet
            try:
                # Import blockchain state management
                from tokenomics.blockchain_state import BlockchainState, Transaction
                
                # Initialize blockchain state if not exists
                if not hasattr(self, 'blockchain_state'):
                    self.blockchain_state = BlockchainState()
                    self.blockchain_state.load_state()
                
                # Create mining reward transaction from network to miner
                mining_transaction = Transaction(
                    sender="NETWORK_MINING_REWARDS",  # Network treasury
                    recipient=miner_address,
                    amount=total_reward,
                    timestamp=time.time()
                )
                
                # Add transaction to blockchain state
                if self.blockchain_state.add_transaction(mining_transaction):
                    # Update miner's balance
                    self.blockchain_state.update_balance(miner_address, total_reward)
                    
                    # Save updated state
                    self.blockchain_state.save_state()
                    
                    logger.info(f"✅ Mining reward transferred: {total_reward:.2f} COIN to {miner_address}")
                    logger.info(f"   Transaction ID: {mining_transaction.transaction_id}")
                    logger.info(f"   New balance: {self.blockchain_state.get_balance(miner_address):.2f} COIN")
                else:
                    logger.error(f"❌ Failed to add mining transaction for {miner_address}")
                    
            except Exception as e:
                logger.error(f"❌ Failed to transfer mining rewards: {e}")
                # Fallback to logging only
                logger.info(f"🎉 Mining rewards calculated for {miner_address}: {total_reward:.2f} COIN")
            
        except Exception as e:
            logger.error(f"❌ Failed to distribute mining rewards: {e}")
    
    def run(self):
        """Run consensus with full peer discovery."""
        if not self.initialize():
            return False
        
        self.running = True
        logger.info("🚀 Consensus started with full network peer discovery")
        logger.info("🌐 Applying λ = η = 1/√2 ≈ 0.7071")
        
        while self.running:
            try:
                # Process from ALL peers
                self.process_all_peer_submissions()
                
                # Log peer status
                stats = self.p2p_discovery.get_peer_statistics()
                logger.info(f"👥 {stats['total_discovered']} peers, {stats['connected']} connected")
                
                time.sleep(10.0)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                time.sleep(5.0)
        
        self.p2p_discovery.stop()
        self.running = False
        logger.info("✅ Consensus service stopped")
        return True

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
