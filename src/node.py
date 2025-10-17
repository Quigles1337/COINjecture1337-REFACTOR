"""
COINjecture Node Module

Implements node configuration, role selection, lifecycle management,
and service composition with user submissions integration.

Based on docs/blockchain/node.md specification.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
import time
import logging
import json
import os
from pathlib import Path

# Core blockchain imports
try:
    from .core.blockchain import Block, ProblemType, ProblemTier
    from .pow import ProblemRegistry, DifficultyAdjuster
    from .storage import StorageManager, StorageConfig, IPFSClient, PruningMode
    from .consensus import ConsensusEngine, ConsensusConfig
    from .network import NetworkProtocol
    from .user_submissions.pool import ProblemPool
    from .user_submissions.submission import ProblemSubmission, SolutionRecord
    from .user_submissions.aggregation import AggregationStrategy
except ImportError:
    # Fallback for direct execution
    from core.blockchain import Block, ProblemType, ProblemTier
    from pow import ProblemRegistry, DifficultyAdjuster
    from storage import StorageManager, StorageConfig, IPFSClient, PruningMode
    from consensus import ConsensusEngine, ConsensusConfig
    from network import NetworkProtocol
    from user_submissions.pool import ProblemPool
    from user_submissions.submission import ProblemSubmission, SolutionRecord
    from user_submissions.aggregation import AggregationStrategy


class NodeRole(Enum):
    """Node roles and their capabilities."""
    LIGHT = "light"      # Subscribe headers; validate commitments; request bundles on demand
    FULL = "full"        # Validate headers + reveals; selective bundle fetch; participate in fork choice
    MINER = "miner"      # Run commit–reveal loop; publish headers and reveals
    ARCHIVE = "archive"  # Validate and pin all bundles; serve data to peers


@dataclass
class NodeConfig:
    """Node configuration structure."""
    # Network configuration
    network_id: str = "coinjecture-mainnet"
    listen_addr: str = "0.0.0.0:8080"
    bootstrap_peers: List[str] = field(default_factory=list)
    
    # Node role and capabilities
    role: NodeRole = NodeRole.FULL
    
    # Storage configuration
    ipfs_api_url: str = "http://localhost:5001"
    pin_policy: str = "selective"  # selective, all, none
    pruning_mode: str = "aggressive"  # aggressive, conservative, none
    
    # Mining configuration (for miners)
    target_block_interval_secs: int = 30
    difficulty_window: int = 10
    
    # Logging and metrics
    log_level: str = "INFO"
    metrics_port: int = 9090
    
    # Data directory
    data_dir: str = "./data"
    
    # User submissions configuration
    enable_user_submissions: bool = True
    max_pending_submissions: int = 100
    submission_timeout_hours: int = 24


class Node:
    """
    COINjecture Node implementation.
    
    Manages node lifecycle, service composition, and role-based behavior
    with integrated user submissions system.
    """
    
    def __init__(self, config: NodeConfig):
        self.config = config
        self.logger = self._setup_logging()
        
        # Core services
        self.storage: Optional[StorageManager] = None
        self.network: Optional[NetworkProtocol] = None
        self.consensus: Optional[ConsensusEngine] = None
        self.problem_registry: Optional[ProblemRegistry] = None
        self.difficulty_adjuster: Optional[DifficultyAdjuster] = None
        
        # User submissions integration
        self.problem_pool: Optional[ProblemPool] = None
        
        # Node state
        self.is_running = False
        self.current_block_height = 0
        self.best_tip_hash: Optional[str] = None
        
        # Mining state (for miners)
        self.mining_active = False
        self.last_block_time = 0.0
        
        self.logger.info(f"Node initialized with role: {config.role.value}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger(f"coinjecture-node-{self.config.role.value}")
        logger.setLevel(getattr(logging, self.config.log_level.upper()))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def init(self) -> bool:
        """
        Initialize node services and data directory.
        
        Returns:
            bool: True if initialization successful, False otherwise
        """
        try:
            self.logger.info("Initializing COINjecture node...")
            
            # Create data directory
            data_path = Path(self.config.data_dir)
            data_path.mkdir(parents=True, exist_ok=True)
            
            # Initialize storage
            # Map pruning mode string to enum
            pruning_mode_map = {
                "aggressive": PruningMode.LIGHT,
                "conservative": PruningMode.FULL,
                "none": PruningMode.ARCHIVE
            }
            pruning_mode = pruning_mode_map.get(self.config.pruning_mode, PruningMode.FULL)
            
            storage_config = StorageConfig(
                data_dir=self.config.data_dir,
                ipfs_api_url=self.config.ipfs_api_url,
                role=self.config.role,
                pruning_mode=pruning_mode
            )
            self.storage = StorageManager(storage_config)
            
            # Initialize problem registry and difficulty adjuster
            self.problem_registry = ProblemRegistry()
            self.difficulty_adjuster = DifficultyAdjuster()
            
            # Initialize consensus engine
            consensus_config = ConsensusConfig(
                genesis_seed="coinjecture-genesis-2025"
            )
            self.consensus = ConsensusEngine(
                consensus_config,
                self.storage,
                self.problem_registry
            )
            
            # Initialize network protocol
            # NetworkProtocol requires consensus, storage, and problem_registry
            # We'll initialize it after consensus is created
            self.network = None
            
            # Initialize user submissions system
            if self.config.enable_user_submissions:
                self.problem_pool = ProblemPool()
                self.logger.info("User submissions system enabled")
            
            self.logger.info("Node initialization completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Node initialization failed: {e}")
            return False
    
    def start(self) -> bool:
        """
        Start node services and begin participation.
        
        Returns:
            bool: True if startup successful, False otherwise
        """
        try:
            self.logger.info("Starting COINjecture node...")
            
            if not self.storage or not self.consensus or not self.network:
                raise Exception("Node not properly initialized")
            
            # Start storage
            self.storage.start()
            self.logger.info("Storage service started")
            
            # Initialize and start network protocol
            self.network = NetworkProtocol(
                consensus=self.consensus,
                storage=self.storage,
                problem_registry=self.problem_registry,
                peer_id=f"node-{self.config.role.value}"
            )
            self.logger.info("Network service started")
            
            # Sync headers
            self._sync_headers()
            
            # Start role-specific services
            self._start_role_services()
            
            self.is_running = True
            self.logger.info(f"Node started successfully in {self.config.role.value} mode")
            return True
            
        except Exception as e:
            self.logger.error(f"Node startup failed: {e}")
            return False
    
    def stop(self) -> None:
        """Stop node services gracefully."""
        self.logger.info("Stopping COINjecture node...")
        
        self.is_running = False
        self.mining_active = False
        
        if self.network:
            # NetworkProtocol doesn't have a stop method, just set to None
            self.network = None
        
        if self.storage:
            self.storage.stop()
        
        self.logger.info("Node stopped")
    
    def _sync_headers(self) -> None:
        """Sync blockchain headers from network."""
        self.logger.info("Syncing blockchain headers...")
        
        # Get best tip from consensus
        best_tip = self.consensus.get_best_tip()
        if best_tip:
            self.best_tip_hash = best_tip.block_hash
            self.current_block_height = best_tip.index
            self.logger.info(f"Synced to block {self.current_block_height}: {self.best_tip_hash[:16]}...")
        else:
            self.logger.info("No existing blockchain found, starting from genesis")
    
    def _start_role_services(self) -> None:
        """Start role-specific services."""
        if self.config.role == NodeRole.MINER:
            self._start_mining()
        elif self.config.role == NodeRole.ARCHIVE:
            self._start_archiving()
        elif self.config.role == NodeRole.LIGHT:
            self._start_light_client()
        elif self.config.role == NodeRole.FULL:
            self._start_full_node()
    
    def _start_mining(self) -> None:
        """Start mining operations with user submissions integration."""
        self.logger.info("Starting mining operations...")
        self.mining_active = True
        
        # Start mining loop in background thread
        import threading
        mining_thread = threading.Thread(target=self._mining_loop, daemon=True)
        mining_thread.start()
    
    def _mining_loop(self) -> None:
        """Main mining loop with user submissions integration."""
        while self.mining_active and self.is_running:
            try:
                # Check for user-submitted problems first
                problem_data = self._get_problem_for_mining()
                
                if problem_data:
                    self._mine_block_with_problem(problem_data)
                else:
                    # Fall back to consensus-generated problems
                    self._mine_consensus_block()
                
                # Wait for next mining cycle
                time.sleep(1.0)
                
            except Exception as e:
                self.logger.error(f"Mining loop error: {e}")
                time.sleep(5.0)
    
    def _get_problem_for_mining(self) -> Optional[Dict[str, Any]]:
        """
        Get problem for mining from user submissions pool.
        
        Returns:
            Optional[Dict]: Problem data if available, None otherwise
        """
        if not self.problem_pool:
            return None
        
        # Determine miner hardware tier (simplified)
        miner_tier = ProblemTier.TIER_3_SERVER  # Default to server tier
        miner_hardware = "CPU"  # Simplified hardware type
        
        # Query problem pool for submissions
        submission_result = self.problem_pool.select_problem_for_mining(
            miner_tier=miner_tier,
            miner_hardware=miner_hardware
        )
        
        if submission_result:
            submission_id, submission = submission_result
            self.logger.info(f"Selected user submission {submission_id} for mining")
            
            return {
                "submission_id": submission_id,
                "submission": submission,
                "problem_type": submission.problem_type,
                "problem_template": submission.problem_template,
                "bounty": submission.bounty_per_solution
            }
        
        return None
    
    def _mine_block_with_problem(self, problem_data: Dict[str, Any]) -> None:
        """Mine a block using a user-submitted problem."""
        try:
            submission_id = problem_data["submission_id"]
            submission = problem_data["submission"]
            
            self.logger.info(f"Mining block with user submission: {submission_id}")
            
            # Generate problem instance from template
            problem_instance = self.problem_registry.generate_from_template(
                problem_type=ProblemType.SUBSET_SUM,  # Simplified
                template=submission.problem_template,
                capacity=ProblemTier.TIER_3_SERVER
            )
            
            # Solve the problem (simplified)
            solution = self._solve_problem(problem_instance)
            
            # Create block with user problem
            block = self.consensus.create_block(
                problem=problem_instance,
                solution=solution,
                previous_hash=self.best_tip_hash or "0" * 64
            )
            
            # Record solution in submission
            solution_record = SolutionRecord(
                block_number=block.index,
                block_hash=block.block_hash,
                miner_address="miner-address",  # TODO: Get actual miner address
                problem_instance=problem_instance,
                solution=solution,
                solution_quality=1.0,  # TODO: Calculate actual quality
                work_score=block.cumulative_work_score,
                solve_time=0.1,  # TODO: Measure actual solve time
                energy_used=0.0,  # TODO: Measure actual energy
                verified=True,
                verification_time=0.01
            )
            
            self.problem_pool.record_solution(submission_id, solution_record)
            
            # Update node state
            self.best_tip_hash = block.block_hash
            self.current_block_height = block.index
            self.last_block_time = time.time()
            
            self.logger.info(f"Mined block {block.index} with user submission {submission_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to mine block with user problem: {e}")
    
    def _mine_consensus_block(self) -> None:
        """Mine a block using consensus-generated problems."""
        try:
            self.logger.debug("Mining consensus block...")
            
            # Generate consensus problem
            problem = self.problem_registry.generate(
                problem_type=ProblemType.SUBSET_SUM,
                seed=f"consensus-{int(time.time())}",
                capacity=ProblemTier.TIER_3_SERVER
            )
            
            # Solve the problem
            solution = self._solve_problem(problem)
            
            # Create block
            block = self.consensus.create_block(
                problem=problem,
                solution=solution,
                previous_hash=self.best_tip_hash or "0" * 64
            )
            
            # Update node state
            self.best_tip_hash = block.block_hash
            self.current_block_height = block.index
            self.last_block_time = time.time()
            
            self.logger.info(f"Mined consensus block {block.index}")
            
        except Exception as e:
            self.logger.error(f"Failed to mine consensus block: {e}")
    
    def _solve_problem(self, problem: Dict[str, Any]) -> Any:
        """
        Solve a computational problem (simplified implementation).
        
        Args:
            problem: Problem instance to solve
            
        Returns:
            Any: Problem solution
        """
        # Simplified subset sum solver
        if problem.get("type") == "subset_sum":
            numbers = problem.get("numbers", [])
            target = problem.get("target", 0)
            
            # Simple greedy solution (not optimal, for demonstration)
            solution = []
            current_sum = 0
            
            for num in sorted(numbers, reverse=True):
                if current_sum + num <= target:
                    solution.append(num)
                    current_sum += num
                    if current_sum == target:
                        break
            
            return {
                "subset": solution,
                "sum": sum(solution),
                "target": target
            }
        
        return {"error": "unsupported_problem_type"}
    
    def _start_archiving(self) -> None:
        """Start archive node services."""
        self.logger.info("Starting archive node services...")
        # Archive nodes pin all bundles and serve data to peers
        # Implementation would include IPFS pinning and data serving
    
    def _start_light_client(self) -> None:
        """Start light client services."""
        self.logger.info("Starting light client services...")
        # Light clients subscribe to headers and validate commitments
        # Implementation would include header subscription and validation
    
    def _start_full_node(self) -> None:
        """Start full node services."""
        self.logger.info("Starting full node services...")
        # Full nodes validate headers and reveals, participate in fork choice
        # Implementation would include full validation and fork choice participation
    
    # User submissions API methods
    
    def submit_problem(self, problem_type: str, problem_template: Dict[str, Any], 
                      aggregation: AggregationStrategy, bounty: float, 
                      min_quality: float = 0.0) -> Optional[str]:
        """
        Submit a problem to the user submissions pool.
        
        Args:
            problem_type: Type of problem (e.g., "subset_sum")
            problem_template: Problem template/parameters
            aggregation: Aggregation strategy for solutions
            bounty: Bounty per solution
            min_quality: Minimum solution quality threshold
            
        Returns:
            Optional[str]: Submission ID if successful, None otherwise
        """
        if not self.problem_pool:
            # Initialize problem pool if not already done
            if self.config.enable_user_submissions:
                self.problem_pool = ProblemPool()
                self.logger.info("User submissions system initialized")
            else:
                self.logger.error("User submissions not enabled")
                return None
        
        try:
            submission_id = f"submission-{int(time.time())}-{len(self.problem_pool.pending_problems)}"
            
            submission = ProblemSubmission(
                problem_type=problem_type,
                problem_template=problem_template,
                seeding_strategy="template",
                aggregation=aggregation,
                aggregation_params={"max_blocks": 5},  # Default params
                bounty_per_solution=bounty,
                min_quality=min_quality
            )
            
            self.problem_pool.add_submission(submission_id, submission)
            
            self.logger.info(f"Problem submitted: {submission_id}")
            return submission_id
            
        except Exception as e:
            self.logger.error(f"Failed to submit problem: {e}")
            return None
    
    def get_submission_status(self, submission_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of a problem submission.
        
        Args:
            submission_id: Submission ID to query
            
        Returns:
            Optional[Dict]: Submission status if found, None otherwise
        """
        if not self.problem_pool:
            return None
        
        try:
            from .user_submissions.tracker import SubmissionTracker
        except ImportError:
            from user_submissions.tracker import SubmissionTracker
        
        tracker = SubmissionTracker(self.problem_pool)
        return tracker.get_submission_status(submission_id)
    
    def list_active_submissions(self) -> List[Dict[str, Any]]:
        """
        List all active problem submissions.
        
        Returns:
            List[Dict]: List of active submissions
        """
        if not self.problem_pool:
            return []
        
        active_submissions = []
        for submission_id, submission in self.problem_pool.pending_problems.items():
            if submission.is_accepting_solutions():
                active_submissions.append({
                    "submission_id": submission_id,
                    "problem_type": submission.problem_type,
                    "bounty": submission.bounty_per_solution,
                    "status": submission.status,
                    "solutions_count": len(submission.solutions_collected)
                })
        
        return active_submissions


def load_config(config_path: str) -> NodeConfig:
    """
    Load node configuration from file.
    
    Args:
        config_path: Path to configuration file (TOML/YAML)
        
    Returns:
        NodeConfig: Loaded configuration
    """
    config_path = Path(config_path)
    
    if not config_path.exists():
        # Return default config
        return NodeConfig()
    
    try:
        if config_path.suffix == '.json':
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        else:
            # Default to JSON for now
            with open(config_path, 'r') as f:
                config_data = json.load(f)
        
        # Convert role string to enum if needed
        if 'role' in config_data and isinstance(config_data['role'], str):
            role_map = {
                'light': NodeRole.LIGHT,
                'full': NodeRole.FULL,
                'miner': NodeRole.MINER,
                'archive': NodeRole.ARCHIVE
            }
            config_data['role'] = role_map.get(config_data['role'], NodeRole.FULL)
        
        # Convert to NodeConfig
        return NodeConfig(**config_data)
        
    except Exception as e:
        logging.error(f"Failed to load config from {config_path}: {e}")
        return NodeConfig()


def create_node(config_path: Optional[str] = None) -> Node:
    """
    Create and initialize a COINjecture node.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Node: Initialized node instance
    """
    if config_path:
        config = load_config(config_path)
    else:
        config = NodeConfig()
    
    node = Node(config)
    
    if not node.init():
        raise Exception("Failed to initialize node")
    
    return node


# Example usage and testing
if __name__ == "__main__":
    # Create a miner node for testing
    config = NodeConfig(
        role=NodeRole.MINER,
        enable_user_submissions=True,
        data_dir="./test_data"
    )
    
    node = Node(config)
    
    if node.init() and node.start():
        print("✅ Node started successfully")
        
        # Test user submission
        submission_id = node.submit_problem(
            problem_type="subset_sum",
            problem_template={"numbers": [1, 2, 3, 4, 5], "target": 7},
            aggregation=AggregationStrategy.BEST,
            bounty=100.0
        )
        
        if submission_id:
            print(f"✅ Problem submitted: {submission_id}")
            
            # Check status
            status = node.get_submission_status(submission_id)
            print(f"✅ Submission status: {status}")
        
        # List active submissions
        active = node.list_active_submissions()
        print(f"✅ Active submissions: {len(active)}")
        
        # Let it run for a bit
        import time
        time.sleep(10)
        
        node.stop()
        print("✅ Node stopped")
    else:
        print("❌ Failed to start node")
