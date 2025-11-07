# COINjecture Consensus Engine

**Version:** 4.5.0+
**Author:** Quigles1337 <adz@alphx.io>
**Status:** Production Ready (Fully Featured)

---

## Overview

COINjecture implements a **Proof-of-Authority (PoA)** consensus mechanism with deterministic validator rotation, Merkle tree state verification, and 2-second block times. The system is designed for institutional-grade reliability with Byzantine fault tolerance.

### Key Features

- **Proof-of-Authority** - Authorized validators produce blocks deterministically
- **Round-robin validator rotation** - Fair, predictable block production
- **2-second block time** - High throughput for institutional use cases
- **Byzantine Fault Tolerance** - Tolerates up to (n-1)/3 malicious validators
- **Merkle tree verification** - Efficient state and transaction verification
- **Immutable block storage** - SQLite with enforcement triggers
- **30M gas limit per block** - Maximum 1000 transactions per block

---

## Architecture

The consensus engine consists of four primary subsystems working in concert:

```mermaid
graph TB
    subgraph "Consensus Engine Core"
        Engine[Engine<br/>Block Production Loop<br/>Validator Rotation]
        Builder[Block Builder<br/>Transaction Selection<br/>Gas Management]
        StateTransition[State Transition<br/>Account Updates<br/>Nonce Management]
        Storage[Block Storage<br/>Immutable SQLite<br/>Chain State]
    end

    subgraph "External Dependencies"
        Mempool[Mempool<br/>Priority Queue<br/>Transaction Pool]
        StateManager[State Manager<br/>Account Database<br/>Balance Tracking]
        P2P[P2P Network<br/>Block Broadcast<br/>Peer Sync]
        API[REST API<br/>Block Queries<br/>Status Endpoints]
    end

    subgraph "Data Structures"
        Block[Block<br/>Header + Body<br/>Merkle Roots]
        Merkle[Merkle Trees<br/>TxRoot + StateRoot<br/>Proof Verification]
    end

    Engine -->|produce block| Builder
    Builder -->|collect txs| Mempool
    Builder -->|build| Block
    Block -->|compute roots| Merkle
    Builder -->|apply txs| StateTransition
    StateTransition -->|update accounts| StateManager
    Engine -->|save| Storage
    Storage -->|read chain head| Engine
    Engine -->|broadcast| P2P
    P2P -->|receive blocks| Engine
    API -->|query blocks| Storage
    API -->|consensus stats| Engine

    style Engine fill:#ff6b6b
    style Builder fill:#4ecdc4
    style StateTransition fill:#ffe66d
    style Storage fill:#95e1d3
```

---

## Block Structure

Blocks consist of a header (metadata + cryptographic commitments) and a body (transaction list).

```mermaid
graph LR
    subgraph "Block Header"
        BlockNumber[Block Number<br/>uint64]
        ParentHash[Parent Hash<br/>32 bytes]
        StateRoot[State Root<br/>Merkle Hash]
        TxRoot[Tx Root<br/>Merkle Hash]
        Timestamp[Timestamp<br/>Unix seconds]
        Validator[Validator<br/>Ed25519 pubkey]
        Difficulty[Difficulty<br/>Always 1]
        Nonce[Nonce<br/>Always 0]
        GasLimit[Gas Limit<br/>30M max]
        GasUsed[Gas Used<br/>Actual usage]
        ExtraData[Extra Data<br/>32 bytes]
    end

    subgraph "Block Body"
        TxList[Transaction List<br/>Max 1000 txs]
    end

    subgraph "Computed Fields"
        BlockHash[Block Hash<br/>SHA-256 of header]
    end

    BlockNumber --> BlockHash
    ParentHash --> BlockHash
    StateRoot --> BlockHash
    TxRoot --> BlockHash
    Timestamp --> BlockHash
    Validator --> BlockHash
    Difficulty --> BlockHash
    Nonce --> BlockHash
    GasLimit --> BlockHash
    GasUsed --> BlockHash
    ExtraData --> BlockHash

    TxList -.->|hashed to| TxRoot

    style BlockHash fill:#ff6b6b
    style StateRoot fill:#4ecdc4
    style TxRoot fill:#4ecdc4
```

### Block Header Fields

| Field | Type | Description |
|-------|------|-------------|
| `BlockNumber` | uint64 | Sequential block height (0 = genesis) |
| `ParentHash` | [32]byte | SHA-256 hash of parent block header |
| `StateRoot` | [32]byte | Merkle root of account state after applying block |
| `TxRoot` | [32]byte | Merkle root of transaction hashes in block |
| `Timestamp` | int64 | Unix timestamp when block was produced |
| `Validator` | [32]byte | Ed25519 public key of validator who produced block |
| `Difficulty` | uint64 | Always 1 (PoA has no mining difficulty) |
| `Nonce` | uint64 | Always 0 (PoA has no mining nonce) |
| `GasLimit` | uint64 | Maximum gas allowed per block (30M) |
| `GasUsed` | uint64 | Actual gas consumed by transactions |
| `ExtraData` | [32]byte | Reserved for protocol upgrades |
| `BlockHash` | [32]byte | SHA-256 hash of canonical header encoding |

### Transaction List

The block body contains a list of transactions selected from the mempool. Transactions are:

- **Priority-sorted** - Higher priority transactions included first
- **Gas-limited** - Total gas_used <= gas_limit (30M)
- **Nonce-ordered** - Transactions with correct sequential nonces
- **Balance-validated** - Sender balance >= (amount + fee)

---

## Consensus Algorithm

### Validator Rotation (Round-Robin)

Validators take turns producing blocks in a deterministic round-robin fashion:

```
validator_index = block_number % validator_count
expected_validator = validators[validator_index]
```

```mermaid
graph TD
    subgraph "Validator Set"
        V0[Validator 0<br/>Alice]
        V1[Validator 1<br/>Bob]
        V2[Validator 2<br/>Carol]
    end

    subgraph "Block Production Timeline"
        B0[Block 0<br/>Alice]
        B1[Block 1<br/>Bob]
        B2[Block 2<br/>Carol]
        B3[Block 3<br/>Alice]
        B4[Block 4<br/>Bob]
        B5[Block 5<br/>Carol]
    end

    V0 -->|produces| B0
    V1 -->|produces| B1
    V2 -->|produces| B2
    V0 -->|produces| B3
    V1 -->|produces| B4
    V2 -->|produces| B5

    B0 -->|parent| B1
    B1 -->|parent| B2
    B2 -->|parent| B3
    B3 -->|parent| B4
    B4 -->|parent| B5

    style V0 fill:#ff6b6b
    style V1 fill:#4ecdc4
    style V2 fill:#ffe66d
```

### Block Production Flow

Every 2 seconds, the consensus engine checks if it's the node's turn to produce a block:

```mermaid
graph TD
    Start([Block Timer Tick<br/>Every 2 seconds]) --> CheckTurn{Is it our<br/>validator turn?}

    CheckTurn -->|No| Skip[Skip this round<br/>Wait for next tick]
    CheckTurn -->|Yes| GetParent[Get current<br/>chain head]

    GetParent --> SelectTxs[Select transactions<br/>from mempool]
    SelectTxs --> ValidateTxs[Validate nonces<br/>and balances]
    ValidateTxs --> BuildBlock[Build block with<br/>selected transactions]

    BuildBlock --> ComputeTxRoot[Compute Merkle<br/>tx_root]
    ComputeTxRoot --> ApplyTxs[Apply transactions<br/>to state]

    ApplyTxs --> UpdateAccounts[Update sender/<br/>recipient accounts]
    UpdateAccounts --> ComputeStateRoot[Compute Merkle<br/>state_root]

    ComputeStateRoot --> FinalizeBlock[Finalize block<br/>compute block_hash]
    FinalizeBlock --> UpdateChain[Update chain head<br/>height++]

    UpdateChain --> SaveDB[Save block to<br/>SQLite database]
    SaveDB --> Broadcast[Broadcast block<br/>to P2P network]

    Broadcast --> Callback[Trigger onNewBlock<br/>callback]
    Callback --> End([Wait for next tick])
    Skip --> End

    style Start fill:#95e1d3
    style CheckTurn fill:#ff6b6b
    style BuildBlock fill:#4ecdc4
    style ApplyTxs fill:#ffe66d
    style Broadcast fill:#95e1d3
    style End fill:#95e1d3
```

### Block Validation (Receiving Blocks)

When a block is received from the P2P network, it undergoes strict validation:

```mermaid
graph TD
    Receive([Receive block<br/>from P2P]) --> CheckHash{Block hash<br/>valid?}

    CheckHash -->|No| RejectHash[Reject: Invalid hash]
    CheckHash -->|Yes| CheckValidator{Validator<br/>authorized?}

    CheckValidator -->|No| RejectValidator[Reject: Unauthorized validator]
    CheckValidator -->|Yes| CheckNumber{Block number<br/>= height + 1?}

    CheckNumber -->|No| RejectNumber[Reject: Height mismatch]
    CheckNumber -->|Yes| CheckParent{Parent hash<br/>matches current?}

    CheckParent -->|No| RejectParent[Reject: Parent mismatch<br/>possible fork]
    CheckParent -->|Yes| CheckTxRoot{Tx root<br/>valid?}

    CheckTxRoot -->|No| RejectTxRoot[Reject: Invalid tx_root]
    CheckTxRoot -->|Yes| ApplyBlock[Apply transactions<br/>to state]

    ApplyBlock --> ComputeState[Compute resulting<br/>state_root]
    ComputeState --> CheckStateRoot{State root<br/>matches block?}

    CheckStateRoot -->|No| RejectStateRoot[Reject: State mismatch]
    CheckStateRoot -->|Yes| AcceptBlock[Accept block<br/>Update chain head]

    AcceptBlock --> SaveBlock[Save to database]
    SaveBlock --> Success([Block accepted])

    RejectHash --> Failure([Block rejected])
    RejectValidator --> Failure
    RejectNumber --> Failure
    RejectParent --> Failure
    RejectTxRoot --> Failure
    RejectStateRoot --> Failure

    style Receive fill:#95e1d3
    style CheckHash fill:#ff6b6b
    style CheckValidator fill:#ff6b6b
    style CheckNumber fill:#ff6b6b
    style CheckParent fill:#ff6b6b
    style CheckTxRoot fill:#ff6b6b
    style CheckStateRoot fill:#ff6b6b
    style AcceptBlock fill:#4ecdc4
    style Success fill:#95e1d3
    style Failure fill:#f38181
```

---

## State Transitions

Transactions modify account state (balances and nonces) in a deterministic, atomic manner.

### Transaction Application Flow

```mermaid
graph TD
    Start([Transaction]) --> GetAccounts[Get sender and<br/>recipient accounts]

    GetAccounts --> CheckNonce{Sender nonce<br/>matches tx.nonce?}
    CheckNonce -->|No| RejectNonce[Reject: Invalid nonce]
    CheckNonce -->|Yes| CheckBalance{Sender balance >=<br/>amount + fee?}

    CheckBalance -->|No| RejectBalance[Reject: Insufficient funds]
    CheckBalance -->|Yes| DebitSender[Debit sender:<br/>balance -= amount + fee]

    DebitSender --> IncrementNonce[Increment sender:<br/>nonce++]
    IncrementNonce --> CreditRecipient[Credit recipient:<br/>balance += amount]

    CreditRecipient --> UpdateSender[Update sender<br/>in database]
    UpdateSender --> UpdateRecipient[Update recipient<br/>in database]

    UpdateRecipient --> RemoveMempool[Remove tx from<br/>mempool]
    RemoveMempool --> Success([Transaction applied])

    RejectNonce --> Failure([Transaction rejected])
    RejectBalance --> Failure

    style Start fill:#95e1d3
    style CheckNonce fill:#ff6b6b
    style CheckBalance fill:#ff6b6b
    style DebitSender fill:#ffe66d
    style CreditRecipient fill:#ffe66d
    style Success fill:#95e1d3
    style Failure fill:#f38181
```

### Account State Updates

```mermaid
graph LR
    subgraph "Before Transaction"
        SenderBefore[Sender<br/>Balance: 1000<br/>Nonce: 5]
        RecipientBefore[Recipient<br/>Balance: 500<br/>Nonce: 10]
    end

    subgraph "Transaction"
        Tx[Transfer 100<br/>Fee: 1<br/>From: Sender<br/>To: Recipient]
    end

    subgraph "After Transaction"
        SenderAfter[Sender<br/>Balance: 899<br/>Nonce: 6]
        RecipientAfter[Recipient<br/>Balance: 600<br/>Nonce: 10]
    end

    SenderBefore -->|apply tx| Tx
    RecipientBefore -->|apply tx| Tx
    Tx -->|updates| SenderAfter
    Tx -->|updates| RecipientAfter

    style Tx fill:#4ecdc4
    style SenderBefore fill:#ffe66d
    style RecipientBefore fill:#ffe66d
    style SenderAfter fill:#95e1d3
    style RecipientAfter fill:#95e1d3
```

---

## Merkle Trees

Merkle trees provide efficient cryptographic commitments to large datasets (transactions and account state).

### Merkle Tree Construction

```mermaid
graph TD
    subgraph "Leaf Nodes"
        L0[Hash 0]
        L1[Hash 1]
        L2[Hash 2]
        L3[Hash 3]
        L4[Hash 4]
        L5[Hash 5]
        L6[Hash 6]
        L7[Hash 7]
    end

    subgraph "Internal Nodes"
        I0[H01 = SHA256<br/>Hash0 + Hash1]
        I1[H23 = SHA256<br/>Hash2 + Hash3]
        I2[H45 = SHA256<br/>Hash4 + Hash5]
        I3[H67 = SHA256<br/>Hash6 + Hash7]

        I4[H0123 = SHA256<br/>H01 + H23]
        I5[H4567 = SHA256<br/>H45 + H67]
    end

    subgraph "Root Level"
        MerkleRoot[Merkle Root<br/>SHA256 H0123 + H4567]
    end

    L0 --> I0
    L1 --> I0
    L2 --> I1
    L3 --> I1
    L4 --> I2
    L5 --> I2
    L6 --> I3
    L7 --> I3

    I0 --> I4
    I1 --> I4
    I2 --> I5
    I3 --> I5

    I4 --> MerkleRoot
    I5 --> MerkleRoot

    style MerkleRoot fill:#ff6b6b
    style I4 fill:#4ecdc4
    style I5 fill:#4ecdc4
```

### Transaction Root (tx_root)

The `tx_root` is computed by hashing all transaction hashes in the block:

1. Compute SHA-256 hash of each transaction
2. Build binary Merkle tree from transaction hashes
3. Store root in block header as `TxRoot`

**Purpose:** Efficiently prove a transaction exists in a block without providing all transactions.

### State Root (state_root)

The `state_root` is computed by hashing all account states after applying the block:

1. After applying all transactions, compute SHA-256 hash of each account (address + balance + nonce)
2. Build binary Merkle tree from account hashes
3. Store root in block header as `StateRoot`

**Purpose:** Cryptographic commitment to the entire account state at a specific block height.

---

## Block Storage

Blocks are stored immutably in SQLite with triggers preventing modification or deletion.

### Database Schema Network

```mermaid
graph TB
    subgraph "Core Tables"
        Blocks[blocks<br/>Immutable block storage<br/>block_number PRIMARY KEY]
        ChainState[chain_state<br/>Current head tracking<br/>Single row id=1]
        Validators[validators<br/>Authorized validators<br/>address PRIMARY KEY]
    end

    subgraph "Views"
        BlockTxView[block_transactions<br/>JOIN blocks + transactions]
        ChainStatsView[chain_stats<br/>Aggregate metrics]
    end

    subgraph "Triggers"
        InsertTrigger[trigger_blocks_update_chain_state<br/>AFTER INSERT ON blocks]
        ValidatorTrigger[trigger_blocks_update_validator_stats<br/>AFTER INSERT ON blocks]
        ImmutableTrigger[trigger_blocks_immutable<br/>BEFORE UPDATE ON blocks]
        NoDeleteTrigger[trigger_blocks_no_delete<br/>BEFORE DELETE ON blocks]
    end

    Blocks -->|references| ChainState
    Blocks -->|references| Validators
    Blocks -.->|joined in| BlockTxView
    ChainState -.->|aggregated in| ChainStatsView

    InsertTrigger -->|updates| ChainState
    ValidatorTrigger -->|updates| Validators
    ImmutableTrigger -->|protects| Blocks
    NoDeleteTrigger -->|protects| Blocks

    style Blocks fill:#ff6b6b
    style ChainState fill:#4ecdc4
    style Validators fill:#ffe66d
    style ImmutableTrigger fill:#f38181
    style NoDeleteTrigger fill:#f38181
```

### Immutability Enforcement

```sql
-- Prevent block modification
CREATE TRIGGER trigger_blocks_immutable
BEFORE UPDATE ON blocks
BEGIN
    SELECT RAISE(ABORT, 'Blocks are immutable and cannot be modified');
END;

-- Prevent block deletion
CREATE TRIGGER trigger_blocks_no_delete
BEFORE DELETE ON blocks
BEGIN
    SELECT RAISE(ABORT, 'Blocks are immutable and cannot be deleted');
END;
```

### Automatic Chain State Updates

```sql
-- Auto-update chain_state on new block insertion
CREATE TRIGGER trigger_blocks_update_chain_state
AFTER INSERT ON blocks
BEGIN
    UPDATE chain_state
    SET
        head_block_number = NEW.block_number,
        head_block_hash = NEW.block_hash,
        total_blocks = total_blocks + 1,
        total_transactions = total_transactions + NEW.tx_count,
        updated_at = strftime('%s', 'now')
    WHERE id = 1;
END;
```

---

## Configuration

### YAML Configuration

```yaml
consensus:
  enabled: true
  block_time: 2s
  validators:
    - "a1b2c3d4e5f6..."  # Validator 1 (hex-encoded Ed25519 pubkey)
    - "f6e5d4c3b2a1..."  # Validator 2
    - "1234567890ab..."  # Validator 3
  validator_key: "a1b2c3d4e5f6..."  # This node's validator key (64 hex chars)
  genesis_timestamp: 0  # 0 = use current time
```

### Single-Node Development Mode

For testing without multiple validators:

```yaml
consensus:
  enabled: true
  block_time: 2s
  validators: []          # Empty = single validator mode
  validator_key: ""       # Empty = generate random key
  genesis_timestamp: 0
```

When `validators` is empty:
- The node uses its own `validator_key` as the only validator
- If `validator_key` is also empty, a random key is generated (with warning)
- The node produces blocks every 2 seconds automatically

### Go Configuration Struct

```go
type ConsensusConfig struct {
    Enabled          bool          `mapstructure:"enabled"`
    BlockTime        time.Duration `mapstructure:"block_time"`
    Validators       []string      `mapstructure:"validators"`        // Hex addresses
    ValidatorKey     string        `mapstructure:"validator_key"`     // This node's key
    GenesisTimestamp int64         `mapstructure:"genesis_timestamp"` // 0 = now
}
```

---

## API Integration

### Consensus Statistics Endpoint

**GET** `/v1/status`

Returns consensus engine statistics:

```json
{
  "api_version": "4.3.0",
  "consensus": {
    "block_height": 12345,
    "is_validator": true,
    "validator_count": 3,
    "block_time": "2s",
    "current_block_hash": "a1b2c3d4",
    "current_block_txs": 150,
    "current_block_gas_used": 4500000
  },
  "rate_limiter": { ... },
  "p2p_stats": { ... },
  "mempool_size": 42
}
```

### Block Query Endpoints

**GET** `/v1/blocks/latest`

Returns the latest block.

**GET** `/v1/blocks/number/:number`

Returns block by block number.

**GET** `/v1/blocks/:hash`

Returns block by block hash (hex-encoded).

---

## Security Considerations

### Byzantine Fault Tolerance

The system tolerates up to `(n-1)/3` malicious validators:

| Validator Count | Byzantine Tolerance |
|----------------|---------------------|
| 1 | 0 (no tolerance) |
| 4 | 1 malicious validator |
| 7 | 2 malicious validators |
| 10 | 3 malicious validators |
| 100 | 33 malicious validators |

**Requirement:** At least 2/3 of validators must be honest for consensus to remain secure.

### Attack Vectors

```mermaid
graph TD
    subgraph "Attack Scenarios"
        A1[Double Spend Attack]
        A2[Validator Collusion]
        A3[Long-Range Attack]
        A4[Timestamp Manipulation]
        A5[State Root Forgery]
    end

    subgraph "Mitigations"
        M1[Nonce enforcement<br/>prevents replay]
        M2[2/3 honest requirement<br/>BFT threshold]
        M3[Immutable storage<br/>cannot rewrite history]
        M4[Timestamp validation<br/>P2P clock sync]
        M5[Merkle verification<br/>cryptographic proofs]
    end

    A1 -->|mitigated by| M1
    A2 -->|mitigated by| M2
    A3 -->|mitigated by| M3
    A4 -->|mitigated by| M4
    A5 -->|mitigated by| M5

    style A1 fill:#f38181
    style A2 fill:#f38181
    style A3 fill:#f38181
    style A4 fill:#f38181
    style A5 fill:#f38181
    style M1 fill:#95e1d3
    style M2 fill:#95e1d3
    style M3 fill:#95e1d3
    style M4 fill:#95e1d3
    style M5 fill:#95e1d3
```

### Validator Security

Validators must:

1. **Secure private keys** - Use hardware security modules (HSMs) in production
2. **Monitor for slashing conditions** - Track malicious behavior by other validators
3. **Maintain uptime** - Missed blocks reduce network throughput
4. **Sync clocks** - Use NTP for accurate timestamps
5. **Validate incoming blocks** - Never accept blocks without full validation

---

## Performance Metrics

### Block Production

- **Block time:** 2 seconds (deterministic)
- **Max transactions per block:** 1000
- **Max gas per block:** 30,000,000
- **Average gas per transaction:** 30,000
- **Theoretical throughput:** 500 TPS (transactions per second)

### Merkle Tree Performance

| Account Count | Tree Depth | Hash Operations |
|--------------|------------|-----------------|
| 1,000 | 10 | 1,999 |
| 10,000 | 14 | 19,999 |
| 100,000 | 17 | 199,999 |
| 1,000,000 | 20 | 1,999,999 |

**Time complexity:** O(n) for building tree, O(log n) for proof verification

### Database Performance

- **Block insertion:** <10ms (single transaction with triggers)
- **Block retrieval by number:** <1ms (primary key index)
- **Block retrieval by hash:** <5ms (unique index)
- **Chain head query:** <1ms (single row table)

---

## Monitoring

### Prometheus Metrics

The consensus engine exposes metrics at `/metrics`:

```
# Block production
coinjecture_blocks_produced_total{validator="alice"} 1234

# Block height
coinjecture_block_height 12345

# Block production time
coinjecture_block_production_duration_seconds{quantile="0.5"} 0.150
coinjecture_block_production_duration_seconds{quantile="0.99"} 0.500

# Transaction processing
coinjecture_block_transactions_total 185423
coinjecture_block_gas_used_total 5562690000

# Validator stats
coinjecture_validator_blocks_produced{address="a1b2c3d4"} 4115
coinjecture_validator_last_block_timestamp{address="a1b2c3d4"} 1704067200
```

### Logging

Consensus events are logged with structured fields:

```
INFO  Consensus engine started  block_time=2s validators=3 validator_key=a1b2c3d4
INFO  Producing new block  block_number=12346
INFO  New block produced  block_number=12346 block_hash=f1e2d3c4 tx_count=150 gas_used=4500000 state_root=a9b8c7d6
INFO  Processing received block  block_number=12347 block_hash=d4c3b2a1 validator=f6e5d4c3
INFO  Block accepted and applied  block_number=12347 block_hash=d4c3b2a1
```

---

## Troubleshooting

### Problem: Node not producing blocks

**Symptoms:**
- Block height not increasing
- Logs show "Not our turn to validate, skipping block production"

**Causes:**
1. Node's validator key not in validator set
2. Validator rotation skipping this node
3. Consensus engine not started

**Solutions:**
1. Check `consensus.validators` includes this node's public key
2. Verify `consensus.validator_key` matches one of the configured validators
3. Ensure `consensus.enabled = true` in config
4. Check logs for consensus startup confirmation

### Problem: Received block rejected

**Symptoms:**
- Logs show "Block rejected: ..."
- Block height diverges from network

**Causes:**
1. Unauthorized validator produced block
2. Parent hash mismatch (fork detected)
3. State root mismatch (invalid state transition)
4. Timestamp out of acceptable range

**Solutions:**
1. Verify all nodes have identical validator configuration
2. Check for network partitions causing forks
3. Ensure all nodes apply transactions identically
4. Sync system clocks with NTP

### Problem: State root mismatch

**Symptoms:**
- Blocks rejected with "state root mismatch"
- Nodes have divergent state

**Causes:**
1. Non-deterministic state transitions
2. Race conditions in transaction application
3. Database corruption

**Solutions:**
1. Ensure transaction ordering is deterministic (nonce-based)
2. Use proper locking in state manager
3. Verify SQLite database integrity: `PRAGMA integrity_check`
4. Resync from genesis if state is corrupted

---

## Development Roadmap

### Completed (v4.5.0+)

**Core Consensus (v4.5.0):**
- [x] Block structure with Merkle trees
- [x] PoA consensus engine with round-robin rotation
- [x] Block builder with mempool integration
- [x] State transition logic
- [x] Block storage with immutability
- [x] Genesis block initialization
- [x] Daemon integration
- [x] Single-node development mode

**Advanced Features (v4.5.0+):**
- [x] **Fork choice rule** - Longest valid chain with hash tiebreaker
- [x] **Chain reorganization** - Atomic state rollback with snapshots
- [x] **P2P block broadcasting** - Full libp2p integration with gossipsub
- [x] **Block sync protocol** - Historical block downloads from peers
- [x] **Validator slashing** - 4 offense types with reputation scoring
- [x] **Checkpoint system** - Fast sync from configurable checkpoints
- [x] **Consensus tests** - 15 engine tests, 11 builder tests, 5 integration tests
- [x] **Load testing** - TPS measurement framework with real-time metrics

### Code References

**Advanced Features:**
- **Fork choice:** [go/pkg/consensus/fork_choice.go](../go/pkg/consensus/fork_choice.go)
- **Slashing system:** [go/pkg/consensus/slashing.go](../go/pkg/consensus/slashing.go)
- **Checkpoint system:** [go/pkg/consensus/checkpoint.go](../go/pkg/consensus/checkpoint.go)
- **Engine tests:** [go/pkg/consensus/engine_test.go](../go/pkg/consensus/engine_test.go)
- **Builder tests:** [go/pkg/consensus/builder_test.go](../go/pkg/consensus/builder_test.go)
- **Integration tests:** [go/test/integration/multi_node_test.go](../go/test/integration/multi_node_test.go)
- **Load testing:** [go/cmd/loadtest/main.go](../go/cmd/loadtest/main.go)

### Future Enhancements

Potential improvements for v5.0:
- [ ] **Dynamic validator set** - Add/remove validators via governance
- [ ] **Finality gadget** - Explicit finality after N blocks
- [ ] **Cross-chain bridges** - Inter-blockchain communication
- [ ] **Optimistic rollups** - Layer 2 scaling solutions

---

## References

### Code Locations

- **Consensus engine:** [go/pkg/consensus/engine.go](../go/pkg/consensus/engine.go)
- **Block structure:** [go/pkg/consensus/block.go](../go/pkg/consensus/block.go)
- **Block builder:** [go/pkg/consensus/builder.go](../go/pkg/consensus/builder.go)
- **Merkle trees:** [go/pkg/consensus/merkle.go](../go/pkg/consensus/merkle.go)
- **Block storage:** [go/pkg/state/blocks.go](../go/pkg/state/blocks.go)
- **Database migration:** [migrations/002_consensus_blocks.sql](../migrations/002_consensus_blocks.sql)
- **Configuration:** [go/pkg/config/config.go](../go/pkg/config/config.go)
- **Daemon integration:** [go/cmd/coinjectured/main.go](../go/cmd/coinjectured/main.go)

### External Resources

- **Proof-of-Authority:** [Ethereum PoA Networks](https://wiki.parity.io/Proof-of-Authority-Chains)
- **Merkle Trees:** [Bitcoin Merkle Trees](https://en.bitcoin.it/wiki/Protocol_documentation#Merkle_Trees)
- **Byzantine Fault Tolerance:** [Practical Byzantine Fault Tolerance](http://pmg.csail.mit.edu/papers/osdi99.pdf)

---

## Appendix: Consensus Pseudocode

### Block Production Loop

```python
def block_production_loop():
    ticker = new_ticker(block_time)

    while true:
        wait_for_tick(ticker)

        if not is_our_turn(block_height + 1):
            continue  # Skip this round

        # Build block
        parent_hash = current_block.block_hash
        transactions = mempool.select_top_transactions(max=1000, gas_limit=30M)

        block = Block(
            block_number=block_height + 1,
            parent_hash=parent_hash,
            transactions=transactions,
            validator=our_validator_key
        )

        # Compute Merkle roots
        block.tx_root = compute_merkle_root([tx.hash for tx in transactions])

        # Apply transactions to state
        for tx in transactions:
            apply_transaction(tx)

        # Compute state root
        account_hashes = [hash(account) for account in all_accounts]
        block.state_root = compute_merkle_root(account_hashes)

        # Finalize block
        block.block_hash = sha256(block.header)

        # Update chain
        current_block = block
        block_height += 1

        # Persist
        db.save_block(block)

        # Broadcast
        p2p.broadcast_block(block)

        log.info(f"Produced block {block.block_number}")
```

### Validator Rotation

```python
def is_our_turn(block_number):
    validator_count = len(validators)
    validator_index = block_number % validator_count
    expected_validator = validators[validator_index]
    return expected_validator == our_validator_key
```

### Transaction Application

```python
def apply_transaction(tx):
    # Get accounts
    sender = db.get_account(tx.from_address)
    recipient = db.get_account(tx.to_address)

    # Validate
    if sender.nonce != tx.nonce:
        raise InvalidNonce()
    if sender.balance < (tx.amount + tx.fee):
        raise InsufficientFunds()

    # Update sender
    sender.balance -= (tx.amount + tx.fee)
    sender.nonce += 1
    db.update_account(sender)

    # Update recipient
    recipient.balance += tx.amount
    db.update_account(recipient)

    # Remove from mempool
    mempool.remove_transaction(tx.hash)
```

---

**End of Consensus Documentation**
