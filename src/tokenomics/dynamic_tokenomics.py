"""
Dynamic Work Score Tokenomics System
====================================

A revolutionary approach to blockchain tokenomics that adapts to actual network behavior
rather than using static parameters. Everything emerges from measured work scores.

Key Features:
- No static supply targets or block time schedules
- Rewards based on actual computational work contribution
- Market-driven tier selection for miners
- Natural deflation through cumulative work growth
- Dynamic difficulty adjustment based on work score distribution
"""

from __future__ import annotations
import time
import math
import random
import statistics
from dataclasses import dataclass, field
from typing import Optional, Tuple
from collections import deque
from enum import Enum

# Import existing classes from the blockchain system
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.blockchain import (
    Block, ComputationalComplexity, ProblemTier, HardwareType,
    calculate_computational_work_score, generate_subset_sum_problem,
    solve_subset_sum, subset_sum_complexity, EnergyMetrics
)


@dataclass
class HardwareProfile:
    """
    Represents a miner's hardware capabilities for dynamic tier selection.
    This class is missing from the original codebase but needed for the tokenomics system.
    """
    hardware_type: HardwareType
    computational_capability: float  # 0.0 to 1.0, where 1.0 is best possible
    cpu_cores: int
    memory_gb: float
    storage_gb: float
    gpu_available: bool
    network_speed_mbps: float
    battery_powered: bool
    energy_efficiency: float  # 0.0 to 1.0, higher is more efficient
    accessibility_score: float  # 0.0 to 1.0, higher means more accessible hardware


@dataclass
class WorkScoreRecord:
    """Record of work done in a block"""
    block_number: int
    work_score: float
    reward: float
    capacity: ProblemTier
    problem_size: int
    measured_solve_time: float
    measured_verify_time: float
    asymmetry_ratio: float
    timestamp: float


@dataclass
class CapacityMetrics:
    """Performance metrics for a specific capacity"""
    capacity: ProblemTier
    blocks_mined: int
    total_work_score: float
    avg_work_score: float
    avg_solve_time: float
    avg_asymmetry: float
    recent_records: deque


@dataclass
class DynamicWorkScoreTokenomics:
    """
    Tokenomics that adapts to actual network behavior.
    No static targets - everything emerges from measured work scores.
    """
    
    # ============================================
    # ONLY TRUE CONSTANTS (from computational theory)
    # ============================================
    
    COMPLEXITY_BASE: float = 2.0  # Subset Sum is O(2^n)
    VERIFY_COMPLEXITY_LINEAR: bool = True  # Verification is O(n)
    
    # ============================================
    # EVERYTHING ELSE IS DYNAMIC
    # ============================================
    
    def __init__(self, blockchain_state=None):
        # Track actual network behavior
        self.work_score_history: list[WorkScoreRecord] = []
        self.capacity_performance: dict[ProblemTier, CapacityMetrics] = {}
        
        # Dynamic supply emerges from network growth
        self.cumulative_work_score: float = 0.0
        self.total_coins_issued: float = 0.0
        
        # Dynamic block time emerges from verification performance
        self.recent_verification_times: deque = deque(maxlen=100)
        self.recent_solve_times: deque = deque(maxlen=100)
        
        # Blockchain state for wallet integration
        self.blockchain_state = blockchain_state
        
    def calculate_block_reward(self,
                              block: Block,
                              complexity: ComputationalComplexity) -> float:
        """
        Reward is purely a function of:
        1. This block's work score relative to recent network work
        2. The marginal contribution this work makes to cumulative progress
        
        NO static targets, NO arbitrary multipliers.
        """
        
        # 1. Get this block's work score (already calculated from complexity)
        block_work_score = calculate_computational_work_score(complexity)
        
        # 2. Get recent network average (rolling window)
        recent_avg_work = self._get_recent_average_work()
        
        # 3. Reward is proportional to work contribution
        # Use more reasonable scaling to ensure meaningful rewards
        if recent_avg_work > 0:
            work_ratio = block_work_score / recent_avg_work
            # Use square root scaling for more reasonable rewards
            base_reward = math.sqrt(1 + work_ratio) * 10  # Scale up by 10x for meaningful rewards
        else:
            # Genesis case: first blocks get reasonable reward
            base_reward = 50.0
        
        # 4. Apply deflation based on network maturity
        # As cumulative work grows, new work becomes less "novel"
        deflation_factor = self._calculate_deflation_factor()
        
        # 5. Apply diversity bonus for underrepresented capacities
        diversity_bonus = self._calculate_diversity_bonus(block.mining_capacity)
        
        # 6. Final reward
        reward = base_reward * deflation_factor * diversity_bonus
        
        return reward
    
    def _get_recent_average_work(self, window: int = 100) -> float:
        """
        Calculate average work score from recent blocks.
        This creates a moving baseline - no static target needed.
        """
        
        if len(self.work_score_history) < window:
            window = len(self.work_score_history)
        
        if window == 0:
            return 1.0  # Genesis default
        
        recent_scores = [record.work_score for record in self.work_score_history[-window:]]
        return statistics.mean(recent_scores)
    
    def _calculate_deflation_factor(self) -> float:
        """
        Deflation emerges from network growth dynamics.
        
        Key insight: As the network does more cumulative work,
        each additional unit of work represents a smaller fraction
        of total progress.
        
        This is like Bitcoin's supply limit, but DERIVED from work
        rather than arbitrarily set.
        """
        
        if self.cumulative_work_score == 0:
            return 1.0
        
        # More reasonable deflation: much gentler curve
        # Use square root scaling instead of exponential
        # This prevents rewards from becoming too small too quickly
        work_factor = math.sqrt(self.cumulative_work_score + 1)
        deflation = 1.0 / (1.0 + work_factor * 0.001)  # Much gentler deflation
        
        return max(0.1, deflation)  # Floor at 10% to maintain reasonable rewards
    
    def _calculate_diversity_bonus(self, capacity: ProblemTier) -> float:
        """
        Apply diversity bonus for underrepresented capacities.
        
        This encourages miners to join capacities that are underrepresented,
        promoting network diversity and preventing any single capacity from
        dominating the network.
        """
        
        # Get current market dynamics
        dynamics = self.get_capacity_market_dynamics()
        
        if capacity not in dynamics:
            # No data yet - no bonus
            return 1.0
        
        market_share = dynamics[capacity]['market_share']
        
        # Apply bonus based on market share
        # Lower market share = higher bonus
        if market_share < 0.05:  # Less than 5% market share
            return 1.5  # 50% bonus for severely underrepresented
        elif market_share < 0.1:  # Less than 10% market share
            return 1.3  # 30% bonus for underrepresented
        elif market_share < 0.15:  # Less than 15% market share
            return 1.15  # 15% bonus for slightly underrepresented
        elif market_share > 0.4:  # More than 40% market share
            return 0.9  # 10% penalty for overrepresented
        else:
            return 1.0  # No bonus/penalty for balanced representation
    
    def record_block(self, block: Block, complexity: ComputationalComplexity, reward: float, miner_address: str = None):
        """Record block metrics for dynamic adjustment and credit rewards to miner"""
        
        block_work_score = calculate_computational_work_score(complexity)
        
        # Update cumulative metrics
        self.cumulative_work_score += block_work_score
        self.total_coins_issued += reward
        
        # Record work score
        record = WorkScoreRecord(
            block_number=block.index,
            work_score=block_work_score,
            reward=reward,
            capacity=block.mining_capacity,
            problem_size=complexity.problem_size,
            measured_solve_time=complexity.measured_solve_time,
            measured_verify_time=complexity.measured_verify_time,
            asymmetry_ratio=complexity.asymmetry_time,
            timestamp=block.timestamp
        )
        
        self.work_score_history.append(record)
        
        # Update capacity-specific metrics
        self._update_capacity_metrics(block.mining_capacity, record)
        
        # Update verification time tracking
        self.recent_verification_times.append(complexity.measured_verify_time)
        self.recent_solve_times.append(complexity.measured_solve_time)
        
        # NEW: Credit reward to miner's wallet if blockchain state is available
        if self.blockchain_state and miner_address:
            # Credit reward to miner's balance
            self.blockchain_state.update_balance(miner_address, reward)
            
            # Create coinbase transaction
            from .blockchain_state import Transaction
            coinbase_tx = Transaction(
                sender="COINBASE",
                recipient=miner_address,
                amount=reward,
                timestamp=block.timestamp
            )
            
            # Add to transaction history
            self.blockchain_state.transaction_history[miner_address].append(coinbase_tx)
            
            print(f"💰 Credited {reward:.6f} coins to miner {miner_address}")
    
    def _update_capacity_metrics(self, capacity: ProblemTier, record: WorkScoreRecord):
        """Track performance by capacity - no assumptions about relative difficulty"""
        
        if capacity not in self.capacity_performance:
            self.capacity_performance[capacity] = CapacityMetrics(
                capacity=capacity,
                blocks_mined=0,
                total_work_score=0.0,
                avg_work_score=0.0,
                avg_solve_time=0.0,
                avg_asymmetry=0.0,
                recent_records=deque(maxlen=50)
            )
        
        metrics = self.capacity_performance[capacity]
        metrics.blocks_mined += 1
        metrics.total_work_score += record.work_score
        metrics.recent_records.append(record)
        
        # Recalculate averages from recent data
        recent = list(metrics.recent_records)
        metrics.avg_work_score = statistics.mean(r.work_score for r in recent)
        metrics.avg_solve_time = statistics.mean(r.measured_solve_time for r in recent)
        metrics.avg_asymmetry = statistics.mean(r.asymmetry_ratio for r in recent)
    
    def get_dynamic_block_time(self) -> float:
        """
        Block time emerges from actual network performance.
        
        Based on how long verification actually takes,
        not an arbitrary 10-minute target.
        """
        
        if len(self.recent_verification_times) < 10:
            # Bootstrap: use theoretical minimum
            return 1.0  # 1 second default
        
        # Median verification time (robust to outliers)
        median_verify = statistics.median(self.recent_verification_times)
        
        # Block time needs to be long enough for:
        # 1. Verification (median_verify)
        # 2. Network propagation (~10x verification for global consensus)
        # 3. Mining competition window (allow multiple miners to compete)
        
        network_propagation_multiplier = 10
        competition_multiplier = 5  # Allow 5x propagation time for competition
        
        target_block_time = median_verify * network_propagation_multiplier * competition_multiplier
        
        return max(1.0, target_block_time)  # Minimum 1 second
    
    def get_difficulty_adjustment(self) -> float:
        """
        Difficulty adjusts to maintain work score growth rate.
        
        Not targeting a specific block time or supply schedule,
        but rather maintaining healthy work score distribution.
        """
        
        if len(self.work_score_history) < 100:
            return 1.0  # No adjustment until enough data
        
        # Analyze work score distribution
        recent_100 = self.work_score_history[-100:]
        recent_50 = self.work_score_history[-50:]
        
        avg_work_recent = statistics.mean(r.work_score for r in recent_50)
        avg_work_historical = statistics.mean(r.work_score for r in recent_100)
        
        # If recent work is much higher/lower than historical, adjust
        if avg_work_historical > 0:
            work_ratio = avg_work_recent / avg_work_historical
            
            # Gentle adjustment: only change if ratio is outside [0.7, 1.3]
            if work_ratio > 1.3:
                # Work scores increasing - increase difficulty
                return 1.1  # 10% harder
            elif work_ratio < 0.7:
                # Work scores decreasing - decrease difficulty
                return 0.9  # 10% easier
        
        return 1.0  # No adjustment needed
    
    def get_capacity_market_dynamics(self) -> dict[ProblemTier, dict]:
        """
        Analyze economic equilibrium across capacities.
        
        Instead of forcing ratios, observe what the market naturally produces.
        If one capacity is over/under-represented, miners will adjust.
        """
        
        total_blocks = len(self.work_score_history)
        if total_blocks == 0:
            return {}
        
        dynamics = {}
        
        for capacity, metrics in self.capacity_performance.items():
            # Market share
            market_share = metrics.blocks_mined / total_blocks
            
            # Profitability indicator
            # Higher work score per time = more profitable
            work_per_second = metrics.avg_work_score / max(0.001, metrics.avg_solve_time)
            
            # Compare to network average
            all_work_scores = [r.work_score for r in self.work_score_history[-100:]]
            all_solve_times = [r.measured_solve_time for r in self.work_score_history[-100:]]
            avg_work_per_second = statistics.mean(
                w / max(0.001, t) for w, t in zip(all_work_scores, all_solve_times)
            )
            
            relative_profitability = work_per_second / avg_work_per_second if avg_work_per_second > 0 else 1.0
            
            dynamics[capacity] = {
                'blocks_mined': metrics.blocks_mined,
                'market_share': market_share,
                'avg_work_score': metrics.avg_work_score,
                'avg_solve_time': metrics.avg_solve_time,
                'work_per_second': work_per_second,
                'relative_profitability': relative_profitability,
                'status': self._get_capacity_status(market_share, relative_profitability)
            }
        
        return dynamics
    
    def _get_capacity_status(self, market_share: float, profitability: float) -> str:
        """Classify capacity health"""
        
        if profitability > 1.2:
            return "OVERPERFORMING - Expect more miners"
        elif profitability < 0.8:
            return "UNDERPERFORMING - Expect fewer miners"
        elif market_share < 0.05:
            return "UNDERREPRESENTED - 50% bonus applied"
        elif market_share < 0.1:
            return "UNDERREPRESENTED - 30% bonus applied"
        elif market_share < 0.15:
            return "UNDERREPRESENTED - 15% bonus applied"
        elif market_share > 0.4:
            return "OVERREPRESENTED - 10% penalty applied"
        else:
            return "BALANCED - No adjustment"
    
    def get_network_state(self) -> dict:
        """Complete network economics snapshot"""
        
        return {
            'cumulative_work_score': self.cumulative_work_score,
            'total_coins_issued': self.total_coins_issued,
            'coins_per_work_unit': self.total_coins_issued / max(1, self.cumulative_work_score),
            'current_deflation_factor': self._calculate_deflation_factor(),
            'blocks_mined': len(self.work_score_history),
            'dynamic_block_time': self.get_dynamic_block_time(),
            'difficulty_adjustment': self.get_difficulty_adjustment(),
            'capacity_dynamics': self.get_capacity_market_dynamics(),
            'recent_avg_work': self._get_recent_average_work(),
            'work_score_trend': self._analyze_work_score_trend()
        }
    
    def _analyze_work_score_trend(self) -> dict:
        """Analyze how work scores are evolving"""
        
        if len(self.work_score_history) < 100:
            return {'status': 'INSUFFICIENT_DATA'}
        
        recent_50 = [r.work_score for r in self.work_score_history[-50:]]
        older_50 = [r.work_score for r in self.work_score_history[-100:-50]]
        
        recent_mean = statistics.mean(recent_50)
        older_mean = statistics.mean(older_50)
        
        trend = (recent_mean - older_mean) / older_mean if older_mean > 0 else 0
        
        return {
            'recent_mean': recent_mean,
            'historical_mean': older_mean,
            'trend_percent': trend * 100,
            'status': 'INCREASING' if trend > 0.05 else 'DECREASING' if trend < -0.05 else 'STABLE'
        }


# ============================================
# ENHANCED: MARKET-DRIVEN TIER SELECTION
# ============================================

class MarketDrivenMining:
    """
    Miners choose tiers based on profitability.
    No forced ratios - market equilibrium emerges naturally.
    """
    
    def __init__(self, tokenomics: DynamicWorkScoreTokenomics):
        self.tokenomics = tokenomics
        self.hardware_capabilities = {}  # miner_id -> capabilities
    
    def estimate_profitability(self,
                              miner_hardware: HardwareProfile,
                              tier: ProblemTier) -> float:
        """
        Estimate profit for mining a given tier with specific hardware.
        
        Miners use this to choose which tier to mine.
        """
        
        # Get tier metrics from network
        tier_metrics = self.tokenomics.tier_performance.get(tier)
        
        if not tier_metrics:
            # No data yet - use theoretical estimates
            return self._estimate_theoretical_profitability(miner_hardware, tier)
        
        # Expected work score for this tier
        expected_work = tier_metrics.avg_work_score
        
        # Expected solve time for this hardware/tier combo
        # This depends on hardware capabilities
        expected_time = self._estimate_solve_time(miner_hardware, tier, tier_metrics.avg_solve_time)
        
        # Expected reward
        recent_avg = self.tokenomics._get_recent_average_work()
        if recent_avg > 0:
            work_ratio = expected_work / recent_avg
            base_reward = math.log1p(work_ratio)
        else:
            base_reward = 1.0
        
        deflation = self.tokenomics._calculate_deflation_factor()
        expected_reward = base_reward * deflation
        
        # Profit = reward / time (higher is better)
        profitability = expected_reward / max(0.001, expected_time)
        
        return profitability
    
    def select_capacity_for_hardware(self, miner_hardware: HardwareProfile) -> ProblemTier:
        """
        Select capacity based on hardware capability, not profitability.
        
        Hardware capability determines which capacity category the miner
        should work in, ensuring natural distribution across all capacities.
        """
        capability = miner_hardware.computational_capability
        
        # Map capability (0.0-1.0) to appropriate capacity
        if capability < 0.3:
            return ProblemTier.TIER_1_MOBILE
        elif capability < 0.5:
            return ProblemTier.TIER_2_DESKTOP
        elif capability < 0.7:
            return ProblemTier.TIER_3_WORKSTATION
        elif capability < 0.9:
            return ProblemTier.TIER_4_SERVER
        else:
            return ProblemTier.TIER_5_CLUSTER
    
    def _estimate_solve_time(self,
                            hardware: HardwareProfile,
                            tier: ProblemTier,
                            network_avg_time: float) -> float:
        """
        Estimate solve time for this hardware on this tier.
        
        Uses hardware capability score and network average.
        """
        
        # Hardware capability (0.0 to 1.0)
        capability = hardware.computational_capability
        
        # Better hardware solves faster
        # capability = 1.0 -> 1.0x network average
        # capability = 0.5 -> 2.0x network average
        # capability = 0.2 -> 5.0x network average
        
        time_multiplier = 1.0 / max(0.1, capability)
        
        estimated_time = network_avg_time * time_multiplier
        
        return estimated_time
    
    def _estimate_theoretical_profitability(self,
                                           hardware: HardwareProfile,
                                           tier: ProblemTier) -> float:
        """Fallback when no network data exists"""
        
        # Use tier size ranges to estimate
        size_ranges = {
            ProblemTier.TIER_1_MOBILE: (8, 12),
            ProblemTier.TIER_2_DESKTOP: (12, 16),
            ProblemTier.TIER_3_WORKSTATION: (16, 20),
            ProblemTier.TIER_4_SERVER: (20, 24),
            ProblemTier.TIER_5_CLUSTER: (24, 32),
        }
        
        min_size, max_size = size_ranges[tier]
        avg_size = (min_size + max_size) / 2
        
        # Theoretical work score: 2^n
        theoretical_work = 2 ** avg_size
        
        # Theoretical time based on hardware
        theoretical_time = theoretical_work / (hardware.computational_capability * 1e6)
        
        return theoretical_work / theoretical_time


# ============================================
# EXAMPLE: DYNAMIC SYSTEM IN ACTION
# ============================================

def demonstrate_dynamic_tokenomics():
    """Show how the system adapts without static targets"""
    
    tokenomics = DynamicWorkScoreTokenomics()
    market = MarketDrivenMining(tokenomics)
    
    print("=== DYNAMIC WORK SCORE TOKENOMICS ===\n")
    print("No static targets. System adapts to actual network behavior.\n")
    
    # Simulate 1000 blocks with varied hardware profiles
    hardware_types = [
        # Mobile hardware (20% of miners)
        HardwareProfile(
            hardware_type=HardwareType.MOBILE_LIGHTWEIGHT,
            computational_capability=0.15,
            cpu_cores=4,
            memory_gb=4.0,
            storage_gb=64.0,
            gpu_available=False,
            network_speed_mbps=50.0,
            battery_powered=True,
            energy_efficiency=0.8,
            accessibility_score=0.9
        ),
        # Desktop hardware (30% of miners)
        HardwareProfile(
            hardware_type=HardwareType.DESKTOP_STANDARD,
            computational_capability=0.5,
            cpu_cores=8,
            memory_gb=16.0,
            storage_gb=512.0,
            gpu_available=False,
            network_speed_mbps=100.0,
            battery_powered=False,
            energy_efficiency=0.6,
            accessibility_score=0.7
        ),
        # Workstation hardware (25% of miners)
        HardwareProfile(
            hardware_type=HardwareType.WORKSTATION_ADVANCED,
            computational_capability=0.7,
            cpu_cores=16,
            memory_gb=32.0,
            storage_gb=1024.0,
            gpu_available=True,
            network_speed_mbps=200.0,
            battery_powered=False,
            energy_efficiency=0.5,
            accessibility_score=0.6
        ),
        # Server hardware (20% of miners)
        HardwareProfile(
            hardware_type=HardwareType.SERVER_HIGH_PERFORMANCE,
            computational_capability=0.85,
            cpu_cores=32,
            memory_gb=64.0,
            storage_gb=2048.0,
            gpu_available=True,
            network_speed_mbps=1000.0,
            battery_powered=False,
            energy_efficiency=0.4,
            accessibility_score=0.3
        ),
        # Cluster hardware (5% of miners)
        HardwareProfile(
            hardware_type=HardwareType.CLUSTER_DISTRIBUTED,
            computational_capability=0.95,
            cpu_cores=64,
            memory_gb=128.0,
            storage_gb=4096.0,
            gpu_available=True,
            network_speed_mbps=10000.0,
            battery_powered=False,
            energy_efficiency=0.3,
            accessibility_score=0.1
        )
    ]
    
    for block_num in range(1, 1001):
        # Select hardware type based on distribution
        if block_num <= 200:  # 20% mobile
            hardware = hardware_types[0]
        elif block_num <= 500:  # 30% desktop
            hardware = hardware_types[1]
        elif block_num <= 750:  # 25% workstation
            hardware = hardware_types[2]
        elif block_num <= 950:  # 20% server
            hardware = hardware_types[3]
        else:  # 5% cluster
            hardware = hardware_types[4]
        
        # Miner selects capacity based on hardware capability
        selected_capacity = market.select_capacity_for_hardware(hardware)
        
        # Simulate mining
        problem = generate_subset_sum_problem(seed=f"block_{block_num}", tier=selected_capacity)
        solution = solve_subset_sum(problem)
        
        # Mock complexity measurement
        complexity = subset_sum_complexity(
            problem=problem,
            solution=solution,
            solve_time=random.uniform(0.1, 10.0),
            verify_time=random.uniform(0.001, 0.01),
            solve_memory=1000000,
            verify_memory=10000,
            energy_metrics=EnergyMetrics(0, 0, 0, 0, 0, 0, 0, 0, 0)
        )
        
        # Calculate reward
        mock_block = Block(
            index=block_num,
            timestamp=time.time(),
            previous_hash="",
            transactions=[],
            merkle_root="",
            problem=problem,
            solution=solution,
            complexity=complexity,
            mining_capacity=selected_capacity,
            cumulative_work_score=tokenomics.cumulative_work_score,
            block_hash=""
        )
        
        reward = tokenomics.calculate_block_reward(mock_block, complexity)
        tokenomics.record_block(mock_block, complexity, reward)
        
        # Print periodic updates
        if block_num in [1, 10, 100, 500, 1000]:
            print(f"\n=== Block {block_num} ===")
            state = tokenomics.get_network_state()
            print(f"Cumulative Work: {state['cumulative_work_score']:,.0f}")
            print(f"Total Coins Issued: {state['total_coins_issued']:.6f}")
            print(f"Coins per Work Unit: {state['coins_per_work_unit']:.10f}")
            print(f"Deflation Factor: {state['current_deflation_factor']:.6f}")
            print(f"Dynamic Block Time: {state['dynamic_block_time']:.2f}s")
            print(f"Recent Avg Work: {state['recent_avg_work']:,.0f}")
            
            print("\nCapacity Distribution:")
            for capacity, data in state['capacity_dynamics'].items():
                # Calculate diversity bonus for this capacity
                diversity_bonus = tokenomics._calculate_diversity_bonus(capacity)
                print(f"  {capacity.name}:")
                print(f"    Market Share: {data['market_share']*100:.1f}%")
                print(f"    Relative Profitability: {data['relative_profitability']:.2f}x")
                print(f"    Diversity Bonus: {diversity_bonus:.2f}x")
                print(f"    Status: {data['status']}")


if __name__ == "__main__":
    demonstrate_dynamic_tokenomics()
