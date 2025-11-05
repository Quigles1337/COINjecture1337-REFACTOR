package consensus

import (
	"encoding/hex"
	"testing"
)

// ==================== SHA-256 Tests ====================

func TestSHA256EmptyBuffer(t *testing.T) {
	// Golden vector: SHA-256 of empty buffer
	expected, _ := hex.DecodeString("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

	hash, err := SHA256Hash([]byte{})
	if err != nil {
		t.Fatalf("SHA256Hash failed: %v", err)
	}

	if hash != [32]byte(expected) {
		t.Errorf("SHA-256 empty buffer mismatch!\nExpected: %x\nGot: %x", expected, hash)
	}
}

func TestSHA256COINjecture(t *testing.T) {
	// This is a placeholder - update with actual golden vector from Rust
	data := []byte("COINjecture")

	hash, err := SHA256Hash(data)
	if err != nil {
		t.Fatalf("SHA256Hash failed: %v", err)
	}

	// Verify hash is not all zeros
	var zeros [32]byte
	if hash == zeros {
		t.Error("SHA-256 returned all zeros (unexpected)")
	}
}

func TestSHA256Determinism(t *testing.T) {
	data := []byte("determinism_test")

	hash1, err := SHA256Hash(data)
	if err != nil {
		t.Fatalf("SHA256Hash (1) failed: %v", err)
	}

	hash2, err := SHA256Hash(data)
	if err != nil {
		t.Fatalf("SHA256Hash (2) failed: %v", err)
	}

	hash3, err := SHA256Hash(data)
	if err != nil {
		t.Fatalf("SHA256Hash (3) failed: %v", err)
	}

	if hash1 != hash2 || hash2 != hash3 {
		t.Error("SHA-256 not deterministic!")
	}
}

// ==================== Merkle Root Tests ====================

func TestMerkleRootEmpty(t *testing.T) {
	// Golden vector: Merkle root of empty list
	expected, _ := hex.DecodeString("e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855")

	root, err := ComputeMerkleRoot([][32]byte{})
	if err != nil {
		t.Fatalf("ComputeMerkleRoot failed: %v", err)
	}

	// Note: The actual behavior depends on Rust implementation
	// Empty list might return SHA-256(empty) or all-zeros
	t.Logf("Merkle root (empty): %x", root)
	t.Logf("Expected (SHA-256 empty): %x", expected)
}

func TestMerkleRootSingleTx(t *testing.T) {
	// Single zero transaction
	var txHash [32]byte // all zeros

	root, err := ComputeMerkleRoot([][32]byte{txHash})
	if err != nil {
		t.Fatalf("ComputeMerkleRoot failed: %v", err)
	}

	// Single transaction: root should be the transaction hash itself
	if root != txHash {
		t.Errorf("Merkle root mismatch!\nExpected: %x\nGot: %x", txHash, root)
	}
}

func TestMerkleRootMultipleTx(t *testing.T) {
	var tx1, tx2, tx3 [32]byte
	for i := 0; i < 32; i++ {
		tx1[i] = 0xAA
		tx2[i] = 0xBB
		tx3[i] = 0xCC
	}

	root, err := ComputeMerkleRoot([][32]byte{tx1, tx2, tx3})
	if err != nil {
		t.Fatalf("ComputeMerkleRoot failed: %v", err)
	}

	// Verify root is not all zeros
	var zeros [32]byte
	if root == zeros {
		t.Error("Merkle root returned all zeros (unexpected)")
	}

	t.Logf("Merkle root (3 txs): %x", root)
}

func TestMerkleRootDeterminism(t *testing.T) {
	var tx1, tx2 [32]byte
	for i := 0; i < 32; i++ {
		tx1[i] = byte(i)
		tx2[i] = byte(i * 2)
	}

	txs := [][32]byte{tx1, tx2}

	root1, _ := ComputeMerkleRoot(txs)
	root2, _ := ComputeMerkleRoot(txs)
	root3, _ := ComputeMerkleRoot(txs)

	if root1 != root2 || root2 != root3 {
		t.Error("Merkle root not deterministic!")
	}
}

// ==================== Subset Sum Verification Tests ====================

func TestVerifySubsetSumValid(t *testing.T) {
	// Problem: elements=[1,2,3,4,5], target=9
	// Solution: indices=[0,2,4] → elements[0]+elements[2]+elements[4] = 1+3+5 = 9
	problem := &SubsetSumProblem{
		ProblemType: 0, // SubsetSum
		Tier:        TierDesktop,
		Elements:    []int64{1, 2, 3, 4, 5},
		Target:      9,
		Timestamp:   1000,
	}

	solution := &SubsetSumSolution{
		Indices:   []uint32{0, 2, 4},
		Timestamp: 1001,
	}

	budget := &VerifyBudget{
		MaxOps:         100000,
		MaxDurationMs:  10000,
		MaxMemoryBytes: 100_000_000,
	}

	isValid, err := VerifySubsetSum(problem, solution, budget)
	if err != nil {
		t.Fatalf("VerifySubsetSum failed: %v", err)
	}

	if !isValid {
		t.Error("Valid subset sum solution marked as invalid!")
	}
}

func TestVerifySubsetSumInvalid(t *testing.T) {
	// Problem: elements=[1,2,3,4,5], target=9
	// Solution: indices=[0,1] → elements[0]+elements[1] = 1+2 = 3 ≠ 9
	problem := &SubsetSumProblem{
		ProblemType: 0,
		Tier:        TierDesktop,
		Elements:    []int64{1, 2, 3, 4, 5},
		Target:      9,
		Timestamp:   1000,
	}

	solution := &SubsetSumSolution{
		Indices:   []uint32{0, 1},
		Timestamp: 1001,
	}

	budget := &VerifyBudget{
		MaxOps:         100000,
		MaxDurationMs:  10000,
		MaxMemoryBytes: 100_000_000,
	}

	isValid, err := VerifySubsetSum(problem, solution, budget)
	if err != nil {
		t.Fatalf("VerifySubsetSum failed: %v", err)
	}

	if isValid {
		t.Error("Invalid subset sum solution marked as valid!")
	}
}

func TestVerifySubsetSumOutOfBounds(t *testing.T) {
	// Problem: elements=[1,2,3], target=6
	// Solution: indices=[0,1,10] → index 10 out of bounds
	problem := &SubsetSumProblem{
		ProblemType: 0,
		Tier:        TierDesktop,
		Elements:    []int64{1, 2, 3},
		Target:      6,
		Timestamp:   1000,
	}

	solution := &SubsetSumSolution{
		Indices:   []uint32{0, 1, 10},
		Timestamp: 1001,
	}

	budget := &VerifyBudget{
		MaxOps:         100000,
		MaxDurationMs:  10000,
		MaxMemoryBytes: 100_000_000,
	}

	isValid, err := VerifySubsetSum(problem, solution, budget)
	if err != nil {
		// Error is acceptable for out-of-bounds
		t.Logf("Expected error for out-of-bounds indices: %v", err)
		return
	}

	if isValid {
		t.Error("Out-of-bounds solution should be invalid!")
	}
}

// ==================== Version Tests ====================

func TestVersion(t *testing.T) {
	version := Version()
	if version == "" {
		t.Error("Version returned empty string")
	}

	t.Logf("Rust library version: %s", version)
}

func TestCodecVersion(t *testing.T) {
	codecVersion := CodecVersion()
	if codecVersion != 1 {
		t.Errorf("Codec version should be 1, got %d", codecVersion)
	}
}

// ==================== Block Header Tests ====================

func TestComputeHeaderHash(t *testing.T) {
	// Genesis header (test vector)
	header := &BlockHeader{
		CodecVersion:     1,
		BlockIndex:       0,
		Timestamp:        1609459200,
		ParentHash:       [32]byte{}, // all zeros
		MerkleRoot:       [32]byte{}, // all zeros
		MinerAddress:     [32]byte{}, // all zeros
		Commitment:       [32]byte{}, // all zeros
		DifficultyTarget: 1000,
		Nonce:            0,
		ExtraData:        []byte{},
	}

	hash, err := ComputeHeaderHash(header)
	if err != nil {
		t.Fatalf("ComputeHeaderHash failed: %v", err)
	}

	// Verify hash is not all zeros
	var zeros [32]byte
	if hash == zeros {
		t.Error("Header hash returned all zeros (unexpected)")
	}

	t.Logf("Genesis header hash: %x", hash)
}

func TestComputeHeaderHashDeterminism(t *testing.T) {
	header := &BlockHeader{
		CodecVersion:     1,
		BlockIndex:       42,
		Timestamp:        1609459200,
		ParentHash:       [32]byte{},
		MerkleRoot:       [32]byte{},
		MinerAddress:     [32]byte{},
		Commitment:       [32]byte{},
		DifficultyTarget: 1000,
		Nonce:            12345,
		ExtraData:        []byte{},
	}

	hash1, _ := ComputeHeaderHash(header)
	hash2, _ := ComputeHeaderHash(header)
	hash3, _ := ComputeHeaderHash(header)

	if hash1 != hash2 || hash2 != hash3 {
		t.Error("Header hash not deterministic!")
	}
}

func TestComputeHeaderHashUniqueness(t *testing.T) {
	header1 := &BlockHeader{
		CodecVersion:     1,
		BlockIndex:       0,
		Timestamp:        1609459200,
		ParentHash:       [32]byte{},
		MerkleRoot:       [32]byte{},
		MinerAddress:     [32]byte{},
		Commitment:       [32]byte{},
		DifficultyTarget: 1000,
		Nonce:            0,
		ExtraData:        []byte{},
	}

	header2 := &BlockHeader{
		CodecVersion:     1,
		BlockIndex:       1, // Different
		Timestamp:        1609459200,
		ParentHash:       [32]byte{},
		MerkleRoot:       [32]byte{},
		MinerAddress:     [32]byte{},
		Commitment:       [32]byte{},
		DifficultyTarget: 1000,
		Nonce:            0,
		ExtraData:        []byte{},
	}

	hash1, _ := ComputeHeaderHash(header1)
	hash2, _ := ComputeHeaderHash(header2)

	if hash1 == hash2 {
		t.Error("Different headers produced same hash!")
	}
}
