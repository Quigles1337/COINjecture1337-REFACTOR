// Unit tests for Merkle tree utilities
package consensus

import (
	"crypto/sha256"
	"testing"
)

// TestComputeMerkleRoot_Empty tests empty tree
func TestComputeMerkleRoot_Empty(t *testing.T) {
	hashes := [][32]byte{}
	root := ComputeMerkleRoot(hashes)

	expected := [32]byte{}
	if root != expected {
		t.Errorf("Expected empty root, got %x", root)
	}
}

// TestComputeMerkleRoot_SingleLeaf tests single-leaf tree
func TestComputeMerkleRoot_SingleLeaf(t *testing.T) {
	leaf := sha256.Sum256([]byte("test"))
	hashes := [][32]byte{leaf}

	root := ComputeMerkleRoot(hashes)

	if root != leaf {
		t.Errorf("Expected root to equal leaf, got %x", root)
	}
}

// TestComputeMerkleRoot_TwoLeaves tests two-leaf tree
func TestComputeMerkleRoot_TwoLeaves(t *testing.T) {
	leaf1 := sha256.Sum256([]byte("leaf1"))
	leaf2 := sha256.Sum256([]byte("leaf2"))
	hashes := [][32]byte{leaf1, leaf2}

	root := ComputeMerkleRoot(hashes)

	// Manually compute expected root
	combined := append(leaf1[:], leaf2[:]...)
	expected := sha256.Sum256(combined)

	if root != expected {
		t.Errorf("Expected root %x, got %x", expected, root)
	}
}

// TestComputeMerkleRoot_ThreeLeaves tests odd-number leaf tree
func TestComputeMerkleRoot_ThreeLeaves(t *testing.T) {
	leaf1 := sha256.Sum256([]byte("leaf1"))
	leaf2 := sha256.Sum256([]byte("leaf2"))
	leaf3 := sha256.Sum256([]byte("leaf3"))
	hashes := [][32]byte{leaf1, leaf2, leaf3}

	root := ComputeMerkleRoot(hashes)

	// Manually compute expected root
	// Level 1: H(leaf1 + leaf2), H(leaf3 + leaf3)
	combined12 := append(leaf1[:], leaf2[:]...)
	h12 := sha256.Sum256(combined12)

	combined33 := append(leaf3[:], leaf3[:]...) // Duplicate last leaf
	h33 := sha256.Sum256(combined33)

	// Level 2: H(h12 + h33)
	combinedFinal := append(h12[:], h33[:]...)
	expected := sha256.Sum256(combinedFinal)

	if root != expected {
		t.Errorf("Expected root %x, got %x", expected, root)
	}
}

// TestComputeMerkleRoot_FourLeaves tests balanced tree
func TestComputeMerkleRoot_FourLeaves(t *testing.T) {
	leaf1 := sha256.Sum256([]byte("leaf1"))
	leaf2 := sha256.Sum256([]byte("leaf2"))
	leaf3 := sha256.Sum256([]byte("leaf3"))
	leaf4 := sha256.Sum256([]byte("leaf4"))
	hashes := [][32]byte{leaf1, leaf2, leaf3, leaf4}

	root := ComputeMerkleRoot(hashes)

	// Manually compute expected root
	combined12 := append(leaf1[:], leaf2[:]...)
	h12 := sha256.Sum256(combined12)

	combined34 := append(leaf3[:], leaf4[:]...)
	h34 := sha256.Sum256(combined34)

	combinedFinal := append(h12[:], h34[:]...)
	expected := sha256.Sum256(combinedFinal)

	if root != expected {
		t.Errorf("Expected root %x, got %x", expected, root)
	}
}

// TestComputeMerkleRoot_EightLeaves tests larger balanced tree
func TestComputeMerkleRoot_EightLeaves(t *testing.T) {
	hashes := make([][32]byte, 8)
	for i := 0; i < 8; i++ {
		hashes[i] = sha256.Sum256([]byte{byte(i)})
	}

	root := ComputeMerkleRoot(hashes)

	// Verify root is non-zero
	if root == [32]byte{} {
		t.Error("Expected non-zero root for 8 leaves")
	}

	// Test determinism - same input should give same root
	root2 := ComputeMerkleRoot(hashes)
	if root != root2 {
		t.Error("Expected deterministic root computation")
	}
}

// TestComputeMerkleRoot_Deterministic tests that same inputs produce same outputs
func TestComputeMerkleRoot_Deterministic(t *testing.T) {
	hashes := [][32]byte{
		sha256.Sum256([]byte("a")),
		sha256.Sum256([]byte("b")),
		sha256.Sum256([]byte("c")),
	}

	root1 := ComputeMerkleRoot(hashes)
	root2 := ComputeMerkleRoot(hashes)

	if root1 != root2 {
		t.Error("Merkle root computation is not deterministic")
	}
}

// TestComputeMerkleRoot_DifferentInputs tests that different inputs produce different outputs
func TestComputeMerkleRoot_DifferentInputs(t *testing.T) {
	hashes1 := [][32]byte{
		sha256.Sum256([]byte("a")),
		sha256.Sum256([]byte("b")),
	}

	hashes2 := [][32]byte{
		sha256.Sum256([]byte("a")),
		sha256.Sum256([]byte("c")), // Different second leaf
	}

	root1 := ComputeMerkleRoot(hashes1)
	root2 := ComputeMerkleRoot(hashes2)

	if root1 == root2 {
		t.Error("Different inputs should produce different Merkle roots")
	}
}

// TestComputeMerkleRoot_OrderMatters tests that order of leaves affects root
func TestComputeMerkleRoot_OrderMatters(t *testing.T) {
	leaf1 := sha256.Sum256([]byte("leaf1"))
	leaf2 := sha256.Sum256([]byte("leaf2"))

	hashes1 := [][32]byte{leaf1, leaf2}
	hashes2 := [][32]byte{leaf2, leaf1}

	root1 := ComputeMerkleRoot(hashes1)
	root2 := ComputeMerkleRoot(hashes2)

	if root1 == root2 {
		t.Error("Order of leaves should affect Merkle root")
	}
}

// TestComputeTxRoot tests transaction root computation
func TestComputeTxRoot(t *testing.T) {
	txHashes := [][32]byte{
		sha256.Sum256([]byte("tx1")),
		sha256.Sum256([]byte("tx2")),
		sha256.Sum256([]byte("tx3")),
	}

	txRoot := ComputeTxRoot(txHashes)

	// Should match ComputeMerkleRoot
	expected := ComputeMerkleRoot(txHashes)
	if txRoot != expected {
		t.Errorf("ComputeTxRoot should match ComputeMerkleRoot")
	}
}

// TestComputeTxRoot_Empty tests empty transaction list
func TestComputeTxRoot_Empty(t *testing.T) {
	txHashes := [][32]byte{}
	txRoot := ComputeTxRoot(txHashes)

	expected := [32]byte{}
	if txRoot != expected {
		t.Errorf("Expected empty tx_root for empty transaction list")
	}
}

// TestComputeStateRoot tests state root computation
func TestComputeStateRoot(t *testing.T) {
	accountHashes := [][32]byte{
		sha256.Sum256([]byte("account1")),
		sha256.Sum256([]byte("account2")),
	}

	stateRoot := ComputeStateRoot(accountHashes)

	// Should match ComputeMerkleRoot
	expected := ComputeMerkleRoot(accountHashes)
	if stateRoot != expected {
		t.Errorf("ComputeStateRoot should match ComputeMerkleRoot")
	}
}

// TestVerifyMerkleProof_ValidProof tests valid Merkle proof verification
func TestVerifyMerkleProof_ValidProof(t *testing.T) {
	// Create a simple 4-leaf tree
	leaf0 := sha256.Sum256([]byte("leaf0"))
	leaf1 := sha256.Sum256([]byte("leaf1"))
	leaf2 := sha256.Sum256([]byte("leaf2"))
	leaf3 := sha256.Sum256([]byte("leaf3"))

	hashes := [][32]byte{leaf0, leaf1, leaf2, leaf3}
	root := ComputeMerkleRoot(hashes)

	// Compute proof for leaf0 (index 0)
	// Proof path: [leaf1, H(leaf2 + leaf3)]
	combined23 := append(leaf2[:], leaf3[:]...)
	h23 := sha256.Sum256(combined23)

	proof := [][32]byte{leaf1, h23}

	valid := VerifyMerkleProof(leaf0, proof, root, 0)
	if !valid {
		t.Error("Expected valid Merkle proof for leaf0")
	}
}

// TestVerifyMerkleProof_InvalidProof tests invalid Merkle proof
func TestVerifyMerkleProof_InvalidProof(t *testing.T) {
	leaf0 := sha256.Sum256([]byte("leaf0"))
	leaf1 := sha256.Sum256([]byte("leaf1"))
	leaf2 := sha256.Sum256([]byte("leaf2"))
	leaf3 := sha256.Sum256([]byte("leaf3"))

	hashes := [][32]byte{leaf0, leaf1, leaf2, leaf3}
	root := ComputeMerkleRoot(hashes)

	// Create invalid proof
	fakeProof := [][32]byte{
		sha256.Sum256([]byte("fake1")),
		sha256.Sum256([]byte("fake2")),
	}

	valid := VerifyMerkleProof(leaf0, fakeProof, root, 0)
	if valid {
		t.Error("Expected invalid Merkle proof to fail verification")
	}
}

// TestVerifyMerkleProof_WrongLeaf tests proof with wrong leaf
func TestVerifyMerkleProof_WrongLeaf(t *testing.T) {
	leaf0 := sha256.Sum256([]byte("leaf0"))
	leaf1 := sha256.Sum256([]byte("leaf1"))
	leaf2 := sha256.Sum256([]byte("leaf2"))
	leaf3 := sha256.Sum256([]byte("leaf3"))

	hashes := [][32]byte{leaf0, leaf1, leaf2, leaf3}
	root := ComputeMerkleRoot(hashes)

	// Compute proof for leaf0
	combined23 := append(leaf2[:], leaf3[:]...)
	h23 := sha256.Sum256(combined23)
	proof := [][32]byte{leaf1, h23}

	// Try to verify with wrong leaf
	wrongLeaf := sha256.Sum256([]byte("wrong"))
	valid := VerifyMerkleProof(wrongLeaf, proof, root, 0)
	if valid {
		t.Error("Expected proof verification to fail with wrong leaf")
	}
}

// TestVerifyMerkleProof_TwoLeafTree tests proof for 2-leaf tree
func TestVerifyMerkleProof_TwoLeafTree(t *testing.T) {
	leaf0 := sha256.Sum256([]byte("leaf0"))
	leaf1 := sha256.Sum256([]byte("leaf1"))

	hashes := [][32]byte{leaf0, leaf1}
	root := ComputeMerkleRoot(hashes)

	// Proof for leaf0: [leaf1]
	proof := [][32]byte{leaf1}

	valid := VerifyMerkleProof(leaf0, proof, root, 0)
	if !valid {
		t.Error("Expected valid proof for leaf0 in 2-leaf tree")
	}

	// Proof for leaf1: [leaf0]
	proof1 := [][32]byte{leaf0}
	valid1 := VerifyMerkleProof(leaf1, proof1, root, 1)
	if !valid1 {
		t.Error("Expected valid proof for leaf1 in 2-leaf tree")
	}
}

// TestVerifyMerkleProof_EightLeafTree tests proof for larger tree
func TestVerifyMerkleProof_EightLeafTree(t *testing.T) {
	// Create 8-leaf tree
	leaves := make([][32]byte, 8)
	for i := 0; i < 8; i++ {
		leaves[i] = sha256.Sum256([]byte{byte(i)})
	}

	root := ComputeMerkleRoot(leaves)

	// Build proof for leaf at index 3
	// Tree structure:
	//           root
	//        /        \
	//      h0123      h4567
	//     /    \      /    \
	//   h01    h23  h45    h67
	//  / \    / \   / \    / \
	// 0   1  2  3  4  5   6  7

	// Proof path for index 3: [leaf2, h01, h4567]
	combined01 := append(leaves[0][:], leaves[1][:]...)
	h01 := sha256.Sum256(combined01)

	combined45 := append(leaves[4][:], leaves[5][:]...)
	h45 := sha256.Sum256(combined45)

	combined67 := append(leaves[6][:], leaves[7][:]...)
	h67 := sha256.Sum256(combined67)

	combined4567 := append(h45[:], h67[:]...)
	h4567 := sha256.Sum256(combined4567)

	proof := [][32]byte{leaves[2], h01, h4567}

	valid := VerifyMerkleProof(leaves[3], proof, root, 3)
	if !valid {
		t.Error("Expected valid proof for leaf 3 in 8-leaf tree")
	}
}

// BenchmarkComputeMerkleRoot_8Leaves benchmarks 8-leaf tree
func BenchmarkComputeMerkleRoot_8Leaves(b *testing.B) {
	hashes := make([][32]byte, 8)
	for i := 0; i < 8; i++ {
		hashes[i] = sha256.Sum256([]byte{byte(i)})
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		ComputeMerkleRoot(hashes)
	}
}

// BenchmarkComputeMerkleRoot_1000Leaves benchmarks 1000-leaf tree (typical block size)
func BenchmarkComputeMerkleRoot_1000Leaves(b *testing.B) {
	hashes := make([][32]byte, 1000)
	for i := 0; i < 1000; i++ {
		hashes[i] = sha256.Sum256([]byte{byte(i % 256), byte(i / 256)})
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		ComputeMerkleRoot(hashes)
	}
}

// BenchmarkVerifyMerkleProof benchmarks proof verification
func BenchmarkVerifyMerkleProof(b *testing.B) {
	// Create 1000-leaf tree
	hashes := make([][32]byte, 1000)
	for i := 0; i < 1000; i++ {
		hashes[i] = sha256.Sum256([]byte{byte(i % 256), byte(i / 256)})
	}

	root := ComputeMerkleRoot(hashes)

	// Create a simple proof (this is simplified - real proof would need proper construction)
	proof := make([][32]byte, 10) // log2(1000) ≈ 10
	for i := 0; i < 10; i++ {
		proof[i] = sha256.Sum256([]byte{byte(i)})
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		VerifyMerkleProof(hashes[0], proof, root, 0)
	}
}
