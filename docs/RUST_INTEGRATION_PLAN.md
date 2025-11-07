# Rust Integration Plan for Network B
**COINjecture Migration Testnet - Institutional-Grade Integration**

**Version:** 4.5.0+
**Author:** Quigles1337 <adz@alphx.io>
**Estimated Duration:** 2-3 weeks
**Status:** Ready for Implementation

---

## Executive Summary

This document outlines the step-by-step plan to integrate Rust cryptographic bindings into the Go consensus layer for Network B (Migration Testnet). This ensures cryptographic parity with the Python implementation and enables safe migration from Python→Go validators.

**Key Objectives:**
1. Replace Go native `crypto/sha256` with Rust FFI calls
2. Achieve 100% parity with Python+PyO3 implementation
3. Pass all golden vector tests
4. Enable shadow mode deployment (Python + Go validators)
5. Support gradual cutover to Go-only validators

---

## Architecture Overview

### Current State (Network A)
```
┌─────────────────────────────────────┐
│      Go Consensus (Native)          │
│   crypto/sha256 (Go stdlib)         │
└─────────────────────────────────────┘
```

### Target State (Network B)
```
┌─────────────────────────────────────┐
│      Go Consensus (Rust-backed)     │
│   consensus.SHA256Hash() (Rust FFI) │
└────────────────┬────────────────────┘
                 │ CGO/FFI
                 ↓
┌─────────────────────────────────────┐
│    Rust Core (libcoinjecture_core)  │
│  - SHA-256, Merkle, Subset Sum      │
│  - Same code used by Python         │
└─────────────────────────────────────┘
```

---

## Phase 1: Rust Library Preparation (3-4 days)

### Task 1.1: Verify Rust Core Build
**Priority:** Critical
**Assignee:** Systems Engineer
**Duration:** 1 day

**Steps:**
1. Build Rust library with C FFI exports
   ```bash
   cd rust/coinjecture-core
   cargo build --release --features ffi
   ```

2. Verify shared library created:
   - Linux: `target/release/libcoinjecture_core.so`
   - Windows: `target/release/coinjecture_core.dll`
   - macOS: `target/release/libcoinjecture_core.dylib`

3. Check exported symbols:
   ```bash
   nm -D target/release/libcoinjecture_core.so | grep coinjecture
   ```

   Expected symbols:
   - `coinjecture_sha256_hash`
   - `coinjecture_compute_merkle_root`
   - `coinjecture_verify_subset_sum`
   - `coinjecture_compute_header_hash`

**Acceptance Criteria:**
- [ ] Rust library builds successfully on Linux/Windows/macOS
- [ ] All C FFI symbols exported correctly
- [ ] No undefined symbols or missing dependencies

**Risks:**
- Rust toolchain version mismatch
- Missing system dependencies (openssl, etc.)

**Mitigation:**
- Use Docker for reproducible builds
- Document exact Rust version (currently 1.75+)

---

### Task 1.2: Update C Header File
**Priority:** High
**Assignee:** Systems Engineer
**Duration:** 0.5 days

**Steps:**
1. Verify `rust/coinjecture-core/include/coinjecture.h` matches Rust exports

2. Ensure header includes:
   ```c
   // Result codes
   typedef enum {
       COINJ_OK = 0,
       COINJ_ERR_INVALID_INPUT = 1,
       COINJ_ERR_OUT_OF_MEMORY = 2,
       COINJ_ERR_VERIFICATION_FAILED = 3,
       COINJ_ERR_ENCODING = 4,
       COINJ_ERR_INTERNAL = 5
   } CoinjResult;

   // SHA-256 hashing
   CoinjResult coinjecture_sha256_hash(
       const uint8_t* data,
       uint32_t data_len,
       uint8_t* hash_out
   );

   // Merkle tree computation
   CoinjResult coinjecture_compute_merkle_root(
       const uint8_t* hashes,
       uint32_t hash_count,
       uint8_t* root_out
   );
   ```

3. Add institutional documentation comments

**Acceptance Criteria:**
- [ ] Header file compiles with gcc/clang
- [ ] All function signatures match Rust exports
- [ ] Documentation comments complete

---

### Task 1.3: Create Golden Vector Test Suite
**Priority:** Critical
**Assignee:** Backend Engineer
**Duration:** 2 days

**Steps:**
1. Create `rust/coinjecture-core/golden/network_b_vectors.json`:
   ```json
   {
     "version": "4.5.0+",
     "test_vectors": [
       {
         "name": "empty_input_sha256",
         "input": "",
         "expected_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
       },
       {
         "name": "hello_world_sha256",
         "input": "68656c6c6f20776f726c64",
         "expected_hash": "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
       }
     ],
     "merkle_vectors": [...],
     "block_header_vectors": [...]
   }
   ```

2. Generate vectors using Python implementation:
   ```python
   import coinjecture._core as rust
   import hashlib

   # SHA-256 test
   data = b"hello world"
   rust_hash = rust.sha256_hash(data)
   python_hash = hashlib.sha256(data).hexdigest()
   assert rust_hash == python_hash
   ```

3. Create Rust test harness:
   ```rust
   #[test]
   fn test_golden_vectors() {
       let vectors = load_golden_vectors("golden/network_b_vectors.json");
       for vec in vectors.sha256_tests {
           let result = sha256_hash(&vec.input);
           assert_eq!(hex::encode(result), vec.expected_hash);
       }
   }
   ```

**Acceptance Criteria:**
- [ ] 50+ test vectors covering all operations
- [ ] Rust tests pass 100%
- [ ] Python tests pass 100%
- [ ] Go tests (to be added) pass 100%

---

## Phase 2: Go Integration (5-7 days)

### Task 2.1: Update merkle.go to Use Rust
**Priority:** Critical
**Assignee:** Backend Engineer
**Duration:** 2 days

**Current Code:**
```go
// go/pkg/consensus/merkle.go
import "crypto/sha256"

func ComputeMerkleRoot(hashes [][32]byte) ([32]byte, error) {
    // Uses Go native SHA-256
    hasher := sha256.New()
    // ...
}
```

**Target Code:**
```go
// go/pkg/consensus/merkle.go
import "github.com/Quigles1337/coinjecture/go/pkg/consensus"

func ComputeMerkleRoot(hashes [][32]byte) ([32]byte, error) {
    // Delegate to Rust via FFI
    return RustComputeMerkleRoot(hashes)
}
```

**Steps:**
1. Remove `crypto/sha256` import
2. Replace all `sha256.Sum256()` calls with `consensus.SHA256Hash()`
3. Update `ComputeMerkleRoot()` to call `RustComputeMerkleRoot()`
4. Add error handling for Rust FFI calls

**Files to Modify:**
- `go/pkg/consensus/merkle.go`
- `go/pkg/consensus/merkle_test.go`

**Testing:**
```bash
cd go/pkg/consensus
CGO_ENABLED=1 go test -v -run TestMerkle
```

**Acceptance Criteria:**
- [ ] All tests pass with Rust backend
- [ ] Merkle roots match golden vectors
- [ ] No performance regression (< 5% slowdown acceptable)

---

### Task 2.2: Update block.go to Use Rust
**Priority:** Critical
**Assignee:** Backend Engineer
**Duration:** 2 days

**Current Code:**
```go
// go/pkg/consensus/block.go
func (b *Block) ComputeHash() [32]byte {
    headerBytes := b.SerializeHeader()
    return sha256.Sum256(headerBytes)
}
```

**Target Code:**
```go
// go/pkg/consensus/block.go
func (b *Block) ComputeHash() [32]byte {
    headerBytes := b.SerializeHeader()
    hash, err := SHA256Hash(headerBytes)
    if err != nil {
        // Institutional error handling
        panic(fmt.Sprintf("Block hash computation failed: %v", err))
    }
    return hash
}
```

**Steps:**
1. Replace all `sha256.Sum256()` with `SHA256Hash()`
2. Update `ComputeTxRoot()` to use Rust Merkle
3. Add institutional error handling
4. Update all test fixtures

**Files to Modify:**
- `go/pkg/consensus/block.go`
- `go/pkg/consensus/block_test.go`
- `go/pkg/consensus/builder.go`

**Testing:**
```bash
CGO_ENABLED=1 go test -v -run TestBlock
```

**Acceptance Criteria:**
- [ ] Block hashes match Python implementation
- [ ] All block tests pass
- [ ] No breaking changes to API

---

### Task 2.3: Add Feature Flag for Rust Backend
**Priority:** High
**Assignee:** Backend Engineer
**Duration:** 1 day

**Implementation:**
```go
// go/pkg/config/config.go
type ConsensusConfig struct {
    UseRustBindings bool `mapstructure:"use_rust_bindings"`
    // ...
}

// go/pkg/consensus/hash.go
func SHA256Hash(data []byte) ([32]byte, error) {
    if config.UseRustBindings {
        return RustSHA256Hash(data)
    }
    // Fallback to Go native
    return sha256.Sum256(data), nil
}
```

**Benefits:**
- Gradual rollout (enable per-node)
- A/B testing in production
- Quick rollback if issues found

**Acceptance Criteria:**
- [ ] Feature flag configurable via YAML
- [ ] Feature flag configurable via env var
- [ ] Default: false (safe fallback)
- [ ] Logs indicate which backend is active

---

### Task 2.4: Update All Test Suites
**Priority:** High
**Assignee:** Backend Engineer + QA
**Duration:** 2 days

**Test Files to Update:**
- `go/pkg/consensus/engine_test.go`
- `go/pkg/consensus/builder_test.go`
- `go/pkg/consensus/block_test.go`
- `go/test/integration/multi_node_test.go`

**Steps:**
1. Add `CGO_ENABLED=1` requirement to test runner
2. Link Rust library in test environment
3. Add golden vector validation tests
4. Update fixtures to use Rust hashes

**New Test:**
```go
func TestRustParity(t *testing.T) {
    // Load golden vectors
    vectors := loadGoldenVectors("../../../rust/coinjecture-core/golden/network_b_vectors.json")

    for _, vec := range vectors.SHA256Tests {
        input, _ := hex.DecodeString(vec.Input)
        result, err := SHA256Hash(input)
        require.NoError(t, err)

        expected, _ := hex.DecodeString(vec.ExpectedHash)
        assert.Equal(t, expected, result[:], vec.Name)
    }
}
```

**Acceptance Criteria:**
- [ ] All existing tests pass with Rust backend
- [ ] New parity tests added (20+ tests)
- [ ] 100% golden vector coverage
- [ ] CI/CD pipeline updated for CGO

---

## Phase 3: CI/CD Integration (2-3 days)

### Task 3.1: Update GitHub Actions
**Priority:** High
**Assignee:** DevOps Engineer
**Duration:** 1 day

**File:** `.github/workflows/go-rust-integration.yml`

```yaml
name: Go + Rust Integration Tests

on: [push, pull_request]

jobs:
  test-rust-integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Rust
        uses: actions-rs/toolchain@v1
        with:
          toolchain: 1.75.0
          override: true

      - name: Build Rust Core
        run: |
          cd rust/coinjecture-core
          cargo build --release --features ffi

      - name: Setup Go
        uses: actions/setup-go@v4
        with:
          go-version: '1.21'

      - name: Run Go Tests with Rust Backend
        env:
          CGO_ENABLED: 1
          LD_LIBRARY_PATH: ${{ github.workspace }}/rust/coinjecture-core/target/release
        run: |
          cd go
          go test -v -tags rust_ffi ./pkg/consensus/...
```

**Acceptance Criteria:**
- [ ] CI builds Rust library
- [ ] CI runs Go tests with Rust backend
- [ ] CI fails if golden vectors don't match
- [ ] Cross-platform testing (Linux/macOS/Windows)

---

### Task 3.2: Create Docker Images
**Priority:** Medium
**Assignee:** DevOps Engineer
**Duration:** 1 day

**File:** `docker/Dockerfile.network-b`

```dockerfile
FROM rust:1.75 AS rust-builder
WORKDIR /build
COPY rust/coinjecture-core ./
RUN cargo build --release --features ffi

FROM golang:1.21 AS go-builder
WORKDIR /build
COPY --from=rust-builder /build/target/release/libcoinjecture_core.so /usr/local/lib/
COPY go ./
RUN CGO_ENABLED=1 go build -o coinjectured ./cmd/coinjectured

FROM ubuntu:22.04
RUN apt-get update && apt-get install -y ca-certificates
COPY --from=rust-builder /build/target/release/libcoinjecture_core.so /usr/local/lib/
COPY --from=go-builder /build/coinjectured /usr/local/bin/
RUN ldconfig
ENTRYPOINT ["/usr/local/bin/coinjectured"]
```

**Acceptance Criteria:**
- [ ] Docker image builds successfully
- [ ] Image size < 100MB
- [ ] Rust library properly linked
- [ ] Runs on all platforms

---

## Phase 4: Shadow Mode Deployment (1 week)

### Task 4.1: Deploy Python + Go Hybrid Network
**Priority:** Critical
**Assignee:** DevOps + Backend Engineer
**Duration:** 3 days

**Network Topology:**
```
Python Validator (validator1) ←→ Go Validator (validator2)
                ↕                           ↕
           Go Validator (validator3)
```

**Deployment Steps:**
1. Deploy 1 Python validator with existing codebase
2. Deploy 2 Go validators with Rust backend
3. Configure shared bootstrap peers
4. Enable shadow mode logging

**Shadow Mode Config:**
```yaml
consensus:
  shadow_mode:
    enabled: true
    compare_with_validator: "validator1"  # Python validator
    alert_on_divergence: true
    log_all_comparisons: true
```

**Monitoring:**
```python
# Monitor for divergence
if go_block_hash != python_block_hash:
    log.critical(f"HASH DIVERGENCE: block={block_num} go={go_hash} py={py_hash}")
    alert_ops_team()
```

**Acceptance Criteria:**
- [ ] All 3 validators producing blocks
- [ ] Zero hash divergence over 24 hours
- [ ] Round-robin rotation working
- [ ] P2P mesh stable

---

### Task 4.2: Gradual Cutover
**Priority:** High
**Assignee:** DevOps Engineer
**Duration:** 4 days

**Cutover Plan:**

| Day | Python Validators | Go Validators | Status |
|-----|-------------------|---------------|--------|
| 1   | 1                 | 2             | Shadow mode |
| 2   | 1                 | 3             | Monitoring |
| 3   | 0                 | 4             | Go primary |
| 4   | 0                 | 5             | Full cutover |

**Rollback Procedure:**
```bash
# If issues detected, immediately:
systemctl stop coinjectured-validator2
systemctl start python-validator-backup
# Network falls back to Python validators
```

**Acceptance Criteria:**
- [ ] Zero consensus failures during cutover
- [ ] All blocks validated by both Python and Go
- [ ] No state divergence
- [ ] Rollback procedure tested and working

---

## Phase 5: Production Hardening (Ongoing)

### Task 5.1: Performance Optimization
**Priority:** Medium
**Duration:** Ongoing

**Optimizations:**
1. Cache Merkle tree computations
2. Parallelize hash operations
3. Optimize FFI call overhead
4. Profile hot paths

**Benchmarks:**
```bash
cd go/pkg/consensus
CGO_ENABLED=1 go test -bench=. -benchmem
```

**Target Metrics:**
- Block hash computation: < 1ms
- Merkle root (1000 txs): < 10ms
- FFI overhead: < 100μs per call

---

### Task 5.2: Security Audit
**Priority:** Critical
**Duration:** 2 weeks (external)

**Scope:**
1. Rust FFI boundary checks
2. Memory safety in CGO code
3. Cryptographic correctness
4. Side-channel resistance

**Deliverable:** Security audit report from external firm

---

## Success Criteria

### Phase 1 Success:
- [ ] Rust library builds on all platforms
- [ ] C header file complete and tested
- [ ] 50+ golden vectors created and passing

### Phase 2 Success:
- [ ] All Go consensus code using Rust backend
- [ ] 100% test coverage maintained
- [ ] Zero golden vector failures
- [ ] Feature flag working

### Phase 3 Success:
- [ ] CI/CD pipeline green
- [ ] Docker images working
- [ ] Cross-platform builds passing

### Phase 4 Success:
- [ ] Shadow mode running 7 days with zero divergence
- [ ] Gradual cutover completed successfully
- [ ] Python validators retired gracefully

### Phase 5 Success:
- [ ] Performance meets or exceeds native Go
- [ ] External security audit passed
- [ ] Production deployment stable

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Rust/Go hash mismatch | Medium | Critical | Comprehensive golden vectors, shadow mode |
| CGO performance overhead | Low | Medium | Benchmarking, optimization, caching |
| Build system complexity | Medium | Low | Docker, reproducible builds |
| Memory leaks in FFI | Low | High | Valgrind, leak detection, code review |
| Consensus divergence | Low | Critical | Shadow mode, rollback procedure, monitoring |

---

## Timeline Summary

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| 1. Rust Prep | 3-4 days | None |
| 2. Go Integration | 5-7 days | Phase 1 |
| 3. CI/CD | 2-3 days | Phase 2 |
| 4. Shadow Mode | 7 days | Phase 3 |
| 5. Hardening | Ongoing | Phase 4 |

**Total Estimated Time:** 2-3 weeks for shadow mode deployment
**Additional Time:** 2-4 weeks for full production hardening

---

## Resources Required

### Team:
- 1 Systems Engineer (Rust expert)
- 1 Backend Engineer (Go expert)
- 1 DevOps Engineer (deployment/CI/CD)
- 1 QA Engineer (testing/validation)

### Infrastructure:
- 5 validator VMs (hybrid Python + Go)
- CI/CD runners with Rust + Go
- Monitoring/alerting infrastructure

### Budget:
- Infrastructure: ~$350/month
- External audit: ~$15K-$25K
- Team time: ~6 person-weeks

---

## Appendix A: Build Commands Reference

### Build Rust Library:
```bash
cd rust/coinjecture-core
cargo build --release --features ffi
cargo test --features ffi
```

### Build Go with Rust:
```bash
cd go
export CGO_ENABLED=1
export CGO_LDFLAGS="-L../rust/coinjecture-core/target/release"
go build ./cmd/coinjectured
```

### Run Tests:
```bash
CGO_ENABLED=1 go test -v ./pkg/consensus/...
```

### Generate Golden Vectors:
```bash
cd rust/coinjecture-core
cargo run --bin generate-vectors > golden/network_b_vectors.json
```

---

## Appendix B: Troubleshooting

### Issue: "libcoinjecture_core.so: cannot open shared object file"

**Solution:**
```bash
export LD_LIBRARY_PATH=/path/to/rust/target/release:$LD_LIBRARY_PATH
# Or permanently:
sudo ldconfig /path/to/rust/target/release
```

### Issue: Hash divergence detected

**Diagnosis:**
```bash
# Compare block hashes
curl http://python-validator:8080/v1/blocks/latest | jq .block_hash
curl http://go-validator:8080/v1/blocks/latest | jq .block_hash

# Check Rust library version
ldd /usr/local/lib/libcoinjecture_core.so
```

---

**Document Version:** 1.0
**Last Updated:** 2025-11-06
**Contact:** Quigles1337 <adz@alphx.io>
