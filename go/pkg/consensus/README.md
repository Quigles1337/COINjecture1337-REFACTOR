# Consensus Package: Go → Rust FFI Bindings

This package provides Go bindings to Rust consensus-critical functions via CGO.

## Architecture

```
Go Application (API server, mining node)
    ↓ Import
Go Package (pkg/consensus)
    ↓ CGO
C FFI Layer (include/coinjecture.h)
    ↓ Dynamic linking
Rust Core Library (libcoinjecture_core.dll/so)
```

## Requirements

### 1. CGO Compiler

CGO requires a C compiler to build:

**Windows:**
- Install [MinGW-w64](https://www.mingw-w64.org/) or MSVC Build Tools
- Add to PATH: `C:\mingw64\bin`

**Linux:**
- `sudo apt install build-essential` (Debian/Ubuntu)
- `sudo yum install gcc` (RHEL/CentOS)

**macOS:**
- `xcode-select --install`

### 2. Rust Core Library

Build the Rust shared library:

```bash
cd rust/coinjecture-core
cargo build --release --features ffi
```

This produces:
- **Windows**: `target/release/coinjecture_core.dll`
- **Linux**: `target/release/libcoinjecture_core.so`
- **macOS**: `target/release/libcoinjecture_core.dylib`

### 3. Enable CGO

```bash
# Windows (PowerShell)
$env:CGO_ENABLED = "1"

# Linux/macOS (Bash)
export CGO_ENABLED=1
```

## Building

```bash
cd go
CGO_ENABLED=1 go build ./pkg/consensus
```

## Testing

```bash
cd go
CGO_ENABLED=1 go test ./pkg/consensus -v
```

## Usage Example

```go
package main

import (
    "fmt"
    "github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/consensus"
)

func main() {
    // SHA-256 hashing
    data := []byte("COINjecture")
    hash, err := consensus.SHA256Hash(data)
    if err != nil {
        panic(err)
    }
    fmt.Printf("SHA-256: %x\n", hash)

    // Subset sum verification
    problem := &consensus.SubsetSumProblem{
        ProblemType: 0,
        Tier:        consensus.TierDesktop,
        Elements:    []int64{1, 2, 3, 4, 5},
        Target:      9,
        Timestamp:   1000,
    }

    solution := &consensus.SubsetSumSolution{
        Indices:   []uint32{0, 2, 4}, // 1+3+5=9
        Timestamp: 1001,
    }

    budget := &consensus.VerifyBudget{
        MaxOps:         100000,
        MaxDurationMs:  10000,
        MaxMemoryBytes: 100_000_000,
    }

    isValid, err := consensus.VerifySubsetSum(problem, solution, budget)
    if err != nil {
        panic(err)
    }
    fmt.Printf("Solution valid: %v\n", isValid)
}
```

## Troubleshooting

### "build constraints exclude all Go files"

**Cause**: CGO is disabled

**Fix**:
```bash
export CGO_ENABLED=1  # or set in environment
go build ./pkg/consensus
```

### "cannot find -lcoinjecture_core"

**Cause**: Rust library not built or not in search path

**Fix**:
```bash
cd rust/coinjecture-core
cargo build --release --features ffi

# Linux: Add to LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$PWD/target/release

# Windows: Add DLL to PATH or copy to system32
```

### "gcc not found"

**Cause**: C compiler not installed

**Fix** (Windows):
```bash
# Install MinGW-w64 from https://www.mingw-w64.org/
# Add C:\mingw64\bin to PATH
```

## Golden Test Vectors

The bindings implement the same golden vectors as Python/Rust:

- `SHA-256("")` → `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `Merkle(empty)` → `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `SubsetSum([1,2,3,4,5], 9, [0,2,4])` → `valid`

See `rust_bindings_test.go` for full test suite.

## Performance

CGO calls have overhead (~200ns per call), but consensus operations are expensive enough (microseconds to milliseconds) that FFI overhead is negligible (<1%).

## Security Considerations

1. **Determinism**: All functions must produce identical results across platforms
2. **Memory safety**: CGO handles pointer conversion, but caller must ensure data validity
3. **Error handling**: All Rust errors are propagated to Go as `error` types
4. **Budget limits**: Proof verification has resource budgets to prevent DoS

## CI/CD Integration

### GitHub Actions

```yaml
- name: Install Rust
  uses: actions-rs/toolchain@v1
  with:
    toolchain: stable

- name: Build Rust core with FFI
  working-directory: rust/coinjecture-core
  run: cargo build --release --features ffi

- name: Test Go bindings
  working-directory: go
  env:
    CGO_ENABLED: 1
    LD_LIBRARY_PATH: ${{ github.workspace }}/rust/coinjecture-core/target/release
  run: go test ./pkg/consensus -v
```

## License

MIT - See LICENSE file in repository root
