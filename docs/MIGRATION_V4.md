# COINjecture v4.0 Migration Guide

## Overview

COINjecture v4.0 introduces significant architectural improvements to align the implementation with the documented specification. This migration guide covers the breaking changes, upgrade procedures, and backward compatibility considerations.

## Breaking Changes

### 1. Block Structure Refactoring

**Before (v3.x)**:
```python
@dataclass
class Block:
    index: int
    timestamp: float
    previous_hash: str
    transactions: list
    merkle_root: str
    problem: dict
    solution: list
    complexity: ComputationalComplexity
    mining_capacity: ProblemTier
    cumulative_work_score: float
    block_hash: str
    offchain_cid: Optional[str] = None
    proof_commitment: Optional[str] = None
```

**After (v4.0)**:
```python
@dataclass
class BlockHeader:
    version: int
    parent_hash: bytes
    height: int
    timestamp: int
    commitments_root: bytes
    tx_root: bytes
    difficulty_target: int
    cumulative_work: int
    miner_pubkey: bytes
    commit_nonce: int
    problem_type: int
    tier: int
    commit_epoch: int
    proof_commitment: bytes
    header_hash: bytes

@dataclass
class Block:
    header: BlockHeader
    transactions: Optional[List[Transaction]] = None
    problem: Optional[dict] = None
    solution: Optional[List[int]] = None
    complexity: Optional[ComputationalComplexity] = None
    offchain_cid: str  # Required - essential for commit-reveal protocol
```

**Migration Impact**:
- All references to `block.block_hash` → `block.calculate_hash()`
- All references to `block.index` → `block.header.height`
- All references to `block.timestamp` → `block.header.timestamp`
- All references to `block.previous_hash` → `block.header.parent_hash.hex()`
- `offchain_cid` is now **required** (no longer optional)
- `proof_commitment` is now part of `BlockHeader` (not `Block`)

### 2. CommitmentLeaf Structure

**New in v4.0**:
```python
@dataclass
class CommitmentLeaf:
    left: bytes  # 32 bytes
    right: bytes  # 32 bytes
    
    def serialize(self) -> bytes:
        return self.left + self.right
    
    @classmethod
    def deserialize(cls, data: bytes) -> 'CommitmentLeaf':
        return cls(left=data[:32], right=data[32:64])
```

**Migration Impact**:
- Commitment creation now uses `CommitmentLeaf` structure
- 64-byte serialization format
- Integration with Merkle tree construction

### 3. Merkle Tree Implementation

**Before (v3.x)**:
```python
def build_merkle_root(data_dicts, *args):
    # Simple concatenation and hash
    return hashlib.sha256("".join(data_hashes).encode('utf-8')).hexdigest()
```

**After (v4.0)**:
```python
class MerkleTree:
    def __init__(self, leaves: List[bytes]):
        self.leaves = leaves
        self.tree = self._build_tree()
    
    def get_root(self) -> bytes:
        return self.tree[-1][0]
    
    def generate_proof(self, leaf_index: int) -> MerkleProof:
        # Proper proof generation
    
    @staticmethod
    def verify_proof(leaf: bytes, proof: MerkleProof, root: bytes) -> bool:
        # Proper proof verification
```

**Migration Impact**:
- Proper Merkle tree construction with proof generation
- Proof verification for commitment validation
- Integration with block header commitments_root

### 4. P2P Networking

**Before (v3.x)**:
```python
class NetworkProtocol:
    def __init__(self, consensus, storage, problem_registry, peer_id):
        # Simulated networking
        self.topics = {...}
        self.message_handlers = {...}
```

**After (v4.0)**:
```python
class NetworkProtocol:
    def __init__(self, consensus, storage, problem_registry, peer_id, 
                 libp2p_config=None, gossipsub_config=None, rpc_config=None):
        # Real libp2p integration
        self.host = LibP2PHost(libp2p_config)
        self.gossipsub = GossipsubManager(self.host, gossipsub_config)
        self.rpc_handler = RPCHandler(consensus, storage, rpc_config)
    
    async def start(self) -> None:
        await self.host.start()
        await self.gossipsub.start()
        await self.rpc_handler.start()
    
    async def stop(self) -> None:
        await self.rpc_handler.stop()
        await self.gossipsub.stop()
        await self.host.stop()
```

**Migration Impact**:
- All networking is now async
- Real libp2p integration instead of simulation
- Gossipsub topics for message propagation
- RPC handlers for blockchain sync

### 5. Node Lifecycle

**Before (v3.x)**:
```python
class Node:
    def start(self) -> bool:
        # Synchronous startup
        self.network = NetworkProtocol(...)
        self._sync_headers()
        self._start_role_services()
        return True
    
    def stop(self) -> None:
        # Synchronous shutdown
        self.network = None
```

**After (v4.0)**:
```python
class Node:
    async def start(self) -> bool:
        # Async startup
        self.network = NetworkProtocol(...)
        await self.network.start()
        await self._sync_headers()
        await self._start_role_services()
        return True
    
    async def stop(self) -> None:
        # Async shutdown
        if self.network:
            await self.network.stop()
```

**Migration Impact**:
- All node operations are now async
- Proper P2P connection management
- Async block propagation

## Upgrade Procedures

### 1. Database Migration

**Step 1: Backup existing data**
```bash
# Backup blockchain database
cp data/blockchain.db data/blockchain.db.backup
cp data/blockchain_state.json data/blockchain_state.json.backup
```

**Step 2: Update database schema**
```python
# The storage module will automatically handle schema updates
# No manual migration required
```

**Step 3: Verify data integrity**
```python
# Check that existing blocks can be loaded with new structure
from src.storage import StorageManager
storage = StorageManager(config)
block = storage.get_block("genesis_hash")
assert block.header.height == 0
```

### 2. Node Upgrade

**Step 1: Install new dependencies**
```bash
pip install -r requirements.txt
# This will install py-libp2p, multiaddr, base58
```

**Step 2: Update node configuration**
```python
# Update node config for new networking
config = NodeConfig(
    data_dir="data",
    role=NodeRole.MINER,
    bootstrap_peers=[
        "/ip4/167.172.213.70/tcp/8000/p2p/12D3KooW...",
        "/ip4/127.0.0.1/tcp/8001/p2p/12D3KooW..."
    ],
    # ... other config
)
```

**Step 3: Start node with new architecture**
```python
# Node startup is now async
node = Node(config)
if node.init():
    success = await node.start()
    if success:
        print("Node started successfully")
    else:
        print("Node startup failed")
```

### 3. API Compatibility

**Block API Changes**:
```python
# Before
response = {
    "index": block.index,
    "timestamp": block.timestamp,
    "previous_hash": block.previous_hash,
    "block_hash": block.block_hash,
    "cumulative_work_score": block.cumulative_work_score
}

# After
response = {
    "header": {
        "version": block.header.version,
        "parent_hash": block.header.parent_hash.hex(),
        "height": block.header.height,
        "timestamp": block.header.timestamp,
        "commitments_root": block.header.commitments_root.hex(),
        "tx_root": block.header.tx_root.hex(),
        "difficulty_target": block.header.difficulty_target,
        "cumulative_work": block.header.cumulative_work,
        "miner_pubkey": block.header.miner_pubkey.hex(),
        "commit_nonce": block.header.commit_nonce,
        "problem_type": block.header.problem_type,
        "tier": block.header.tier,
        "commit_epoch": block.header.commit_epoch,
        "proof_commitment": block.header.proof_commitment.hex(),
        "header_hash": block.header.header_hash.hex()
    },
    "block_hash": block.calculate_hash(),
    "offchain_cid": block.offchain_cid
}
```

## Backward Compatibility

### 1. Data Format Compatibility

**Block Storage**:
- Existing blocks are automatically migrated to new format
- Old block hashes remain valid
- Genesis block compatibility maintained

**Database Schema**:
- Automatic schema updates on startup
- No data loss during migration
- Rollback capability maintained

### 2. API Compatibility

**REST API**:
- Block endpoints return new structure
- Legacy fields mapped where possible
- Version header indicates API version

**WebSocket API**:
- Real-time updates use new block structure
- Client libraries need updates
- Backward compatibility layer available

### 3. Network Compatibility

**P2P Protocol**:
- New nodes can connect to old nodes
- Graceful degradation for missing features
- Automatic protocol negotiation

**Bootstrap Peers**:
- Existing bootstrap peers remain functional
- New peer discovery mechanisms
- Enhanced connection reliability

## Testing

### 1. Unit Tests

```bash
# Run updated unit tests
python -m pytest tests/ -v
```

### 2. Integration Tests

```bash
# Run 3-node P2P integration test
python tests/test_p2p_integration.py
```

### 3. Migration Tests

```bash
# Test database migration
python scripts/test_migration.py
```

## Rollback Plan

### 1. Emergency Rollback

**Step 1: Stop new nodes**
```bash
# Stop all v4.0 nodes
systemctl stop coinjecture-node
```

**Step 2: Restore backup**
```bash
# Restore database backup
cp data/blockchain.db.backup data/blockchain.db
cp data/blockchain_state.json.backup data/blockchain_state.json
```

**Step 3: Start old nodes**
```bash
# Start v3.x nodes
systemctl start coinjecture-node
```

### 2. Gradual Rollback

**Step 1: Identify issues**
```bash
# Check node logs
tail -f logs/node.log
```

**Step 2: Isolate problematic nodes**
```bash
# Disconnect problematic nodes
# Continue with stable nodes
```

**Step 3: Fix and redeploy**
```bash
# Fix issues and redeploy
# Monitor network stability
```

## Performance Considerations

### 1. Memory Usage

**BlockHeader Structure**:
- More efficient memory usage
- Better serialization performance
- Reduced object overhead

**Merkle Tree**:
- Proper tree construction
- Proof generation optimization
- Verification efficiency

### 2. Network Performance

**LibP2P Integration**:
- Real P2P networking
- Better connection management
- Enhanced message propagation

**Gossipsub Topics**:
- Efficient message routing
- Reduced network overhead
- Better peer discovery

### 3. Storage Performance

**Database Schema**:
- Optimized queries
- Better indexing
- Reduced storage overhead

## Security Considerations

### 1. Cryptographic Security

**BlockHeader Validation**:
- Proper field validation
- Enhanced security checks
- Better error handling

**Merkle Proof Verification**:
- Cryptographic proof validation
- Tamper detection
- Integrity verification

### 2. Network Security

**LibP2P Security**:
- Noise protocol encryption
- Secure peer connections
- Enhanced authentication

**Message Security**:
- Signed messages
- Tamper detection
- Replay protection

## Support and Resources

### 1. Documentation

- [ARCHITECTURE.md](docs/guides/ARCHITECTURE.md) - Updated architecture
- [API Documentation](docs/api/) - API reference
- [Network Protocol](docs/blockchain/network.md) - P2P protocol

### 2. Community

- GitHub Issues: Report bugs and issues
- Discord: Community support
- Documentation: Updated guides

### 3. Migration Support

- Migration scripts available
- Automated testing tools
- Community support channels

## Conclusion

COINjecture v4.0 represents a significant architectural improvement that aligns the implementation with the documented specification. While there are breaking changes, the migration process is designed to be smooth with proper backward compatibility and rollback capabilities.

The new architecture provides:
- Proper blockchain structures
- Real P2P networking
- Enhanced security
- Better performance
- Improved maintainability

For questions or issues during migration, please refer to the support resources or contact the development team.
