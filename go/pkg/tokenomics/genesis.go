// Genesis allocation and initial token distribution
package tokenomics

import (
	"fmt"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/state"
)

// GenesisAllocation represents initial token distribution
type GenesisAllocation struct {
	Address     [32]byte // Recipient address
	Amount      uint64   // Amount in wei
	Description string   // Purpose (e.g., "Team", "Liquidity", "Treasury")
	Vesting     *VestingSchedule // Optional vesting schedule
}

// VestingSchedule defines token unlock schedule
type VestingSchedule struct {
	StartBlock    uint64  // When vesting starts
	CliffBlocks   uint64  // Cliff period (no unlock)
	VestingBlocks uint64  // Total vesting duration
	InitialUnlock float64 // % unlocked immediately (0.0 - 1.0)
}

// DefaultGenesisAllocations returns institutional-grade initial distribution
//
// Total: 10,000,000 $BEANS (10M of 21M max supply)
//
// Breakdown:
// - 30% Team & Advisors (3M $BEANS) - 1 year cliff, 4 year vesting
// - 20% Foundation/Treasury (2M $BEANS) - No vesting (operational funds)
// - 15% Early Backers (1.5M $BEANS) - 6 month cliff, 2 year vesting
// - 15% Ecosystem Development (1.5M $BEANS) - No vesting (grants, partnerships)
// - 10% Liquidity Pools (1M $BEANS) - No vesting (DEX liquidity)
// - 10% Community Rewards (1M $BEANS) - No vesting (airdrops, competitions)
func DefaultGenesisAllocations(
	teamAddr, foundationAddr, backersAddr, ecosystemAddr, liquidityAddr, communityAddr [32]byte,
) []GenesisAllocation {

	blocksPerMonth := uint64(30 * 24 * 60 * 60 / 2) // ~1,296,000 blocks at 2s
	blocksPerYear := blocksPerMonth * 12             // ~15,552,000 blocks

	return []GenesisAllocation{
		// Team & Advisors: 3M $BEANS with 1 year cliff, 4 year vesting
		{
			Address:     teamAddr,
			Amount:      3_000_000 * WeiPerCoin,
			Description: "Team & Advisors",
			Vesting: &VestingSchedule{
				StartBlock:    0,
				CliffBlocks:   blocksPerYear,     // 1 year cliff
				VestingBlocks: blocksPerYear * 4, // 4 year vesting
				InitialUnlock: 0.0,               // Nothing unlocked initially
			},
		},

		// Foundation/Treasury: 2M $BEANS unlocked immediately
		{
			Address:     foundationAddr,
			Amount:      2_000_000 * WeiPerCoin,
			Description: "Foundation & Treasury",
			Vesting:     nil, // Fully unlocked
		},

		// Early Backers: 1.5M $BEANS with 6 month cliff, 2 year vesting
		{
			Address:     backersAddr,
			Amount:      1_500_000 * WeiPerCoin,
			Description: "Early Backers & Investors",
			Vesting: &VestingSchedule{
				StartBlock:    0,
				CliffBlocks:   blocksPerMonth * 6, // 6 month cliff
				VestingBlocks: blocksPerYear * 2,  // 2 year vesting
				InitialUnlock: 0.0,
			},
		},

		// Ecosystem Development: 1.5M $BEANS unlocked immediately
		{
			Address:     ecosystemAddr,
			Amount:      1_500_000 * WeiPerCoin,
			Description: "Ecosystem Development (Grants & Partnerships)",
			Vesting:     nil, // Fully unlocked
		},

		// Liquidity Pools: 1M $BEANS unlocked immediately
		{
			Address:     liquidityAddr,
			Amount:      1_000_000 * WeiPerCoin,
			Description: "Liquidity Pools (DEX & Market Making)",
			Vesting:     nil, // Fully unlocked
		},

		// Community Rewards: 1M $BEANS unlocked immediately
		{
			Address:     communityAddr,
			Amount:      1_000_000 * WeiPerCoin,
			Description: "Community Rewards (Airdrops & Competitions)",
			Vesting:     nil, // Fully unlocked
		},
	}
}

// ApplyGenesisAllocations applies genesis allocations to state
func ApplyGenesisAllocations(
	allocations []GenesisAllocation,
	stateManager *state.StateManager,
	log *logger.Logger,
) error {

	var totalAllocated uint64

	for i, alloc := range allocations {
		// Create account with allocation
		if err := stateManager.CreateAccount(alloc.Address, alloc.Amount); err != nil {
			return fmt.Errorf("failed to create genesis account %d: %w", i, err)
		}

		totalAllocated += alloc.Amount

		vestingInfo := "Fully unlocked"
		if alloc.Vesting != nil {
			vestingInfo = fmt.Sprintf("Vesting: cliff=%d blocks, duration=%d blocks, initial=%.1f%%",
				alloc.Vesting.CliffBlocks,
				alloc.Vesting.VestingBlocks,
				alloc.Vesting.InitialUnlock*100,
			)
		}

		log.WithFields(logger.Fields{
			"address":     fmt.Sprintf("%x", alloc.Address[:8]),
			"amount":      FormatCoinAmount(alloc.Amount),
			"description": alloc.Description,
			"vesting":     vestingInfo,
		}).Info("Genesis allocation created")
	}

	log.WithFields(logger.Fields{
		"total_allocated": FormatCoinAmount(totalAllocated),
		"accounts":        len(allocations),
	}).Info("All genesis allocations applied successfully")

	return nil
}

// CalculateVestedAmount calculates how much has vested at a given block
func CalculateVestedAmount(
	allocation GenesisAllocation,
	currentBlock uint64,
) uint64 {

	// No vesting schedule = fully unlocked
	if allocation.Vesting == nil {
		return allocation.Amount
	}

	v := allocation.Vesting

	// Before vesting starts
	if currentBlock < v.StartBlock {
		return 0
	}

	// During cliff period
	blocksSinceStart := currentBlock - v.StartBlock
	if blocksSinceStart < v.CliffBlocks {
		// Only initial unlock available
		return uint64(float64(allocation.Amount) * v.InitialUnlock)
	}

	// After full vesting period
	if blocksSinceStart >= v.VestingBlocks {
		return allocation.Amount // Fully vested
	}

	// During vesting period (linear vesting)
	vestingProgress := float64(blocksSinceStart-v.CliffBlocks) / float64(v.VestingBlocks-v.CliffBlocks)

	initialUnlocked := uint64(float64(allocation.Amount) * v.InitialUnlock)
	vestingAmount := allocation.Amount - initialUnlocked
	vestedAmount := uint64(float64(vestingAmount) * vestingProgress)

	return initialUnlocked + vestedAmount
}

// VestingTracker tracks vesting schedules for genesis allocations
type VestingTracker struct {
	allocations map[[32]byte]GenesisAllocation
	log         *logger.Logger
}

// NewVestingTracker creates a new vesting tracker
func NewVestingTracker(log *logger.Logger) *VestingTracker {
	return &VestingTracker{
		allocations: make(map[[32]byte]GenesisAllocation),
		log:         log,
	}
}

// AddAllocation registers a vesting allocation
func (vt *VestingTracker) AddAllocation(alloc GenesisAllocation) {
	if alloc.Vesting != nil {
		vt.allocations[alloc.Address] = alloc
		vt.log.WithFields(logger.Fields{
			"address": fmt.Sprintf("%x", alloc.Address[:8]),
			"amount":  FormatCoinAmount(alloc.Amount),
		}).Info("Vesting allocation registered")
	}
}

// GetVestedAmount returns the currently vested amount for an address
func (vt *VestingTracker) GetVestedAmount(address [32]byte, currentBlock uint64) uint64 {
	alloc, exists := vt.allocations[address]
	if !exists {
		return 0
	}
	return CalculateVestedAmount(alloc, currentBlock)
}

// IsVestingComplete checks if vesting is complete for an address
func (vt *VestingTracker) IsVestingComplete(address [32]byte, currentBlock uint64) bool {
	alloc, exists := vt.allocations[address]
	if !exists {
		return true // No vesting = already complete
	}

	if alloc.Vesting == nil {
		return true
	}

	blocksSinceStart := currentBlock - alloc.Vesting.StartBlock
	return blocksSinceStart >= alloc.Vesting.VestingBlocks
}
