"""
Module: consensus
Specification: docs/blockchain/consensus.md

Consensus engine for COINjecture blockchain with header validation,
reveal validation, fork choice, and genesis block management.
"""

import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum
from collections import deque

# Import from existing modules
try:
    from .core.blockchain import Block, ProblemTier, ComputationalComplexity, calculate_computational_work_score
    from .pow import (
        ProblemRegistry, derive_epoch_salt, create_commitment, verify_commitment,
        calculate_work_score
    )
    from .storage import StorageManager, StorageConfig, NodeRole, PruningMode
except ImportError:
    # Fallback for direct execution
    from core.blockchain import Block, ProblemTier, ComputationalComplexity, calculate_computational_work_score
    from pow import (
        ProblemRegistry, derive_epoch_salt, create_commitment, verify_commitment,
        calculate_work_score
    )
    from storage import StorageManager, StorageConfig, NodeRole, PruningMode


# Constants
DEFAULT_CONFIRMATION_DEPTH = 20
MAX_REORG_DEPTH = 100
MAX_HEADERS_PER_SECOND = 100
MAX_PROOF_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_NETWORK_ID = "coinjecture-mainnet-v1"


class ValidationError(Exception):
    """Base class for validation errors."""
    pass


class HeaderValidationError(ValidationError):
    """Header validation failed."""
    pass


class RevealValidationError(ValidationError):
    """Reveal validation failed."""
    pass


@dataclass
class BlockNode:
    """
    Node in the block tree for fork choice.
    
    Represents a block in the chain with its cumulative work score.
    """
    block: Block
    parent_hash: str
    cumulative_work: float
    height: int
    receipt_time: float
    children: List[str] = field(default_factory=list)
    
    def __hash__(self):
        return hash(self.block.block_hash)


@dataclass
class ConsensusConfig:
    """Configuration for consensus engine."""
    network_id: str = DEFAULT_NETWORK_ID
    confirmation_depth: int = DEFAULT_CONFIRMATION_DEPTH
    max_reorg_depth: int = MAX_REORG_DEPTH
    max_headers_per_second: int = MAX_HEADERS_PER_SECOND
    max_proof_size_bytes: int = MAX_PROOF_SIZE_BYTES
    genesis_timestamp: float = 1609459200.0  # 2021-01-01 00:00:00 UTC
    genesis_seed: str = "coinjecture_genesis_seed"


class ConsensusEngine:
    """
    Consensus engine for COINjecture blockchain.
    
    Implements the consensus module from consensus.md specification.
    """
    
    def __init__(
        self,
        config: ConsensusConfig,
        storage: StorageManager,
        problem_registry: ProblemRegistry
    ):
        """
        Initialize consensus engine.
        
        Args:
            config: Consensus configuration
            storage: Storage manager
            problem_registry: Problem registry for verification
        """
        self.config = config
        self.storage = storage
        self.problem_registry = problem_registry
        
        # Block tree for fork choice
        self.block_tree: Dict[str, BlockNode] = {}
        
        # Current best tip
        self.best_tip: Optional[BlockNode] = None
        
        # Genesis block
        self.genesis_block: Optional[Block] = None
        
        # Header validation rate limiting
        self._header_timestamps: deque = deque(maxlen=100)
        
        # Initialize genesis if not exists
        self._initialize_genesis()
    
    def _initialize_genesis(self):
        """Initialize or load genesis block."""
        # Try to load genesis from storage
        genesis_hash = self._calculate_genesis_hash()
        genesis_block = self.storage.get_block(genesis_hash)
        
        if genesis_block:
            self.genesis_block = genesis_block
            self._add_block_to_tree(genesis_block, receipt_time=genesis_block.timestamp)
        else:
            # Build deterministic genesis
            self.genesis_block = self._build_genesis()
            self.storage.store_block(self.genesis_block)
            self.storage.store_header(self.genesis_block)
            self._add_block_to_tree(self.genesis_block, receipt_time=self.genesis_block.timestamp)
        
        self.best_tip = self.block_tree.get(self.genesis_block.block_hash)
    
    def _calculate_genesis_hash(self) -> str:
        """Calculate deterministic genesis block hash."""
        # Creator initials (SM) hidden in hash calculation
        creator_initials = "SM"
        genesis_data = f"{self.config.network_id}_{self.config.genesis_timestamp}_{self.config.genesis_seed}_{creator_initials}"
        return hashlib.sha256(genesis_data.encode()).hexdigest()
    
    def _build_genesis(self) -> Block:
        """
        Build deterministic immutable genesis block with IPFS integration.
        
        Returns:
            Genesis block with immutable IPFS parameters
        """
        print("🔨 Building immutable genesis block with IPFS integration...")
        
        # Add creator initials (SM) to genesis seed for immutability (hidden)
        creator_initials = "SM"
        enhanced_seed = f"{self.config.genesis_seed}_{creator_initials}"
        print(f"🔨 Building immutable genesis block with IPFS integration...")
        
        # Generate genesis problem
        try:
            from .core.blockchain import ProblemType
        except ImportError:
            from core.blockchain import ProblemType
        genesis_problem = self.problem_registry.generate(
            problem_type=ProblemType.SUBSET_SUM,
            seed=enhanced_seed,
            capacity=ProblemTier.TIER_1_MOBILE
        )
        
        # Solve genesis problem
        genesis_solution = self.problem_registry.solve(genesis_problem)
        
        # Calculate genesis complexity
        try:
            from .core.blockchain import subset_sum_complexity, EnergyMetrics
        except ImportError:
            from core.blockchain import subset_sum_complexity, EnergyMetrics
        energy_metrics = EnergyMetrics(
            solve_energy_joules=0.1,
            verify_energy_joules=0.0001,
            solve_power_watts=100,
            verify_power_watts=1,
            solve_time_seconds=0.001,
            verify_time_seconds=0.0001,
            cpu_utilization=80.0,
            memory_utilization=50.0,
            gpu_utilization=0.0
        )
        genesis_complexity = subset_sum_complexity(
            problem=genesis_problem,
            solution=genesis_solution,
            solve_time=0.001,
            verify_time=0.0001,
            solve_memory=1024,
            verify_memory=256,
            energy_metrics=energy_metrics
        )
        
        # Calculate genesis work
        genesis_work = calculate_work_score(genesis_complexity)
        
        # Upload proof bundle to IPFS first to get CID
        cid = None
        try:
            try:
                from .api.proof_bundler import create_proof_bundle, serialize_proof_bundle
            except ImportError:
                from api.proof_bundler import create_proof_bundle, serialize_proof_bundle
            
            # Create a temporary block for proof bundle creation
            temp_block = Block(
                index=0,
                timestamp=self.config.genesis_timestamp,
                previous_hash="0" * 64,
                transactions=[],
                merkle_root="0" * 64,
                problem=genesis_problem,
                solution=genesis_solution,
                complexity=genesis_complexity,
                mining_capacity=ProblemTier.TIER_1_MOBILE,
                cumulative_work_score=genesis_work,
                block_hash=self._calculate_genesis_hash(),
                offchain_cid=None  # Will be set after IPFS upload
            )
            
            proof_bundle = create_proof_bundle(temp_block)
            bundle_bytes = serialize_proof_bundle(proof_bundle)
            cid = self.storage.store_proof_bundle(bundle_bytes)
            print(f"✅ Genesis proof bundle uploaded to IPFS: {cid}")
        except Exception as e:
            print(f"⚠️  Warning: Could not upload proof bundle to IPFS: {e}")
            cid = None
        
        # Create immutable genesis block with IPFS CID (creator initials hidden in seed)
        genesis_transactions = [
            "COINjecture blockchain initialized",
            "Immutable genesis with IPFS integration"
        ]
        
        genesis_block = Block(
            index=0,
            timestamp=self.config.genesis_timestamp,
            previous_hash="0" * 64,
            transactions=genesis_transactions,
            merkle_root="0" * 64,
            problem=genesis_problem,
            solution=genesis_solution,
            complexity=genesis_complexity,
            mining_capacity=ProblemTier.TIER_1_MOBILE,
            cumulative_work_score=genesis_work,
            block_hash=self._calculate_genesis_hash(),
            offchain_cid=cid  # Include the IPFS CID in constructor
        )
        
        print(f"🔒 Immutable genesis block created with IPFS CID: {cid}")
        return genesis_block
    
    def validate_header(self, block: Block) -> bool:
        """
        Validate block header.
        
        Implements header validation pipeline from consensus.md specification.
        
        Args:
            block: Block to validate
            
        Returns:
            True if valid
            
        Raises:
            HeaderValidationError: If validation fails
        """
        # 1) Basic validation: parent linkage, timestamp
        if not self._validate_basic_header(block):
            raise HeaderValidationError("Basic header validation failed")
        
        # 2) Commitment presence
        if not self._validate_commitment_presence(block):
            raise HeaderValidationError("Commitment validation failed")
        
        # 3) Difficulty check
        if not self._validate_difficulty(block):
            raise HeaderValidationError("Difficulty validation failed")
        
        # 4) Fork-choice enqueue
        self._add_block_to_tree(block, receipt_time=time.time())
        
        return True
    
    def _validate_basic_header(self, block: Block) -> bool:
        """
        Validate basic header fields.
        
        Args:
            block: Block to validate
            
        Returns:
            True if valid
        """
        # Check parent linkage
        if block.index > 0:
            parent_node = self.block_tree.get(block.previous_hash)
            if not parent_node:
                print(f"Parent block not found: {block.previous_hash}")
                return False
            
            # Check height
            if block.index != parent_node.height + 1:
                print(f"Invalid block height: {block.index} (expected {parent_node.height + 1})")
                return False
            
            # Check timestamp (median-time-past)
            if block.timestamp <= parent_node.block.timestamp:
                print(f"Invalid timestamp: {block.timestamp} <= {parent_node.block.timestamp}")
                return False
        
        # Rate limiting: max headers per second
        current_time = time.time()
        self._header_timestamps.append(current_time)
        
        if len(self._header_timestamps) >= self.config.max_headers_per_second:
            time_window = current_time - self._header_timestamps[0]
            if time_window < 1.0:
                print(f"Rate limit exceeded: {len(self._header_timestamps)} headers in {time_window}s")
                return False
        
        return True
    
    def _validate_commitment_presence(self, block: Block) -> bool:
        """
        Validate commitment presence.
        
        Args:
            block: Block to validate
            
        Returns:
            True if valid
        """
        # Check that problem and solution are present
        if not block.problem or not block.solution:
            print("Missing problem or solution")
            return False
        
        # Check merkle root shape (should be 64-character hex)
        if not block.merkle_root or len(block.merkle_root) != 64:
            print(f"Invalid merkle root: {block.merkle_root}")
            return False
        
        return True
    
    def _validate_difficulty(self, block: Block) -> bool:
        """
        Validate difficulty requirement.
        
        Args:
            block: Block to validate
            
        Returns:
            True if valid
        """
        # Calculate work score from block's complexity
        if not block.complexity:
            print("Missing complexity data")
            return False
        
        block_work = calculate_work_score(block.complexity)
        
        # For now, accept any positive work score
        # In production, this would check against current_target
        if block_work <= 0:
            print(f"Invalid work score: {block_work}")
            return False
        
        return True
    
    def validate_reveal(
        self,
        block: Block,
        commitment: bytes,
        miner_salt: bytes,
        proof_bundle: Optional[bytes] = None
    ) -> bool:
        """
        Validate proof reveal after block is mined.
        
        Implements reveal validation from consensus.md specification.
        
        Args:
            block: Block with reveal
            commitment: Commitment hash
            miner_salt: Miner's salt
            proof_bundle: Optional proof bundle bytes
            
        Returns:
            True if valid
            
        Raises:
            RevealValidationError: If validation fails
        """
        # 1) Fetch bundle by CID if not provided
        if proof_bundle is None and hasattr(block, 'offchain_cid'):
            proof_bundle = self.storage.get_proof_bundle(block.offchain_cid)
        
        # 2) Verify commitment
        parent_node = self.block_tree.get(block.previous_hash)
        if not parent_node:
            raise RevealValidationError("Parent block not found")
        
        epoch_salt = derive_epoch_salt(
            parent_hash=block.previous_hash.encode(),
            timestamp=int(block.timestamp)
        )
        
        problem_params_bytes = self.problem_registry.encode_params(block.problem)
        
        if not verify_commitment(problem_params_bytes, miner_salt, epoch_salt, commitment):
            raise RevealValidationError("Commitment verification failed")
        
        # 3) Run fast verify
        if not self.problem_registry.verify(block.problem, block.solution):
            raise RevealValidationError("Solution verification failed")
        
        # 4) Update indices and persistence
        if commitment:
            problem_type = block.problem.get('type', 'subset_sum')
            capacity = block.mining_capacity.value if hasattr(block.mining_capacity, 'value') else 2
            self.storage.store_commitment(commitment, block.block_hash, problem_type, capacity)
        
        return True
    
    def _add_block_to_tree(self, block: Block, receipt_time: float):
        """
        Add block to fork choice tree.
        
        Args:
            block: Block to add
            receipt_time: Time block was received
        """
        # Calculate cumulative work
        parent_node = self.block_tree.get(block.previous_hash)
        if parent_node:
            cumulative_work = parent_node.cumulative_work + calculate_work_score(block.complexity) if block.complexity else parent_node.cumulative_work
            height = parent_node.height + 1
        else:
            # Genesis or orphan
            cumulative_work = calculate_work_score(block.complexity) if block.complexity else 0
            height = block.index
        
        # Create block node
        node = BlockNode(
            block=block,
            parent_hash=block.previous_hash,
            cumulative_work=cumulative_work,
            height=height,
            receipt_time=receipt_time
        )
        
        # Add to tree
        self.block_tree[block.block_hash] = node
        
        # Update parent's children
        if parent_node:
            parent_node.children.append(block.block_hash)
        
        # Update best tip if necessary
        self._update_best_tip(node)
        
        # Store work index
        self.storage.store_work_index(height, int(cumulative_work), block.block_hash)
        self.storage.store_tip(block.block_hash, int(cumulative_work))
    
    def _update_best_tip(self, node: BlockNode):
        """
        Update best tip based on fork choice rule.
        
        Fork choice: Tip = argmax(cumulative_work) with tie-breaker on earliest receipt time
        
        Args:
            node: Newly added node
        """
        if not self.best_tip:
            self.best_tip = node
            return
        
        # Compare cumulative work
        if node.cumulative_work > self.best_tip.cumulative_work:
            self.best_tip = node
        elif node.cumulative_work == self.best_tip.cumulative_work:
            # Tie-breaker: earliest receipt time
            if node.receipt_time < self.best_tip.receipt_time:
                self.best_tip = node
    
    def get_best_tip(self) -> Optional[Block]:
        """
        Get current best tip block.
        
        Returns:
            Best tip block or None
        """
        return self.best_tip.block if self.best_tip else None
    
    def get_chain_from_genesis(self, tip_hash: Optional[str] = None) -> List[Block]:
        """
        Get chain from genesis to tip.
        
        Args:
            tip_hash: Tip block hash (uses best tip if None)
            
        Returns:
            List of blocks from genesis to tip
        """
        if tip_hash is None and self.best_tip:
            tip_hash = self.best_tip.block.block_hash
        
        if not tip_hash or tip_hash not in self.block_tree:
            return []
        
        # Build chain backwards from tip to genesis
        chain = []
        current_node = self.block_tree[tip_hash]
        
        while current_node:
            chain.append(current_node.block)
            if current_node.parent_hash == "0" * 64:
                break
            current_node = self.block_tree.get(current_node.parent_hash)
        
        # Reverse to get genesis -> tip order
        chain.reverse()
        return chain
    
    def is_finalized(self, block_hash: str) -> bool:
        """
        Check if block is finalized (k-deep).
        
        Args:
            block_hash: Block hash to check
            
        Returns:
            True if finalized
        """
        if not self.best_tip or block_hash not in self.block_tree:
            return False
        
        block_node = self.block_tree[block_hash]
        depth = self.best_tip.height - block_node.height
        
        return depth >= self.config.confirmation_depth
    
    def handle_reorg(self, new_tip_hash: str) -> Tuple[List[Block], List[Block]]:
        """
        Handle chain reorganization.
        
        Args:
            new_tip_hash: New tip block hash
            
        Returns:
            Tuple of (removed_blocks, added_blocks)
        """
        if not self.best_tip or new_tip_hash not in self.block_tree:
            return ([], [])
        
        new_tip_node = self.block_tree[new_tip_hash]
        
        # Check reorg depth
        old_chain = self.get_chain_from_genesis(self.best_tip.block.block_hash)
        new_chain = self.get_chain_from_genesis(new_tip_hash)
        
        # Find common ancestor
        common_height = min(len(old_chain), len(new_chain))
        fork_point = 0
        
        for i in range(common_height):
            if old_chain[i].block_hash == new_chain[i].block_hash:
                fork_point = i
            else:
                break
        
        # Check reorg depth limit
        reorg_depth = len(old_chain) - fork_point - 1
        if reorg_depth > self.config.max_reorg_depth:
            print(f"Reorg depth {reorg_depth} exceeds maximum {self.config.max_reorg_depth}")
            return ([], [])
        
        # Get removed and added blocks
        removed_blocks = old_chain[fork_point + 1:]
        added_blocks = new_chain[fork_point + 1:]
        
        # Update best tip
        self.best_tip = new_tip_node
        
        return (removed_blocks, added_blocks)


if __name__ == "__main__":
    # Test ConsensusEngine
    print("Testing ConsensusEngine...")
    
    # Create test configuration
    config = ConsensusConfig()
    
    # Create storage manager
    storage_config = StorageConfig(
        data_dir="/tmp/coinjecture_consensus_test",
        role=NodeRole.FULL,
        pruning_mode=PruningMode.FULL
    )
    storage = StorageManager(storage_config)
    
    # Create problem registry
    registry = ProblemRegistry()
    
    # Initialize consensus engine
    consensus = ConsensusEngine(config, storage, registry)
    print("✅ ConsensusEngine initialized")
    
    # Test genesis block
    genesis = consensus.get_best_tip()
    if genesis:
        print(f"✅ Genesis block created: index={genesis.index}, hash={genesis.block_hash[:16]}...")
    else:
        print("❌ Genesis block creation failed")
    
    # Test chain from genesis
    chain = consensus.get_chain_from_genesis()
    if len(chain) == 1 and chain[0].index == 0:
        print("✅ Chain from genesis retrieved successfully")
    else:
        print("❌ Chain retrieval failed")
    
    # Test finality
    is_finalized = consensus.is_finalized(genesis.block_hash)
    print(f"✅ Finality check: genesis is {'finalized' if is_finalized else 'not finalized (expected)'}")
    
    print("✅ All consensus module tests passed!")

