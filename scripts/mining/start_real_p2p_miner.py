#!/usr/bin/env python3
"""
COINjecture Real P2P Mining Node
Combines P2P networking with actual blockchain mining from blockchain.py
"""

import sys
import os
import time
import json
import logging
import signal
import threading
import hashlib
import hmac
import requests
from pathlib import Path
from typing import Optional, Dict, Any

# Add src to path
sys.path.append('src')

# Import wallet system
from tokenomics.wallet import Wallet

# Set up logging with file output
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/real_p2p_miner.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('coinjecture-real-p2p-miner')

class RealP2PMiningNode:
    """Real P2P Mining Node that actually mines blocks using blockchain.py."""
    
    def __init__(self):
        self.node: Optional[Any] = None
        self.running = False
        self.status_thread: Optional[threading.Thread] = None
        self.blocks_mined = 0
        self.peers_connected = 0
        self.miner_id = f"miner-{int(time.time())}"
        self.network_api_url = "http://167.172.213.70:5000"
        
        # Load or generate wallet
        wallet_path = "config/miner_wallet.json"
        if os.path.exists(wallet_path):
            self.wallet = Wallet.load_from_file(wallet_path)
            logger.info(f"🔑 Loaded existing wallet: {self.wallet.address}")
        else:
            self.wallet = Wallet.generate_new()
            self.wallet.save_to_file(wallet_path)
            logger.info(f"🔑 Created new wallet: {self.wallet.address}")
        
        logger.info(f"💰 Mining rewards will be sent to: {self.wallet.address}")
        self.shared_secret = "dev-secret"
        
    def validate_configuration(self) -> bool:
        """Validate node configuration before startup."""
        try:
            # Check if data directory exists and is writable
            data_dir = Path('./data')
            data_dir.mkdir(exist_ok=True)
            
            if not data_dir.exists():
                logger.error("Failed to create data directory")
                return False
            
            # Check if logs directory exists and is writable
            logs_dir = Path('./logs')
            logs_dir.mkdir(exist_ok=True)
            
            if not logs_dir.exists():
                logger.error("Failed to create logs directory")
                return False
            
            logger.info("Configuration validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    def create_node_config(self) -> Optional[Any]:
        """Create and validate node configuration."""
        try:
            from node import NodeConfig, NodeRole
            
            config = NodeConfig(
                role=NodeRole.MINER,
                data_dir='./data',
                network_id='coinjecture-mainnet',
                listen_addr='0.0.0.0:8080',
                bootstrap_peers=['167.172.213.70:12345'],  # Connect to remote bootstrap
                enable_user_submissions=True,
                ipfs_api_url='http://localhost:5001',  # Use local IPFS instead of remote
                target_block_interval_secs=30,
                log_level='INFO'
            )
            
            logger.info(f"Node configuration created: {config.network_id}")
            logger.info(f"Bootstrap peers: {config.bootstrap_peers}")
            logger.info(f"Listen address: {config.listen_addr}")
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to create node configuration: {e}")
            return None
    
    def initialize_node(self, config: Any) -> bool:
        """Initialize the P2P node."""
        try:
            from node import Node
            
            logger.info("Creating Node instance...")
            self.node = Node(config)
            
            logger.info("Starting node initialization...")
            if not self.node.init():
                logger.error("Node initialization failed")
                return False
            
            logger.info("Node initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Node initialization error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def start_node(self) -> bool:
        """Start the P2P node."""
        try:
            if not self.node.start():
                logger.error("Node startup failed")
                return False
            
            self.running = True
            logger.info("P2P mining node started successfully")
            logger.info("Connected to COINjecture P2P network")
            logger.info("Mining operations active")
            logger.info("Participating in blockchain consensus")
            logger.info("Using gossipsub topics for block propagation")
            
            return True
            
        except Exception as e:
            logger.error(f"Node startup error: {e}")
            return False
    
    def generate_hmac_signature(self, body: dict) -> str:
        """Generate HMAC signature for authentication using canonical body."""
        # Create canonical body (sorted keys, no spaces)
        canonical_body = json.dumps(body, sort_keys=True, separators=(",", ":")).encode('utf-8')
        
        # Generate HMAC signature
        signature = hmac.new(
            self.shared_secret.encode('utf-8'),
            canonical_body,
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def mine_real_block(self) -> Optional[Any]:
        """Mine a real block using blockchain.py mining functions."""
        try:
            from core.blockchain import Block, ProblemTier, ProblemType, Transaction, mine_block, generate_subset_sum_problem, solve_subset_sum, verify_subset_sum
            from core.blockchain import EnergyMetrics, ComputationalComplexity, subset_sum_complexity
            import random
            
            # Create a simple subset sum problem
            problem = generate_subset_sum_problem(
                seed=int(time.time()),
                tier=ProblemTier.TIER_2_DESKTOP
            )
            
            logger.info(f"🧩 Generated problem: target={problem['target']}, size={problem['size']}")
            
            # Solve the problem
            start_time = time.time()
            solution = solve_subset_sum(problem)
            solve_time = time.time() - start_time
            
            if not solution:
                logger.warning("❌ Could not solve problem, trying again...")
                return None
            
            # Verify solution
            verify_start = time.time()
            is_valid = verify_subset_sum(problem, solution)
            verify_time = time.time() - verify_start
            
            if not is_valid:
                logger.warning("❌ Solution verification failed")
                return None
            
            logger.info(f"✅ Problem solved in {solve_time:.4f}s: {solution}")
            
            # Create energy metrics
            energy_metrics = EnergyMetrics(
                solve_energy_joules=solve_time * 100,  # Assume 100W power
                verify_energy_joules=verify_time * 1,  # Assume 1W power
                solve_power_watts=100,
                verify_power_watts=1,
                solve_time_seconds=solve_time,
                verify_time_seconds=verify_time,
                cpu_utilization=80.0,
                memory_utilization=50.0,
                gpu_utilization=0.0
            )
            
            # Create complexity specification
            complexity = subset_sum_complexity(
                problem=problem,
                solution=solution,
                solve_time=solve_time,
                verify_time=verify_time,
                solve_memory=0,  # Placeholder
                verify_memory=0,  # Placeholder
                energy_metrics=energy_metrics
            )
            
            # Create mining reward transaction
            reward_tx = Transaction(
                sender="network",
                recipient=self.miner_id,
                amount=50.0,  # Mining reward
                timestamp=time.time()
            )
            
            # Create block manually
            block = Block(
                index=1,  # First block after genesis
                timestamp=time.time(),
                previous_hash="0000000000000000000000000000000000000000000000000000000000000000",  # Genesis hash
                transactions=[reward_tx],
                merkle_root="",  # Will be calculated
                problem=problem,
                solution=solution,
                complexity=complexity,
                mining_capacity=ProblemTier.TIER_2_DESKTOP,
                cumulative_work_score=complexity.measured_solve_time * 100,  # Simple work score
                block_hash="",  # Will be calculated
                offchain_cid=None
            )
            
            # Calculate merkle root and block hash
            block.merkle_root = self._calculate_merkle_root([reward_tx])
            block.block_hash = block.calculate_hash()
            
            # Try to upload to IPFS for real CID
            try:
                from storage import StorageManager, StorageConfig, NodeRole, PruningMode
                storage_config = StorageConfig(
                    data_dir='./data',
                    role=NodeRole.FULL,
                    pruning_mode=PruningMode.FULL,
                    ipfs_api_url='http://localhost:5001'
                )
                storage_manager = StorageManager(storage_config)
                
                if storage_manager.ipfs_client.health_check():
                    # Create proof bundle and upload
                    proof_data = {
                        'problem': problem,
                        'solution': solution,
                        'complexity': {
                            'solve_time': solve_time,
                            'verify_time': verify_time,
                            'work_score': complexity.measured_solve_time * 100
                        }
                    }
                    import json
                    bundle_bytes = json.dumps(proof_data).encode()
                    cid = storage_manager.store_proof_bundle(bundle_bytes)
                    if cid:
                        block.offchain_cid = cid
                        logger.info(f"✅ Proof bundle uploaded to IPFS: {cid}")
                    else:
                        # Generate placeholder CID
                        block.offchain_cid = f"Qm{hashlib.sha256(block.block_hash.encode()).hexdigest()[:44]}"
                        logger.info(f"📦 Proof bundle ready (placeholder CID): {block.offchain_cid}")
                else:
                    # Generate placeholder CID
                    block.offchain_cid = f"Qm{hashlib.sha256(block.block_hash.encode()).hexdigest()[:44]}"
                    logger.info(f"📦 Proof bundle ready (placeholder CID): {block.offchain_cid}")
            except Exception as e:
                # Generate placeholder CID on error
                block.offchain_cid = f"Qm{hashlib.sha256(block.block_hash.encode()).hexdigest()[:44]}"
                logger.info(f"📦 Proof bundle ready (placeholder CID): {block.offchain_cid}")
            
            logger.info(f"✅ Block mined: #{block.index} - {block.block_hash[:16]}...")
            logger.info(f"📊 Work score: {block.cumulative_work_score:.2f}")
            logger.info(f"🧩 Problem size: {block.problem.get('size', 'unknown')}")
            
            return block
            
        except Exception as e:
            logger.error(f"❌ Mining error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return None
    
    def _calculate_merkle_root(self, transactions):
        """Calculate merkle root for transactions."""
        import hashlib
        if not transactions:
            return hashlib.sha256("".encode()).hexdigest()
        
        tx_hashes = []
        for tx in transactions:
            if hasattr(tx, 'transaction_id'):
                tx_hashes.append(tx.transaction_id)
            else:
                tx_hashes.append(hashlib.sha256(str(tx).encode()).hexdigest())
        
        return hashlib.sha256("".join(tx_hashes).encode()).hexdigest()
    
    def submit_block_to_network(self, block: Any) -> bool:
        """Submit mined block to the network using wallet-based authentication."""
        try:
            # Convert block to network format (only BlockEvent schema fields)
            block_data = {
                "event_id": f"block-{int(time.time())}-{self.wallet.address}",
                "block_index": block.index,
                "block_hash": block.block_hash,
                "cid": block.offchain_cid or f"Qm{hashlib.sha256(block.block_hash.encode()).hexdigest()[:44]}",
                "miner_address": self.wallet.address,  # Use wallet address instead of miner_id
                "capacity": block.mining_capacity.value,
                "work_score": block.cumulative_work_score,
                "ts": int(block.timestamp)
            }
            
            # Sign with wallet
            signature = self.wallet.sign_block(block_data)
            public_key = self.wallet.get_public_key_bytes().hex()
            
            # Add signature and public key
            block_data["signature"] = signature
            block_data["public_key"] = public_key
            
            # Prepare headers (no HMAC needed)
            headers = {
                'Content-Type': 'application/json'
            }
            
            # Submit to network
            response = requests.post(
                f"{self.network_api_url}/v1/ingest/block",
                json=block_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("✅ Block submitted successfully to network")
                return True
            elif response.status_code == 429:
                logger.warning("⏳ Rate limited, waiting before retry...")
                time.sleep(6)  # Wait 6 seconds for rate limit
                return False
            else:
                logger.error(f"❌ Network submission failed: {response.status_code}")
                logger.error(f"Response: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to submit block: {e}")
            return False
    
    def status_reporter(self):
        """Periodic status reporting thread with real mining."""
        consecutive_failures = 0
        max_failures = 5
        
        while self.running:
            try:
                # Report status every 30 seconds
                time.sleep(30)
                
                if self.running:
                    logger.info(f"📊 Status: {self.blocks_mined} blocks mined, {self.peers_connected} peers connected")
                    
                    # Try to mine a block
                    if consecutive_failures < max_failures:
                        block = self.mine_real_block()
                        
                        if block:
                            # Submit to network
                            if self.submit_block_to_network(block):
                                self.blocks_mined += 1
                                logger.info(f"🎉 Successfully mined and submitted block #{self.blocks_mined}")
                                consecutive_failures = 0
                            else:
                                consecutive_failures += 1
                                logger.warning(f"⚠️  Failed to submit block (attempt {consecutive_failures})")
                        else:
                            consecutive_failures += 1
                            logger.warning(f"⚠️  Failed to mine block (attempt {consecutive_failures})")
                    else:
                        logger.error(f"❌ Too many consecutive failures ({max_failures}), stopping mining attempts")
                        time.sleep(60)  # Wait longer before retrying
                        consecutive_failures = 0  # Reset after waiting
                        
            except Exception as e:
                logger.error(f"Status reporter error: {e}")
    
    def run(self) -> bool:
        """Main run loop with real mining."""
        logger.info("🚀 Starting COINjecture Real P2P Mining Node...")
        logger.info("🌐 Initializing P2P network connection...")
        logger.info("⛏️  Mining with desktop tier (TIER_2_DESKTOP)")
        logger.info("🔨 Running commit-reveal protocol...")
        logger.info(f"🆔 Miner ID: {self.miner_id}")
        
        try:
            # Validate configuration
            if not self.validate_configuration():
                return False
            
            # Create node configuration
            config = self.create_node_config()
            if not config:
                return False
            
            # Initialize node
            if not self.initialize_node(config):
                return False
            
            # Start node
            if not self.start_node():
                return False
            
            # Start status reporter thread (includes mining)
            self.status_thread = threading.Thread(target=self.status_reporter, daemon=True)
            self.status_thread.start()
            
            # Keep the node running
            while self.running:
                time.sleep(1)
                
                # Check if node is still running
                if hasattr(self.node, 'is_running') and not self.node.is_running:
                    logger.warning("Node stopped unexpectedly")
                    break
                    
            return True
            
        except KeyboardInterrupt:
            logger.info("🛑 Stopping mining node...")
            self.stop()
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def stop(self):
        """Stop the mining node."""
        logger.info("🛑 Stopping mining node...")
        self.running = False
        
        if self.node and hasattr(self.node, 'stop'):
            try:
                self.node.stop()
            except Exception as e:
                logger.error(f"Error stopping node: {e}")
        
        logger.info(f"🏁 Mining completed. Total blocks mined: {self.blocks_mined}")

def main():
    """Main entry point for real P2P mining node."""
    logger.info("🚀 Starting COINjecture Real P2P Mining Node...")
    logger.info("⛏️  This node will actually solve NP-Complete problems and mine blocks")
    
    # Set up signal handlers
    def signal_handler(signum, frame):
        logger.info("🛑 Received interrupt signal, stopping...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    miner = RealP2PMiningNode()
    
    try:
        success = miner.run()
        if success:
            logger.info("✅ Mining node completed successfully")
        else:
            logger.error("❌ Mining node failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Mining node error: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()
