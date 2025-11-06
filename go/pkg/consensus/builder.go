// Block builder - collects transactions from mempool and builds blocks
package consensus

import (
	"fmt"
	"time"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/mempool"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/state"
)

// BlockBuilder builds new blocks from mempool transactions
type BlockBuilder struct {
	mempool      *mempool.Mempool
	stateManager *state.StateManager
	log          *logger.Logger

	// Configuration
	maxTxPerBlock uint64 // Maximum transactions per block
	maxGasPerBlock uint64 // Maximum gas per block
	minBlockTime   time.Duration // Minimum time between blocks
}

// NewBlockBuilder creates a new block builder
func NewBlockBuilder(mp *mempool.Mempool, sm *state.StateManager, log *logger.Logger) *BlockBuilder {
	return &BlockBuilder{
		mempool:        mp,
		stateManager:   sm,
		log:            log,
		maxTxPerBlock:  1000,                // Max 1000 transactions per block
		maxGasPerBlock: 30000000,            // 30M gas per block
		minBlockTime:   2 * time.Second,     // Minimum 2 seconds between blocks
	}
}

// BuildBlock builds a new block from mempool transactions
// Returns the block and any transactions that were included
func (bb *BlockBuilder) BuildBlock(parentHash [32]byte, blockNumber uint64, validator [32]byte) (*Block, error) {
	bb.log.WithFields(logger.Fields{
		"block_number": blockNumber,
		"validator":    fmt.Sprintf("%x", validator[:8]),
	}).Info("Building new block")

	// Get transactions from mempool (ordered by priority)
	mempoolTxs := bb.mempool.GetTopTransactions(int(bb.maxTxPerBlock))

	// Filter and validate transactions
	validTxs := make([]*mempool.Transaction, 0, len(mempoolTxs))
	var totalGas uint64

	for _, tx := range mempoolTxs {
		// Check gas limit
		if totalGas+tx.GasLimit > bb.maxGasPerBlock {
			bb.log.WithField("tx_hash", fmt.Sprintf("%x", tx.Hash[:8])).Debug("Transaction would exceed block gas limit, skipping")
			continue
		}

		// Validate transaction against current state
		// TODO: Full validation with Rust FFI
		account, err := bb.stateManager.GetAccount(tx.From)
		if err != nil {
			bb.log.WithError(err).WithField("tx_hash", fmt.Sprintf("%x", tx.Hash[:8])).Warn("Failed to get account for transaction")
			continue
		}

		// Check nonce
		if tx.Nonce != account.Nonce {
			bb.log.WithFields(logger.Fields{
				"tx_hash":      fmt.Sprintf("%x", tx.Hash[:8]),
				"expected":     account.Nonce,
				"got":          tx.Nonce,
			}).Debug("Transaction nonce mismatch")
			continue
		}

		// Check balance
		totalCost := tx.Amount + tx.Fee
		if account.Balance < totalCost {
			bb.log.WithFields(logger.Fields{
				"tx_hash":    fmt.Sprintf("%x", tx.Hash[:8]),
				"balance":    account.Balance,
				"total_cost": totalCost,
			}).Debug("Insufficient balance for transaction")
			continue
		}

		// Transaction is valid, include it
		validTxs = append(validTxs, tx)
		totalGas += tx.GasLimit
	}

	// Create block
	block := NewBlock(blockNumber, parentHash, validator, validTxs)

	// Finalize block (computes hashes)
	block.Finalize()

	bb.log.WithFields(logger.Fields{
		"block_number": blockNumber,
		"block_hash":   fmt.Sprintf("%x", block.BlockHash[:8]),
		"tx_count":     len(validTxs),
		"gas_used":     block.GasUsed,
	}).Info("Block built successfully")

	return block, nil
}

// ApplyBlock applies a block's transactions to the state
// Returns the new state root and any errors
func (bb *BlockBuilder) ApplyBlock(block *Block) ([32]byte, error) {
	bb.log.WithFields(logger.Fields{
		"block_number": block.BlockNumber,
		"block_hash":   fmt.Sprintf("%x", block.BlockHash[:8]),
		"tx_count":     len(block.Transactions),
	}).Info("Applying block to state")

	// Start a state snapshot for rollback if needed
	// TODO: Implement state snapshots

	// Apply each transaction
	for i, tx := range block.Transactions {
		if err := bb.applyTransaction(tx, block.BlockNumber); err != nil {
			bb.log.WithError(err).WithFields(logger.Fields{
				"tx_hash": fmt.Sprintf("%x", tx.Hash[:8]),
				"tx_index": i,
			}).Error("Failed to apply transaction")
			// TODO: Rollback state
			return [32]byte{}, fmt.Errorf("failed to apply transaction %d: %w", i, err)
		}
	}

	// Compute new state root
	// TODO: Implement proper state root computation
	stateRoot := [32]byte{}

	bb.log.WithFields(logger.Fields{
		"block_number": block.BlockNumber,
		"state_root":   fmt.Sprintf("%x", stateRoot[:8]),
	}).Info("Block applied successfully")

	return stateRoot, nil
}

// applyTransaction applies a single transaction to the state
func (bb *BlockBuilder) applyTransaction(tx *mempool.Transaction, blockNumber uint64) error {
	// Get sender account
	sender, err := bb.stateManager.GetAccount(tx.From)
	if err != nil {
		return fmt.Errorf("failed to get sender account: %w", err)
	}

	// Get recipient account (create if doesn't exist)
	recipient, err := bb.stateManager.GetAccount(tx.To)
	if err != nil {
		// Create new account
		recipient = &state.Account{
			Address:   tx.To,
			Balance:   0,
			Nonce:     0,
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}
	}

	// Deduct from sender
	totalCost := tx.Amount + tx.Fee
	if sender.Balance < totalCost {
		return fmt.Errorf("insufficient balance: need %d, have %d", totalCost, sender.Balance)
	}

	sender.Balance -= totalCost
	sender.Nonce++
	sender.UpdatedAt = time.Now()

	// Add to recipient
	recipient.Balance += tx.Amount
	recipient.UpdatedAt = time.Now()

	// Update state
	if err := bb.stateManager.UpdateAccount(sender.Address, sender.Balance, sender.Nonce); err != nil {
		return fmt.Errorf("failed to update sender account: %w", err)
	}

	if err := bb.stateManager.UpdateAccount(recipient.Address, recipient.Balance, recipient.Nonce); err != nil {
		return fmt.Errorf("failed to update recipient account: %w", err)
	}

	// Remove transaction from mempool
	if err := bb.mempool.RemoveTransaction(tx.Hash); err != nil {
		bb.log.WithError(err).Warn("Failed to remove transaction from mempool")
	}

	bb.log.WithFields(logger.Fields{
		"tx_hash": fmt.Sprintf("%x", tx.Hash[:8]),
		"from":    fmt.Sprintf("%x", tx.From[:8]),
		"to":      fmt.Sprintf("%x", tx.To[:8]),
		"amount":  tx.Amount,
		"fee":     tx.Fee,
	}).Debug("Transaction applied")

	return nil
}

// EstimateBlockTime estimates when the next block should be produced
func (bb *BlockBuilder) EstimateBlockTime(lastBlockTime time.Time) time.Time {
	nextTime := lastBlockTime.Add(bb.minBlockTime)

	// If we're behind schedule, produce immediately
	if nextTime.Before(time.Now()) {
		return time.Now()
	}

	return nextTime
}
