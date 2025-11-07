// Package consensus - Rust Parity Tests
//
// These tests verify 100% cryptographic parity between Go+Rust and pure Rust implementations.
// CRITICAL: All tests must pass for Network B deployment. Any failure indicates consensus divergence.

//go:build cgo
// +build cgo

package consensus

import (
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"runtime"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// GoldenVectors represents the test vector file structure
type GoldenVectors struct {
	Version      string         `json:"version"`
	GeneratedAt  string         `json:"generated_at"`
	TotalVectors int            `json:"total_vectors"`
	Description  string         `json:"description"`
	Purpose      string         `json:"purpose"`
	Vectors      []GoldenVector `json:"vectors"`
}

// GoldenVector represents a single test case
type GoldenVector struct {
	TestName      string            `json:"test_name"`
	Operation     string            `json:"operation"`
	InputHex      string            `json:"input_hex,omitempty"`
	InputSize     int               `json:"input_size,omitempty"`
	ExpectedHash  string            `json:"expected_hash,omitempty"`
	TxHashes      []string          `json:"tx_hashes,omitempty"`
	TxCount       int               `json:"tx_count,omitempty"`
	FirstTxHash   string            `json:"first_tx_hash,omitempty"`
	LastTxHash    string            `json:"last_tx_hash,omitempty"`
	ExpectedRoot  string            `json:"expected_root,omitempty"`
	Header        *BlockHeaderJSON  `json:"header,omitempty"`
}

// BlockHeaderJSON represents block header in JSON format
type BlockHeaderJSON struct {
	CodecVersion     uint32 `json:"codec_version"`
	BlockIndex       uint32 `json:"block_index"`
	Timestamp        int64  `json:"timestamp"`
	ParentHash       string `json:"parent_hash"`
	MerkleRoot       string `json:"merkle_root"`
	MinerAddress     string `json:"miner_address"`
	Commitment       string `json:"commitment"`
	DifficultyTarget uint32 `json:"difficulty_target"`
	Nonce            uint64 `json:"nonce"`
	ExtraData        string `json:"extra_data"`
}

// loadGoldenVectors loads test vectors from JSON file
func loadGoldenVectors(t *testing.T) *GoldenVectors {
	// Get path relative to this file
	_, filename, _, ok := runtime.Caller(0)
	require.True(t, ok, "Failed to get caller info")

	baseDir := filepath.Dir(filename) // go/pkg/consensus
	repoRoot := filepath.Join(baseDir, "..", "..", "..") // Root of repo
	vectorsPath := filepath.Join(repoRoot, "rust", "coinjecture-core", "golden", "network_b_vectors.json")

	// Read file
	data, err := os.ReadFile(vectorsPath)
	require.NoError(t, err, "Failed to read golden vectors file: %s", vectorsPath)

	// Parse JSON
	var vectors GoldenVectors
	err = json.Unmarshal(data, &vectors)
	require.NoError(t, err, "Failed to parse golden vectors JSON")

	require.Equal(t, 50, vectors.TotalVectors, "Expected 50 golden vectors")
	require.Equal(t, 50, len(vectors.Vectors), "Expected 50 vectors in array")

	t.Logf("✅ Loaded %d golden test vectors (version %s)", vectors.TotalVectors, vectors.Version)

	return &vectors
}

// hexDecode is a test helper to decode hex strings
func hexDecode(t *testing.T, hexStr string) []byte {
	if hexStr == "" {
		return []byte{}
	}
	data, err := hex.DecodeString(hexStr)
	require.NoError(t, err, "Failed to decode hex: %s", hexStr)
	return data
}

// hexDecode32 decodes hex string to [32]byte
func hexDecode32(t *testing.T, hexStr string) [32]byte {
	var arr [32]byte
	data := hexDecode(t, hexStr)
	require.Equal(t, 32, len(data), "Expected 32 bytes for hash")
	copy(arr[:], data)
	return arr
}

// ==================== SHA-256 Parity Tests ====================

func TestRustParity_SHA256(t *testing.T) {
	vectors := loadGoldenVectors(t)

	passCount := 0
	failCount := 0

	for _, vec := range vectors.Vectors {
		if vec.Operation != "SHA256" {
			continue
		}

		t.Run(vec.TestName, func(t *testing.T) {
			// Decode input
			input := hexDecode(t, vec.InputHex)

			// Compute hash via Rust FFI
			actualHash, err := SHA256Hash(input)
			require.NoError(t, err, "SHA256Hash failed")

			// Compare with expected
			expectedHash := hexDecode32(t, vec.ExpectedHash)

			if assert.Equal(t, expectedHash, actualHash, "Hash mismatch for %s", vec.TestName) {
				passCount++
				t.Logf("✅ PASS: %s", vec.TestName)
			} else {
				failCount++
				t.Errorf("❌ FAIL: %s\n  Input: %s\n  Expected: %s\n  Got:      %s",
					vec.TestName, vec.InputHex, vec.ExpectedHash, hex.EncodeToString(actualHash[:]))
			}
		})
	}

	t.Logf("\n📊 SHA-256 Results: %d passed, %d failed out of %d total",
		passCount, failCount, passCount+failCount)

	require.Zero(t, failCount, "SHA-256 parity test failures detected")
}

// ==================== Merkle Root Parity Tests ====================

func TestRustParity_MerkleRoot(t *testing.T) {
	vectors := loadGoldenVectors(t)

	passCount := 0
	failCount := 0

	for _, vec := range vectors.Vectors {
		if vec.Operation != "MERKLE" {
			continue
		}

		t.Run(vec.TestName, func(t *testing.T) {
			// Decode transaction hashes
			var txHashes [][32]byte
			for _, hashHex := range vec.TxHashes {
				txHashes = append(txHashes, hexDecode32(t, hashHex))
			}

			// Compute Merkle root via Rust FFI
			actualRoot, err := ComputeMerkleRoot(txHashes)
			require.NoError(t, err, "ComputeMerkleRoot failed")

			// Compare with expected
			expectedRoot := hexDecode32(t, vec.ExpectedRoot)

			if assert.Equal(t, expectedRoot, actualRoot, "Merkle root mismatch for %s", vec.TestName) {
				passCount++
				t.Logf("✅ PASS: %s (%d transactions)", vec.TestName, len(txHashes))
			} else {
				failCount++
				t.Errorf("❌ FAIL: %s\n  TxCount:  %d\n  Expected: %s\n  Got:      %s",
					vec.TestName, len(txHashes), vec.ExpectedRoot, hex.EncodeToString(actualRoot[:]))
			}
		})
	}

	t.Logf("\n📊 Merkle Root Results: %d passed, %d failed out of %d total",
		passCount, failCount, passCount+failCount)

	require.Zero(t, failCount, "Merkle root parity test failures detected")
}

// ==================== Block Header Parity Tests ====================

func TestRustParity_BlockHeader(t *testing.T) {
	vectors := loadGoldenVectors(t)

	passCount := 0
	failCount := 0

	for _, vec := range vectors.Vectors {
		if vec.Operation != "BLOCK_HEADER" {
			continue
		}

		t.Run(vec.TestName, func(t *testing.T) {
			require.NotNil(t, vec.Header, "Header cannot be nil")

			// Convert JSON header to Go struct
			header := &BlockHeader{
				CodecVersion:     vec.Header.CodecVersion,
				BlockIndex:       vec.Header.BlockIndex,
				Timestamp:        vec.Header.Timestamp,
				ParentHash:       hexDecode32(t, vec.Header.ParentHash),
				MerkleRoot:       hexDecode32(t, vec.Header.MerkleRoot),
				MinerAddress:     hexDecode32(t, vec.Header.MinerAddress),
				Commitment:       hexDecode32(t, vec.Header.Commitment),
				DifficultyTarget: vec.Header.DifficultyTarget,
				Nonce:            vec.Header.Nonce,
				ExtraData:        hexDecode(t, vec.Header.ExtraData),
			}

			// Compute header hash via Rust FFI
			actualHash, err := ComputeHeaderHash(header)
			require.NoError(t, err, "ComputeHeaderHash failed")

			// Compare with expected
			expectedHash := hexDecode32(t, vec.ExpectedHash)

			if assert.Equal(t, expectedHash, actualHash, "Block header hash mismatch for %s", vec.TestName) {
				passCount++
				t.Logf("✅ PASS: %s (block %d)", vec.TestName, header.BlockIndex)
			} else {
				failCount++
				t.Errorf("❌ FAIL: %s\n  Block:    %d\n  Expected: %s\n  Got:      %s",
					vec.TestName, header.BlockIndex, vec.ExpectedHash, hex.EncodeToString(actualHash[:]))
			}
		})
	}

	t.Logf("\n📊 Block Header Results: %d passed, %d failed out of %d total",
		passCount, failCount, passCount+failCount)

	require.Zero(t, failCount, "Block header parity test failures detected")
}

// ==================== Comprehensive Parity Test ====================

func TestRustParity_AllVectors(t *testing.T) {
	vectors := loadGoldenVectors(t)

	stats := make(map[string]int)
	failures := make(map[string]int)

	for _, vec := range vectors.Vectors {
		stats[vec.Operation]++

		var err error
		var passed bool

		switch vec.Operation {
		case "SHA256":
			input := hexDecode(t, vec.InputHex)
			actualHash, err := SHA256Hash(input)
			if err == nil {
				expectedHash := hexDecode32(t, vec.ExpectedHash)
				passed = actualHash == expectedHash
			}

		case "MERKLE":
			var txHashes [][32]byte
			for _, hashHex := range vec.TxHashes {
				txHashes = append(txHashes, hexDecode32(t, hashHex))
			}
			actualRoot, err := ComputeMerkleRoot(txHashes)
			if err == nil {
				expectedRoot := hexDecode32(t, vec.ExpectedRoot)
				passed = actualRoot == expectedRoot
			}

		case "BLOCK_HEADER":
			if vec.Header != nil {
				header := &BlockHeader{
					CodecVersion:     vec.Header.CodecVersion,
					BlockIndex:       vec.Header.BlockIndex,
					Timestamp:        vec.Header.Timestamp,
					ParentHash:       hexDecode32(t, vec.Header.ParentHash),
					MerkleRoot:       hexDecode32(t, vec.Header.MerkleRoot),
					MinerAddress:     hexDecode32(t, vec.Header.MinerAddress),
					Commitment:       hexDecode32(t, vec.Header.Commitment),
					DifficultyTarget: vec.Header.DifficultyTarget,
					Nonce:            vec.Header.Nonce,
					ExtraData:        hexDecode(t, vec.Header.ExtraData),
				}
				actualHash, err := ComputeHeaderHash(header)
				if err == nil {
					expectedHash := hexDecode32(t, vec.ExpectedHash)
					passed = actualHash == expectedHash
				}
			}
		}

		if err != nil || !passed {
			failures[vec.Operation]++
			t.Errorf("❌ Vector %s (%s) FAILED", vec.TestName, vec.Operation)
		}
	}

	// Print summary
	t.Log("\n" + "═"*60)
	t.Log("  RUST-GO PARITY TEST SUMMARY")
	t.Log("═"*60)

	totalTests := 0
	totalFailed := 0

	for operation, count := range stats {
		failed := failures[operation]
		passed := count - failed
		totalTests += count
		totalFailed += failed

		status := "✅ PASS"
		if failed > 0 {
			status = "❌ FAIL"
		}

		t.Logf("  %s: %s (%d/%d passed)", operation, status, passed, count)
	}

	t.Log("─"*60)
	t.Logf("  TOTAL: %d/%d passed (%.1f%%)",
		totalTests-totalFailed, totalTests,
		float64(totalTests-totalFailed)/float64(totalTests)*100)
	t.Log("═"*60)

	if totalFailed > 0 {
		t.Fatalf("\n🚨 CRITICAL: %d/%d parity tests FAILED!\n"+
			"   This indicates consensus divergence between Rust and Go.\n"+
			"   DO NOT deploy Network B until all tests pass.\n",
			totalFailed, totalTests)
	}

	t.Log("\n✅ ALL PARITY TESTS PASSED - Ready for Network B deployment")
}

// ==================== Benchmark Tests ====================

func BenchmarkRustSHA256_Small(b *testing.B) {
	input := []byte("hello world")
	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		_, _ = SHA256Hash(input)
	}
}

func BenchmarkRustSHA256_Large(b *testing.B) {
	input := make([]byte, 10240) // 10KB
	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		_, _ = SHA256Hash(input)
	}
}

func BenchmarkRustMerkleRoot_100Txs(b *testing.B) {
	// Generate 100 transaction hashes
	txHashes := make([][32]byte, 100)
	for i := 0; i < 100; i++ {
		h, _ := SHA256Hash([]byte{byte(i)})
		txHashes[i] = h
	}

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		_, _ = ComputeMerkleRoot(txHashes)
	}
}

func BenchmarkRustBlockHeader(b *testing.B) {
	header := &BlockHeader{
		CodecVersion:     1,
		BlockIndex:       1000,
		Timestamp:        1704067200,
		ParentHash:       [32]byte{},
		MerkleRoot:       [32]byte{},
		MinerAddress:     [32]byte{},
		Commitment:       [32]byte{},
		DifficultyTarget: 10000,
		Nonce:            999999,
		ExtraData:        []byte("benchmark"),
	}

	b.ResetTimer()

	for i := 0; i < b.N; i++ {
		_, _ = ComputeHeaderHash(header)
	}
}

// ==================== Version Info Tests ====================

func TestRustVersion(t *testing.T) {
	version := Version()
	t.Logf("Rust library version: %s", version)
	assert.NotEmpty(t, version, "Version should not be empty")
}

func TestRustCodecVersion(t *testing.T) {
	codecVersion := CodecVersion()
	t.Logf("Codec version: %d", codecVersion)
	assert.Equal(t, uint32(1), codecVersion, "Codec version should be 1")
}
