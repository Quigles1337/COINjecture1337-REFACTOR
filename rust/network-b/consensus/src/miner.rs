// Mining Loop with NP-hard Proof-of-Work
// Implements commit-reveal protocol to prevent grinding attacks

use coinject_core::{
    Address, Block, BlockHeader, Clause, CoinbaseTransaction, Commitment, Hash, ProblemType,
    Solution, SolutionReveal, Transaction,
};
use coinject_tokenomics::RewardCalculator;
use crate::WorkScoreCalculator;
use rand::Rng;
use std::sync::Arc;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};
use tokio::sync::RwLock;

/// Mining configuration
pub struct MiningConfig {
    pub miner_address: Address,
    pub target_block_time: Duration,
    pub min_difficulty: u32,
    pub max_difficulty: u32,
}

impl Default for MiningConfig {
    fn default() -> Self {
        MiningConfig {
            miner_address: Address::from_bytes([0u8; 32]),
            target_block_time: Duration::from_secs(60), // 1 minute blocks
            min_difficulty: 20,
            max_difficulty: 40,
        }
    }
}

/// Mining statistics
#[derive(Clone, Debug)]
pub struct MiningStats {
    pub blocks_mined: u64,
    pub total_work_score: f64,
    pub average_solve_time: Duration,
    pub hash_rate: f64, // hashes per second
}

/// Miner that solves NP-hard problems and mines blocks
pub struct Miner {
    config: MiningConfig,
    work_calculator: WorkScoreCalculator,
    reward_calculator: RewardCalculator,
    stats: Arc<RwLock<MiningStats>>,
    difficulty: u32,
}

impl Miner {
    pub fn new(config: MiningConfig) -> Self {
        Miner {
            config,
            work_calculator: WorkScoreCalculator::new(),
            reward_calculator: RewardCalculator::new(),
            stats: Arc::new(RwLock::new(MiningStats {
                blocks_mined: 0,
                total_work_score: 0.0,
                average_solve_time: Duration::from_secs(0),
                hash_rate: 0.0,
            })),
            difficulty: 20, // Starting difficulty (leading zeros in hash)
        }
    }

    /// Generate a random NP-hard problem for mining
    pub fn generate_problem(&self, block_height: u64) -> ProblemType {
        let mut rng = rand::thread_rng();

        // Use block height to seed problem complexity
        let problem_size = 10 + (block_height % 10) as usize;

        // Randomly choose problem type
        match rng.gen_range(0..3) {
            0 => {
                // Subset Sum
                let numbers: Vec<i64> = (0..problem_size)
                    .map(|_| rng.gen_range(1..1000))
                    .collect();
                let sum: i64 = numbers.iter().sum();
                let target = rng.gen_range(sum / 3..sum / 2);

                ProblemType::SubsetSum { numbers, target }
            }
            1 => {
                // SAT (Boolean Satisfiability)
                let variables = problem_size;
                let num_clauses = variables * 3; // 3-SAT
                let clauses = (0..num_clauses)
                    .map(|_| {
                        let mut literals = Vec::new();
                        for _ in 0..3 {
                            let var = rng.gen_range(0..variables) as i32 + 1;
                            let literal = if rng.gen_bool(0.5) { var } else { -var };
                            literals.push(literal);
                        }
                        Clause { literals }
                    })
                    .collect();

                ProblemType::SAT { variables, clauses }
            }
            _ => {
                // TSP (Traveling Salesman Problem)
                let cities = problem_size.min(15); // Cap TSP at 15 cities
                let mut distances = vec![vec![0u64; cities]; cities];
                for i in 0..cities {
                    for j in i+1..cities {
                        let dist = rng.gen_range(1..100);
                        distances[i][j] = dist;
                        distances[j][i] = dist;
                    }
                }

                ProblemType::TSP { cities, distances }
            }
        }
    }

    /// Solve NP-hard problem using backtracking/heuristics
    pub fn solve_problem(&self, problem: &ProblemType) -> Option<(Solution, Duration, usize)> {
        let start_time = Instant::now();
        let mut memory_used = 0;

        let solution = match problem {
            ProblemType::SubsetSum { numbers, target } => {
                // Dynamic programming solution (pseudo-polynomial time)
                self.solve_subset_sum(numbers, *target, &mut memory_used)
            }
            ProblemType::SAT { variables, clauses } => {
                // DPLL algorithm for SAT
                self.solve_sat(*variables, &clauses, &mut memory_used)
            }
            ProblemType::TSP { cities, distances } => {
                // Greedy nearest neighbor heuristic
                self.solve_tsp(*cities, distances, &mut memory_used)
            }
            ProblemType::Custom { .. } => None,
        };

        let solve_time = start_time.elapsed();
        solution.map(|s| (s, solve_time, memory_used))
    }

    /// Subset sum solver using dynamic programming
    fn solve_subset_sum(&self, numbers: &[i64], target: i64, memory: &mut usize) -> Option<Solution> {
        let n = numbers.len();
        let sum: i64 = numbers.iter().sum();

        if target > sum || target < 0 {
            return None;
        }

        // DP table
        let offset = sum.abs() as usize;
        let range = (2 * offset + 1) as usize;
        let mut dp = vec![vec![false; range]; n + 1];
        *memory += dp.len() * dp[0].len();

        dp[0][offset] = true;

        for i in 1..=n {
            for j in 0..range {
                dp[i][j] = dp[i-1][j];
                let num = numbers[i-1];
                let prev_idx = j as i64 - num;
                if prev_idx >= 0 && prev_idx < range as i64 {
                    dp[i][j] |= dp[i-1][prev_idx as usize];
                }
            }
        }

        let target_idx = (offset as i64 + target) as usize;
        if !dp[n][target_idx] {
            return None;
        }

        // Backtrack to find solution
        let mut indices = Vec::new();
        let mut curr_sum = target;
        for i in (1..=n).rev() {
            if curr_sum == 0 {
                break;
            }
            let num = numbers[i-1];
            if curr_sum >= num {
                let prev_idx = (offset as i64 + curr_sum - num) as usize;
                if prev_idx < range && dp[i-1][prev_idx] {
                    indices.push(i-1);
                    curr_sum -= num;
                }
            }
        }

        Some(Solution::SubsetSum(indices))
    }

    /// SAT solver using random search
    fn solve_sat(&self, variables: usize, clauses: &[Clause], memory: &mut usize) -> Option<Solution> {
        // Simple randomized search (not full DPLL for simplicity)
        *memory += variables * 8;

        let mut rng = rand::thread_rng();
        for _ in 0..1000 { // Try 1000 random assignments
            let assignment: Vec<bool> = (0..variables).map(|_| rng.gen_bool(0.5)).collect();

            let satisfied = clauses.iter().all(|clause| {
                clause.literals.iter().any(|&literal| {
                    let var_idx = (literal.abs() - 1) as usize;
                    let value = assignment.get(var_idx).copied().unwrap_or(false);
                    if literal > 0 {
                        value
                    } else {
                        !value
                    }
                })
            });

            if satisfied {
                return Some(Solution::SAT(assignment));
            }
        }

        None
    }

    /// TSP solver using nearest neighbor heuristic
    fn solve_tsp(&self, cities: usize, distances: &[Vec<u64>], memory: &mut usize) -> Option<Solution> {
        if cities == 0 {
            return None;
        }

        *memory += cities * 8;

        let mut tour = Vec::with_capacity(cities);
        let mut visited = vec![false; cities];
        let mut current = 0;

        tour.push(current);
        visited[current] = true;

        for _ in 1..cities {
            let mut nearest = None;
            let mut min_dist = u64::MAX;

            for next in 0..cities {
                if !visited[next] {
                    let dist = distances[current][next];
                    if dist < min_dist {
                        min_dist = dist;
                        nearest = Some(next);
                    }
                }
            }

            if let Some(next) = nearest {
                current = next;
                tour.push(current);
                visited[current] = true;
            }
        }

        Some(Solution::TSP(tour))
    }

    /// Mine a block with commit-reveal protocol
    pub async fn mine_block(
        &mut self,
        prev_hash: Hash,
        height: u64,
        transactions: Vec<Transaction>,
    ) -> Option<Block> {
        println!("\n=== Mining Block {} ===", height);

        // 1. Generate NP-hard problem
        let problem = self.generate_problem(height);
        println!("Generated problem: {:?}", problem);

        // 2. Solve the problem and measure performance
        let solve_result = self.solve_problem(&problem)?;
        let (solution, solve_time, solve_memory) = solve_result;
        println!("Solved in {:?} using {} bytes", solve_time, solve_memory);

        // 3. Verify solution
        let verify_start = Instant::now();
        if !solution.verify(&problem) {
            println!("Solution verification failed!");
            return None;
        }
        let verify_time = verify_start.elapsed();
        let verify_memory = 1024; // Approximate verification memory

        // 4. Calculate work score
        let work_score = self.work_calculator.calculate(
            &problem,
            &solution,
            solve_time,
            verify_time,
            solve_memory,
            verify_memory,
            0.001, // Energy per operation
        );
        println!("Work score: {}", work_score);

        // 5. Create commitment (prevents grinding)
        let epoch_salt = Hash::new(&height.to_le_bytes());
        let commitment = Commitment::create(&problem, &solution, &epoch_salt);
        println!("Commitment created: {:?}", commitment.hash);

        // 6. Build block header with commitment
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs() as i64;

        let transactions_root = Self::merkle_root(&transactions);
        let solutions_root = Hash::new(&bincode::serialize(&solution).unwrap_or_default());

        let mut header = BlockHeader {
            version: 1,
            height,
            prev_hash,
            timestamp,
            transactions_root,
            solutions_root,
            commitment: commitment.clone(),
            work_score,
            miner: self.config.miner_address,
            nonce: 0,
        };

        // 7. Mine the header (find nonce that meets difficulty)
        let header_hash = self.mine_header(&mut header)?;
        println!("Header mined: {:?}", header_hash);

        // 8. Calculate block reward and create coinbase transaction
        let reward_amount = self.reward_calculator.calculate_reward(work_score);
        let coinbase = CoinbaseTransaction::new(self.config.miner_address, reward_amount, height);
        println!("Block reward: {} tokens", reward_amount);

        // 9. Create solution reveal
        let solution_reveal = SolutionReveal {
            problem: problem.clone(),
            solution: solution.clone(),
            commitment,
        };

        // 10. Update stats
        self.update_stats(work_score, solve_time).await;

        Some(Block {
            header,
            coinbase,
            transactions,
            solution_reveal,
        })
    }

    /// Mine header by finding nonce that meets difficulty target
    fn mine_header(&self, header: &mut BlockHeader) -> Option<Hash> {
        let target_prefix = "0".repeat(self.difficulty as usize);
        let start_time = Instant::now();
        let mut hashes = 0u64;

        for nonce in 0..u64::MAX {
            header.nonce = nonce;
            let hash = header.hash();
            hashes += 1;

            let hash_hex = hex::encode(hash.as_bytes());
            if hash_hex.starts_with(&target_prefix) {
                let elapsed = start_time.elapsed().as_secs_f64();
                let hash_rate = hashes as f64 / elapsed;
                println!("Found nonce {} after {} hashes ({:.2} H/s)", nonce, hashes, hash_rate);
                return Some(hash);
            }

            // Print progress every million hashes
            if nonce % 1_000_000 == 0 && nonce > 0 {
                let elapsed = start_time.elapsed().as_secs_f64();
                let hash_rate = hashes as f64 / elapsed;
                println!("Mining... {} hashes ({:.2} H/s)", hashes, hash_rate);
            }
        }

        None
    }

    /// Calculate merkle root of transactions
    fn merkle_root(transactions: &[Transaction]) -> Hash {
        if transactions.is_empty() {
            return Hash::ZERO;
        }

        let leaves: Vec<Vec<u8>> = transactions
            .iter()
            .map(|tx| bincode::serialize(tx).unwrap_or_default())
            .collect();

        let tree = coinject_core::MerkleTree::new(leaves);
        tree.root()
    }

    /// Update mining statistics
    async fn update_stats(&mut self, work_score: f64, solve_time: Duration) {
        let mut stats = self.stats.write().await;
        stats.blocks_mined += 1;
        stats.total_work_score += work_score;

        // Update average solve time
        let total_time = stats.average_solve_time.as_secs_f64() * (stats.blocks_mined - 1) as f64
            + solve_time.as_secs_f64();
        stats.average_solve_time = Duration::from_secs_f64(total_time / stats.blocks_mined as f64);
    }

    /// Get current mining stats
    pub async fn get_stats(&self) -> MiningStats {
        self.stats.read().await.clone()
    }

    /// Adjust mining difficulty based on block time
    pub fn adjust_difficulty(&mut self, actual_block_time: Duration) {
        let target = self.config.target_block_time.as_secs_f64();
        let actual = actual_block_time.as_secs_f64();

        if actual < target * 0.8 {
            // Blocks too fast, increase difficulty
            self.difficulty = (self.difficulty + 1).min(self.config.max_difficulty);
            println!("Difficulty increased to {}", self.difficulty);
        } else if actual > target * 1.2 {
            // Blocks too slow, decrease difficulty
            self.difficulty = (self.difficulty.saturating_sub(1)).max(self.config.min_difficulty);
            println!("Difficulty decreased to {}", self.difficulty);
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_problem_generation() {
        let config = MiningConfig::default();
        let miner = Miner::new(config);

        let problem = miner.generate_problem(0);
        println!("Generated problem: {:?}", problem);

        match problem {
            ProblemType::SubsetSum { ref numbers, .. } => assert!(!numbers.is_empty()),
            ProblemType::SAT { variables, .. } => assert!(variables > 0),
            ProblemType::TSP { cities, .. } => assert!(cities > 0),
            _ => panic!("Unexpected problem type"),
        }
    }

    #[tokio::test]
    async fn test_subset_sum_solver() {
        let config = MiningConfig::default();
        let miner = Miner::new(config);

        let problem = ProblemType::SubsetSum {
            numbers: vec![3, 6, 7, 9, 12],
            target: 15,
        };

        let result = miner.solve_problem(&problem);
        assert!(result.is_some());

        let (solution, _time, _memory) = result.unwrap();
        assert!(solution.verify(&problem));
    }

    #[tokio::test]
    async fn test_tsp_solver() {
        let config = MiningConfig::default();
        let miner = Miner::new(config);

        let problem = ProblemType::TSP {
            cities: 5,
            distances: vec![
                vec![0, 10, 15, 20, 25],
                vec![10, 0, 35, 25, 30],
                vec![15, 35, 0, 30, 20],
                vec![20, 25, 30, 0, 15],
                vec![25, 30, 20, 15, 0],
            ],
        };

        let result = miner.solve_problem(&problem);
        assert!(result.is_some());

        let (solution, _time, _memory) = result.unwrap();
        assert!(solution.verify(&problem));
    }
}
