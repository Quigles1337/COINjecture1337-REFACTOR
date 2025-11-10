// Dimensional Pool State with Exponential Tokenomics
// Implements the COINjecture white paper mathematics
//
// Core Mathematics:
// - Satoshi Constant: η = λ = 1/√2 (critical complex equilibrium)
// - Unit Circle Constraint: |μ|² = η² + λ² = 1
// - Dimensional Scales: Dn = e^(-η·τn)
// - Normalized Allocation: p_n = Dn / Σ(Dk²)^(1/2)
// - Phase Evolution: θ(τ) = λτ = τ/√2
//
// Reference: COINjecture White Paper v2.3, Mathematical Proof

use coinject_core::{Address, Balance, DimensionalPool, Hash};
use serde::{Deserialize, Serialize};
use sled::Db;
use std::sync::Arc;

/// Satoshi Constant: η = λ = 1/√2 (critical damping at unit circle)
pub const SATOSHI_ETA: f64 = 0.7071067811865476; // 1/√2
pub const SATOSHI_LAMBDA: f64 = 0.7071067811865476; // 1/√2

/// Three dimensional economic scales (dimensionless time points τn)
/// From white paper: D_n = e^(-η·τ_n)
pub const DIMENSIONAL_SCALES: [(DimensionalPool, f64, f64, &str); 3] = [
    (DimensionalPool::D1, 0.00, 1.000, "Genesis"),        // τ₁=0.00, D₁=1.000
    (DimensionalPool::D2, 0.20, 0.867, "Coupling"),       // τ₂=0.20, D₂=0.867
    (DimensionalPool::D3, 0.41, 0.750, "First Harmonic"), // τ₃=0.41, D₃=0.750
];

/// Normalized allocation ratios (from white paper conservation constraint)
/// Σ(D_n²) = 3.177, normalized allocations: p_n = D_n / √3.177
pub const ALLOCATION_RATIOS: [(DimensionalPool, f64); 3] = [
    (DimensionalPool::D1, 0.561), // 56.1%
    (DimensionalPool::D2, 0.486), // 48.6%
    (DimensionalPool::D3, 0.421), // 42.1%
];

/// Pool liquidity data
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PoolLiquidity {
    /// Pool type
    pub pool: DimensionalPool,
    /// Current liquidity (total tokens in pool)
    pub liquidity: Balance,
    /// Dimensional scale factor D_n = e^(-η·τ_n)
    pub dimensional_factor: f64,
    /// Allocation ratio p_n (normalized)
    pub allocation_ratio: f64,
    /// Current dimensionless time τ (for phase evolution)
    pub tau: f64,
    /// Phase angle θ(τ) = λτ = τ/√2
    pub phase: f64,
    /// Last update block height
    pub last_update_height: u64,
}

/// Pool swap record
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct PoolSwapRecord {
    /// Swap transaction hash
    pub tx_hash: Hash,
    /// Swapper address
    pub from: Address,
    /// Source pool
    pub pool_from: DimensionalPool,
    /// Destination pool
    pub pool_to: DimensionalPool,
    /// Amount swapped in
    pub amount_in: Balance,
    /// Amount swapped out
    pub amount_out: Balance,
    /// Swap ratio (amount_out / amount_in)
    pub swap_ratio: f64,
    /// Block height when swap occurred
    pub block_height: u64,
}

/// Dimensional Pool State Manager
pub struct DimensionalPoolState {
    db: Arc<Db>,
}

impl DimensionalPoolState {
    /// Create new dimensional pool state manager
    pub fn new(db: Arc<Db>) -> Self {
        DimensionalPoolState { db }
    }

    /// Initialize pools with genesis liquidity
    pub fn initialize_pools(&self, total_supply: Balance, genesis_height: u64) -> Result<(), String> {
        for (pool, tau, d_n, name) in DIMENSIONAL_SCALES.iter() {
            // Calculate initial liquidity based on allocation ratio
            let allocation = self.get_allocation_ratio(*pool);
            let initial_liquidity = (total_supply as f64 * allocation) as Balance;

            let pool_liquidity = PoolLiquidity {
                pool: *pool,
                liquidity: initial_liquidity,
                dimensional_factor: *d_n,
                allocation_ratio: allocation,
                tau: *tau,
                phase: self.calculate_phase(*tau),
                last_update_height: genesis_height,
            };

            self.save_pool_liquidity(&pool_liquidity)?;

            println!("✅ Initialized pool {:?} ({}) with {} tokens (D_n={:.3}, p_n={:.3})",
                pool, name, initial_liquidity, d_n, allocation);
        }

        Ok(())
    }

    /// Get pool liquidity
    pub fn get_pool_liquidity(&self, pool: &DimensionalPool) -> Option<PoolLiquidity> {
        let key = Self::make_pool_key(pool);
        self.db.get(key).ok()?.map(|bytes| {
            bincode::deserialize(&bytes).ok()
        })?
    }

    /// Save pool liquidity
    fn save_pool_liquidity(&self, pool: &PoolLiquidity) -> Result<(), String> {
        let key = Self::make_pool_key(&pool.pool);
        let value = bincode::serialize(pool)
            .map_err(|e| format!("Failed to serialize pool: {}", e))?;

        self.db
            .insert(key, value)
            .map_err(|e| format!("Failed to insert pool: {}", e))?;

        self.db
            .flush()
            .map_err(|e| format!("Failed to flush: {}", e))?;

        Ok(())
    }

    /// Execute pool swap with exponential dimensional ratios
    /// Implements: amount_out = amount_in × (D_from / D_to)
    pub fn execute_swap(
        &self,
        pool_from: DimensionalPool,
        pool_to: DimensionalPool,
        amount_in: Balance,
        min_amount_out: Balance,
        block_height: u64,
    ) -> Result<Balance, String> {
        // Get pool liquidities
        let mut liquidity_from = self.get_pool_liquidity(&pool_from)
            .ok_or("Source pool not found")?;
        let mut liquidity_to = self.get_pool_liquidity(&pool_to)
            .ok_or("Destination pool not found")?;

        // Check source pool has enough liquidity
        if liquidity_from.liquidity < amount_in {
            return Err(format!("Insufficient liquidity in source pool: has {}, needs {}",
                liquidity_from.liquidity, amount_in));
        }

        // Calculate swap ratio using dimensional factors
        // Ratio = D_from / D_to (exponential scaling)
        let swap_ratio = liquidity_from.dimensional_factor / liquidity_to.dimensional_factor;
        let amount_out = (amount_in as f64 * swap_ratio) as Balance;

        // Check slippage protection
        if amount_out < min_amount_out {
            return Err(format!("Slippage exceeded: got {}, minimum {}",
                amount_out, min_amount_out));
        }

        // Check destination pool has enough liquidity
        if liquidity_to.liquidity < amount_out {
            return Err(format!("Insufficient liquidity in destination pool: has {}, needs {}",
                liquidity_to.liquidity, amount_out));
        }

        // Update pool liquidities
        liquidity_from.liquidity -= amount_in;
        liquidity_from.last_update_height = block_height;

        liquidity_to.liquidity -= amount_out;
        liquidity_to.last_update_height = block_height;

        // Save updated pools
        self.save_pool_liquidity(&liquidity_from)?;
        self.save_pool_liquidity(&liquidity_to)?;

        Ok(amount_out)
    }

    /// Calculate dimensional factor: D_n = e^(-η·τ_n)
    pub fn calculate_dimensional_factor(&self, tau: f64) -> f64 {
        (-SATOSHI_ETA * tau).exp()
    }

    /// Calculate phase evolution: θ(τ) = λτ = τ/√2
    pub fn calculate_phase(&self, tau: f64) -> f64 {
        SATOSHI_LAMBDA * tau
    }

    /// Get normalized allocation ratio for pool
    pub fn get_allocation_ratio(&self, pool: DimensionalPool) -> f64 {
        ALLOCATION_RATIOS.iter()
            .find(|(p, _)| p == &pool)
            .map(|(_, ratio)| *ratio)
            .unwrap_or(0.0)
    }

    /// Get dimensional factor for pool
    pub fn get_dimensional_factor(&self, pool: DimensionalPool) -> f64 {
        DIMENSIONAL_SCALES.iter()
            .find(|(p, _, _, _)| p == &pool)
            .map(|(_, _, d_n, _)| *d_n)
            .unwrap_or(1.0)
    }

    /// Get dimensionless time τ for pool
    pub fn get_tau(&self, pool: DimensionalPool) -> f64 {
        DIMENSIONAL_SCALES.iter()
            .find(|(p, _, _, _)| p == &pool)
            .map(|(_, tau, _, _)| *tau)
            .unwrap_or(0.0)
    }

    /// Record swap transaction
    pub fn record_swap(
        &self,
        tx_hash: Hash,
        from: Address,
        pool_from: DimensionalPool,
        pool_to: DimensionalPool,
        amount_in: Balance,
        amount_out: Balance,
        block_height: u64,
    ) -> Result<(), String> {
        let swap_ratio = (amount_out as f64) / (amount_in as f64);

        let swap_record = PoolSwapRecord {
            tx_hash,
            from,
            pool_from,
            pool_to,
            amount_in,
            amount_out,
            swap_ratio,
            block_height,
        };

        let key = Self::make_swap_key(&tx_hash);
        let value = bincode::serialize(&swap_record)
            .map_err(|e| format!("Failed to serialize swap: {}", e))?;

        self.db
            .insert(key, value)
            .map_err(|e| format!("Failed to insert swap: {}", e))?;

        self.db
            .flush()
            .map_err(|e| format!("Failed to flush: {}", e))?;

        Ok(())
    }

    /// Get swap record by transaction hash
    pub fn get_swap_record(&self, tx_hash: &Hash) -> Option<PoolSwapRecord> {
        let key = Self::make_swap_key(tx_hash);
        self.db.get(key).ok()?.map(|bytes| {
            bincode::deserialize(&bytes).ok()
        })?
    }

    /// Get all pool liquidities
    pub fn get_all_pools(&self) -> Vec<PoolLiquidity> {
        let mut pools = Vec::new();
        for (pool, _, _, _) in DIMENSIONAL_SCALES.iter() {
            if let Some(liquidity) = self.get_pool_liquidity(pool) {
                pools.push(liquidity);
            }
        }
        pools
    }

    /// Calculate total liquidity across all pools
    pub fn total_liquidity(&self) -> Balance {
        self.get_all_pools()
            .iter()
            .map(|p| p.liquidity)
            .sum()
    }

    // Key generation helpers
    fn make_pool_key(pool: &DimensionalPool) -> Vec<u8> {
        let mut key = b"pool:".to_vec();
        key.push(*pool as u8);
        key
    }

    fn make_swap_key(tx_hash: &Hash) -> Vec<u8> {
        let mut key = b"swap:".to_vec();
        key.extend_from_slice(tx_hash.as_bytes());
        key
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_satoshi_constant() {
        // Verify η = λ = 1/√2
        let sqrt_2 = 2.0_f64.sqrt();
        assert!((SATOSHI_ETA - 1.0 / sqrt_2).abs() < 1e-10);
        assert!((SATOSHI_LAMBDA - 1.0 / sqrt_2).abs() < 1e-10);
    }

    #[test]
    fn test_unit_circle_constraint() {
        // Verify |μ|² = η² + λ² = 1
        let magnitude_squared = SATOSHI_ETA.powi(2) + SATOSHI_LAMBDA.powi(2);
        assert!((magnitude_squared - 1.0).abs() < 1e-10);
    }

    #[test]
    fn test_dimensional_factors() {
        // Verify D_n = e^(-η·τ_n)
        for (_, tau, expected_d, _) in DIMENSIONAL_SCALES.iter() {
            let calculated_d = (-SATOSHI_ETA * tau).exp();
            assert!((calculated_d - expected_d).abs() < 0.001,
                "D_n mismatch for τ={}: expected {}, got {}", tau, expected_d, calculated_d);
        }
    }

    #[test]
    fn test_allocation_ratios_sum() {
        // Allocation ratios should be dimensionless and properly normalized
        let sum: f64 = ALLOCATION_RATIOS.iter().map(|(_, r)| r).sum();
        // Sum should be approximately 1.468 (normalized by √3.177)
        assert!(sum > 1.4 && sum < 1.5);
    }

    #[test]
    fn test_phase_evolution() {
        // θ(τ) = λτ = τ/√2
        let tau = 1.0;
        let phase = SATOSHI_LAMBDA * tau;
        let expected = tau / 2.0_f64.sqrt();
        assert!((phase - expected).abs() < 1e-10);
    }
}
