// Unit tests for consensus Engine
package consensus

import (
	"crypto/sha256"
	"testing"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/mempool"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/state"
)

// Helper: Create test engine
func createTestEngine(t *testing.T, validators [][32]byte, validatorKey [32]byte, isValidator bool) *Engine {
	cfg := ConsensusConfig{
		BlockTime:    2 * time.Second,
		Validators:   validators,
		ValidatorKey: validatorKey,
		IsValidator:  isValidator,
	}

	mempoolCfg := mempool.Config{
		MaxSize:           1000,
		MaxTxAge:          time.Hour,
		CleanupInterval:   time.Minute,
		PriorityThreshold: 0.0,
	}
	mp := mempool.NewMempool(mempoolCfg, logger.NewLogger("debug"))

	sm, err := state.NewStateManager(":memory:", logger.NewLogger("debug"))
	if err != nil {
		t.Fatalf("Failed to create state manager: %v", err)
	}

	log := logger.NewLogger("debug")

	return NewEngine(cfg, mp, sm, log)
}

// TestNewEngine tests engine creation
func TestNewEngine(t *testing.T) {
	validators := [][32]byte{{1}, {2}, {3}}
	validatorKey := [32]byte{1}

	engine := createTestEngine(t, validators, validatorKey, true)

	if engine == nil {
		t.Fatal("NewEngine returned nil")
	}

	if len(engine.config.Validators) != 3 {
		t.Errorf("Expected 3 validators, got %d", len(engine.config.Validators))
	}

	if engine.config.ValidatorKey != validatorKey {
		t.Error("Validator key mismatch")
	}

	if !engine.config.IsValidator {
		t.Error("Expected isValidator to be true")
	}

	if engine.config.BlockTime != 2*time.Second {
		t.Errorf("Expected block time 2s, got %v", engine.config.BlockTime)
	}
}

// TestEngine_Start tests engine startup
func TestEngine_Start(t *testing.T) {
	validators := [][32]byte{{1}, {2}, {3}}
	validatorKey := [32]byte{1}

	engine := createTestEngine(t, validators, validatorKey, true)
	defer engine.Stop()

	if err := engine.Start(); err != nil {
		t.Fatalf("Engine.Start failed: %v", err)
	}

	// Check genesis was initialized
	if engine.currentBlock == nil {
		t.Error("Genesis block not initialized")
	}

	if engine.currentBlock.BlockNumber != 0 {
		t.Errorf("Expected genesis block number 0, got %d", engine.currentBlock.BlockNumber)
	}

	if engine.blockHeight != 0 {
		t.Errorf("Expected block height 0, got %d", engine.blockHeight)
	}

	// Check fork choice initialized
	if engine.forkChoice == nil {
		t.Error("Fork choice not initialized")
	}
}

// TestEngine_isOurTurn tests round-robin validator selection
func TestEngine_isOurTurn(t *testing.T) {
	validators := [][32]byte{{1}, {2}, {3}}
	validatorKey := [32]byte{1} // We are validator 0

	engine := createTestEngine(t, validators, validatorKey, true)

	// Block 0: validator 0's turn (0 % 3 = 0)
	if !engine.isOurTurn(0) {
		t.Error("Expected block 0 to be our turn")
	}

	// Block 1: validator 1's turn (1 % 3 = 1)
	if engine.isOurTurn(1) {
		t.Error("Expected block 1 NOT to be our turn")
	}

	// Block 2: validator 2's turn (2 % 3 = 2)
	if engine.isOurTurn(2) {
		t.Error("Expected block 2 NOT to be our turn")
	}

	// Block 3: validator 0's turn again (3 % 3 = 0)
	if !engine.isOurTurn(3) {
		t.Error("Expected block 3 to be our turn")
	}
}

// TestEngine_isAuthorizedValidator tests validator authorization
func TestEngine_isAuthorizedValidator(t *testing.T) {
	validators := [][32]byte{{1}, {2}, {3}}
	validatorKey := [32]byte{1}

	engine := createTestEngine(t, validators, validatorKey, true)

	// Authorized validators
	if !engine.isAuthorizedValidator([32]byte{1}) {
		t.Error("Validator 1 should be authorized")
	}
	if !engine.isAuthorizedValidator([32]byte{2}) {
		t.Error("Validator 2 should be authorized")
	}
	if !engine.isAuthorizedValidator([32]byte{3}) {
		t.Error("Validator 3 should be authorized")
	}

	// Unauthorized validator
	if engine.isAuthorizedValidator([32]byte{99}) {
		t.Error("Validator 99 should NOT be authorized")
	}
}

// TestEngine_GetCurrentBlock tests current block retrieval
func TestEngine_GetCurrentBlock(t *testing.T) {
	validators := [][32]byte{{1}}
	validatorKey := [32]byte{1}

	engine := createTestEngine(t, validators, validatorKey, true)
	defer engine.Stop()

	if err := engine.Start(); err != nil {
		t.Fatalf("Engine.Start failed: %v", err)
	}

	block := engine.GetCurrentBlock()
	if block == nil {
		t.Fatal("GetCurrentBlock returned nil")
	}

	if block.BlockNumber != 0 {
		t.Errorf("Expected block number 0, got %d", block.BlockNumber)
	}
}

// TestEngine_GetBlockHeight tests block height retrieval
func TestEngine_GetBlockHeight(t *testing.T) {
	validators := [][32]byte{{1}}
	validatorKey := [32]byte{1}

	engine := createTestEngine(t, validators, validatorKey, true)
	defer engine.Stop()

	if err := engine.Start(); err != nil {
		t.Fatalf("Engine.Start failed: %v", err)
	}

	height := engine.GetBlockHeight()
	if height != 0 {
		t.Errorf("Expected height 0, got %d", height)
	}
}

// TestEngine_ProcessBlock_ValidBlock tests processing a valid block
func TestEngine_ProcessBlock_ValidBlock(t *testing.T) {
	validators := [][32]byte{{1}, {2}}
	validatorKey := [32]byte{1}

	engine := createTestEngine(t, validators, validatorKey, true)
	defer engine.Stop()

	if err := engine.Start(); err != nil {
		t.Fatalf("Engine.Start failed: %v", err)
	}

	// Create a valid block from authorized validator
	genesis := engine.GetCurrentBlock()
	block := NewBlock(1, genesis.BlockHash, [32]byte{2}, []*mempool.Transaction{})
	block.Finalize()

	// Process block
	if err := engine.ProcessBlock(block); err != nil {
		t.Fatalf("ProcessBlock failed: %v", err)
	}

	// Block should be accepted by fork choice
	if engine.GetBlockHeight() != 1 {
		t.Errorf("Expected height 1 after processing, got %d", engine.GetBlockHeight())
	}

	if engine.GetCurrentBlock().BlockHash != block.BlockHash {
		t.Error("Current block should be the processed block")
	}
}

// TestEngine_ProcessBlock_InvalidBlock tests rejecting an invalid block
func TestEngine_ProcessBlock_InvalidBlock(t *testing.T) {
	validators := [][32]byte{{1}}
	validatorKey := [32]byte{1}

	engine := createTestEngine(t, validators, validatorKey, true)
	defer engine.Stop()

	if err := engine.Start(); err != nil {
		t.Fatalf("Engine.Start failed: %v", err)
	}

	// Create an invalid block (tampered hash)
	genesis := engine.GetCurrentBlock()
	block := NewBlock(1, genesis.BlockHash, [32]byte{1}, []*mempool.Transaction{})
	block.Finalize()
	block.BlockHash = sha256.Sum256([]byte("fake")) // Tamper hash

	// Process block should fail
	if err := engine.ProcessBlock(block); err == nil {
		t.Fatal("Expected ProcessBlock to reject invalid block, but it succeeded")
	}
}

// TestEngine_ProcessBlock_UnauthorizedValidator tests rejecting blocks from unauthorized validators
func TestEngine_ProcessBlock_UnauthorizedValidator(t *testing.T) {
	validators := [][32]byte{{1}, {2}}
	validatorKey := [32]byte{1}

	engine := createTestEngine(t, validators, validatorKey, true)
	defer engine.Stop()

	if err := engine.Start(); err != nil {
		t.Fatalf("Engine.Start failed: %v", err)
	}

	// Create block from unauthorized validator
	genesis := engine.GetCurrentBlock()
	block := NewBlock(1, genesis.BlockHash, [32]byte{99}, []*mempool.Transaction{}) // Validator 99 not authorized
	block.Finalize()

	// Process block should fail
	if err := engine.ProcessBlock(block); err == nil {
		t.Fatal("Expected ProcessBlock to reject unauthorized validator, but it succeeded")
	}
}

// TestEngine_SetNewBlockCallback tests new block callback
func TestEngine_SetNewBlockCallback(t *testing.T) {
	validators := [][32]byte{{1}}
	validatorKey := [32]byte{1}

	engine := createTestEngine(t, validators, validatorKey, false) // Non-validator to prevent auto-production

	callbackCalled := false
	var callbackBlock *Block

	engine.SetNewBlockCallback(func(block *Block) {
		callbackCalled = true
		callbackBlock = block
	})

	// Manually trigger callback by creating a block
	testBlock := NewBlock(1, [32]byte{}, validatorKey, []*mempool.Transaction{})
	testBlock.Finalize()

	// Trigger callback directly (simulate block production)
	if engine.onNewBlock != nil {
		engine.onNewBlock(testBlock)
	}

	// Give callback time to execute (it runs in goroutine)
	time.Sleep(50 * time.Millisecond)

	if !callbackCalled {
		t.Error("New block callback was not called")
	}

	if callbackBlock == nil {
		t.Error("Callback did not receive block")
	}

	if callbackBlock != nil && callbackBlock.BlockHash != testBlock.BlockHash {
		t.Error("Callback received wrong block")
	}
}

// TestEngine_GetStats tests engine statistics
func TestEngine_GetStats(t *testing.T) {
	validators := [][32]byte{{1}, {2}, {3}}
	validatorKey := [32]byte{1}

	engine := createTestEngine(t, validators, validatorKey, true)
	defer engine.Stop()

	if err := engine.Start(); err != nil {
		t.Fatalf("Engine.Start failed: %v", err)
	}

	stats := engine.GetStats()

	if stats == nil {
		t.Fatal("GetStats returned nil")
	}

	// Check expected fields
	if _, ok := stats["block_height"]; !ok {
		t.Error("Stats missing block_height")
	}

	if _, ok := stats["is_validator"]; !ok {
		t.Error("Stats missing is_validator")
	}

	if _, ok := stats["validator_count"]; !ok {
		t.Error("Stats missing validator_count")
	}

	if stats["validator_count"] != 3 {
		t.Errorf("Expected validator_count 3, got %v", stats["validator_count"])
	}

	if stats["is_validator"] != true {
		t.Error("Expected is_validator to be true")
	}
}

// TestEngine_ForkChoice_Integration tests fork choice integration
func TestEngine_ForkChoice_Integration(t *testing.T) {
	validators := [][32]byte{{1}, {2}}
	validatorKey := [32]byte{1}

	engine := createTestEngine(t, validators, validatorKey, true)
	defer engine.Stop()

	if err := engine.Start(); err != nil {
		t.Fatalf("Engine.Start failed: %v", err)
	}

	genesis := engine.GetCurrentBlock()

	// Create two competing blocks at height 1
	block1 := NewBlock(1, genesis.BlockHash, [32]byte{1}, []*mempool.Transaction{})
	block1.Finalize()

	block2 := NewBlock(1, genesis.BlockHash, [32]byte{2}, []*mempool.Transaction{})
	block2.Finalize()

	// Process first block
	if err := engine.ProcessBlock(block1); err != nil {
		t.Fatalf("Failed to process block1: %v", err)
	}

	// Current should be block1
	if engine.GetCurrentBlock().BlockHash != block1.BlockHash {
		t.Error("Expected block1 to be canonical")
	}

	// Process second block (same height, different hash)
	if err := engine.ProcessBlock(block2); err != nil {
		t.Fatalf("Failed to process block2: %v", err)
	}

	// Fork choice should pick one based on hash (lower hash wins)
	currentHash := engine.GetCurrentBlock().BlockHash
	if currentHash != block1.BlockHash && currentHash != block2.BlockHash {
		t.Error("Current block should be one of the two competing blocks")
	}
}

// TestEngine_MultipleBlocks tests processing a chain of blocks
func TestEngine_MultipleBlocks(t *testing.T) {
	validators := [][32]byte{{1}}
	validatorKey := [32]byte{1}

	engine := createTestEngine(t, validators, validatorKey, true)
	defer engine.Stop()

	if err := engine.Start(); err != nil {
		t.Fatalf("Engine.Start failed: %v", err)
	}

	// Build a chain of 5 blocks
	parentHash := engine.GetCurrentBlock().BlockHash
	for i := uint64(1); i <= 5; i++ {
		block := NewBlock(i, parentHash, validatorKey, []*mempool.Transaction{})
		block.Finalize()

		if err := engine.ProcessBlock(block); err != nil {
			t.Fatalf("Failed to process block %d: %v", i, err)
		}

		parentHash = block.BlockHash
	}

	// Check final height
	if engine.GetBlockHeight() != 5 {
		t.Errorf("Expected height 5, got %d", engine.GetBlockHeight())
	}
}

// TestEngine_Stop tests engine shutdown
func TestEngine_Stop(t *testing.T) {
	validators := [][32]byte{{1}}
	validatorKey := [32]byte{1}

	engine := createTestEngine(t, validators, validatorKey, true)

	if err := engine.Start(); err != nil {
		t.Fatalf("Engine.Start failed: %v", err)
	}

	// Stop should not panic
	engine.Stop()

	// Give time for cleanup
	time.Sleep(50 * time.Millisecond)

	// Context should be cancelled
	select {
	case <-engine.ctx.Done():
		// Expected
	default:
		t.Error("Engine context was not cancelled after Stop")
	}
}

// TestEngine_NonValidator tests engine behavior as non-validator
func TestEngine_NonValidator(t *testing.T) {
	validators := [][32]byte{{1}, {2}}
	validatorKey := [32]byte{99} // Not in validator set

	engine := createTestEngine(t, validators, validatorKey, false)
	defer engine.Stop()

	if err := engine.Start(); err != nil {
		t.Fatalf("Engine.Start failed: %v", err)
	}

	// Non-validator should not produce blocks
	// Block timer should not be started
	if engine.blockTimer != nil {
		t.Error("Non-validator should not have block timer")
	}

	// But should be able to process blocks from other validators
	genesis := engine.GetCurrentBlock()
	block := NewBlock(1, genesis.BlockHash, [32]byte{1}, []*mempool.Transaction{})
	block.Finalize()

	if err := engine.ProcessBlock(block); err != nil {
		t.Fatalf("Non-validator should be able to process blocks: %v", err)
	}

	if engine.GetBlockHeight() != 1 {
		t.Errorf("Expected height 1, got %d", engine.GetBlockHeight())
	}
}

// BenchmarkEngine_ProcessBlock benchmarks block processing
func BenchmarkEngine_ProcessBlock(b *testing.B) {
	validators := [][32]byte{{1}}
	validatorKey := [32]byte{1}

	engine := createTestEngine(&testing.T{}, validators, validatorKey, true)
	defer engine.Stop()

	engine.Start()

	// Create blocks to process
	blocks := make([]*Block, b.N)
	parentHash := engine.GetCurrentBlock().BlockHash
	for i := 0; i < b.N; i++ {
		block := NewBlock(uint64(i+1), parentHash, validatorKey, []*mempool.Transaction{})
		block.Finalize()
		blocks[i] = block
		parentHash = block.BlockHash
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_ = engine.ProcessBlock(blocks[i])
	}
}
