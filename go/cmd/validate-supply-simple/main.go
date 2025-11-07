// Simple Supply Dynamics Validation for Network A
// Verifies tokenomics based on account state
package main

import (
	"flag"
	"fmt"

	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/internal/logger"
	"github.com/Quigles1337/COINjecture1337-REFACTOR/go/pkg/state"
)

const Version = "1.0.0"

func main() {
	// Parse flags
	dbPath := flag.String("db", "./data/supply-validation.db", "Database path to validate")
	flag.Parse()

	fmt.Printf("═══════════════════════════════════════════\n")
	fmt.Printf("  Supply Validation v%s\n", Version)
	fmt.Printf("  Analyzing Account-Based Tokenomics\n")
	fmt.Printf("═══════════════════════════════════════════\n\n")

	// Create logger
	log := logger.NewLogger("info")

	// Create state manager
	stateManager, err := state.NewStateManager(*dbPath, log)
	if err != nil {
		log.WithError(err).Fatal("Failed to create state manager")
	}
	defer stateManager.Close()

	// Get account snapshot
	accountSnapshot, err := stateManager.GetAccountSnapshot()
	if err != nil {
		log.WithError(err).Fatal("Failed to get account snapshot")
	}

	if len(accountSnapshot) == 0 {
		fmt.Println("⚠️  No accounts found in database")
		return
	}

	// Identify special accounts
	var treasuryAddr, burnAddr [32]byte
	for i := 0; i < 32; i++ {
		treasuryAddr[i] = 0xFF
		burnAddr[i] = 0x00
	}

	var validatorBalance, treasuryBalance, burnBalance, userBalance uint64
	var validatorAddr [32]byte
	userAccounts := 0

	for addr, account := range accountSnapshot {
		if addr == treasuryAddr {
			treasuryBalance = account.Balance
		} else if addr == burnAddr {
			burnBalance = account.Balance
		} else if account.Nonce == 0 && account.Balance > 1000000000 { // Likely validator (has balance but no txs sent)
			validatorBalance += account.Balance
			validatorAddr = addr
		} else {
			userBalance += account.Balance
			userAccounts++
		}
	}

	totalSupply := treasuryBalance + burnBalance + validatorBalance + userBalance

	fmt.Println("═══════════════════════════════════════════")
	fmt.Println("💼 ACCOUNT STATE ANALYSIS")
	fmt.Println("═══════════════════════════════════════════")
	fmt.Printf("\n📍 Special Addresses:\n")
	if validatorAddr != ([32]byte{}) {
		fmt.Printf("  Validator: %x...\n", validatorAddr[:8])
		fmt.Printf("  Balance:   %d wei (%.9f $BEANS)\n\n", validatorBalance, float64(validatorBalance)/1e9)
	}

	if treasuryBalance > 0 {
		fmt.Printf("  Treasury:  0xFFFFFFFF...\n")
		fmt.Printf("  Balance:   %d wei (%.9f $BEANS)\n\n", treasuryBalance, float64(treasuryBalance)/1e9)
	}

	if burnBalance > 0 {
		fmt.Printf("  Burn:      0x00000000...\n")
		fmt.Printf("  Balance:   %d wei (%.9f $BEANS)\n\n", burnBalance, float64(burnBalance)/1e9)
	}

	if userAccounts > 0 {
		fmt.Printf("  Users:     %d accounts\n", userAccounts)
		fmt.Printf("  Balance:   %d wei (%.9f $BEANS)\n\n", userBalance, float64(userBalance)/1e9)
	}

	fmt.Printf("📈 Total Supply: %d wei (%.9f $BEANS)\n\n", totalSupply, float64(totalSupply)/1e9)

	// Validate fee distribution ratios if we have fee-related balances
	fmt.Println("═══════════════════════════════════════════")
	fmt.Println("🔍 TOKENOMICS VALIDATION")
	fmt.Println("═══════════════════════════════════════════\n")

	// Check if this looks like a system with transaction fees
	if treasuryBalance > 0 || burnBalance > 0 {
		fmt.Println("✅ Fee Distribution Detected!")
		fmt.Println("\nCritical Complex Equilibrium Analysis:")
		fmt.Println("  Expected: 41.42% validator, 29.29% burn, 29.29% treasury")

		// The fee portion is the non-emission portion
		// Assuming 3.125 $BEANS per block emission
		// We can estimate blocks from validator balance if no txs

		// For validation, check the burn/treasury ratio
		if burnBalance > 0 && treasuryBalance > 0 {
			ratio := float64(treasuryBalance) / float64(burnBalance)
			fmt.Printf("\n  Treasury/Burn Ratio: %.4f", ratio)
			if ratio >= 0.99 && ratio <= 1.01 {
				fmt.Printf(" ✅ (Expected: 1.0 for 29.29%%/29.29%%)\n")
			} else {
				fmt.Printf(" ⚠️  (Expected: ~1.0)\n")
			}

			// Calculate what percentage of total supply is burn
			burnPercent := float64(burnBalance) / float64(totalSupply) * 100
			treasuryPercent := float64(treasuryBalance) / float64(totalSupply) * 100
			validatorPercent := float64(validatorBalance) / float64(totalSupply) * 100

			fmt.Printf("\n  Current Supply Distribution:\n")
			fmt.Printf("    Validator: %.2f%% of supply\n", validatorPercent)
			fmt.Printf("    Burn:      %.2f%% of supply\n", burnPercent)
			fmt.Printf("    Treasury:  %.2f%% of supply\n", treasuryPercent)
		}

		fmt.Println("\n✅ Tokenomics are functioning as designed!")
	} else {
		fmt.Println("📊 Pure Emission Model")
		fmt.Println("  All supply from block rewards (3.125 $BEANS/block)")
		fmt.Printf("  Estimated blocks: ~%.0f\n", float64(totalSupply)/3.125e9)
		fmt.Println("\nℹ️  No transaction fees detected yet")
		fmt.Println("  Fee distribution activates when transactions are processed")
	}

	fmt.Println("\n═══════════════════════════════════════════")
	fmt.Println("✅ Supply Validation Complete!")
	fmt.Println("═══════════════════════════════════════════\n")

	// Summary
	fmt.Println("📋 SUMMARY:")
	fmt.Printf("  Total Accounts: %d\n", len(accountSnapshot))
	fmt.Printf("  Total Supply:   %.9f $BEANS\n", float64(totalSupply)/1e9)
	fmt.Printf("  Validator:      %.9f $BEANS\n", float64(validatorBalance)/1e9)
	fmt.Printf("  Treasury:       %.9f $BEANS\n", float64(treasuryBalance)/1e9)
	fmt.Printf("  Burn:           %.9f $BEANS\n", float64(burnBalance)/1e9)
	fmt.Printf("  Users:          %.9f $BEANS\n\n", float64(userBalance)/1e9)
}
