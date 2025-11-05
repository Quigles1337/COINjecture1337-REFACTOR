# Refactor Plan: COINjecture v4.0.0
## Clean Architecture with Consensus Safety

**Date:** 2025-11-01
**Version:** 4.0.0-refactor
**Goal:** Establish clean architectural boundaries without breaking existing behavior

---

## Overview

This refactor introduces `src/coinjecture/` as a clean, well-typed package alongside the existing `src/` production code. The refactor **does not break public APIs** and provides backward-compatible shim imports.

### Architectural Vision

```
src/
├── coinjecture/              # NEW: Refactored package with clean boundaries
│   ├── types.py              # Canonical type definitions (frozen dataclasses)
│   ├── consensus/
│   │   └── codec.py          # Deterministic msgpack encoding + hashing
│   └── proofs/
│       ├── interface.py      # Abstract Solver ABC + SubsetSumSolver
│       └── limits.py         # Tier-based resource admission control
│
├── consensus.py              # EXISTING: Production consensus engine (kept)
├── pow.py                    # EXISTING: PoW system (kept)
├── network.py                # EXISTING: P2P + equilibrium gossip (kept)
├── storage.py                # EXISTING: SQLite + IPFS backend (kept)
├── node.py                   # EXISTING: Node lifecycle (kept)
├── cli.py                    # EXISTING: CLI commands (kept)
└── api/                      # EXISTING: REST endpoints (kept)
```

**Key Principle:** Existing code remains untouched. New code uses modern patterns. Migration happens incrementally.

---

## Package Layout: src/coinjecture/

### 1. types.py - Domain Type System

**Purpose:** Canonical type definitions with clear on-wire vs. internal separation.

**Exports:**
```python
# Type Aliases (NewType for domain modeling)
BlockHash, TxHash, MerkleRoot, Address, Signature, PublicKey, CID
Commitment, EpochSalt, MinerSalt, SolutionHash

# Enums
ProblemTierEnum, ProblemClassEnum

# On-Wire Types (frozen=True, immutable)
BlockHeader, Transaction, ProofReveal, ComplexityMetrics, BlockWireFormat

# Internal Types (mutable, for processing)
BlockNode, PeerInfo, ChainTip, MempoolEntry

# Config Types
ConsensusConfig, NetworkConfig, StorageConfig

# Errors
ValidationError, HeaderValidationError, RevealValidationError,
TierLimitExceeded, CommitmentMismatch, InvalidSignature
```

**Design Rationale:**
- **Frozen dataclasses** for consensus types → prevents accidental mutation
- **NewType wrappers** (BlockHash, Address) → type-safe, prevents mix-ups
- **Enum for tiers** → exhaustive matching, better than magic strings
- **Separation of concerns** → on-wire (network) vs. internal (processing)

**Migration Path:**
```python
# Old code (src/consensus.py)
from core.blockchain import Block, ProblemTier

# New code (future migration)
from coinjecture.types import BlockWireFormat, ProblemTierEnum
```

---

### 2. consensus/codec.py - Canonical Serialization

**Purpose:** Deterministic encoding/decoding of consensus-critical data.

**Key Functions:**
```python
# Encoding (frozen types → bytes)
encode_header(header: BlockHeader) -> bytes
encode_transaction(tx: Transaction) -> bytes
encode_proof_reveal(reveal: ProofReveal) -> bytes
encode_block(block: BlockWireFormat) -> bytes

# Decoding (bytes → frozen types)
decode_header(data: bytes) -> BlockHeader
decode_transaction(data: bytes) -> Transaction
decode_proof_reveal(data: bytes) -> ProofReveal

# Hashing (consensus-critical!)
compute_header_hash(header: BlockHeader) -> BlockHash
compute_transaction_hash(tx: Transaction) -> TxHash
compute_merkle_root(tx_hashes: List[TxHash]) -> MerkleRoot

# Commitment Verification
verify_reveal_commitment(reveal: ProofReveal) -> bool
create_commitment(...) -> Commitment
```

**Encoding Strategy:**
- **Primary:** msgspec (fast, deterministic msgpack)
- **Fallback:** JSON with sorted keys (portable, deterministic)
- **Detection:** `HAS_MSGSPEC` flag at module level

**Field Ordering (CRITICAL):**
```python
# BlockHeader fields MUST serialize in this order:
1. index
2. timestamp
3. previous_hash
4. merkle_root
5. problem_commitment
6. work_score
7. cumulative_work
8. tier

# ANY change to order = hard fork!
```

**Golden Vector Protection:**
- All hashes covered by `tests/spec/test_codec_golden.py`
- Test failures indicate consensus breakage
- Hashes MUST NOT change across versions (unless intentional hard fork)

**Strict Decode Rules (Defense Layer 1):**

The codec enforces **strict validation** on all deserialization paths to prevent:
- Consensus drift from malformed inputs
- Malicious crafted payloads (overlong varint, NaN/Inf)
- Accidental incompatibility from codec upgrades

**Validation Rules (Rust + Python):**

1. **Codec Version Check**
   - Reject if `codec_version != CODEC_VERSION` (currently 1)
   - Prevents parsing data from incompatible protocol versions
   - Implementation: `rust/coinjecture-core/src/codec.rs:42-48`

2. **Unknown Field Rejection**
   - Reject msgpack/JSON with unexpected keys
   - Prevents forward compatibility issues
   - Implementation: `rust/coinjecture-core/src/codec.rs:103-115`
   - Python fallback: `python/src/coinjecture/consensus/codec.py:78-92`

3. **Required Field Validation**
   - All consensus-critical fields MUST be present
   - Missing fields = immediate decode failure
   - Enforced via Rust `#[serde(deny_unknown_fields)]`

4. **Numeric Bounds**
   - Reject NaN, Inf, -Inf in floats
   - Reject negative timestamps
   - Reject varint longer than canonical encoding
   - Implementation: `rust/coinjecture-core/src/types.rs:124-138`

5. **Size Limits**
   - `MAX_BLOCK_SIZE`: 10 MB (hard limit)
   - `MAX_TX_PER_BLOCK`: 10,000 transactions
   - `MAX_PROOF_ELEMENTS`: 1,000 elements
   - Implementation: `rust/coinjecture-core/src/types.rs:18-23`

**Testing Strategy:**

Strict decode is validated by:
- Golden vector tests: `rust/coinjecture-core/tests/golden_tests.rs`
- Rejection tests: `rust/coinjecture-core/tests/codec_rejection_tests.rs`
- Parity validation: `.github/workflows/parity.yml` (dual-run mode)
- Property tests: `python/tests/property/test_codec_properties.py`

**CI Enforcement:**

All PRs MUST pass:
1. Parity workflow (no hash drift)
2. Golden vector comparison (base vs PR branch)
3. Codec rejection tests (18 negative test cases)

See: `.github/workflows/parity.yml` for gate enforcement

---

### 3. proofs/interface.py - Solver Abstraction

**Purpose:** Pluggable proof-of-work backends with guaranteed verification properties.

**Core Abstractions:**

```python
class Solver(ABC):
    """All PoW solvers must implement this interface."""

    @abstractmethod
    def solve(instance, limits, timeout) -> ProofSolution:
        """Generate solution within resource limits."""

    @abstractmethod
    def verify(instance, solution, limits) -> ProofVerificationResult:
        """Verify solution in polynomial time (MUST be O(n) or better)."""

    @abstractmethod
    def cost_hint(instance) -> float:
        """Estimate work score for fee calculation."""

    @abstractmethod
    def complexity_bound(problem_size) -> ComplexityMetrics:
        """Theoretical complexity (for asymmetry proof)."""

    @abstractmethod
    def generate_problem(tier, parent_hash, epoch_salt) -> ProofInstance:
        """Deterministic problem generation (prevents grinding)."""
```

**Concrete Implementation:**
```python
class SubsetSumSolver(Solver):
    """Subset Sum (NP-Complete, 2^n solve / O(n) verify)"""
    # Full implementation in interface.py:236-447
```

**Solver Registry:**
```python
_SOLVER_REGISTRY = {
    "subset_sum": SubsetSumSolver,
    # Future: "sat": SATSolver,
    #         "graph_coloring": GraphColoringSolver,
}

solver = get_solver("subset_sum")
solution = solver.solve(instance, limits)
result = solver.verify(instance, solution, limits)
```

**Design Benefits:**
- **Extensibility:** Add new problem types without touching consensus
- **Testability:** Mock solvers for unit tests
- **Type Safety:** ProofInstance, ProofSolution are well-typed
- **Resource Safety:** Limits enforced at interface boundary

---

### 4. proofs/limits.py - Admission Control

**Purpose:** Prevent DoS by enforcing tier-based resource caps.

**Tier Limits Matrix:**

| Tier | Hardware | Max Size | Max Solve Time | Max Memory | Max Proof Size |
|------|----------|----------|----------------|------------|----------------|
| TIER_1_MOBILE | Mobile/Battery | 12 elements | 60s | 256 MB | 64 KB |
| TIER_2_DESKTOP | Desktop (4-core) | 16 elements | 300s (5min) | 1 GB | 256 KB |
| TIER_3_WORKSTATION | Workstation (8-core) | 20 elements | 900s (15min) | 4 GB | 1 MB |
| TIER_4_SERVER | Server (16-core) | 24 elements | 1800s (30min) | 16 GB | 4 MB |
| TIER_5_CLUSTER | Cluster (64+ core) | 32 elements | 3600s (1hr) | 64 GB | 10 MB |

**Validation API:**
```python
# Get limits for tier
limits = get_tier_limits(ProblemTierEnum.TIER_2_DESKTOP)

# Validate individual dimensions
validate_problem_size(tier, problem_size)
validate_solve_time(tier, solve_time_seconds)
validate_memory_usage(tier, memory_bytes)
validate_proof_size(tier, proof_bytes)

# Validate everything at once
validate_all_limits(tier, problem_size, solution_size,
                   solve_time, verify_time, memory, proof_bytes)
```

**Helper Functions:**
```python
# Recommend tier based on hardware
tier = recommend_tier_for_hardware(
    cpu_cores=8, memory_gb=16, is_mobile=False
)
# Returns: TIER_3_WORKSTATION

# Estimate expected work score range
min_score, max_score = estimate_work_score_range(tier)
# TIER_3: (65536.0, 1048576.0)  # 2^16 to 2^20
```

**Security Properties:**
- **Admission Control:** Reject proofs exceeding limits before verification
- **Fair Competition:** Each tier competes within its hardware class
- **DoS Prevention:** Cannot submit 10MB proof to stall verifiers

---

## Migration Strategy (NO BREAKING CHANGES)

### Phase 1: Shim Imports (Backward Compatible)

**Goal:** Allow existing code to work unchanged while new code uses refactored types.

```python
# src/coinjecture/__init__.py
"""Backward-compatible shims for gradual migration."""

# Re-export existing types for compatibility
from ..core.blockchain import Block, ProblemTier  # Old types
from . import types  # New types

# Provide both old and new names
BlockWireFormat = types.BlockWireFormat  # New
ProblemTierEnum = types.ProblemTierEnum  # New
```

**Result:** Code using `from core.blockchain import Block` still works!

### Phase 2: Parallel Execution (Validation)

**Goal:** Run both old and new codecs in parallel, compare outputs.

```python
# In block validation
def validate_block_v4(block):
    # Compute hash with NEW codec
    new_hash = coinjecture.consensus.codec.compute_header_hash(new_header)

    # Compute hash with OLD method
    old_hash = block.calculate_hash()

    # Assert equivalence
    assert new_hash == old_hash, "Codec divergence!"
```

**Duration:** Run for 1000 blocks on testnet, verify 100% match.

### Phase 3: Feature Flag Switch

**Goal:** Toggle between old and new implementation with config.

```python
# config.yaml
consensus:
  use_refactored_codec: true  # Enable new codec
  validate_against_legacy: true  # Parallel validation

# In code
if config.consensus.use_refactored_codec:
    hash = coinjecture.consensus.codec.compute_header_hash(header)
else:
    hash = legacy_calculate_hash(block)
```

**Rollback:** If issues found, flip flag to `false` instantly.

### Phase 4: Legacy Code Removal

**Goal:** Remove old implementation after new code proven in production.

**Timeline:**
- **Months 1-2:** Shim imports + parallel validation (testnet)
- **Months 3-4:** Feature flag enabled (50% mainnet nodes)
- **Month 5:** Feature flag default=true (100% nodes)
- **Month 6:** Remove legacy code, cleanup shims

---

## Testing Strategy

### 1. Golden Vector Tests (`tests/spec/test_codec_golden.py`)

**Purpose:** Detect consensus-breaking changes.

```python
def test_genesis_header_hash():
    """This hash MUST NEVER change."""
    genesis_header = create_genesis_header()
    hash = codec.compute_header_hash(genesis_header)

    # Golden hash (computed 2025-11-01, v4.0.0)
    expected = "abc123...def"  # Real hash after first run

    assert hash == expected, "CONSENSUS BREAK DETECTED!"
```

**Coverage:**
- ✅ BlockHeader serialization + hashing
- ✅ Transaction serialization + hashing
- ✅ Merkle tree construction
- ✅ Commitment scheme

### 2. Property Tests (`tests/property/test_tokenomics.py`)

**Purpose:** Verify invariants hold under random inputs.

```python
from hypothesis import given, strategies as st

@given(st.floats(min_value=0, max_value=1e9))
def test_reward_monotonicity(work_score):
    """reward(x) >= reward(x - epsilon)"""
    reward1 = calculate_reward(work_score)
    reward2 = calculate_reward(work_score - 0.01)
    assert reward1 >= reward2

@given(st.integers(min_value=8, max_value=32))
def test_tier_assignment_coverage(problem_size):
    """Every valid problem_size maps to exactly one tier."""
    tier = assign_tier_for_size(problem_size)
    assert tier in ProblemTierEnum
```

### 3. Fuzz Tests (`tests/fuzz/test_proof_inputs.py`)

**Purpose:** Find crashes/panics on malformed inputs.

```python
@given(st.lists(st.integers(), max_size=100))
def test_subset_sum_no_crash(elements):
    """Solver should not crash on any list of ints."""
    try:
        solver = SubsetSumSolver()
        instance = create_instance(elements, target=sum(elements)//2)
        solver.solve(instance, limits)
    except (ValueError, TierLimitExceeded):
        pass  # Expected errors OK
    except Exception as e:
        pytest.fail(f"Unexpected crash: {e}")
```

### 4. Integration Tests

**End-to-End Flows:**
- Mine block → Submit to API → Validate → Accept → Propagate
- Generate problem → Solve → Commit → Reveal → Verify
- IPFS upload → Pin → Retrieve → Validate CID

---

## Quality Gates (CI/CD)

### Pre-Commit Hooks (`.pre-commit-config.yaml`)
- ✅ Black (code formatting)
- ✅ Ruff (linting + security checks)
- ✅ mypy (type checking on refactored code)
- ✅ Bandit (security scan)
- ✅ Detect private keys (prevent leaks)

### GitHub Actions (`.github/workflows/ci.yml`)
- ✅ Lint (black, ruff)
- ✅ Type check (mypy on src/coinjecture/)
- ✅ Unit tests (pytest with coverage)
- ✅ Security scan (bandit, pip-audit)
- ✅ CodeQL analysis (optional)

**Coverage Target:** ≥70% for new code, ≥50% overall

---

## Deployment Checklist

### Before Merge to Main
- [ ] All tests passing (unit, golden, property, fuzz)
- [ ] Golden vector hashes populated with real values
- [ ] mypy clean on src/coinjecture/
- [ ] No security warnings from bandit/ruff
- [ ] Documentation updated (README, ARCHITECTURE.md)
- [ ] CHANGELOG.md entry for v4.0.0

### Before Testnet Deploy
- [ ] P0 security findings addressed (SEC-001, SEC-002, SEC-005)
- [ ] Parallel validation passing (1000 blocks)
- [ ] IPFS CID recovery completed
- [ ] Rate limiting deployed on API

### Before Mainnet Deploy
- [ ] 2-week soak test on testnet (zero consensus issues)
- [ ] Third-party security audit (optional but recommended)
- [ ] Community review period (1 week)
- [ ] Rollback procedure tested

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        Application Layer                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │   CLI    │  │   API    │  │  Node    │  │ Network  │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       │             │              │              │          │
└───────┼─────────────┼──────────────┼──────────────┼─────────┘
        │             │              │              │
┌───────▼─────────────▼──────────────▼──────────────▼─────────┐
│                    Refactored Core                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  coinjecture/types.py - Canonical Type System          │ │
│  │  • Frozen dataclasses (immutable consensus types)      │ │
│  │  • NewType wrappers (BlockHash, Address, etc.)         │ │
│  │  • On-wire vs. internal type separation                │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  coinjecture/consensus/codec.py - Deterministic I/O    │ │
│  │  • msgspec primary, JSON fallback                      │ │
│  │  • Canonical field ordering                            │ │
│  │  • compute_header_hash() - CONSENSUS CRITICAL          │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  coinjecture/proofs/interface.py - PoW Abstraction     │ │
│  │  • Solver ABC (solve, verify, cost_hint)               │ │
│  │  • SubsetSumSolver (NP-Complete baseline)              │ │
│  │  • Pluggable solver registry                           │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  coinjecture/proofs/limits.py - Resource Control       │ │
│  │  • Tier-based admission (5 tiers: mobile → cluster)    │ │
│  │  • DoS prevention (time, memory, size caps)            │ │
│  │  • Hardware-based tier recommendations                 │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
        │
┌───────▼──────────────────────────────────────────────────────┐
│                    Legacy Production Code                     │
│  • src/consensus.py (fork choice, validation)                │
│  • src/pow.py (commit-reveal protocol)                       │
│  • src/storage.py (SQLite + IPFS)                            │
│  • src/network.py (equilibrium gossip v3.17.0)               │
│  • src/tokenomics/ (dynamic work-score rewards)              │
└───────────────────────────────────────────────────────────────┘
```

---

## Success Metrics

**Code Quality:**
- ✅ 100% type coverage in `src/coinjecture/` (mypy)
- ✅ ≥70% test coverage on new code
- ✅ Zero P0 security findings

**Performance:**
- ⏱️ Header hash computation: <1ms
- ⏱️ Block encoding: <10ms
- ⏱️ Merkle tree (1000 txs): <50ms

**Correctness:**
- ✅ 1000+ blocks validated with parallel execution (new == old)
- ✅ Golden vectors stable across Python 3.10, 3.11, 3.12
- ✅ Zero consensus forks during testnet soak

---

## Future Enhancements (Out of Scope for v4.0)

1. **Multi-Problem Support** - Register SAT, Graph Coloring solvers
2. **ZK Proofs** - Zero-knowledge verification for privacy
3. **Sharding** - Horizontal scaling via state sharding
4. **Cross-Chain Bridges** - IBC-style interoperability
5. **WASM Solver Runtime** - Sandboxed custom problem execution

---

## Conclusion

This refactor establishes a **clean foundation** for COINjecture's next phase while **preserving all existing functionality**. The modular design enables future innovation (new problem types, alternative consensus) without disrupting the production blockchain.

**Key Takeaway:** Good architecture is **invisible to users** but **obvious to developers**.

---

**Document Version:** 1.0
**Last Updated:** 2025-11-01
**Author:** 6-Agent Refactor Team + Implementation
**Contact:** adz@alphx.io
