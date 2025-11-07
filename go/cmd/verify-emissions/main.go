// Emission Verification Tool
// Calculates total emissions across all halvings to verify cap at ≤11M BEANS

package main

import (
	"fmt"
)

const (
	WeiPerCoin          = 1_000_000_000 // 10^9 wei = 1 BEANS
	MaxSupply           = 21_000_000 * WeiPerCoin
	GenesisSupply       = 10_000_000 * WeiPerCoin
	AvailableForEmission = MaxSupply - GenesisSupply // 11M BEANS
	InitialBlockReward  = 3_125_000_000              // 3.125 BEANS
	RewardHalvingBlocks = 1_051_200                  // ~24.3 days at 2s blocks
	MinBlockReward      = 100_000_000                // 0.1 BEANS
)

func formatBeans(wei uint64) string {
	coins := float64(wei) / float64(WeiPerCoin)
	if coins >= 1_000_000 {
		return fmt.Sprintf("%.2fM", coins/1_000_000)
	} else if coins >= 1000 {
		return fmt.Sprintf("%.2fK", coins/1000)
	}
	return fmt.Sprintf("%.4f", coins)
}

func main() {
	fmt.Println("═══════════════════════════════════════════════════════")
	fmt.Println("  $BEANS Emission Verification")
	fmt.Println("  Confirming cumulative emissions ≤ 11M BEANS")
	fmt.Println("═══════════════════════════════════════════════════════")
	fmt.Println()

	fmt.Printf("Genesis Supply:        %s BEANS\n", formatBeans(GenesisSupply))
	fmt.Printf("Max Supply:            %s BEANS\n", formatBeans(MaxSupply))
	fmt.Printf("Available to Emit:     %s BEANS\n", formatBeans(AvailableForEmission))
	fmt.Printf("Initial Block Reward:  %s BEANS\n", formatBeans(InitialBlockReward))
	fmt.Printf("Halving Interval:      %d blocks (~%.1f days)\n", RewardHalvingBlocks, float64(RewardHalvingBlocks*2)/86400.0)
	fmt.Printf("Minimum Block Reward:  %s BEANS\n", formatBeans(MinBlockReward))
	fmt.Println()

	fmt.Println("═══════════════════════════════════════════════════════")
	fmt.Println("  Emission Schedule by Period")
	fmt.Println("═══════════════════════════════════════════════════════")
	fmt.Println()

	currentReward := InitialBlockReward
	totalEmitted := uint64(0)
	period := 1
	startBlock := uint64(0)

	fmt.Printf("%-8s %-15s %-15s %-15s %-15s %-15s\n",
		"Period", "Start Block", "End Block", "Reward/Block", "Period Total", "Cumulative")
	fmt.Println("─────────────────────────────────────────────────────────────────────────────────────")

	for currentReward >= MinBlockReward {
		endBlock := startBlock + RewardHalvingBlocks - 1
		periodEmission := uint64(currentReward) * uint64(RewardHalvingBlocks)
		totalEmitted += periodEmission

		fmt.Printf("%-8d %-15d %-15d %-15s %-15s %-15s\n",
			period,
			startBlock,
			endBlock,
			formatBeans(uint64(currentReward)),
			formatBeans(periodEmission),
			formatBeans(totalEmitted),
		)

		// Check if we've exceeded available supply
		if totalEmitted > AvailableForEmission {
			fmt.Println()
			fmt.Println("⚠️  WARNING: Emissions exceed available supply!")
			fmt.Printf("   Total Emitted: %s BEANS\n", formatBeans(totalEmitted))
			fmt.Printf("   Available:     %s BEANS\n", formatBeans(AvailableForEmission))
			fmt.Printf("   Overflow:      %s BEANS\n", formatBeans(totalEmitted-AvailableForEmission))
			return
		}

		// Next period
		startBlock = endBlock + 1
		currentReward = currentReward / 2
		period++

		// Safety limit (prevent infinite loop)
		if period > 50 {
			fmt.Println()
			fmt.Println("⚠️  Safety limit reached (50 periods)")
			break
		}
	}

	fmt.Println()
	fmt.Println("═══════════════════════════════════════════════════════")
	fmt.Println("  VERIFICATION SUMMARY")
	fmt.Println("═══════════════════════════════════════════════════════")
	fmt.Println()

	remainingSupply := AvailableForEmission - totalEmitted
	utilizationPct := float64(totalEmitted) / float64(AvailableForEmission) * 100

	fmt.Printf("Total Periods:         %d\n", period-1)
	fmt.Printf("Total Blocks:          %d (~%.1f days at 2s blocks)\n",
		startBlock, float64(startBlock*2)/86400.0)
	fmt.Printf("Total Emitted:         %s BEANS\n", formatBeans(totalEmitted))
	fmt.Printf("Available to Emit:     %s BEANS\n", formatBeans(AvailableForEmission))
	fmt.Printf("Remaining Supply:      %s BEANS\n", formatBeans(remainingSupply))
	fmt.Printf("Supply Utilization:    %.2f%%\n", utilizationPct)
	fmt.Println()

	if totalEmitted <= AvailableForEmission {
		fmt.Println("✅ VERIFICATION PASSED!")
		fmt.Printf("   Emissions stay within available supply (%.2f%% utilized)\n", utilizationPct)
		fmt.Println()
		fmt.Printf("Final Supply:          %s BEANS (genesis) + %s BEANS (emitted) = %s BEANS\n",
			formatBeans(GenesisSupply),
			formatBeans(totalEmitted),
			formatBeans(GenesisSupply+totalEmitted),
		)
		fmt.Printf("Max Supply Cap:        %s BEANS\n", formatBeans(MaxSupply))
		fmt.Println()
		fmt.Println("   The emission schedule respects the 21M BEANS hard cap! 🎯")
	} else {
		fmt.Println("❌ VERIFICATION FAILED!")
		fmt.Println("   Emissions exceed available supply")
	}

	fmt.Println()
}
