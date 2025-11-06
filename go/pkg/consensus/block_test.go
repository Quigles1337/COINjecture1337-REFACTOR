// Unit tests for Block structure and validation
package consensus

import (
	"crypto/sha256"
	"testing"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/mempool"
)

// TestNewBlock tests basic block creation
func TestNewBlock(t *testing.T) {
	validator := [32]byte{1, 2, 3}
	parentHash := sha256.Sum256([]byte("parent"))

	// Create empty block
	block := NewBlock(1, parentHash, validator, []*mempool.Transaction{})

	if block.BlockNumber != 1 {
		t.Errorf("Expected block number 1, got %d", block.BlockNumber)
	}

	if block.ParentHash != parentHash {
		t.Errorf("Parent hash mismatch")
	}

	if block.Validator != validator {
		t.Errorf("Validator mismatch")
	}

	if block.Difficulty != 1 {
		t.Errorf("Expected difficulty 1, got %d", block.Difficulty)
	}

	if block.GasLimit != 30000000 {
		t.Errorf("Expected gas limit 30M, got %d", block.GasLimit)
	}

	if len(block.Transactions) != 0 {
		t.Errorf("Expected 0 transactions, got %d", len(block.Transactions))
	}
}

// TestNewBlock_WithTransactions tests block with transactions
func TestNewBlock_WithTransactions(t *testing.T) {
	validator := [32]byte{1, 2, 3}
	parentHash := sha256.Sum256([]byte("parent"))

	// Create mock transactions
	txs := []*mempool.Transaction{
		{
			Hash:      sha256.Sum256([]byte("tx1")),
			From:      [32]byte{10},
			To:        [32]byte{20},
			Amount:    100,
			Fee:       1,
			Nonce:     1,
			Timestamp: time.Now().Unix(),
			Priority:  10.0,
		},
		{
			Hash:      sha256.Sum256([]byte("tx2")),
			From:      [32]byte{11},
			To:        [32]byte{21},
			Amount:    200,
			Fee:       2,
			Nonce:     2,
			Timestamp: time.Now().Unix(),
			Priority:  20.0,
		},
	}

	block := NewBlock(1, parentHash, validator, txs)

	if len(block.Transactions) != 2 {
		t.Errorf("Expected 2 transactions, got %d", len(block.Transactions))
	}

	if block.Transactions[0].Hash != txs[0].Hash {
		t.Error("Transaction 0 mismatch")
	}

	if block.Transactions[1].Hash != txs[1].Hash {
		t.Error("Transaction 1 mismatch")
	}
}

// TestNewGenesisBlock tests genesis block creation
func TestNewGenesisBlock(t *testing.T) {
	validator := [32]byte{5, 6, 7}

	genesis := NewGenesisBlock(validator)

	if genesis.BlockNumber != 0 {
		t.Errorf("Expected genesis block number 0, got %d", genesis.BlockNumber)
	}

	// Parent hash should be all zeros
	zeroHash := [32]byte{}
	if genesis.ParentHash != zeroHash {
		t.Error("Genesis parent hash should be all zeros")
	}

	if genesis.Validator != validator {
		t.Error("Genesis validator mismatch")
	}

	if len(genesis.Transactions) != 0 {
		t.Error("Genesis block should have no transactions")
	}

	// Check roots are computed
	// Genesis has no transactions, so tx_root is empty (all zeros)
	if genesis.TxRoot != zeroHash {
		t.Error("Genesis tx_root should be empty (no transactions)")
	}

	if genesis.StateRoot != zeroHash {
		t.Error("Genesis state_root should be zero")
	}

	// Block hash should be computed (non-zero)
	if genesis.BlockHash == zeroHash {
		t.Error("Genesis block_hash not computed")
	}
}

// TestBlock_ComputeHash tests block hash computation
func TestBlock_ComputeHash(t *testing.T) {
	block := NewBlock(42, [32]byte{1}, [32]byte{2}, []*mempool.Transaction{})

	hash1 := block.ComputeHash()
	hash2 := block.ComputeHash()

	// Should be deterministic
	if hash1 != hash2 {
		t.Error("ComputeHash not deterministic")
	}

	// Should not be zero
	if hash1 == [32]byte{} {
		t.Error("ComputeHash returned zero hash")
	}
}

// TestBlock_ComputeHash_DifferentBlocks tests that different blocks produce different hashes
func TestBlock_ComputeHash_DifferentBlocks(t *testing.T) {
	block1 := NewBlock(1, [32]byte{}, [32]byte{1}, []*mempool.Transaction{})
	block2 := NewBlock(2, [32]byte{}, [32]byte{1}, []*mempool.Transaction{})

	hash1 := block1.ComputeHash()
	hash2 := block2.ComputeHash()

	if hash1 == hash2 {
		t.Error("Different blocks should produce different hashes")
	}
}

// TestBlock_Finalize tests block finalization
func TestBlock_Finalize(t *testing.T) {
	validator := [32]byte{3, 4, 5}
	parentHash := sha256.Sum256([]byte("parent"))

	tx := &mempool.Transaction{
		Hash:      sha256.Sum256([]byte("tx1")),
		From:      [32]byte{10},
		To:        [32]byte{20},
		Amount:    100,
		Fee:       1,
		Nonce:     1,
		Timestamp: time.Now().Unix(),
		Priority:  10.0,
	}

	block := NewBlock(1, parentHash, validator, []*mempool.Transaction{tx})

	// Manually set some fields
	block.GasUsed = 21000
	block.StateRoot = sha256.Sum256([]byte("state"))

	// Finalize should compute tx_root and block_hash
	block.Finalize()

	// Verify tx_root is non-zero
	if block.TxRoot == [32]byte{} {
		t.Error("TxRoot not computed during Finalize")
	}

	// Verify block_hash is non-zero
	if block.BlockHash == [32]byte{} {
		t.Error("BlockHash not computed during Finalize")
	}
}

// TestBlock_IsValid_ValidBlock tests validation of valid block
func TestBlock_IsValid_ValidBlock(t *testing.T) {
	validator := [32]byte{7, 8, 9}
	parentHash := sha256.Sum256([]byte("parent"))

	block := NewBlock(1, parentHash, validator, []*mempool.Transaction{})
	block.GasUsed = 0 // No transactions, no gas
	block.Finalize()

	if !block.IsValid() {
		t.Error("Valid block marked as invalid")
	}
}

// TestBlock_IsValid_GasExceeded tests validation with gas exceeded
func TestBlock_IsValid_GasExceeded(t *testing.T) {
	validator := [32]byte{7, 8, 9}
	parentHash := sha256.Sum256([]byte("parent"))

	block := NewBlock(1, parentHash, validator, []*mempool.Transaction{})
	block.Finalize()

	// Manually tamper with gas after finalization to simulate exceeded gas
	block.GasLimit = 1000000
	block.GasUsed = 1000001 // Exceeds limit

	if block.IsValid() {
		t.Errorf("Block with exceeded gas should be invalid (GasLimit=%d, GasUsed=%d)", block.GasLimit, block.GasUsed)
	}
}

// TestBlock_IsValid_InvalidHash tests validation with wrong block hash
func TestBlock_IsValid_InvalidHash(t *testing.T) {
	validator := [32]byte{7, 8, 9}
	parentHash := sha256.Sum256([]byte("parent"))

	block := NewBlock(1, parentHash, validator, []*mempool.Transaction{})
	block.Finalize()

	// Tamper with block hash
	block.BlockHash = sha256.Sum256([]byte("fake"))

	if block.IsValid() {
		t.Error("Block with invalid hash should fail validation")
	}
}

// TestBlock_IsValid_TamperedData tests validation with tampered data
func TestBlock_IsValid_TamperedData(t *testing.T) {
	validator := [32]byte{7, 8, 9}
	parentHash := sha256.Sum256([]byte("parent"))

	block := NewBlock(1, parentHash, validator, []*mempool.Transaction{})
	block.Finalize()

	// Save original hash
	originalHash := block.BlockHash

	// Tamper with block number
	block.BlockNumber = 999

	// Recompute hash (should differ from original)
	newHash := block.ComputeHash()

	if newHash == originalHash {
		t.Error("Tampering should change block hash")
	}

	// Block with original hash but tampered data is invalid
	block.BlockHash = originalHash
	if block.IsValid() {
		t.Error("Block with tampered data should fail validation")
	}
}

// TestBlock_Header tests header encoding
func TestBlock_Header(t *testing.T) {
	validator := [32]byte{11, 12, 13}
	parentHash := sha256.Sum256([]byte("parent"))

	block := NewBlock(5, parentHash, validator, []*mempool.Transaction{})
	block.Timestamp = 1700000000
	block.GasUsed = 500000
	block.TxRoot = sha256.Sum256([]byte("txroot"))
	block.StateRoot = sha256.Sum256([]byte("stateroot"))

	header := block.Header()

	// Header should not be nil
	if header == nil {
		t.Error("Header() returned nil")
	}

	// Header should contain correct block number
	if header.BlockNumber != block.BlockNumber {
		t.Error("Header BlockNumber mismatch")
	}
}

// TestBlock_Timestamp tests timestamp is set
func TestBlock_Timestamp(t *testing.T) {
	block := NewBlock(1, [32]byte{}, [32]byte{1}, []*mempool.Transaction{})

	if block.Timestamp == 0 {
		t.Error("Block timestamp not set")
	}

	now := time.Now().Unix()
	if block.Timestamp < now-5 || block.Timestamp > now+5 {
		t.Errorf("Block timestamp %d not close to current time %d", block.Timestamp, now)
	}
}

// TestBlock_ExtraData tests extra data field
func TestBlock_ExtraData(t *testing.T) {
	block := NewBlock(1, [32]byte{}, [32]byte{1}, []*mempool.Transaction{})

	// Extra data should be 32 bytes
	if len(block.ExtraData) != 32 {
		t.Errorf("Extra data should be 32 bytes, got %d", len(block.ExtraData))
	}

	// Should be all zeros initially
	allZeros := true
	for _, b := range block.ExtraData {
		if b != 0 {
			allZeros = false
			break
		}
	}

	if !allZeros {
		t.Error("Extra data should be all zeros initially")
	}

	// Should be modifiable
	block.ExtraData[0] = 42
	if block.ExtraData[0] != 42 {
		t.Error("Extra data not modifiable")
	}
}

// TestBlock_Difficulty tests difficulty field
func TestBlock_Difficulty(t *testing.T) {
	block := NewBlock(1, [32]byte{}, [32]byte{1}, []*mempool.Transaction{})

	// PoA blocks always have difficulty 1
	if block.Difficulty != 1 {
		t.Errorf("PoA difficulty should be 1, got %d", block.Difficulty)
	}
}

// TestBlock_Nonce tests nonce field
func TestBlock_Nonce(t *testing.T) {
	block := NewBlock(1, [32]byte{}, [32]byte{1}, []*mempool.Transaction{})

	// PoA blocks always have nonce 0
	if block.Nonce != 0 {
		t.Errorf("PoA nonce should be 0, got %d", block.Nonce)
	}
}

// TestBlock_MultipleTransactions tests block with many transactions
func TestBlock_MultipleTransactions(t *testing.T) {
	validator := [32]byte{15, 16, 17}

	// Create 10 transactions
	txs := make([]*mempool.Transaction, 10)
	for i := 0; i < 10; i++ {
		txs[i] = &mempool.Transaction{
			Hash:      sha256.Sum256([]byte{byte(i)}),
			From:      [32]byte{byte(i)},
			To:        [32]byte{byte(i + 100)},
			Amount:    uint64(i * 100),
			Fee:       uint64(i),
			Nonce:     uint64(i),
			Timestamp: time.Now().Unix(),
			Priority:  float64(i * 10),
		}
	}

	block := NewBlock(1, [32]byte{}, validator, txs)
	block.Finalize()

	if len(block.Transactions) != 10 {
		t.Errorf("Expected 10 transactions, got %d", len(block.Transactions))
	}

	// Verify tx_root is computed correctly
	txHashes := make([][32]byte, 10)
	for i, tx := range txs {
		txHashes[i] = tx.Hash
	}
	expectedTxRoot := ComputeMerkleRoot(txHashes)

	if block.TxRoot != expectedTxRoot {
		t.Error("TxRoot mismatch")
	}
}

// TestBlock_Clone tests that blocks can be copied safely
func TestBlock_Clone(t *testing.T) {
	original := NewBlock(1, [32]byte{1}, [32]byte{2}, []*mempool.Transaction{})
	original.Finalize()

	// Manual clone (no built-in clone method)
	clone := &Block{
		BlockNumber:  original.BlockNumber,
		ParentHash:   original.ParentHash,
		StateRoot:    original.StateRoot,
		TxRoot:       original.TxRoot,
		Timestamp:    original.Timestamp,
		Validator:    original.Validator,
		Difficulty:   original.Difficulty,
		Nonce:        original.Nonce,
		GasLimit:     original.GasLimit,
		GasUsed:      original.GasUsed,
		ExtraData:    original.ExtraData,
		Transactions: original.Transactions,
		BlockHash:    original.BlockHash,
	}

	// Verify clone matches original
	if clone.BlockHash != original.BlockHash {
		t.Error("Clone block hash mismatch")
	}

	// Modifying clone shouldn't affect original
	clone.BlockNumber = 999
	if original.BlockNumber == 999 {
		t.Error("Modifying clone affected original")
	}
}

// BenchmarkNewBlock benchmarks block creation
func BenchmarkNewBlock(b *testing.B) {
	validator := [32]byte{1, 2, 3}
	parentHash := [32]byte{4, 5, 6}
	txs := []*mempool.Transaction{}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		NewBlock(uint64(i), parentHash, validator, txs)
	}
}

// BenchmarkBlock_Finalize benchmarks block finalization
func BenchmarkBlock_Finalize(b *testing.B) {
	validator := [32]byte{1, 2, 3}

	// Create block with 100 transactions
	txs := make([]*mempool.Transaction, 100)
	for i := 0; i < 100; i++ {
		txs[i] = &mempool.Transaction{
			Hash:      sha256.Sum256([]byte{byte(i)}),
			From:      [32]byte{byte(i)},
			To:        [32]byte{byte(i + 100)},
			Amount:    uint64(i),
			Fee:       1,
			Nonce:     uint64(i),
			Timestamp: time.Now().Unix(),
			Priority:  10.0,
		}
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		block := NewBlock(1, [32]byte{}, validator, txs)
		block.Finalize()
	}
}

// BenchmarkBlock_IsValid benchmarks block validation
func BenchmarkBlock_IsValid(b *testing.B) {
	validator := [32]byte{1, 2, 3}
	block := NewBlock(1, [32]byte{}, validator, []*mempool.Transaction{})
	block.Finalize()

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		block.IsValid()
	}
}
