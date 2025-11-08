// Dynamic Fee Market (EIP-1559 style)
// Adjusts base fee based on block congestion

use coinject_core::Balance;
use serde::{Deserialize, Serialize};

/// Fee market configuration
#[derive(Clone, Debug)]
pub struct FeeMarketConfig {
    /// Target transactions per block
    pub target_transactions: usize,
    /// Maximum transactions per block
    pub max_transactions: usize,
    /// Initial base fee
    pub initial_base_fee: Balance,
    /// Maximum base fee change per block (12.5% like EIP-1559)
    pub max_change_denominator: u64,
    /// Minimum base fee (floor)
    pub min_base_fee: Balance,
}

impl Default for FeeMarketConfig {
    fn default() -> Self {
        FeeMarketConfig {
            target_transactions: 100,
            max_transactions: 200,
            initial_base_fee: 1000,
            max_change_denominator: 8, // 1/8 = 12.5%
            min_base_fee: 100,
        }
    }
}

/// Fee market state tracker
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FeeMarket {
    /// Current base fee
    pub base_fee: Balance,
    /// Target transactions per block
    pub target_transactions: usize,
    /// Maximum transactions per block
    pub max_transactions: usize,
    /// Configuration
    #[serde(skip)]
    config: FeeMarketConfig,
}

impl FeeMarket {
    pub fn new(config: FeeMarketConfig) -> Self {
        FeeMarket {
            base_fee: config.initial_base_fee,
            target_transactions: config.target_transactions,
            max_transactions: config.max_transactions,
            config,
        }
    }

    /// Update base fee after a block is mined
    /// Based on EIP-1559 formula: base_fee_delta = base_fee * gas_used_delta / target / max_change_denominator
    pub fn update_base_fee(&mut self, transactions_in_block: usize) {
        let target = self.target_transactions as i64;
        let actual = transactions_in_block as i64;
        let delta = actual - target;

        if delta == 0 {
            return; // No change if exactly at target
        }

        let base = self.base_fee as i64;
        let denominator = self.config.max_change_denominator as i64;

        // Calculate change: base_fee * delta / target / denominator
        let numerator = base * delta;
        let change = numerator / target / denominator;

        // Apply change
        let new_base_fee = (base + change).max(self.config.min_base_fee as i64);
        self.base_fee = new_base_fee as Balance;
    }

    /// Calculate total fee for a transaction
    /// total_fee = base_fee + priority_fee
    pub fn calculate_total_fee(&self, priority_fee: Balance) -> Balance {
        self.base_fee + priority_fee
    }

    /// Check if transaction fee meets minimum requirements
    pub fn validate_fee(&self, total_fee: Balance, priority_fee: Balance) -> bool {
        total_fee >= self.base_fee + priority_fee && total_fee >= self.config.min_base_fee
    }

    /// Get the portion of fee that goes to miner
    /// Miner gets the priority fee (tip)
    pub fn get_miner_reward(&self, total_fee: Balance, priority_fee: Balance) -> Balance {
        priority_fee.min(total_fee)
    }

    /// Get the portion of fee that should be burned
    /// Burns everything except the miner's priority fee
    pub fn get_burn_amount(&self, total_fee: Balance, priority_fee: Balance) -> Balance {
        let miner = self.get_miner_reward(total_fee, priority_fee);
        total_fee.saturating_sub(miner)
    }

    /// Simulate next base fee given expected block fullness
    pub fn simulate_next_base_fee(&self, expected_transactions: usize) -> Balance {
        let mut simulated = self.clone();
        simulated.update_base_fee(expected_transactions);
        simulated.base_fee
    }
}

impl Default for FeeMarket {
    fn default() -> Self {
        Self::new(FeeMarketConfig::default())
    }
}

/// Transaction fee breakdown
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct FeeBreakdown {
    pub total_fee: Balance,
    pub base_fee: Balance,
    pub priority_fee: Balance,
    pub burn_amount: Balance,
    pub miner_reward: Balance,
}

impl FeeBreakdown {
    pub fn new(market: &FeeMarket, total_fee: Balance, priority_fee: Balance) -> Self {
        let burn_amount = market.get_burn_amount(total_fee, priority_fee);
        let miner_reward = market.get_miner_reward(total_fee, priority_fee);

        FeeBreakdown {
            total_fee,
            base_fee: market.base_fee,
            priority_fee,
            burn_amount,
            miner_reward,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_fee_market_initialization() {
        let market = FeeMarket::default();
        assert_eq!(market.base_fee, 1000);
        assert_eq!(market.target_transactions, 100);
    }

    #[test]
    fn test_base_fee_increase_on_congestion() {
        let mut market = FeeMarket::default();
        let initial_fee = market.base_fee;

        // Block is 50% over target (150 txs vs 100 target)
        market.update_base_fee(150);

        assert!(
            market.base_fee > initial_fee,
            "Base fee should increase when block is over target"
        );
    }

    #[test]
    fn test_base_fee_decrease_on_low_usage() {
        let mut market = FeeMarket::default();
        let initial_fee = market.base_fee;

        // Block is 50% under target (50 txs vs 100 target)
        market.update_base_fee(50);

        assert!(
            market.base_fee < initial_fee,
            "Base fee should decrease when block is under target"
        );
    }

    #[test]
    fn test_base_fee_stable_at_target() {
        let mut market = FeeMarket::default();
        let initial_fee = market.base_fee;

        // Block is exactly at target
        market.update_base_fee(100);

        assert_eq!(
            market.base_fee, initial_fee,
            "Base fee should remain stable at target"
        );
    }

    #[test]
    fn test_base_fee_floor() {
        let mut market = FeeMarket::default();
        market.base_fee = 150; // Set to near minimum

        // Very empty blocks should hit floor
        for _ in 0..10 {
            market.update_base_fee(0);
        }

        assert_eq!(
            market.base_fee, market.config.min_base_fee,
            "Base fee should not go below minimum"
        );
    }

    #[test]
    fn test_fee_validation() {
        let market = FeeMarket::default();

        // Valid fee (total >= base + priority)
        assert!(market.validate_fee(1500, 500));

        // Invalid fee (total < base)
        assert!(!market.validate_fee(500, 0));
    }

    #[test]
    fn test_fee_breakdown() {
        let market = FeeMarket::default();
        let total_fee = 2000;
        let priority_fee = 500;

        let breakdown = FeeBreakdown::new(&market, total_fee, priority_fee);

        assert_eq!(breakdown.total_fee, 2000);
        assert_eq!(breakdown.priority_fee, 500);
        assert_eq!(breakdown.miner_reward, 500);
        assert!(breakdown.burn_amount > 0);

        // Total should equal burn + miner reward
        assert_eq!(breakdown.burn_amount + breakdown.miner_reward, total_fee);
    }

    #[test]
    fn test_simulate_next_base_fee() {
        let market = FeeMarket::default();
        let current_fee = market.base_fee;

        // Simulate high congestion
        let next_fee_high = market.simulate_next_base_fee(180);
        assert!(next_fee_high > current_fee);

        // Simulate low congestion
        let next_fee_low = market.simulate_next_base_fee(20);
        assert!(next_fee_low < current_fee);

        // Original market should be unchanged
        assert_eq!(market.base_fee, current_fee);
    }

    #[test]
    fn test_gradual_adjustment() {
        let mut market = FeeMarket::default();
        let initial = market.base_fee;

        // Full blocks should gradually increase fee
        market.update_base_fee(200); // Max capacity
        let after_one = market.base_fee;

        market.update_base_fee(200);
        let after_two = market.base_fee;

        // Each step should increase
        assert!(after_one > initial);
        assert!(after_two > after_one);

        // But not more than max change per block
        let max_change = initial / market.config.max_change_denominator as Balance;
        assert!((after_one - initial) <= max_change * 2); // Allow some rounding
    }
}
