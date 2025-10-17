# COINjecture System Architecture

## Overview

COINjecture is a utility-based blockchain that proves computational work was done through NP-Complete problem solving. Built on Satoshi Nakamoto's foundational insights about proof-of-work consensus and immutable ledgers, COINjecture evolves these concepts with verifiable computational complexity and practical utility.

### Core Architectural Principles

1. **Verifiable Work**: NP-Complete problems provide O(2^n) solve complexity with O(n) verification
2. **Emergent Tokenomics**: Supply, deflation, and block time emerge from measured network behavior
3. **Utility-Based Design**: Consensus layer + optional user-submitted computational work markets
4. **Distributed Participation**: Competition within hardware classes, not across them

For the vision and principles, see [MANIFESTO.md](MANIFESTO.md).

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Submissions Layer                    │
│  (Users submit problems, set bounties, choose aggregation)  │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Problem Pool & Aggregation Engine               │
│     (Manages submissions, tracks solutions, aggregates)     │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Solver Selection (Tier-based)                   │
│  (Hardware profile → optimal tier → profitability estimate)  │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              PoW Engine (NP-Complete Solving)                │
│    (Generate problem → solve → measure complexity metrics)   │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                 Commit-Reveal Protocol                       │
│  (Create commitment → mine header → reveal solution bundle)  │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│                    Consensus Layer                           │
│   (Validate headers → verify reveals → fork choice → tip)    │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│              Block Creation & Storage                        │
│     (Persist blocks → index commitments → IPFS bundles)     │
└────────────────────────┬────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────────┐
│         Tokenomics Engine (Work Score → Rewards)             │
│  (Calculate work score → determine reward → update supply)   │
└─────────────────────────────────────────────────────────────┘
```

## Core Modules

### 3.1 Core Module
**Reference**: [docs/blockchain/core.md](docs/blockchain/core.md)

**Responsibilities**:
- Define canonical on-chain structures: `BlockHeader`, `Block`, `CommitmentLeaf`
- Deterministic hashing and serialization
- Merkle tree construction and proof verification

**Key Structures**:
- `BlockHeader`: version, parent_hash, height, timestamp, commitments_root, tx_root, difficulty_target, cumulative_work, miner_pubkey, commit_nonce, problem_type, tier, commit_epoch, proof_commitment, header_hash
- `CommitmentLeaf`: 64-byte structure binding problem params and solution claims
- `Block`: header + optional transaction data

### 3.2 Consensus Module
**Reference**: [docs/blockchain/consensus.md](docs/blockchain/consensus.md)

**Responsibilities**:
- Validate headers and reveals
- Maintain block tree and choose best tip by cumulative work
- Build deterministic genesis

**Validation Pipeline**:
1. Basic checks: version, timestamp, parent linkage
2. Commitment presence: proof_commitment non-zero, commitments_root valid
3. Difficulty: estimated_work(header) >= current_target
4. Fork-choice: insert node, compute cumulative_work, select tip

**Fork Choice**: `tip = argmax(cumulative_work)` with tie-breaker on earliest receipt time

### 3.3 PoW Module
**Reference**: [docs/blockchain/pow.md](docs/blockchain/pow.md)

**Responsibilities**:
- ProblemRegistry: register/generate/solve/verify problems
- Commit-reveal helpers and salt derivation
- Work score calculation and difficulty mapping

**Problem Registry Interface**:
- `generate(problem_type, seed, tier) -> problem:dict`
- `solve(problem) -> solution:any`
- `verify(problem, solution) -> bool`
- `build_complexity(problem, solution, metrics) -> ComputationalComplexity`

**Problem Type Categories**:
- **Optimization Problems**: Knapsack, TSP, Bin Packing, Job Scheduling
- **Decision Problems**: SAT, Graph Coloring, Clique, Vertex Cover
- **Search Problems**: Subset Sum, Hamiltonian Path, Set Cover
- **Number Theory**: Factorization, Lattice Problems
- **Graph Theory**: Graph Coloring, Clique, Vertex Cover, Hamiltonian Path

**Supported Problems**:

**Production Ready**:
- `subset_sum`: Exact DP solver, NP-Complete, O(2^n) solve, O(n) verify

**In Development**:
- `knapsack`: 0/1 Knapsack problem, NP-Complete, O(2^n) solve, O(n) verify
- `graph_coloring`: Graph k-coloring, NP-Complete, exponential solve, O(n) verify
- `sat`: Boolean satisfiability, NP-Complete, exponential solve, O(n) verify
- `tsp`: Traveling Salesman Problem, NP-Complete, O(n!) solve, O(n) verify

**Scaffold/Research**:
- `factorization`: Integer factorization, NP-Hard, subexponential solve, O(1) verify
- `lattice`: Lattice-based problems, NP-Hard, exponential solve, polynomial verify
- `clique`: Maximum clique, NP-Complete, exponential solve, O(n²) verify
- `vertex_cover`: Minimum vertex cover, NP-Complete, exponential solve, O(n) verify
- `hamiltonian_path`: Hamiltonian path, NP-Complete, O(n!) solve, O(n) verify
- `set_cover`: Set cover problem, NP-Complete, exponential solve, O(n) verify
- `bin_packing`: Bin packing, NP-Hard, exponential solve, O(n) verify
- `job_scheduling`: Job shop scheduling, NP-Hard, exponential solve, O(n) verify

**Work Score Formula**:
```
work_score = 
    time_asymmetry * 
    sqrt(space_asymmetry) * 
    problem_weight * 
    size_factor * 
    quality_score * 
    energy_efficiency
```

**Anti-Grinding**:
- `epoch_salt = H(parent_hash || round(timestamp/epoch))`
- `commitment = H(encode(problem_params) || miner_salt || epoch_salt)`

### 3.4 Network Module
**Reference**: [docs/blockchain/network.md](docs/blockchain/network.md)

**Responsibilities**:
- libp2p host wrapper
- Gossipsub topics for headers, reveals, requests/responses
- RPC for sync and proof fetch

**Gossipsub Topics**:
- `/coinj/headers/1.0.0`: Announce new headers
- `/coinj/commit-reveal/1.0.0`: Reveal bundles and CIDs
- `/coinj/requests/1.0.0`: Fetch requests
- `/coinj/responses/1.0.0`: Fetch responses

**RPC Methods**:
- `get_headers(start_height, count) -> [headers]`
- `get_block_by_hash(hash) -> header or full block`
- `get_proof_by_cid(cid) -> bundle bytes`

### 3.5 Storage Module
**Reference**: [docs/blockchain/storage.md](docs/blockchain/storage.md)

**Responsibilities**:
- Local persistent store for headers/blocks/indices
- IPFS client integration for proof bundles
- Pruning strategies per node role

**Database Schema**:
- `headers`: key=header_hash → header_bytes
- `blocks`: key=block_hash → block_bytes
- `tips`: single key → set of tip hashes
- `work_index`: key=height → cumulative_work
- `commit_index`: key=commitment → cid
- `peer_index`: key=peer_id → metadata

**Pruning Modes**:
- **light**: Headers + commit_index only
- **full**: Recent N epochs of bundles
- **archive**: All data, pinned bundles

### 3.6 Node Module
**Reference**: [docs/blockchain/node.md](docs/blockchain/node.md)

**Responsibilities**:
- Node configuration and role selection
- Compose services: networking, consensus, storage, pow engine
- Lifecycle management

**Node Roles**:
- **light**: Subscribe headers, validate commitments, request bundles on demand
- **full**: Validate headers + reveals, selective bundle fetch, fork choice
- **miner**: Run commit-reveal loop, publish headers and reveals
- **archive**: Validate and pin all bundles, serve data to peers

### 3.7 CLI Module
**Reference**: [docs/blockchain/cli.md](docs/blockchain/cli.md)

**Responsibilities**:
- User-facing commands for node management and chain interaction

**Key Commands**:
- `coinjectured init --role [light|full|miner|archive]`
- `coinjectured run --config PATH`
- `coinjectured mine --problem-type subset_sum --tier desktop`
- `coinjectured get-block --hash HEX`
- `coinjectured get-proof --cid CID`

## Utility Layer

### 4.1 User Submissions System
**Reference**: [src/user_submissions/](src/user_submissions/) directory

**Components**:
- `ProblemSubmission`: User-submitted problem with bounty and aggregation strategy
- `SolutionRecord`: Individual solution with quality, work score, energy metrics
- `ProblemPool`: Manages pending problems and solution collection
- `AggregationStrategy`: ANY, BEST, MULTIPLE, STATISTICAL

**Aggregation Strategies**:
- **ANY**: First valid solution wins (urgent problems)
- **BEST**: Highest quality solution wins (quality matters)
- **MULTIPLE**: Collect multiple diverse solutions (multiple approaches)
- **STATISTICAL**: Collect statistical sample (research problems)

### 4.2 Tokenomics Engine
**Reference**: [DYNAMIC_TOKENOMICS.README.md](DYNAMIC_TOKENOMICS.README.md), [API.README.md](API.README.md)

**Core Functions**:
- `calculate_work_score(complexity_metrics)`: Measure computational work
- `calculate_block_reward(work_score, network_state)`: Determine reward
- `get_deflation_factor(cumulative_work)`: Natural deflation
- `select_optimal_tier(hardware_profile)`: Market-driven tier selection

**Reward Formula**:
```
reward = log(1 + work_score/network_avg) * deflation_factor

where:
  deflation_factor = 1 / (2^(log2(cumulative_work)/10))
```

## Data Flow

### 5.1 Problem Submission Flow
```
User
  ↓ submit_problem(problem_spec, bounty, aggregation_strategy)
ProblemPool
  ↓ add_submission(submission_id, submission)
Storage
  ↓ get_eligible_problems(solver_tier)
Solver
```

### 5.2 Block Creation Flow
```
Solver
  ↓ select_optimal_tier(hardware_profile)
Tier Selection
  ↓ generate_problem(seed, tier)
PoW Engine
  ↓ solve(problem)
Solution
  ↓ measure_complexity(solve_time, verify_time, energy)
Complexity Metrics
  ↓ create_commitment(problem_params, salt)
Commitment
  ↓ mine_header(commitment, difficulty_target)
Header
  ↓ reveal(solution_bundle)
Reveal
  ↓ verify(problem, solution)
Verification
  ↓ calculate_work_score(complexity)
Work Score
  ↓ calculate_reward(work_score, network_state)
Reward
  ↓ record_block(block, complexity, reward)
Blockchain State
```

### 5.3 Consensus Flow
```
Header Gossip
  ↓ receive_header(header_msg)
Header Validation
  ↓ validate_header(version, timestamp, parent, commitment)
Basic Checks
  ↓ check_difficulty(estimated_work >= target)
Difficulty Check
  ↓ fork_choice(cumulative_work)
Tip Selection
  ↓ receive_reveal(bundle_cid)
Reveal Reception
  ↓ verify_commitment(params, salt, commitment)
Commitment Verification
  ↓ verify_solution(problem, solution)
Solution Verification
  ↓ accept_block(header, bundle)
Block Acceptance
  ↓ update_state(cumulative_work, indices)
State Update
```

## Tier System

### 6.1 Hardware Compatibility Categories

| Tier | Name | Problem Size | Target Hardware | Characteristics |
|------|------|--------------|-----------------|-----------------|
| 1 | Mobile | 8-12 elements | Smartphones, tablets, IoT | Energy efficient, fast iteration |
| 2 | Desktop | 12-16 elements | Laptops, basic desktops | Balanced performance |
| 3 | Workstation | 16-20 elements | Gaming PCs, dev machines | Higher compute power |
| 4 | Server | 20-24 elements | Dedicated servers, cloud | Massive parallel processing |
| 5 | Cluster | 24-32 elements | Multi-node, supercomputers | Distributed computation |

### 6.2 Tier Selection

**Process**:
1. Hardware profile assessment (computational_capability, energy_efficiency)
2. Tier metrics retrieval (avg_work_score, avg_solve_time, market_share)
3. Profitability estimation for each tier
4. Select tier with highest profitability

**Profitability Formula**:
```
profitability = expected_reward / (expected_time * energy_cost)

where:
  expected_reward = log(1 + expected_work/network_avg) * deflation_factor
  expected_time = network_avg_time / hardware_capability
```

**Market Equilibrium**:
- High profitability tier → more solvers enter → competition increases → work scores normalize
- Low profitability tier → solvers exit → competition decreases → work scores increase
- System self-balances across all hardware classes

## Key Architectural Principles

### 7.1 Verifiable Work

**NP-Complete/NP-Hard Problems**:
- **Subset Sum**: O(2^n) solve, O(n) verify - production ready
- **Knapsack**: O(2^n) solve, O(n) verify - in development
- **Graph Coloring**: Exponential solve, O(n) verify - in development
- **SAT**: Exponential solve, O(n) verify - in development
- **TSP**: O(n!) solve, O(n) verify - in development
- **Factorization**: Subexponential solve, O(1) verify - research
- **Lattice Problems**: Exponential solve, polynomial verify - research

**Key Properties**:
- Inherent asymmetry (hard to solve, easy to verify)
- Measured complexity metrics prove actual computational work
- Diverse problem types enable different optimization strategies
- Problem registry allows pluggable problem types

**On-Chain Proof**:
- Commitment binds problem parameters before solving
- Solution bundle stored on IPFS
- Verification happens on-chain or via fast probabilistic checks

### 7.2 Emergent Tokenomics

**No Predetermined Schedules**:
- Supply emerges from cumulative work score
- Deflation emerges from network growth (each new unit = smaller fraction of total)
- Block time emerges from verification performance
- Difficulty adjusts to maintain work score distribution

**Dynamic Adaptation**:
```
block_time = median_verify_time * network_propagation * competition_window
difficulty_adjustment = f(recent_work_scores / historical_work_scores)
deflation_factor = 1 / (2^(log2(cumulative_work)/10))
```

### 7.3 Utility-Based Design

**Two Layers**:
1. **Consensus Layer**: Proof of computational work via NP-Complete problems
2. **Utility Layer**: User-submitted computational work markets

**Economic Model**:
- Users submit problems and set bounties
- Solvers earn block rewards + user bounties
- Aggregation strategies enable diverse use cases
- Real economic demand drives real computational supply

### 7.4 Distributed Participation

**Hardware-Class-Relative Competition**:
- Mobile competes with mobile (on optimization)
- Server competes with server (on optimization)
- Work score independent of tier
- Profitability based on efficiency, not hardware scale

**Algorithm Optimization Economy**:
- Better algorithms → higher work scores → more rewards
- Energy efficiency → lower costs → higher profitability
- Competition rewards innovation, not capital expenditure

## Security Model

### 8.1 Commit-Reveal Protocol

**Purpose**: Prevent grinding attacks where miners generate many problems to find easy ones

**Mechanism**:
1. **Commit Phase**: Miner creates `commitment = H(problem_params || miner_salt || epoch_salt)`
2. **Mine Phase**: Miner finds header with sufficient work score
3. **Reveal Phase**: Miner publishes solution bundle, proves commitment matches

**Security Properties**:
- Epoch salt derived from parent hash (unpredictable)
- Miner salt must be unique per header
- Commitment binding prevents changing problem after mining

### 8.2 Fork Choice

**Rule**: `tip = argmax(cumulative_work)` with tie-breaker on earliest receipt time

**Cumulative Work**:
```
cumulative_work[block] = cumulative_work[parent] + work_score[block]
```

**Reorg Protection**:
- Bounded reorg depth (configurable)
- Finality depth k (e.g., 20 blocks) for application-level finality
- Emit events on reorg for application awareness

### 8.3 DOS Protection

**Rate Limiting**:
- Per-peer quotas on messages
- Max headers per peer per second
- Proof size caps

**Validation**:
- Drop malformed messages
- Deduplicate by header_hash/commitment
- Reject oversized payloads

## Implementation Notes

### 9.1 Language-Agnostic Design

**All specifications are implementation-independent**:
- Fixed-width integers for consensus-critical values
- Deterministic serialization (canonical field order, explicit endianness)
- No language-specific types on the wire
- Cross-language compatibility verified through test vectors

**Consensus-Critical**:
- Use scaled integers instead of floats where possible
- Explicit endianness (little-endian for network messages)
- Deterministic encoding for problem parameters

### 9.2 Testing Strategy
**Reference**: [docs/testing.md](docs/testing.md)

**Integration Scenarios**:
- Header-first sync across multiple nodes
- Commit-reveal success path with bundle retrieval
- Invalid reveal rejection (mismatched commitment)
- Reorg handling (longer cumulative-work branch)

**Invariants**:
- Commitment binding/hiding holds for all accepted blocks
- Fork-choice picks max cumulative work deterministically
- Light nodes never accept blocks without valid commitments

### 9.3 Development Environment
**Reference**: [docs/devnet.md](docs/devnet.md)

**Devnet Setup**:
- Launch 3-5 nodes with mixed roles (full, miner, light, archive)
- Temporary data directories for testing
- Bootstrap peer connections
- Enable mining on selected nodes

**Operations**:
- `python scripts/devnet.py up --nodes 4`: Start devnet
- `python scripts/devnet.py down`: Stop and cleanup

## API Integration

**Reference**: [API.README.md](API.README.md) for complete specifications

### Tokenomics APIs
- `calculate_work_score(complexity_metrics) -> float`
- `calculate_block_reward(work_score, network_state) -> float`
- `get_deflation_factor(cumulative_work) -> float`
- `select_optimal_tier(hardware_profile, tier_metrics) -> tier_id`

### User Submissions APIs
- `submit_problem(problem_spec, bounty, aggregation_strategy) -> submission_id`
- `get_eligible_problems(solver_tier) -> list[submission]`
- `record_solution(submission_id, solution_record) -> bool`
- `aggregate_solutions(submission_id, strategy) -> result`

### Network State APIs
- `get_tier_metrics(tier_id) -> tier_metrics`
- `get_network_state() -> network_state`
- `estimate_profitability(hardware_profile, tier_id) -> float`

## Documentation Map

| Document | Purpose |
|----------|---------|
| [MANIFESTO.md](MANIFESTO.md) | Vision and principles |
| [ARCHITECTURE.README.md](ARCHITECTURE.README.md) | This document - system architecture |
| [API.README.md](API.README.md) | Language-agnostic API specifications |
| [DYNAMIC_TOKENOMICS.README.md](DYNAMIC_TOKENOMICS.README.md) | Tokenomics system details |
| [docs/blockchain/core.md](docs/blockchain/core.md) | Core data structures and hashing |
| [docs/blockchain/consensus.md](docs/blockchain/consensus.md) | Consensus rules and fork choice |
| [docs/blockchain/pow.md](docs/blockchain/pow.md) | PoW engine and work score |
| [docs/blockchain/network.md](docs/blockchain/network.md) | Networking and gossip |
| [docs/blockchain/storage.md](docs/blockchain/storage.md) | Storage and IPFS integration |
| [docs/blockchain/node.md](docs/blockchain/node.md) | Node roles and configuration |
| [docs/blockchain/cli.md](docs/blockchain/cli.md) | CLI commands |
| [src/user_submissions/](src/user_submissions/) | User submission system code |
| [docs/testing.md](docs/testing.md) | Testing specifications |
| [docs/devnet.md](docs/devnet.md) | Development environment |

## Getting Started

### Recommended Reading Order

1. **[MANIFESTO.md](MANIFESTO.md)** - Understand the vision and principles
2. **[ARCHITECTURE.README.md](ARCHITECTURE.README.md)** - Understand the system architecture (this document)
3. **[API.README.md](API.README.md)** - Understand the interfaces and data flows
4. **Module-specific READMEs** - Understand implementation details for specific components

### For Different Audiences

**Researchers**:
- Start with MANIFESTO.md for the conceptual foundation
- Read blockchain/pow.README.md for complexity theory application
- Review DYNAMIC_TOKENOMICS.README.md for economic model

**Developers**:
- Start with ARCHITECTURE.README.md for system overview
- Read API.README.md for interface specifications
- Dive into module-specific READMEs for implementation details

**Users**:
- Start with MANIFESTO.md to understand what COINjecture is
- Review API.README.md User Submissions section to submit problems
- Check blockchain/cli.README.md for command-line usage

**Node Operators**:
- Read blockchain/node.README.md for role selection
- Review blockchain/storage.README.md for storage requirements
- Check scripts/devnet.README.md for testing setup

## Summary

COINjecture is a utility-based blockchain that proves computational work through NP-Complete problem solving. The architecture separates hardware capability classes (tiers) from reward mechanisms (work score), enabling distributed participation across heterogeneous hardware. Tokenomics emerge from measured network behavior rather than predetermined schedules, creating a computational work market on-chain.

Built on Satoshi's foundation. Evolved with complexity theory. Driven by real-world utility.
