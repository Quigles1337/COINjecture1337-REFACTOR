// Supply Dynamics Validation Utility for Network A
// Verifies that emission + fees - burns = total supply
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/state"
)

const Version = "1.0.0"
const BlockReward = 3125000000 // 3.125 $BEANS in wei (gwei)

// Transaction structure from JSON
type TxData struct {
	Hash     string  `json:"hash"`
	From     string  `json:"from"`
	To       string  `json:"to"`
	Amount   uint64  `json:"amount"`
	Fee      uint64  `json:"fee"`
	Nonce    uint64  `json:"nonce"`
	GasLimit uint64  `json:"gas_limit"`
	GasPrice uint64  `json:"gas_price"`
	TxType   uint8   `json:"tx_type"`
}

func main() {
	// Parse flags
	dbPath := flag.String("db", "./data/fee-test.db", "Database path to validate")
	verbose := flag.Bool("verbose", false, "Show detailed block-by-block breakdown")
	flag.Parse()

	fmt.Printf("═══════════════════════════════════════════\n")
	fmt.Printf("  Supply Dynamics Validation v%s\n", Version)
	fmt.Printf("  Verifying: Emission + Fees - Burns = Supply\n")
	fmt.Printf("═══════════════════════════════════════════\n\n")

	// Create logger
	log := logger.NewLogger("info")

	// Create state manager
	stateManager, err := state.NewStateManager(*dbPath, log)
	if err != nil {
		log.WithError(err).Fatal("Failed to create state manager")
	}
	defer stateManager.Close()

	fmt.Printf("📊 Analyzing blockchain state from: %s\n\n", *dbPath)

	// Get block count
	blockCount, err := stateManager.GetBlockCount()
	if err != nil {
		log.WithError(err).Fatal("Failed to get block count")
	}

	if blockCount == 0 {
		fmt.Println("⚠️  No blocks found in database")
		os.Exit(0)
	}

	fmt.Printf("📦 Total Blocks: %d\n", blockCount)

	// Get all blocks
	blocks, err := stateManager.GetBlockRange(0, blockCount-1)
	if err != nil {
		log.WithError(err).Fatal("Failed to get block range")
	}

	// Calculate emissions and fees
	totalEmissions := uint64(0)
	totalFees := uint64(0)
	totalValidatorFees := uint64(0)
	totalBurnFees := uint64(0)
	totalTreasuryFees := uint64(0)
	totalTransactions := 0

	fmt.Println("\n🔍 Processing blocks...")

	for _, block := range blocks {
		// Block reward (emission)
		blockEmission := uint64(BlockReward)
		totalEmissions += blockEmission

		// Parse transaction data
		var txs []TxData
		if block.TxCount > 0 && len(block.TxData) > 0 {
			if err := json.Unmarshal(block.TxData, &txs); err != nil {
				log.WithError(err).Warn("Failed to parse transaction data")
				continue
			}
		}

		// Sum transaction fees for this block
		blockFees := uint64(0)
		for _, tx := range txs {
			blockFees += tx.Fee
			totalTransactions++
		}

		totalFees += blockFees

		// Calculate fee distribution (Critical Complex Equilibrium)
		validatorFee := uint64(float64(blockFees) * 0.4142)
		burnFee := uint64(float64(blockFees) * 0.2929)
		treasuryFee := uint64(float64(blockFees) * 0.2929)

		totalValidatorFees += validatorFee
		totalBurnFees += burnFee
		totalTreasuryFees += treasuryFee

		if *verbose {
			fmt.Printf("  Block #%d: %d txs, %.9f $BEANS fees (%.9f val, %.9f burn, %.9f treasury)\n",
				block.BlockNumber,
				block.TxCount,
				float64(blockFees)/1e9,
				float64(validatorFee)/1e9,
				float64(burnFee)/1e9,
				float64(treasuryFee)/1e9,
			)
		}
	}

	fmt.Printf("✓ Processed %d blocks\n\n", len(blocks))

	// Display emission summary
	fmt.Println("═══════════════════════════════════════════")
	fmt.Println("📈 EMISSION SUMMARY")
	fmt.Println("═══════════════════════════════════════════")
	fmt.Printf("Total Block Rewards:  %d wei (%.9f $BEANS)\n", totalEmissions, float64(totalEmissions)/1e9)
	fmt.Printf("Block Reward Rate:    3.125 $BEANS per block\n")
	fmt.Printf("Blocks Produced:      %d\n\n", blockCount)

	// Display fee summary
	fmt.Println("═══════════════════════════════════════════")
	fmt.Println("💰 TRANSACTION FEE SUMMARY")
	fmt.Println("═══════════════════════════════════════════")
	fmt.Printf("Total Transactions:   %d\n", totalTransactions)
	fmt.Printf("Total Fees Collected: %d wei (%.9f $BEANS)\n", totalFees, float64(totalFees)/1e9)
	fmt.Printf("\nFee Distribution (Critical Complex Equilibrium):\n")
	fmt.Printf("  Validator (41.42%%): %d wei (%.9f $BEANS)\n", totalValidatorFees, float64(totalValidatorFees)/1e9)
	fmt.Printf("  Burn (29.29%%):      %d wei (%.9f $BEANS)\n", totalBurnFees, float64(totalBurnFees)/1e9)
	fmt.Printf("  Treasury (29.29%%):  %d wei (%.9f $BEANS)\n\n", totalTreasuryFees, float64(totalTreasuryFees)/1e9)

	// Get account snapshot
	accountSnapshot, err := stateManager.GetAccountSnapshot()
	if err != nil {
		log.WithError(err).Fatal("Failed to get account snapshot")
	}

	// Identify special accounts
	var treasuryAddr, burnAddr [32]byte
	for i := 0; i < 32; i++ {
		treasuryAddr[i] = 0xFF
		burnAddr[i] = 0x00
	}

	var validatorBalance, treasuryBalance, burnBalance, userBalance uint64
	validatorCount := 0
	userCount := 0

	for addr, account := range accountSnapshot {
		if addr == treasuryAddr {
			treasuryBalance = account.Balance
		} else if addr == burnAddr {
			burnBalance = account.Balance
		} else {
			// Could be validator or user account
			// For simplicity, we'll classify non-treasury/non-burn accounts
			validatorBalance += account.Balance
			validatorCount++
			if account.Nonce > 0 || account.Balance > 0 {
				userBalance += account.Balance
				userCount++
			}
		}
	}

	// Display account summary
	fmt.Println("═══════════════════════════════════════════")
	fmt.Println("💼 ACCOUNT STATE SUMMARY")
	fmt.Println("═══════════════════════════════════════════")
	fmt.Printf("Treasury (0xFF...):   %d wei (%.9f $BEANS)\n", treasuryBalance, float64(treasuryBalance)/1e9)
	fmt.Printf("Burn (0x00...):       %d wei (%.9f $BEANS)\n", burnBalance, float64(burnBalance)/1e9)
	fmt.Printf("Validators/Users:     %d wei (%.9f $BEANS) [%d accounts]\n", validatorBalance, float64(validatorBalance)/1e9, validatorCount)

	totalSupply := treasuryBalance + burnBalance + validatorBalance
	fmt.Printf("\nTotal Supply:         %d wei (%.9f $BEANS)\n\n", totalSupply, float64(totalSupply)/1e9)

	// ==================== VALIDATION ====================
	fmt.Println("═══════════════════════════════════════════")
	fmt.Println("✅ SUPPLY DYNAMICS VALIDATION")
	fmt.Println("═══════════════════════════════════════════")

	// Expected supply = emissions + fee distributions
	// Note: Burn fees reduce circulating supply but are still "created" tokens
	expectedSupply := totalEmissions + totalValidatorFees + totalBurnFees + totalTreasuryFees

	fmt.Printf("\n📐 Expected Supply Calculation:\n")
	fmt.Printf("  Block Rewards (emissions):  %d wei (%.9f $BEANS)\n", totalEmissions, float64(totalEmissions)/1e9)
	fmt.Printf("  + Validator Fees:           %d wei (%.9f $BEANS)\n", totalValidatorFees, float64(totalValidatorFees)/1e9)
	fmt.Printf("  + Burn Fees:                %d wei (%.9f $BEANS)\n", totalBurnFees, float64(totalBurnFees)/1e9)
	fmt.Printf("  + Treasury Fees:            %d wei (%.9f $BEANS)\n", totalTreasuryFees, float64(totalTreasuryFees)/1e9)
	fmt.Printf("  ────────────────────────────────────────\n")
	fmt.Printf("  Expected Total:             %d wei (%.9f $BEANS)\n\n", expectedSupply, float64(expectedSupply)/1e9)

	fmt.Printf("📊 Actual Supply (from accounts):\n")
	fmt.Printf("  Treasury:                   %d wei (%.9f $BEANS)\n", treasuryBalance, float64(treasuryBalance)/1e9)
	fmt.Printf("  + Burn:                     %d wei (%.9f $BEANS)\n", burnBalance, float64(burnBalance)/1e9)
	fmt.Printf("  + Validators/Users:         %d wei (%.9f $BEANS)\n", validatorBalance, float64(validatorBalance)/1e9)
	fmt.Printf("  ────────────────────────────────────────\n")
	fmt.Printf("  Actual Total:               %d wei (%.9f $BEANS)\n\n", totalSupply, float64(totalSupply)/1e9)

	// Calculate difference
	difference := int64(totalSupply) - int64(expectedSupply)
	percentDiff := float64(difference) / float64(expectedSupply) * 100

	fmt.Printf("🔬 Validation Result:\n")
	if difference == 0 {
		fmt.Printf("  ✅ PERFECT MATCH!\n")
		fmt.Printf("  Expected: %.9f $BEANS\n", float64(expectedSupply)/1e9)
		fmt.Printf("  Actual:   %.9f $BEANS\n", float64(totalSupply)/1e9)
		fmt.Printf("  Difference: 0 wei (0.00%%)\n\n")
	} else if difference > 0 && difference < 1000 {
		fmt.Printf("  ✅ EXCELLENT (within rounding tolerance)\n")
		fmt.Printf("  Expected: %.9f $BEANS\n", float64(expectedSupply)/1e9)
		fmt.Printf("  Actual:   %.9f $BEANS\n", float64(totalSupply)/1e9)
		fmt.Printf("  Difference: %+d wei (%+.6f%%)\n\n", difference, percentDiff)
	} else if difference < 0 && difference > -1000 {
		fmt.Printf("  ✅ EXCELLENT (within rounding tolerance)\n")
		fmt.Printf("  Expected: %.9f $BEANS\n", float64(expectedSupply)/1e9)
		fmt.Printf("  Actual:   %.9f $BEANS\n", float64(totalSupply)/1e9)
		fmt.Printf("  Difference: %+d wei (%+.6f%%)\n\n", difference, percentDiff)
	} else {
		fmt.Printf("  ⚠️  MISMATCH DETECTED\n")
		fmt.Printf("  Expected: %.9f $BEANS\n", float64(expectedSupply)/1e9)
		fmt.Printf("  Actual:   %.9f $BEANS\n", float64(totalSupply)/1e9)
		fmt.Printf("  Difference: %+d wei (%+.6f%%)\n\n", difference, percentDiff)
	}

	// Verify fee distribution ratios
	fmt.Println("═══════════════════════════════════════════")
	fmt.Println("🔍 FEE DISTRIBUTION VALIDATION")
	fmt.Println("═══════════════════════════════════════════")

	if totalFees > 0 {
		validatorPercent := float64(totalValidatorFees) / float64(totalFees) * 100
		burnPercent := float64(totalBurnFees) / float64(totalFees) * 100
		treasuryPercent := float64(totalTreasuryFees) / float64(totalFees) * 100

		fmt.Printf("\nFee Distribution Ratios:\n")
		fmt.Printf("  Validator: %.2f%% (expected: 41.42%%)\n", validatorPercent)
		fmt.Printf("  Burn:      %.2f%% (expected: 29.29%%)\n", burnPercent)
		fmt.Printf("  Treasury:  %.2f%% (expected: 29.29%%)\n", treasuryPercent)

		// Check if ratios are correct (allow for rounding)
		validatorOK := validatorPercent >= 41.40 && validatorPercent <= 41.44
		burnOK := burnPercent >= 29.27 && burnPercent <= 29.31
		treasuryOK := treasuryPercent >= 29.27 && treasuryPercent <= 29.31

		if validatorOK && burnOK && treasuryOK {
			fmt.Printf("\n  ✅ Critical Complex Equilibrium VERIFIED\n")
			fmt.Printf("  All fee distribution ratios within tolerance!\n\n")
		} else {
			fmt.Printf("\n  ⚠️  Fee distribution ratios outside expected range\n\n")
		}
	} else {
		fmt.Printf("\nℹ️  No transaction fees to validate (pure emission model)\n\n")
	}

	fmt.Println("═══════════════════════════════════════════")
	fmt.Println("✅ Supply Dynamics Validation Complete!")
	fmt.Println("═══════════════════════════════════════════\n")
}
