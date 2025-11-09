// TrustLine credit network with exponential dimensional tokenomics
// Implements XRPL-inspired bilateral credit with COINjecture mathematical framework
//
// Core Mathematics:
// - Satoshi Constant: η = λ = 1/√2 (critical complex equilibrium)
// - Unit Circle Constraint: |μ|² = η² + λ² = 1
// - Dimensional Scales: D_n = e^(-ητ_n)
// - Phase Evolution: θ(τ) = λτ = τ/√2
// - Viviani Oracle: Δ = (d₁ + d₂ + d₃)/(√3/2) - 1

use coinject_core::{Address, Balance, Hash};
use serde::{Deserialize, Serialize};
use sled::Db;
use std::sync::Arc;

/// Satoshi Constant: η = λ = 1/√2 (critical damping at unit circle)
pub const SATOSHI_ETA: f64 = 0.7071067811865476; // 1/√2
pub const SATOSHI_LAMBDA: f64 = 0.7071067811865476; // 1/√2

/// Eight dimensional economic scales (time points in years)
pub const DIMENSIONAL_SCALES: [(u8, f64, &str); 8] = [
    (1, 1.0, "Genesis"),           // D₁ = e^(-η·1)
    (2, 2.0, "Coupling"),          // D₂ = e^(-η·2)
    (3, 3.0, "First Harmonic"),    // D₃ = e^(-η·3)
    (4, 3.819660, "Golden Ratio"), // D₄ = e^(-η·φ^(-1)·6)
    (5, 6.0, "Half-Scale"),        // D₅ = e^(-η·6)
    (6, 7.639320, "Second Golden"), // D₆ = e^(-η·φ^(-1)·12)
    (7, 12.0, "Quarter-Scale"),    // D₇ = e^(-η·12)
    (8, 16.309842, "Euler"),       // D₈ = e^(-η·e·6)
];

/// TrustLine status
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub enum TrustLineStatus {
    /// TrustLine is active
    Active,
    /// TrustLine is frozen
    Frozen,
    /// TrustLine is closed
    Closed,
}

/// Bilateral credit line with dimensional economics
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TrustLine {
    /// Unique identifier (hash of both addresses)
    pub trustline_id: Hash,

    /// First account
    pub account_a: Address,

    /// Second account
    pub account_b: Address,

    /// Credit limit A extends to B (in base units)
    pub limit_a_to_b: Balance,

    /// Credit limit B extends to A (in base units)
    pub limit_b_to_a: Balance,

    /// Current balance (positive = B owes A, negative = A owes B)
    pub balance: i128,

    /// Quality in (percentage, basis points 0-10000)
    pub quality_in: u16,

    /// Quality out (percentage, basis points 0-10000)
    pub quality_out: u16,

    /// Allow rippling through this trustline
    pub ripple_enabled: bool,

    /// Dimensional scale index (1-8)
    pub dimensional_scale: u8,

    /// Phase parameter τ (tau) for credit dynamics
    pub tau: f64,

    /// Viviani oracle performance metric Δ
    pub viviani_delta: f64,

    /// Status
    pub status: TrustLineStatus,

    /// Block height when created
    pub created_at_height: u64,

    /// Block height when last modified
    pub modified_at_height: u64,
}

impl TrustLine {
    /// Calculate dimensional scale factor D_n = e^(-ητ_n)
    pub fn dimensional_factor(&self) -> f64 {
        if self.dimensional_scale < 1 || self.dimensional_scale > 8 {
            return 1.0; // Fallback to unity
        }

        let (_, tau_n, _) = DIMENSIONAL_SCALES[self.dimensional_scale as usize - 1];
        (-SATOSHI_ETA * tau_n).exp()
    }

    /// Calculate phase evolution θ(τ) = λτ = τ/√2
    pub fn phase_evolution(&self) -> f64 {
        SATOSHI_LAMBDA * self.tau
    }

    /// Calculate effective credit limit A→B with dimensional scaling
    pub fn effective_limit_a_to_b(&self) -> Balance {
        let scale = self.dimensional_factor();
        (self.limit_a_to_b as f64 * scale) as Balance
    }

    /// Calculate effective credit limit B→A with dimensional scaling
    pub fn effective_limit_b_to_a(&self) -> Balance {
        let scale = self.dimensional_factor();
        (self.limit_b_to_a as f64 * scale) as Balance
    }

    /// Get available credit for A to lend to B
    pub fn available_credit_a(&self) -> Balance {
        let effective_limit = self.effective_limit_a_to_b();
        let used = if self.balance > 0 { self.balance as Balance } else { 0 };
        effective_limit.saturating_sub(used)
    }

    /// Get available credit for B to lend to A
    pub fn available_credit_b(&self) -> Balance {
        let effective_limit = self.effective_limit_b_to_a();
        let used = if self.balance < 0 { (-self.balance) as Balance } else { 0 };
        effective_limit.saturating_sub(used)
    }

    /// Update Viviani oracle metric
    /// Δ = (d₁ + d₂ + d₃)/(√3/2) - 1
    /// Here we use: d₁ = utilization_a, d₂ = utilization_b, d₃ = phase_evolution
    pub fn update_viviani_oracle(&mut self) {
        let effective_a = self.effective_limit_a_to_b() as f64;
        let effective_b = self.effective_limit_b_to_a() as f64;

        let utilization_a = if effective_a > 0.0 {
            (self.balance.max(0) as f64) / effective_a
        } else {
            0.0
        };

        let utilization_b = if effective_b > 0.0 {
            ((-self.balance).max(0) as f64) / effective_b
        } else {
            0.0
        };

        let phase_normalized = self.phase_evolution() / std::f64::consts::PI;

        // Viviani's theorem: sum of perpendicular distances equals altitude
        let sum_distances = utilization_a + utilization_b + phase_normalized;
        let viviani_altitude = 3.0_f64.sqrt() / 2.0; // Equilateral triangle altitude

        self.viviani_delta = (sum_distances / viviani_altitude) - 1.0;
    }

    /// Check if balance is within limits considering dimensional scaling
    pub fn is_balanced(&self) -> bool {
        if self.balance > 0 {
            (self.balance as Balance) <= self.effective_limit_a_to_b()
        } else {
            ((-self.balance) as Balance) <= self.effective_limit_b_to_a()
        }
    }

    /// Check if address is a participant
    pub fn is_participant(&self, address: &Address) -> bool {
        address == &self.account_a || address == &self.account_b
    }

    /// Evolve phase parameter (called periodically or on transaction)
    pub fn evolve_phase(&mut self, delta_tau: f64) {
        self.tau += delta_tau;
        self.update_viviani_oracle();
    }
}

/// TrustLine state management with dimensional economics
pub struct TrustLineState {
    db: Arc<Db>,
}

impl TrustLineState {
    /// Create new trustline state manager
    pub fn new(db: Arc<Db>) -> Self {
        TrustLineState { db }
    }

    /// Create a new trustline
    pub fn create_trustline(&self, trustline: TrustLine) -> Result<(), String> {
        // Check if trustline already exists
        if self.get_trustline(&trustline.trustline_id).is_some() {
            return Err("TrustLine already exists".to_string());
        }

        // Validate dimensional scale
        if trustline.dimensional_scale < 1 || trustline.dimensional_scale > 8 {
            return Err("Invalid dimensional scale (must be 1-8)".to_string());
        }

        // Validate quality parameters (basis points 0-10000)
        if trustline.quality_in > 10000 || trustline.quality_out > 10000 {
            return Err("Invalid quality parameters (must be 0-10000)".to_string());
        }

        let key = Self::make_key(&trustline.trustline_id);
        let value = bincode::serialize(&trustline)
            .map_err(|e| format!("Failed to serialize trustline: {}", e))?;

        self.db
            .insert(key, value)
            .map_err(|e| format!("Failed to insert trustline: {}", e))?;

        self.db
            .flush()
            .map_err(|e| format!("Failed to flush: {}", e))?;

        Ok(())
    }

    /// Get trustline by ID
    pub fn get_trustline(&self, trustline_id: &Hash) -> Option<TrustLine> {
        let key = Self::make_key(trustline_id);
        self.db.get(key).ok()?.map(|bytes| {
            bincode::deserialize(&bytes).ok()
        })?
    }

    /// Update trustline balance (for payments through the line)
    pub fn update_balance(
        &self,
        trustline_id: &Hash,
        new_balance: i128,
        block_height: u64,
    ) -> Result<(), String> {
        let mut trustline = self
            .get_trustline(trustline_id)
            .ok_or("TrustLine not found".to_string())?;

        if trustline.status != TrustLineStatus::Active {
            return Err("TrustLine is not active".to_string());
        }

        trustline.balance = new_balance;
        trustline.modified_at_height = block_height;

        // Validate balance is within limits
        if !trustline.is_balanced() {
            return Err("Balance exceeds dimensional credit limits".to_string());
        }

        // Update oracle metrics
        trustline.update_viviani_oracle();

        self.save_trustline(&trustline)?;

        Ok(())
    }

    /// Evolve phase for a trustline
    pub fn evolve_trustline_phase(
        &self,
        trustline_id: &Hash,
        delta_tau: f64,
        block_height: u64,
    ) -> Result<(), String> {
        let mut trustline = self
            .get_trustline(trustline_id)
            .ok_or("TrustLine not found".to_string())?;

        trustline.evolve_phase(delta_tau);
        trustline.modified_at_height = block_height;

        self.save_trustline(&trustline)?;

        Ok(())
    }

    /// Update credit limits with dimensional recalibration
    pub fn update_limits(
        &self,
        trustline_id: &Hash,
        limit_a_to_b: Option<Balance>,
        limit_b_to_a: Option<Balance>,
        block_height: u64,
    ) -> Result<(), String> {
        let mut trustline = self
            .get_trustline(trustline_id)
            .ok_or("TrustLine not found".to_string())?;

        if trustline.status != TrustLineStatus::Active {
            return Err("TrustLine is not active".to_string());
        }

        if let Some(limit) = limit_a_to_b {
            trustline.limit_a_to_b = limit;
        }

        if let Some(limit) = limit_b_to_a {
            trustline.limit_b_to_a = limit;
        }

        trustline.modified_at_height = block_height;

        // Validate balance still within new limits
        if !trustline.is_balanced() {
            return Err("Current balance exceeds new limits".to_string());
        }

        trustline.update_viviani_oracle();

        self.save_trustline(&trustline)?;

        Ok(())
    }

    /// Freeze trustline
    pub fn freeze_trustline(
        &self,
        trustline_id: &Hash,
        block_height: u64,
    ) -> Result<(), String> {
        let mut trustline = self
            .get_trustline(trustline_id)
            .ok_or("TrustLine not found".to_string())?;

        trustline.status = TrustLineStatus::Frozen;
        trustline.modified_at_height = block_height;

        self.save_trustline(&trustline)?;

        Ok(())
    }

    /// Close trustline (requires zero balance)
    pub fn close_trustline(
        &self,
        trustline_id: &Hash,
        block_height: u64,
    ) -> Result<(), String> {
        let mut trustline = self
            .get_trustline(trustline_id)
            .ok_or("TrustLine not found".to_string())?;

        if trustline.balance != 0 {
            return Err("Cannot close trustline with non-zero balance".to_string());
        }

        trustline.status = TrustLineStatus::Closed;
        trustline.modified_at_height = block_height;

        self.save_trustline(&trustline)?;

        Ok(())
    }

    /// Get all active trustlines for an address
    pub fn get_trustlines_for_address(&self, address: &Address) -> Vec<TrustLine> {
        let mut trustlines = Vec::new();

        for item in self.db.iter() {
            if let Ok((_, value)) = item {
                if let Ok(trustline) = bincode::deserialize::<TrustLine>(&value) {
                    if trustline.is_participant(address) && trustline.status == TrustLineStatus::Active {
                        trustlines.push(trustline);
                    }
                }
            }
        }

        trustlines
    }

    /// Get trustline between two specific addresses
    pub fn get_trustline_between(
        &self,
        account_a: &Address,
        account_b: &Address,
    ) -> Option<TrustLine> {
        for item in self.db.iter() {
            if let Ok((_, value)) = item {
                if let Ok(trustline) = bincode::deserialize::<TrustLine>(&value) {
                    if (trustline.account_a == *account_a && trustline.account_b == *account_b)
                        || (trustline.account_a == *account_b && trustline.account_b == *account_a)
                    {
                        return Some(trustline);
                    }
                }
            }
        }
        None
    }

    /// Get all trustlines in a specific dimensional scale
    pub fn get_trustlines_by_dimension(&self, dimension: u8) -> Vec<TrustLine> {
        let mut trustlines = Vec::new();

        for item in self.db.iter() {
            if let Ok((_, value)) = item {
                if let Ok(trustline) = bincode::deserialize::<TrustLine>(&value) {
                    if trustline.dimensional_scale == dimension && trustline.status == TrustLineStatus::Active {
                        trustlines.push(trustline);
                    }
                }
            }
        }

        trustlines
    }

    /// Calculate network-wide Viviani oracle metrics
    pub fn calculate_network_viviani(&self) -> f64 {
        let mut total_delta = 0.0;
        let mut count = 0;

        for item in self.db.iter() {
            if let Ok((_, value)) = item {
                if let Ok(trustline) = bincode::deserialize::<TrustLine>(&value) {
                    if trustline.status == TrustLineStatus::Active {
                        total_delta += trustline.viviani_delta;
                        count += 1;
                    }
                }
            }
        }

        if count > 0 {
            total_delta / count as f64
        } else {
            0.0
        }
    }

    /// Save trustline to database
    fn save_trustline(&self, trustline: &TrustLine) -> Result<(), String> {
        let key = Self::make_key(&trustline.trustline_id);
        let value = bincode::serialize(trustline)
            .map_err(|e| format!("Failed to serialize trustline: {}", e))?;

        self.db
            .insert(key, value)
            .map_err(|e| format!("Failed to save trustline: {}", e))?;

        self.db
            .flush()
            .map_err(|e| format!("Failed to flush: {}", e))?;

        Ok(())
    }

    /// Database key prefix for trustlines
    fn make_key(trustline_id: &Hash) -> Vec<u8> {
        let mut key = vec![0x40]; // Prefix 0x40 for trustlines
        key.extend_from_slice(trustline_id.as_bytes());
        key
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn test_dimensional_factor() {
        let trustline = TrustLine {
            trustline_id: Hash::from_bytes([1u8; 32]),
            account_a: Address::from_bytes([2u8; 32]),
            account_b: Address::from_bytes([3u8; 32]),
            limit_a_to_b: 100000,
            limit_b_to_a: 50000,
            balance: 0,
            quality_in: 10000,
            quality_out: 10000,
            ripple_enabled: true,
            dimensional_scale: 1, // Genesis: D₁ = e^(-η·1)
            tau: 0.0,
            viviani_delta: 0.0,
            status: TrustLineStatus::Active,
            created_at_height: 100,
            modified_at_height: 100,
        };

        let factor = trustline.dimensional_factor();
        // D₁ = e^(-0.707·1) ≈ 0.493
        assert!(factor > 0.49 && factor < 0.50);
    }

    #[test]
    fn test_phase_evolution() {
        let mut trustline = TrustLine {
            trustline_id: Hash::from_bytes([1u8; 32]),
            account_a: Address::from_bytes([2u8; 32]),
            account_b: Address::from_bytes([3u8; 32]),
            limit_a_to_b: 100000,
            limit_b_to_a: 50000,
            balance: 0,
            quality_in: 10000,
            quality_out: 10000,
            ripple_enabled: true,
            dimensional_scale: 1,
            tau: 1.0,
            viviani_delta: 0.0,
            status: TrustLineStatus::Active,
            created_at_height: 100,
            modified_at_height: 100,
        };

        let phase = trustline.phase_evolution();
        // θ = λτ = (1/√2)·1 ≈ 0.707
        assert!(phase > 0.70 && phase < 0.71);

        trustline.evolve_phase(1.0);
        assert_eq!(trustline.tau, 2.0);
    }

    #[test]
    fn test_create_trustline() {
        let dir = tempdir().unwrap();
        let db = Arc::new(sled::open(dir.path()).unwrap());
        let state = TrustLineState::new(db);

        let trustline = TrustLine {
            trustline_id: Hash::from_bytes([1u8; 32]),
            account_a: Address::from_bytes([2u8; 32]),
            account_b: Address::from_bytes([3u8; 32]),
            limit_a_to_b: 100000,
            limit_b_to_a: 50000,
            balance: 0,
            quality_in: 10000,
            quality_out: 10000,
            ripple_enabled: true,
            dimensional_scale: 4, // Golden Ratio
            tau: 0.0,
            viviani_delta: 0.0,
            status: TrustLineStatus::Active,
            created_at_height: 100,
            modified_at_height: 100,
        };

        state.create_trustline(trustline.clone()).unwrap();

        let retrieved = state.get_trustline(&trustline.trustline_id);
        assert!(retrieved.is_some());
        assert_eq!(retrieved.unwrap().dimensional_scale, 4);
    }
}
