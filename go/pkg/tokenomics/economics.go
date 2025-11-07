// Package tokenomics - Institutional-grade token economics and distribution
//
// This module handles all token distribution mechanics including:
// - Block rewards (validator compensation)
// - Transaction fee distribution
// - Emission schedule (inflation control)
// - Genesis allocation
// - Treasury/foundation allocations
//
// CRITICAL: All amounts are in WEI (smallest unit, 1 BEANS = 10^9 WEI)
package tokenomics

import (
	"fmt"
	"math/big"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
)

// WEI conversion constants
// Using 10^9 (Gwei-style) to fit within uint64 limits
const (
	WeiPerCoin = 1_000_000_000 // 10^9 wei = 1 BEANS (fits in uint64)
)

// Critical Complex Equilibrium Constants
// Based on "Proof of Critical Complex Equilibrium" by Sarah Marin (October 18, 2025)
//
// Mathematical Foundation:
//   μ = -η + iλ (eigenvalue definition)
//   |μ|² = η² + λ² = 1 (balance condition - unit circle)
//   |Re(μ)| = |Im(μ)| ⇒ η = λ (perfect balance)
//   2λ² = 1 ⇒ λ = η = 1/√2 ≈ 0.7071
//
// At this equilibrium point, the real (damping/stability) and imaginary (coupling/incentive)
// components are equal in magnitude, representing perfect balance in the complex domain.
//
// For fee distribution on a unit sphere (validator² + burn² + treasury² = 1):
//   - Validator (damping): cos(45°) = 1/√2
//   - Burn & Treasury (coupling): sin(45°) × [cos(45°), sin(45°)] = [1/2, 1/2]
//   - Normalized to sum to 100%: divide by (1/√2 + 1)
const (
	// CriticalConstant is the universal equilibrium constant λ = η = 1/√2
	CriticalConstant = 0.707106781186547524 // High precision for consensus-critical calculations

	// SqrtTwo is √2 for unit circle calculations
	SqrtTwo = 1.41421356237309504 // √2

	// OnePlusSqrtTwo is 1 + √2, used for normalization
	OnePlusSqrtTwo = 2.41421356237309504 // 1 + √2

	// UnitCircleNormalization is 1/(1 + √2) for normalizing to unit circle bounds
	UnitCircleNormalization = 0.414213562373095048 // 1/(1 + √2) = 2 - √2
)

// TokenomicsConfig defines the economic parameters of the blockchain
type TokenomicsConfig struct {
	// Genesis allocation (in wei)
	GenesisSupply uint64 // Initial circulating supply (0 for pure emission model)

	// Block rewards
	InitialBlockReward uint64        // Starting reward per block (in wei)
	RewardHalvingBlocks uint64       // Blocks between halvings
	MinBlockReward     uint64        // Minimum reward (never goes below this)

	// Fee distribution
	ValidatorFeeShare float64 // % of fees to validator (0.0 - 1.0)
	BurnFeeShare      float64 // % of fees to burn (deflationary)
	TreasuryFeeShare  float64 // % of fees to treasury

	// Treasury
	TreasuryAddress [32]byte // Treasury address for development/grants
}

// DefaultTokenomicsConfig returns institutional-grade default parameters
func DefaultTokenomicsConfig() TokenomicsConfig {
	return TokenomicsConfig{
		// No genesis allocation - pure emission model
		GenesisSupply: 0,

		// Block rewards: Start at 3.125 BEANS per block (Bitcoin-style)
		// No hard cap - supply grows via emissions, controlled by equilibrium burns
		InitialBlockReward: 3_125_000_000, // 3.125 BEANS (3.125 * 10^9 wei)

		// Halving every 1,051,200 blocks (~24.3 days at 2s blocks)
		RewardHalvingBlocks: 1_051_200,

		// Minimum reward: 0.1 BEANS (never goes below this for security)
		MinBlockReward: 100_000_000, // 0.1 BEANS

		// Fee distribution based on Critical Complex Equilibrium (λ = η = 1/√2)
		// with unit circle constraint: validator² + burn² + treasury² = 1
		//
		// Raw values (on unit sphere):
		//   - Validator (stability): 1/√2 ≈ 0.7071
		//   - Burn (coupling): 1/2 = 0.5
		//   - Treasury (coupling): 1/2 = 0.5
		//   - Sum: 1/√2 + 1 = (1 + √2)/√2 ≈ 1.7071
		//
		// Normalized percentages (sum to 100%):
		//   - Validator: 1/(1+√2) ≈ 41.42%
		//   - Burn: √2/(2(1+√2)) ≈ 29.29%
		//   - Treasury: √2/(2(1+√2)) ≈ 29.29%
		ValidatorFeeShare: UnitCircleNormalization,                    // 41.42% = 1/(1+√2)
		BurnFeeShare:      CriticalConstant * UnitCircleNormalization, // 29.29% = (1/√2)/(1+√2)
		TreasuryFeeShare:  CriticalConstant * UnitCircleNormalization, // 29.29% = (1/√2)/(1+√2)

		// Treasury address (set during initialization)
		TreasuryAddress: [32]byte{},
	}
}

// Economics manages token distribution and supply
type Economics struct {
	config TokenomicsConfig
	log    *logger.Logger

	// Current state
	currentSupply  *big.Int // Total circulating supply (in wei)
	totalBurned    *big.Int // Total tokens burned (deflationary)
	totalRewarded  *big.Int // Total rewards distributed to validators
	totalFees      *big.Int // Total fees collected
	blockHeight    uint64   // Current block height
}

// NewEconomics creates a new token economics manager
func NewEconomics(cfg TokenomicsConfig, log *logger.Logger) *Economics {
	return &Economics{
		config:        cfg,
		log:           log,
		currentSupply: big.NewInt(int64(cfg.GenesisSupply)),
		totalBurned:   big.NewInt(0),
		totalRewarded: big.NewInt(0),
		totalFees:     big.NewInt(0),
		blockHeight:   0,
	}
}

// CalculateBlockReward calculates the reward for a given block height
//
// Uses halving schedule similar to Bitcoin:
// - Reward halves every RewardHalvingBlocks
// - Never goes below MinBlockReward
func (e *Economics) CalculateBlockReward(blockHeight uint64) uint64 {
	// Calculate number of halvings
	halvings := blockHeight / e.config.RewardHalvingBlocks

	// Start with initial reward
	reward := e.config.InitialBlockReward

	// Apply halvings (bit shift right = divide by 2)
	for i := uint64(0); i < halvings; i++ {
		reward = reward / 2

		// Stop at minimum reward
		if reward <= e.config.MinBlockReward {
			return e.config.MinBlockReward
		}
	}

	return reward
}

// DistributeBlockReward distributes rewards for a newly produced block
//
// Returns:
// - validatorReward: Amount to pay the validator
// - burnAmount: Amount to burn (from fees)
// - treasuryAmount: Amount to send to treasury (from fees)
func (e *Economics) DistributeBlockReward(
	blockHeight uint64,
	validator [32]byte,
	totalFees uint64,
) (validatorReward, burnAmount, treasuryAmount uint64) {

	// Calculate base block reward (new token emission)
	baseReward := e.CalculateBlockReward(blockHeight)

	// Calculate fee distribution
	validatorFeeReward := uint64(float64(totalFees) * e.config.ValidatorFeeShare)
	burnAmount = uint64(float64(totalFees) * e.config.BurnFeeShare)
	treasuryAmount = uint64(float64(totalFees) * e.config.TreasuryFeeShare)

	// Validator gets: base reward + fee share
	validatorReward = baseReward + validatorFeeReward

	// Update state (no hard cap - supply grows via emissions)
	e.currentSupply.Add(e.currentSupply, big.NewInt(int64(baseReward)))
	e.totalRewarded.Add(e.totalRewarded, big.NewInt(int64(validatorReward)))
	e.totalFees.Add(e.totalFees, big.NewInt(int64(totalFees)))
	e.totalBurned.Add(e.totalBurned, big.NewInt(int64(burnAmount)))
	e.blockHeight = blockHeight

	e.log.WithFields(logger.Fields{
		"block_height":      blockHeight,
		"validator":         fmt.Sprintf("%x", validator[:8]),
		"base_reward":       formatWei(baseReward),
		"validator_reward":  formatWei(validatorReward),
		"fees_collected":    formatWei(totalFees),
		"burned":            formatWei(burnAmount),
		"treasury":          formatWei(treasuryAmount),
		"current_supply":    formatWei(e.currentSupply.Uint64()),
	}).Info("Block reward distributed")

	return validatorReward, burnAmount, treasuryAmount
}

// GetEmissionSchedule returns the emission schedule for the next N blocks
func (e *Economics) GetEmissionSchedule(startBlock, numBlocks uint64) []EmissionPeriod {
	schedule := []EmissionPeriod{}

	currentReward := e.CalculateBlockReward(startBlock)
	periodStart := startBlock

	for i := uint64(0); i < numBlocks; i++ {
		blockNum := startBlock + i
		reward := e.CalculateBlockReward(blockNum)

		// New period when reward changes (halving)
		if reward != currentReward {
			schedule = append(schedule, EmissionPeriod{
				StartBlock: periodStart,
				EndBlock:   blockNum - 1,
				Reward:     currentReward,
				TotalEmission: currentReward * (blockNum - periodStart),
			})

			periodStart = blockNum
			currentReward = reward
		}
	}

	// Add final period
	if periodStart < startBlock+numBlocks {
		schedule = append(schedule, EmissionPeriod{
			StartBlock: periodStart,
			EndBlock:   startBlock + numBlocks - 1,
			Reward:     currentReward,
			TotalEmission: currentReward * (startBlock + numBlocks - periodStart),
		})
	}

	return schedule
}

// EstimateSupplyAtBlock estimates total supply at a given block height
func (e *Economics) EstimateSupplyAtBlock(blockHeight uint64) *big.Int {
	supply := big.NewInt(int64(e.config.GenesisSupply))

	// Sum all rewards up to this block (no cap)
	for i := uint64(0); i < blockHeight; i++ {
		reward := e.CalculateBlockReward(i)
		supply.Add(supply, big.NewInt(int64(reward)))
	}

	return supply
}

// GetMetrics returns current economic metrics
func (e *Economics) GetMetrics() EconomicsMetrics {
	return EconomicsMetrics{
		CurrentSupply:      e.currentSupply.Uint64(),
		TotalBurned:        e.totalBurned.Uint64(),
		TotalRewarded:      e.totalRewarded.Uint64(),
		TotalFees:          e.totalFees.Uint64(),
		CurrentBlockHeight: e.blockHeight,
		CurrentBlockReward: e.CalculateBlockReward(e.blockHeight),
		InflationRate:      e.calculateInflationRate(),
	}
}

// calculateInflationRate estimates annual inflation rate
func (e *Economics) calculateInflationRate() float64 {
	if e.currentSupply.Uint64() == 0 {
		return 0.0
	}

	// Blocks per year at 2s block time
	blocksPerYear := uint64(365 * 24 * 60 * 60 / 2) // ~15,768,000 blocks

	// Estimate new supply in one year
	futureSupply := e.EstimateSupplyAtBlock(e.blockHeight + blocksPerYear)

	// Calculate inflation rate
	inflationAmount := new(big.Int).Sub(futureSupply, e.currentSupply)
	inflationRate := float64(inflationAmount.Uint64()) / float64(e.currentSupply.Uint64())

	return inflationRate * 100 // Return as percentage
}

// EmissionPeriod represents a period with constant block reward
type EmissionPeriod struct {
	StartBlock    uint64 // First block in period
	EndBlock      uint64 // Last block in period
	Reward        uint64 // Reward per block (in wei)
	TotalEmission uint64 // Total tokens emitted in period (in wei)
}

// EconomicsMetrics holds economic statistics
type EconomicsMetrics struct {
	CurrentSupply      uint64  // Current circulating supply (wei)
	TotalBurned        uint64  // Total burned tokens (wei)
	TotalRewarded      uint64  // Total rewards paid to validators (wei)
	TotalFees          uint64  // Total fees collected (wei)
	CurrentBlockHeight uint64  // Current block height
	CurrentBlockReward uint64  // Current block reward (wei)
	InflationRate      float64 // Estimated annual inflation rate (%)
}

// formatWei formats wei amount as human-readable $BEANS
func formatWei(wei uint64) string {
	if wei == 0 {
		return "0 $BEANS"
	}

	coins := float64(wei) / float64(WeiPerCoin)

	if coins >= 1000000 {
		return fmt.Sprintf("%.2fM $BEANS", coins/1000000)
	} else if coins >= 1000 {
		return fmt.Sprintf("%.2fK $BEANS", coins/1000)
	} else if coins >= 1 {
		return fmt.Sprintf("%.4f $BEANS", coins)
	} else {
		return fmt.Sprintf("%.8f $BEANS", coins)
	}
}

// ParseCoinAmount converts human-readable amount to wei
func ParseCoinAmount(amount float64) uint64 {
	return uint64(amount * float64(WeiPerCoin))
}

// FormatCoinAmount converts wei to human-readable $BEANS
func FormatCoinAmount(wei uint64) string {
	return formatWei(wei)
}
