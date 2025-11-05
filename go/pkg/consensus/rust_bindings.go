// Package consensus provides Go bindings to Rust consensus-critical functions via CGO.
//
// This package delegates all consensus operations to the Rust core library,
// ensuring identical behavior across Python, Go, and Rust implementations.
//
// CRITICAL: These functions must be deterministic and match Python/Rust behavior exactly.
package consensus

/*
#cgo CFLAGS: -I${SRCDIR}/../../../rust/coinjecture-core/include
#cgo LDFLAGS: -L${SRCDIR}/../../../rust/coinjecture-core/target/release -lcoinjecture_core
#cgo windows LDFLAGS: -lws2_32 -luserenv -lbcrypt

#include <stdlib.h>
#include "coinjecture.h"
*/
import "C"
import (
	"errors"
	"fmt"
	"unsafe"
)

// ResultCode represents C FFI result codes
type ResultCode int

const (
	OK                      ResultCode = 0
	ErrorInvalidInput       ResultCode = 1
	ErrorOutOfMemory        ResultCode = 2
	ErrorVerificationFailed ResultCode = 3
	ErrorEncoding           ResultCode = 4
	ErrorInternal           ResultCode = 5
)

// String returns human-readable error message
func (r ResultCode) String() string {
	switch r {
	case OK:
		return "OK"
	case ErrorInvalidInput:
		return "Invalid input"
	case ErrorOutOfMemory:
		return "Out of memory"
	case ErrorVerificationFailed:
		return "Verification failed"
	case ErrorEncoding:
		return "Encoding error"
	case ErrorInternal:
		return "Internal error"
	default:
		return fmt.Sprintf("Unknown error (%d)", r)
	}
}

// ==================== SHA-256 HASHING ====================

// SHA256Hash computes SHA-256 hash of input data.
//
// Returns 32-byte hash on success.
func SHA256Hash(data []byte) ([32]byte, error) {
	var hash [32]byte

	if len(data) == 0 {
		// Empty input - call Rust to get consistent empty hash
		result := C.coinjecture_sha256_hash(nil, 0, (*C.uint8_t)(unsafe.Pointer(&hash[0])))
		if result != C.COINJ_OK {
			return hash, fmt.Errorf("Rust SHA-256 failed: %s", ResultCode(result))
		}
		return hash, nil
	}

	result := C.coinjecture_sha256_hash(
		(*C.uint8_t)(unsafe.Pointer(&data[0])),
		C.uint32_t(len(data)),
		(*C.uint8_t)(unsafe.Pointer(&hash[0])),
	)

	if result != C.COINJ_OK {
		return hash, fmt.Errorf("Rust SHA-256 failed: %s", ResultCode(result))
	}

	return hash, nil
}

// ==================== BLOCK HEADER HASHING ====================

// BlockHeader represents a block header (Go-native struct).
type BlockHeader struct {
	CodecVersion     uint32
	BlockIndex       uint32
	Timestamp        int64
	ParentHash       [32]byte
	MerkleRoot       [32]byte
	MinerAddress     [32]byte
	Commitment       [32]byte
	DifficultyTarget uint32
	Nonce            uint64
	ExtraData        []byte
}

// ComputeHeaderHash computes deterministic hash of block header.
//
// Returns 32-byte hash on success.
func ComputeHeaderHash(header *BlockHeader) ([32]byte, error) {
	var hash [32]byte

	if header == nil {
		return hash, errors.New("header cannot be nil")
	}

	// Convert Go struct to C FFI struct
	cHeader := C.BlockHeaderFFI{
		codec_version:     C.uint32_t(header.CodecVersion),
		block_index:       C.uint32_t(header.BlockIndex),
		timestamp:         C.int64_t(header.Timestamp),
		difficulty_target: C.uint32_t(header.DifficultyTarget),
		nonce:             C.uint64_t(header.Nonce),
		extra_data_len:    C.uint32_t(len(header.ExtraData)),
	}

	// Copy fixed-size arrays
	copy(cHeader.parent_hash[:], header.ParentHash[:])
	copy(cHeader.merkle_root[:], header.MerkleRoot[:])
	copy(cHeader.miner_address[:], header.MinerAddress[:])
	copy(cHeader.commitment[:], header.Commitment[:])

	// Handle extra data (optional)
	if len(header.ExtraData) > 0 {
		cHeader.extra_data = (*C.uint8_t)(unsafe.Pointer(&header.ExtraData[0]))
	} else {
		cHeader.extra_data = nil
	}

	// Call Rust FFI
	result := C.coinjecture_compute_header_hash(
		&cHeader,
		(*C.uint8_t)(unsafe.Pointer(&hash[0])),
	)

	if result != C.COINJ_OK {
		return hash, fmt.Errorf("Rust header hash failed: %s", ResultCode(result))
	}

	return hash, nil
}

// ==================== MERKLE ROOT ====================

// ComputeMerkleRoot computes Merkle root from transaction hashes.
//
// Empty list → all-zeros hash
// Single hash → hash itself
// Multiple hashes → binary tree root
func ComputeMerkleRoot(txHashes [][32]byte) ([32]byte, error) {
	var root [32]byte

	if len(txHashes) == 0 {
		// Empty list - call Rust for consistent behavior
		result := C.coinjecture_compute_merkle_root(nil, 0, (*C.uint8_t)(unsafe.Pointer(&root[0])))
		if result != C.COINJ_OK {
			return root, fmt.Errorf("Rust Merkle root failed: %s", ResultCode(result))
		}
		return root, nil
	}

	// Call Rust FFI with hash array
	result := C.coinjecture_compute_merkle_root(
		(*[32]C.uint8_t)(unsafe.Pointer(&txHashes[0])),
		C.uint32_t(len(txHashes)),
		(*C.uint8_t)(unsafe.Pointer(&root[0])),
	)

	if result != C.COINJ_OK {
		return root, fmt.Errorf("Rust Merkle root failed: %s", ResultCode(result))
	}

	return root, nil
}

// ==================== SUBSET SUM VERIFICATION ====================

// HardwareTier represents computational capacity categories
type HardwareTier uint32

const (
	TierMobile       HardwareTier = 0
	TierDesktop      HardwareTier = 1
	TierWorkstation  HardwareTier = 2
	TierServer       HardwareTier = 3
	TierCluster      HardwareTier = 4
)

// SubsetSumProblem represents a subset sum problem instance.
type SubsetSumProblem struct {
	ProblemType uint32       // 0 = SubsetSum
	Tier        HardwareTier
	Elements    []int64
	Target      int64
	Timestamp   int64
}

// SubsetSumSolution represents a subset sum solution.
type SubsetSumSolution struct {
	Indices   []uint32 // Indices into problem.Elements
	Timestamp int64
}

// VerifyBudget represents verification resource limits.
type VerifyBudget struct {
	MaxOps          uint32
	MaxDurationMs   uint32
	MaxMemoryBytes  uint32
}

// VerifySubsetSum verifies a subset sum solution with budget limits.
//
// Returns true if solution is valid, false if invalid.
// Returns error only on malformed inputs (not on invalid solutions).
func VerifySubsetSum(problem *SubsetSumProblem, solution *SubsetSumSolution, budget *VerifyBudget) (bool, error) {
	if problem == nil || solution == nil || budget == nil {
		return false, errors.New("problem, solution, and budget cannot be nil")
	}

	if len(problem.Elements) == 0 {
		return false, errors.New("problem must have at least one element")
	}

	if len(solution.Indices) == 0 {
		return false, errors.New("solution must have at least one index")
	}

	// Convert Go structs to C FFI structs
	cProblem := C.SubsetSumProblemFFI{
		problem_type:  C.uint32_t(problem.ProblemType),
		tier:          C.uint32_t(problem.Tier),
		elements:      (*C.int64_t)(unsafe.Pointer(&problem.Elements[0])),
		elements_len:  C.uint32_t(len(problem.Elements)),
		target:        C.int64_t(problem.Target),
		timestamp:     C.int64_t(problem.Timestamp),
	}

	cSolution := C.SubsetSumSolutionFFI{
		indices:      (*C.uint32_t)(unsafe.Pointer(&solution.Indices[0])),
		indices_len:  C.uint32_t(len(solution.Indices)),
		timestamp:    C.int64_t(solution.Timestamp),
	}

	cBudget := C.VerifyBudgetFFI{
		max_ops:           C.uint32_t(budget.MaxOps),
		max_duration_ms:   C.uint32_t(budget.MaxDurationMs),
		max_memory_bytes:  C.uint32_t(budget.MaxMemoryBytes),
	}

	var isValid C.int32_t

	// Call Rust FFI
	result := C.coinjecture_verify_subset_sum(
		&cProblem,
		&cSolution,
		&cBudget,
		&isValid,
	)

	if result != C.COINJ_OK {
		return false, fmt.Errorf("Rust verification failed: %s", ResultCode(result))
	}

	return isValid == 1, nil
}

// ==================== VERSION INFO ====================

// Version returns the Rust library version string.
func Version() string {
	cVersion := C.coinjecture_version()
	return C.GoString(cVersion) // Static string, no need to free
}

// CodecVersion returns the codec version number.
func CodecVersion() uint32 {
	return uint32(C.coinjecture_codec_version())
}
