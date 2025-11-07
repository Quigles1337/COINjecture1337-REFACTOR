// Proof-of-Authority consensus engine for COINjecture blockchain
package consensus

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/mempool"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/state"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/tokenomics"
)

// ConsensusConfig holds consensus engine configuration
type ConsensusConfig struct {
	BlockTime    time.Duration // Target time between blocks
	Validators   [][32]byte    // List of authorized validator addresses
	ValidatorKey [32]byte      // This node's validator key (if a validator)
	IsValidator  bool          // Whether this node is a validator
}

// Engine is the Proof-of-Authority consensus engine
type Engine struct {
	config       ConsensusConfig
	builder      *BlockBuilder
	stateManager *state.StateManager
	log          *logger.Logger

	// Current chain state
	currentBlock *Block
	blockHeight  uint64
	chainLock    sync.RWMutex

	// Fork choice and chain reorganization
	forkChoice *ForkChoice

	// Validator slashing
	slashing *SlashingManager

	// Tokenomics - $BEANS distribution
	economics  *tokenomics.Economics
	distributor *tokenomics.RewardDistributor

	// Block production
	blockTimer *time.Ticker
	ctx        context.Context
	cancel     context.CancelFunc

	// Callbacks
	onNewBlock func(*Block) // Called when a new block is produced
	onReorg    func(oldTip *Block, newTip *Block, reorgDepth int) // Called on chain reorg
}

// NewEngine creates a new PoA consensus engine with tokenomics
func NewEngine(
	cfg ConsensusConfig,
	mp *mempool.Mempool,
	sm *state.StateManager,
	log *logger.Logger,
) *Engine {
	ctx, cancel := context.WithCancel(context.Background())

	builder := NewBlockBuilder(mp, sm, log)

	// Create slashing manager with default config
	slashingCfg := DefaultSlashingConfig()
	slashing := NewSlashingManager(slashingCfg, log)

	// Register all validators for slashing tracking
	for _, validator := range cfg.Validators {
		slashing.RegisterValidator(validator)
	}

	// Initialize tokenomics with Critical Complex Equilibrium
	tokenCfg := tokenomics.DefaultTokenomicsConfig()
	// Use first validator as treasury address for now (will be configurable)
	if len(cfg.Validators) > 0 {
		tokenCfg.TreasuryAddress = cfg.Validators[0]
	}

	economics := tokenomics.NewEconomics(tokenCfg, log)
	distributor := tokenomics.NewRewardDistributor(economics, sm, tokenCfg.TreasuryAddress, log)

	log.WithFields(logger.Fields{
		"validator_share": fmt.Sprintf("%.2f%%", tokenCfg.ValidatorFeeShare*100),
		"burn_share":      fmt.Sprintf("%.2f%%", tokenCfg.BurnFeeShare*100),
		"treasury_share":  fmt.Sprintf("%.2f%%", tokenCfg.TreasuryFeeShare*100),
	}).Info("$BEANS tokenomics initialized with Critical Complex Equilibrium")

	return &Engine{
		config:       cfg,
		builder:      builder,
		stateManager: sm,
		log:          log,
		slashing:     slashing,
		economics:    economics,
		distributor:  distributor,
		blockHeight:  0,
		ctx:          ctx,
		cancel:       cancel,
	}
}

// Start starts the consensus engine
func (e *Engine) Start() error {
	e.log.WithFields(logger.Fields{
		"is_validator": e.config.IsValidator,
		"block_time":   e.config.BlockTime,
		"validators":   len(e.config.Validators),
	}).Info("Starting PoA consensus engine")

	// Initialize genesis block if needed
	if e.currentBlock == nil {
		if err := e.initializeGenesis(); err != nil {
			return fmt.Errorf("failed to initialize genesis: %w", err)
		}
	}

	// Start block production if we're a validator
	if e.config.IsValidator {
		go e.blockProductionLoop()
	}

	return nil
}

// Stop stops the consensus engine
func (e *Engine) Stop() {
	e.log.Info("Stopping PoA consensus engine")

	if e.blockTimer != nil {
		e.blockTimer.Stop()
	}

	e.cancel()
}

// initializeGenesis initializes the genesis block
func (e *Engine) initializeGenesis() error {
	e.log.Info("Initializing genesis block")

	// Check if genesis already exists in database
	// TODO: Load from state manager

	// Create genesis block
	genesis := NewGenesisBlock(e.config.ValidatorKey)

	e.chainLock.Lock()
	e.currentBlock = genesis
	e.blockHeight = 0

	// Initialize fork choice with genesis
	e.forkChoice = NewForkChoice(genesis, e.log)
	e.chainLock.Unlock()

	e.log.WithFields(logger.Fields{
		"block_hash":   fmt.Sprintf("%x", genesis.BlockHash[:8]),
		"validator":    fmt.Sprintf("%x", genesis.Validator[:8]),
		"timestamp":    genesis.Timestamp,
	}).Info("Genesis block initialized")

	// TODO: Save to database

	return nil
}

// blockProductionLoop produces blocks at regular intervals
func (e *Engine) blockProductionLoop() {
	e.log.Info("Starting block production loop")

	e.blockTimer = time.NewTicker(e.config.BlockTime)
	defer e.blockTimer.Stop()

	for {
		select {
		case <-e.ctx.Done():
			e.log.Info("Block production loop stopped")
			return

		case <-e.blockTimer.C:
			if err := e.produceBlock(); err != nil {
				e.log.WithError(err).Error("Failed to produce block")
			}
		}
	}
}

// produceBlock produces a new block
func (e *Engine) produceBlock() error {
	e.chainLock.Lock()
	defer e.chainLock.Unlock()

	// Check if it's our turn to validate
	if !e.isOurTurn(e.blockHeight + 1) {
		e.log.Debug("Not our turn to validate, skipping block production")
		return nil
	}

	e.log.WithField("block_number", e.blockHeight+1).Info("Producing new block")

	// Get parent block
	parentHash := [32]byte{}
	if e.currentBlock != nil {
		parentHash = e.currentBlock.BlockHash
	}

	// Build block
	block, err := e.builder.BuildBlock(parentHash, e.blockHeight+1, e.config.ValidatorKey)
	if err != nil {
		return fmt.Errorf("failed to build block: %w", err)
	}

	// Apply block to state
	stateRoot, err := e.builder.ApplyBlock(block)
	if err != nil {
		return fmt.Errorf("failed to apply block: %w", err)
	}

	// Update block with state root
	block.StateRoot = stateRoot
	block.Finalize() // Recompute hash with new state root

	// Add to fork choice
	if e.forkChoice != nil {
		_, err := e.forkChoice.AddBlock(block)
		if err != nil {
			e.log.WithError(err).Warn("Failed to add produced block to fork choice")
		}
	}

	// Update chain state
	e.currentBlock = block
	e.blockHeight++

	// Record successful block production (improves reputation)
	if e.slashing != nil {
		e.slashing.RecordBlockProduced(e.config.ValidatorKey)
	}

	// Distribute block rewards (base reward + transaction fees)
	totalFees := block.GasUsed // Simple fee model: 1 wei per gas unit for now
	if e.distributor != nil {
		if err := e.distributor.DistributeBlockRewards(block.BlockNumber, e.config.ValidatorKey, totalFees); err != nil {
			e.log.WithError(err).Error("Failed to distribute block rewards")
		}
	}

	e.log.WithFields(logger.Fields{
		"block_number": block.BlockNumber,
		"block_hash":   fmt.Sprintf("%x", block.BlockHash[:8]),
		"tx_count":     len(block.Transactions),
		"gas_used":     block.GasUsed,
		"fees":         totalFees,
		"state_root":   fmt.Sprintf("%x", stateRoot[:8]),
	}).Info("New block produced")

	// Trigger callback if set
	if e.onNewBlock != nil {
		go e.onNewBlock(block)
	}

	// TODO: Save block to database

	return nil
}

// isOurTurn determines if it's this validator's turn to produce a block
// Uses round-robin validator rotation for simplicity
func (e *Engine) isOurTurn(blockNumber uint64) bool {
	if len(e.config.Validators) == 0 {
		return false
	}

	// Round-robin: block_number % num_validators
	validatorIndex := int(blockNumber % uint64(len(e.config.Validators)))
	expectedValidator := e.config.Validators[validatorIndex]

	return expectedValidator == e.config.ValidatorKey
}

// ProcessBlock processes a block received from the P2P network
func (e *Engine) ProcessBlock(block *Block) error {
	e.chainLock.Lock()
	defer e.chainLock.Unlock()

	e.log.WithFields(logger.Fields{
		"block_number": block.BlockNumber,
		"block_hash":   fmt.Sprintf("%x", block.BlockHash[:8]),
		"validator":    fmt.Sprintf("%x", block.Validator[:8]),
	}).Info("Processing received block")

	// Check if validator is slashed/jailed
	if e.slashing != nil && !e.slashing.IsValidatorActive(block.Validator) {
		e.log.WithField("validator", fmt.Sprintf("%x", block.Validator[:8])).Warn("Block from slashed/jailed validator rejected")
		return fmt.Errorf("validator is slashed or jailed")
	}

	// Validate block
	if !block.IsValid() {
		// Slash validator for producing invalid block
		if e.slashing != nil {
			e.slashing.Slash(block.Validator, OffenseInvalidBlock, block.BlockNumber, nil)
		}
		return fmt.Errorf("invalid block")
	}

	// Check if validator is authorized
	if !e.isAuthorizedValidator(block.Validator) {
		return fmt.Errorf("unauthorized validator")
	}

	// Record successful block from this validator
	if e.slashing != nil {
		e.slashing.RecordBlockProduced(block.Validator)
	}

	// Add block to fork choice
	shouldReorg, err := e.forkChoice.AddBlock(block)
	if err != nil {
		return fmt.Errorf("fork choice rejected block: %w", err)
	}

	// If fork choice says we should reorganize, do it
	if shouldReorg {
		oldTip := e.currentBlock
		if err := e.handleChainReorganization(oldTip, block); err != nil {
			return fmt.Errorf("chain reorganization failed: %w", err)
		}
	} else {
		e.log.WithFields(logger.Fields{
			"block_number": block.BlockNumber,
			"block_hash":   fmt.Sprintf("%x", block.BlockHash[:8]),
		}).Debug("Block accepted but not canonical (fork)")
	}

	return nil
}

// handleChainReorganization handles switching to a new canonical chain with state rollback
func (e *Engine) handleChainReorganization(oldTip *Block, newTip *Block) error {
	e.log.WithFields(logger.Fields{
		"old_height": oldTip.BlockNumber,
		"old_hash":   fmt.Sprintf("%x", oldTip.BlockHash[:8]),
		"new_height": newTip.BlockNumber,
		"new_hash":   fmt.Sprintf("%x", newTip.BlockHash[:8]),
	}).Warn("Chain reorganization triggered")

	// Step 1: Find common ancestor
	commonAncestor, reorgDepth, err := e.findCommonAncestor(oldTip, newTip)
	if err != nil {
		return fmt.Errorf("failed to find common ancestor: %w", err)
	}

	e.log.WithFields(logger.Fields{
		"ancestor_height": commonAncestor.BlockNumber,
		"ancestor_hash":   fmt.Sprintf("%x", commonAncestor.BlockHash[:8]),
		"reorg_depth":     reorgDepth,
	}).Info("Found common ancestor for reorg")

	// Step 2: Take state snapshot (for rollback if reorg fails)
	snapshot, err := e.stateManager.GetAccountSnapshot()
	if err != nil {
		return fmt.Errorf("failed to create state snapshot: %w", err)
	}

	e.log.WithField("accounts_snapshotted", len(snapshot)).Debug("State snapshot created")

	// Step 3: Get path from common ancestor to new tip
	reorgPath, err := e.forkChoice.GetChainPath(commonAncestor.BlockHash, newTip.BlockHash)
	if err != nil {
		return fmt.Errorf("failed to get reorg path: %w", err)
	}

	e.log.WithField("blocks_to_replay", len(reorgPath)).Info("Calculated reorg path")

	// Step 4: Rollback state to common ancestor
	if err := e.rollbackStateToBlock(commonAncestor); err != nil {
		// Try to restore snapshot
		e.log.WithError(err).Error("State rollback failed, restoring snapshot")
		if restoreErr := e.stateManager.RestoreAccountSnapshot(snapshot); restoreErr != nil {
			return fmt.Errorf("rollback failed and snapshot restore failed: %w (original: %v)", restoreErr, err)
		}
		return fmt.Errorf("state rollback failed: %w", err)
	}

	// Step 5: Replay blocks from reorg path
	for i, block := range reorgPath {
		e.log.WithFields(logger.Fields{
			"block_number": block.BlockNumber,
			"block_hash":   fmt.Sprintf("%x", block.BlockHash[:8]),
			"progress":     fmt.Sprintf("%d/%d", i+1, len(reorgPath)),
		}).Info("Replaying block")

		// Apply block to state
		if _, err := e.builder.ApplyBlock(block); err != nil {
			// Rollback failed, restore snapshot
			e.log.WithError(err).Error("Block replay failed, restoring snapshot")
			if restoreErr := e.stateManager.RestoreAccountSnapshot(snapshot); restoreErr != nil {
				return fmt.Errorf("block replay failed and snapshot restore failed: %w (original: %v)", restoreErr, err)
			}
			return fmt.Errorf("failed to replay block %d: %w", block.BlockNumber, err)
		}
	}

	// Step 6: Update chain state
	e.currentBlock = newTip
	e.blockHeight = newTip.BlockNumber

	// Trigger reorg callback if set
	if e.onReorg != nil {
		go e.onReorg(oldTip, newTip, reorgDepth)
	}

	e.log.WithFields(logger.Fields{
		"new_height":  newTip.BlockNumber,
		"new_hash":    fmt.Sprintf("%x", newTip.BlockHash[:8]),
		"reorg_depth": reorgDepth,
		"blocks_replayed": len(reorgPath),
	}).Info("Chain reorganization complete")

	return nil
}

// findCommonAncestor finds the common ancestor between two blocks
func (e *Engine) findCommonAncestor(block1, block2 *Block) (*Block, int, error) {
	// Build chain from block1 back to genesis
	chain1 := make(map[[32]byte]*Block)
	current := block1
	for current != nil {
		chain1[current.BlockHash] = current
		if current.BlockNumber == 0 {
			break // Genesis
		}
		// Try to get parent from fork choice cache
		parent, exists := e.forkChoice.GetBlock(current.ParentHash)
		if !exists {
			break
		}
		current = parent
	}

	// Walk back from block2 until we find a block in chain1
	current = block2
	depth := 0
	for current != nil {
		if ancestor, exists := chain1[current.BlockHash]; exists {
			return ancestor, depth, nil
		}
		depth++
		if current.BlockNumber == 0 {
			// Reached genesis without finding common ancestor
			return current, depth, nil
		}
		parent, exists := e.forkChoice.GetBlock(current.ParentHash)
		if !exists {
			break
		}
		current = parent
	}

	return nil, 0, fmt.Errorf("no common ancestor found")
}

// rollbackStateToBlock rolls back state by replaying from genesis to target block
func (e *Engine) rollbackStateToBlock(targetBlock *Block) error {
	e.log.WithFields(logger.Fields{
		"target_height": targetBlock.BlockNumber,
		"target_hash":   fmt.Sprintf("%x", targetBlock.BlockHash[:8]),
	}).Info("Rolling back state")

	// Clear account state
	if err := e.stateManager.ClearAccountState(); err != nil {
		return fmt.Errorf("failed to clear account state: %w", err)
	}

	// Clear escrow state
	if err := e.stateManager.ClearEscrowState(); err != nil {
		return fmt.Errorf("failed to clear escrow state: %w", err)
	}

	// If target is genesis (block 0), we're done
	if targetBlock.BlockNumber == 0 {
		e.log.Info("Rolled back to genesis block")
		return nil
	}

	// Build chain from genesis to target
	chain := []*Block{}
	current := targetBlock
	for current.BlockNumber > 0 {
		chain = append([]*Block{current}, chain...) // Prepend
		parent, exists := e.forkChoice.GetBlock(current.ParentHash)
		if !exists {
			return fmt.Errorf("missing parent block %x", current.ParentHash[:8])
		}
		current = parent
	}

	// Replay blocks from genesis to target
	for i, block := range chain {
		e.log.WithFields(logger.Fields{
			"block_number": block.BlockNumber,
			"progress":     fmt.Sprintf("%d/%d", i+1, len(chain)),
		}).Debug("Replaying block for state rollback")

		if _, err := e.builder.ApplyBlock(block); err != nil {
			return fmt.Errorf("failed to replay block %d: %w", block.BlockNumber, err)
		}
	}

	e.log.WithField("blocks_replayed", len(chain)).Info("State rollback complete")
	return nil
}

// isAuthorizedValidator checks if an address is an authorized validator
func (e *Engine) isAuthorizedValidator(address [32]byte) bool {
	for _, validator := range e.config.Validators {
		if validator == address {
			return true
		}
	}
	return false
}

// GetCurrentBlock returns the current block
func (e *Engine) GetCurrentBlock() *Block {
	e.chainLock.RLock()
	defer e.chainLock.RUnlock()
	return e.currentBlock
}

// GetBlockHeight returns the current block height
func (e *Engine) GetBlockHeight() uint64 {
	e.chainLock.RLock()
	defer e.chainLock.RUnlock()
	return e.blockHeight
}

// SetNewBlockCallback sets a callback for when new blocks are produced
func (e *Engine) SetNewBlockCallback(callback func(*Block)) {
	e.onNewBlock = callback
}

// GetStats returns consensus engine statistics
func (e *Engine) GetStats() map[string]interface{} {
	e.chainLock.RLock()
	defer e.chainLock.RUnlock()

	stats := map[string]interface{}{
		"block_height":   e.blockHeight,
		"is_validator":   e.config.IsValidator,
		"validator_count": len(e.config.Validators),
		"block_time":     e.config.BlockTime.String(),
	}

	if e.currentBlock != nil {
		stats["current_block_hash"] = fmt.Sprintf("%x", e.currentBlock.BlockHash[:8])
		stats["current_block_txs"] = len(e.currentBlock.Transactions)
		stats["current_block_gas_used"] = e.currentBlock.GasUsed
	}

	return stats
}
