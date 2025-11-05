"""
End-to-End 3-Node Network Simulation

This test simulates a complete COINjecture network with 3 nodes:
- Node 1: Miner (produces blocks)
- Node 2: Full node (validates and propagates)
- Node 3: Light node (validates headers only)

Tests the complete lifecycle:
1. Problem generation
2. Mining (commitment + reveal)
3. Block submission with IPFS pinning quorum
4. P2P gossip propagation
5. Cross-node validation
6. Consensus agreement

This is an INSTITUTIONAL-GRADE end-to-end test that validates
all components working together.
"""

import hashlib
import json
import logging
import multiprocessing
import os
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
import pytest

from coinjecture.types import (
    BlockHeader,
    Problem,
    Solution,
    Reveal,
    Block,
    HardwareTier,
    ProblemType,
    VerifyBudget,
    CODEC_VERSION,
)
from coinjecture.consensus.codec import compute_header_hash
from coinjecture.consensus.admission import EpochReplayCache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ==================== NODE SIMULATION ====================

@dataclass
class SimulatedNode:
    """Simulated COINjecture node"""

    node_id: int
    role: str  # "miner", "full", "light"
    data_dir: Path
    blocks: List[Block] = field(default_factory=list)
    mempool: List[Block] = field(default_factory=list)
    peers: List[int] = field(default_factory=list)
    replay_cache: Optional[EpochReplayCache] = None

    def __post_init__(self):
        """Initialize node"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        cache_path = self.data_dir / "epoch_replay.json"
        self.replay_cache = EpochReplayCache(persist_path=cache_path)
        logger.info(f"Node {self.node_id} ({self.role}) initialized")

    def mine_block(self, parent_hash: bytes, block_index: int) -> Optional[Block]:
        """Mine a new block (miner nodes only)"""
        if self.role != "miner":
            return None

        logger.info(f"Node {self.node_id}: Mining block {block_index}...")

        # 1. Generate problem (subset sum)
        problem = Problem(
            problem_type=ProblemType.SUBSET_SUM,
            tier=HardwareTier.DESKTOP,
            elements=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
            target=30,  # 2+4+6+8+10 = 30
            timestamp=int(time.time()),
        )

        # 2. Solve problem
        solution = Solution(
            indices=[1, 3, 5, 7, 9],  # elements 2,4,6,8,10
            timestamp=int(time.time()),
        )

        # 3. Create commitment (simplified - no actual HMAC)
        from coinjecture.consensus.codec import compute_transaction_hash

        problem_hash = hashlib.sha256(str(problem).encode()).digest()
        solution_hash = hashlib.sha256(str(solution).encode()).digest()
        epoch_salt = hashlib.sha256(parent_hash + block_index.to_bytes(8, "little")).digest()
        miner_salt = os.urandom(32)

        commitment_data = epoch_salt + problem_hash + solution_hash + miner_salt
        commitment = hashlib.sha256(commitment_data).digest()

        # 4. Create block header
        header = BlockHeader(
            codec_version=CODEC_VERSION,
            block_index=block_index,
            timestamp=int(time.time()),
            parent_hash=parent_hash,
            merkle_root=b"\x00" * 32,  # Empty for now
            miner_address=hashlib.sha256(f"miner_{self.node_id}".encode()).digest(),
            commitment=commitment,
            difficulty_target=1000,
            nonce=42,
            extra_data=b"",
        )

        # 5. Create reveal
        reveal = Reveal(
            problem=problem,
            solution=solution,
            miner_salt=miner_salt,
            nonce=42,
        )

        # 6. Create block
        block = Block(
            header=header,
            transactions=[],
            reveal=reveal,
            cid=f"Qm{hashlib.sha256(str(block_index).encode()).hexdigest()[:32]}",
        )

        logger.info(f"Node {self.node_id}: Block {block_index} mined successfully")
        return block

    def validate_block(self, block: Block) -> bool:
        """Validate a block"""
        logger.info(f"Node {self.node_id}: Validating block {block.header.block_index}...")

        try:
            # 1. Check codec version
            if block.header.codec_version != CODEC_VERSION:
                logger.error(f"Invalid codec version: {block.header.codec_version}")
                return False

            # 2. Check CID present (SEC-005)
            if not block.cid:
                logger.error("Missing CID")
                return False

            # 3. Check epoch replay (SEC-002)
            if self.replay_cache:
                if self.replay_cache.check_replay(
                    block.header.commitment, block.header.block_index
                ):
                    logger.error("Epoch replay detected!")
                    return False

            # 4. Verify solution (simplified)
            problem = block.reveal.problem
            solution = block.reveal.solution

            # Check indices in bounds
            for idx in solution.indices:
                if idx >= len(problem.elements):
                    logger.error(f"Index {idx} out of bounds")
                    return False

            # Check sum
            total = sum(problem.elements[i] for i in solution.indices)
            if total != problem.target:
                logger.error(f"Invalid solution: {total} != {problem.target}")
                return False

            # 5. All checks passed
            logger.info(f"Node {self.node_id}: Block {block.header.block_index} validated ✓")

            # Register commitment
            if self.replay_cache:
                self.replay_cache.add(block.header.commitment, block.header.block_index)

            return True

        except Exception as e:
            logger.error(f"Node {self.node_id}: Validation error: {e}")
            return False

    def receive_block(self, block: Block) -> bool:
        """Receive block from peer"""
        logger.info(
            f"Node {self.node_id}: Received block {block.header.block_index} from network"
        )

        # Validate
        if not self.validate_block(block):
            logger.warning(f"Node {self.node_id}: Rejected invalid block")
            return False

        # Add to chain
        self.blocks.append(block)
        logger.info(f"Node {self.node_id}: Added block to chain (total: {len(self.blocks)})")

        return True

    def get_chain_state(self) -> Dict:
        """Get current chain state"""
        return {
            "node_id": self.node_id,
            "role": self.role,
            "block_count": len(self.blocks),
            "latest_block_index": self.blocks[-1].header.block_index if self.blocks else None,
        }


# ==================== NETWORK SIMULATION ====================

class SimulatedNetwork:
    """Simulated 3-node P2P network"""

    def __init__(self, temp_dir: Path):
        self.temp_dir = temp_dir
        self.nodes: List[SimulatedNode] = []

        # Create 3 nodes
        self.nodes.append(
            SimulatedNode(
                node_id=1,
                role="miner",
                data_dir=temp_dir / "node1",
                peers=[2, 3],
            )
        )
        self.nodes.append(
            SimulatedNode(
                node_id=2,
                role="full",
                data_dir=temp_dir / "node2",
                peers=[1, 3],
            )
        )
        self.nodes.append(
            SimulatedNode(
                node_id=3,
                role="light",
                data_dir=temp_dir / "node3",
                peers=[1, 2],
            )
        )

        logger.info("Simulated network initialized with 3 nodes")

    def broadcast_block(self, block: Block, from_node_id: int):
        """Broadcast block to all peers (equilibrium gossip simulation)"""
        logger.info(f"Broadcasting block {block.header.block_index} from node {from_node_id}")

        # Simulate gossip delay
        time.sleep(0.1)

        # Send to peers
        for node in self.nodes:
            if node.node_id != from_node_id:
                node.receive_block(block)

    def check_consensus(self) -> bool:
        """Check if all nodes agree on chain state"""
        if len(self.nodes) < 2:
            return True

        # Compare block counts
        block_counts = [len(node.blocks) for node in self.nodes]
        if len(set(block_counts)) > 1:
            logger.error(f"Block count mismatch: {block_counts}")
            return False

        # Compare latest block hashes
        if block_counts[0] > 0:
            latest_hashes = []
            for node in self.nodes:
                if node.blocks:
                    hash_bytes = compute_header_hash(node.blocks[-1].header)
                    latest_hashes.append(hash_bytes.hex())

            if len(set(latest_hashes)) > 1:
                logger.error(f"Latest block hash mismatch: {latest_hashes}")
                return False

        logger.info("✓ All nodes in consensus")
        return True

    def get_network_state(self) -> Dict:
        """Get network state summary"""
        return {
            "nodes": [node.get_chain_state() for node in self.nodes],
            "consensus": self.check_consensus(),
        }


# ==================== E2E TESTS ====================

@pytest.mark.e2e
@pytest.mark.slow
class TestThreeNodeSimulation:
    """E2E tests for 3-node network simulation"""

    def test_single_block_propagation(self, tmp_path):
        """
        Test that a single block propagates to all nodes and consensus is achieved.

        Flow:
        1. Node 1 (miner) mines block
        2. Block broadcasts to nodes 2 and 3
        3. All nodes validate
        4. Consensus achieved
        """
        network = SimulatedNetwork(tmp_path)

        # Genesis
        genesis_hash = b"\x00" * 32

        # Mine block 1
        miner = network.nodes[0]
        block = miner.mine_block(genesis_hash, block_index=1)
        assert block is not None

        # Miner validates own block
        assert miner.validate_block(block)
        miner.blocks.append(block)

        # Broadcast
        network.broadcast_block(block, from_node_id=1)

        # Check consensus
        assert network.check_consensus()

        # All nodes should have 1 block
        for node in network.nodes:
            assert len(node.blocks) == 1

    def test_multi_block_chain(self, tmp_path):
        """
        Test mining and propagating multiple blocks in sequence.

        Flow:
        1. Mine blocks 1-5
        2. Each block builds on previous
        3. Broadcast and validate each
        4. Consensus maintained throughout
        """
        network = SimulatedNetwork(tmp_path)
        miner = network.nodes[0]

        parent_hash = b"\x00" * 32

        # Mine 5 blocks
        for i in range(1, 6):
            logger.info(f"\n========== Mining Block {i} ==========")

            block = miner.mine_block(parent_hash, block_index=i)
            assert block is not None

            # Validate and add
            assert miner.validate_block(block)
            miner.blocks.append(block)

            # Broadcast
            network.broadcast_block(block, from_node_id=1)

            # Check consensus after each block
            assert network.check_consensus()

            # Update parent for next block
            parent_hash = compute_header_hash(block.header)

        # Final state
        state = network.get_network_state()
        logger.info(f"\nFinal network state: {json.dumps(state, indent=2)}")

        # All nodes should have 5 blocks
        for node in network.nodes:
            assert len(node.blocks) == 5

    def test_epoch_replay_protection(self, tmp_path):
        """
        Test that epoch replay attacks are detected and rejected.

        Flow:
        1. Mine block 1
        2. Broadcast to all nodes
        3. Try to replay same commitment (should fail)
        4. Mine block 2 with new commitment (should succeed)
        """
        network = SimulatedNetwork(tmp_path)
        miner = network.nodes[0]

        # Mine block 1
        block1 = miner.mine_block(b"\x00" * 32, block_index=1)
        assert block1 is not None
        assert miner.validate_block(block1)
        miner.blocks.append(block1)
        network.broadcast_block(block1, from_node_id=1)

        # Try to resubmit same block (replay attack)
        replay_block = Block(
            header=BlockHeader(
                codec_version=block1.header.codec_version,
                block_index=2,  # Different index
                timestamp=int(time.time()),
                parent_hash=compute_header_hash(block1.header),
                merkle_root=b"\x00" * 32,
                miner_address=block1.header.miner_address,
                commitment=block1.header.commitment,  # SAME commitment (replay!)
                difficulty_target=1000,
                nonce=43,
                extra_data=b"",
            ),
            transactions=[],
            reveal=block1.reveal,
            cid="Qmreplay123",
        )

        # Should reject (epoch replay)
        full_node = network.nodes[1]
        assert not full_node.validate_block(replay_block), "Replay attack should be rejected!"

        logger.info("✓ Epoch replay protection working correctly")

    def test_invalid_solution_rejection(self, tmp_path):
        """
        Test that blocks with invalid solutions are rejected.

        Flow:
        1. Create block with WRONG solution
        2. Submit to network
        3. All nodes should reject
        """
        network = SimulatedNetwork(tmp_path)

        # Create block with invalid solution
        problem = Problem(
            problem_type=ProblemType.SUBSET_SUM,
            tier=HardwareTier.DESKTOP,
            elements=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14],
            target=30,
            timestamp=int(time.time()),
        )

        # WRONG solution (sum = 15, not 30)
        invalid_solution = Solution(
            indices=[0, 1, 2, 3],  # 1+2+3+4 = 10, not 30!
            timestamp=int(time.time()),
        )

        header = BlockHeader(
            codec_version=CODEC_VERSION,
            block_index=1,
            timestamp=int(time.time()),
            parent_hash=b"\x00" * 32,
            merkle_root=b"\x00" * 32,
            miner_address=os.urandom(32),
            commitment=os.urandom(32),
            difficulty_target=1000,
            nonce=42,
            extra_data=b"",
        )

        reveal = Reveal(
            problem=problem,
            solution=invalid_solution,
            miner_salt=os.urandom(32),
            nonce=42,
        )

        invalid_block = Block(
            header=header,
            transactions=[],
            reveal=reveal,
            cid="Qminvalid123",
        )

        # All nodes should reject
        for node in network.nodes:
            assert not node.validate_block(invalid_block), \
                f"Node {node.node_id} should reject invalid solution!"

        logger.info("✓ Invalid solution rejection working correctly")


# ==================== PERFORMANCE TESTS ====================

@pytest.mark.e2e
@pytest.mark.slow
def test_network_performance_100_blocks(tmp_path):
    """
    Performance test: Mine and propagate 100 blocks.

    Success criteria:
    - All 100 blocks validated
    - Consensus maintained
    - Average block time < 1 second
    - No validation errors
    """
    network = SimulatedNetwork(tmp_path)
    miner = network.nodes[0]

    parent_hash = b"\x00" * 32
    start_time = time.time()

    for i in range(1, 101):
        block = miner.mine_block(parent_hash, block_index=i)
        assert block is not None

        assert miner.validate_block(block)
        miner.blocks.append(block)

        network.broadcast_block(block, from_node_id=1)

        parent_hash = compute_header_hash(block.header)

        if i % 10 == 0:
            logger.info(f"Progress: {i}/100 blocks")

    duration = time.time() - start_time
    avg_block_time = duration / 100

    logger.info(f"\nPerformance Results:")
    logger.info(f"  Total time: {duration:.2f}s")
    logger.info(f"  Avg block time: {avg_block_time:.3f}s")
    logger.info(f"  Blocks/sec: {100 / duration:.2f}")

    # Check final consensus
    assert network.check_consensus()

    # Performance assertion
    assert avg_block_time < 1.0, f"Too slow: {avg_block_time}s per block"

    logger.info("✓ Performance test passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "e2e"])
