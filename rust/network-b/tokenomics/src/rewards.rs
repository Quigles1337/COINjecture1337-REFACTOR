// Block reward calculation
// block_reward = base_constant × (work_score / epoch_average_work)

use coinject_core::{Balance, WorkScore};

pub struct RewardCalculator {
    base_constant: f64,
    epoch_average_work: f64,
}

impl RewardCalculator {
    pub fn new() -> Self {
        RewardCalculator {
            base_constant: 10_000_000.0, // 10 million base reward for testing
            epoch_average_work: 1.0,
        }
    }

    /// Calculate block reward from work score
    pub fn calculate_reward(&self, work_score: WorkScore) -> Balance {
        let reward = self.base_constant * (work_score / self.epoch_average_work);
        reward as Balance
    }

    /// Update epoch average (called after each epoch)
    pub fn update_epoch_average(&mut self, average_work: f64) {
        self.epoch_average_work = average_work;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_reward_calculation() {
        let calculator = RewardCalculator::new();
        let reward = calculator.calculate_reward(10.0);
        assert!(reward > 0);
    }
}
