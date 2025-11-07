// Reward distribution - handles actual token distribution to validators and treasury
package tokenomics

import (
	"fmt"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/state"
)

// RewardDistributor distributes block rewards and transaction fees
type RewardDistributor struct {
	economics    *Economics
	stateManager *state.StateManager
	log          *logger.Logger

	// Special addresses
	treasuryAddress [32]byte
	burnAddress     [32]byte // Special burn address (0x00...dead)

	// Statistics
	totalDistributed uint64
	totalBurned      uint64
	blockCount       uint64
}

// NewRewardDistributor creates a new reward distributor
func NewRewardDistributor(
	economics *Economics,
	stateManager *state.StateManager,
	treasuryAddress [32]byte,
	log *logger.Logger,
) *RewardDistributor {

	// Burn address: 0x00...dead (standard burn address pattern)
	var burnAddress [32]byte
	copy(burnAddress[28:], []byte("dead"))

	return &RewardDistributor{
		economics:       economics,
		stateManager:    stateManager,
		log:             log,
		treasuryAddress: treasuryAddress,
		burnAddress:     burnAddress,
	}
}

// DistributeBlockRewards distributes rewards for a newly produced block
//
// This is called by the consensus engine after a block is finalized.
// It handles:
// 1. Block reward to validator (new token emission + fee share)
// 2. Fee burn (deflationary mechanism)
// 3. Treasury allocation (development funding)
func (rd *RewardDistributor) DistributeBlockRewards(
	blockHeight uint64,
	validator [32]byte,
	totalFees uint64,
) error {

	// Calculate distribution amounts
	validatorReward, burnAmount, treasuryAmount := rd.economics.DistributeBlockReward(
		blockHeight,
		validator,
		totalFees,
	)

	rd.log.WithFields(logger.Fields{
		"block_height":     blockHeight,
		"validator":        fmt.Sprintf("%x", validator[:8]),
		"validator_reward": FormatCoinAmount(validatorReward),
		"burn_amount":      FormatCoinAmount(burnAmount),
		"treasury_amount":  FormatCoinAmount(treasuryAmount),
	}).Info("Distributing block rewards")

	// 1. Pay validator (creates account if doesn't exist)
	if err := rd.mintToAccount(validator, validatorReward, "validator reward"); err != nil {
		return fmt.Errorf("failed to pay validator reward: %w", err)
	}

	// 2. Burn tokens (send to burn address - reduces circulating supply)
	if burnAmount > 0 {
		if err := rd.mintToAccount(rd.burnAddress, burnAmount, "fee burn"); err != nil {
			return fmt.Errorf("failed to burn tokens: %w", err)
		}
		rd.totalBurned += burnAmount
	}

	// 3. Pay treasury
	if treasuryAmount > 0 {
		if err := rd.mintToAccount(rd.treasuryAddress, treasuryAmount, "treasury allocation"); err != nil {
			return fmt.Errorf("failed to pay treasury: %w", err)
		}
	}

	// Update statistics
	rd.totalDistributed += validatorReward + burnAmount + treasuryAmount
	rd.blockCount++

	rd.log.WithFields(logger.Fields{
		"total_distributed": FormatCoinAmount(rd.totalDistributed),
		"total_burned":      FormatCoinAmount(rd.totalBurned),
		"blocks_processed":  rd.blockCount,
	}).Debug("Reward distribution statistics updated")

	return nil
}

// mintToAccount creates tokens and adds them to an account
//
// This is the only place where new tokens are created (minted).
// CRITICAL: Only called from DistributeBlockRewards to maintain supply integrity.
func (rd *RewardDistributor) mintToAccount(address [32]byte, amount uint64, purpose string) error {
	// Get current account state
	account, err := rd.stateManager.GetAccount(address)
	if err != nil {
		return fmt.Errorf("failed to get account: %w", err)
	}

	// Add reward to balance
	newBalance := account.Balance + amount

	// Update account state
	if err := rd.stateManager.UpdateAccount(address, newBalance, account.Nonce); err != nil {
		return fmt.Errorf("failed to update account: %w", err)
	}

	rd.log.WithFields(logger.Fields{
		"address":     fmt.Sprintf("%x", address[:8]),
		"amount":      FormatCoinAmount(amount),
		"new_balance": FormatCoinAmount(newBalance),
		"purpose":     purpose,
	}).Debug("Tokens minted to account")

	return nil
}

// GetStatistics returns reward distribution statistics
func (rd *RewardDistributor) GetStatistics() DistributorStats {
	return DistributorStats{
		TotalDistributed: rd.totalDistributed,
		TotalBurned:      rd.totalBurned,
		BlocksProcessed:  rd.blockCount,
		TreasuryAddress:  rd.treasuryAddress,
		BurnAddress:      rd.burnAddress,
	}
}

// DistributorStats holds reward distribution statistics
type DistributorStats struct {
	TotalDistributed uint64   // Total rewards distributed (wei)
	TotalBurned      uint64   // Total tokens burned (wei)
	BlocksProcessed  uint64   // Number of blocks processed
	TreasuryAddress  [32]byte // Treasury address
	BurnAddress      [32]byte // Burn address
}

// GetTreasuryBalance returns the current treasury balance
func (rd *RewardDistributor) GetTreasuryBalance() (uint64, error) {
	account, err := rd.stateManager.GetAccount(rd.treasuryAddress)
	if err != nil {
		return 0, fmt.Errorf("failed to get treasury account: %w", err)
	}
	return account.Balance, nil
}

// GetBurnedSupply returns the total burned supply (sent to burn address)
func (rd *RewardDistributor) GetBurnedSupply() (uint64, error) {
	account, err := rd.stateManager.GetAccount(rd.burnAddress)
	if err != nil {
		return 0, fmt.Errorf("failed to get burn account: %w", err)
	}
	return account.Balance, nil
}

// GetCirculatingSupply calculates the true circulating supply
//
// Circulating = Total Supply - Burned Tokens - Unvested Genesis Allocations
func (rd *RewardDistributor) GetCirculatingSupply(currentBlock uint64, vestingTracker *VestingTracker) (uint64, error) {
	metrics := rd.economics.GetMetrics()
	totalSupply := metrics.CurrentSupply

	// Subtract burned tokens
	burnedSupply, err := rd.GetBurnedSupply()
	if err != nil {
		return 0, fmt.Errorf("failed to get burned supply: %w", err)
	}

	// TODO: Subtract unvested genesis allocations if vesting tracker provided

	circulatingSupply := totalSupply - burnedSupply

	return circulatingSupply, nil
}
