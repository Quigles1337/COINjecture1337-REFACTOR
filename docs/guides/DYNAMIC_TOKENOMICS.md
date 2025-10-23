# COINjecture Dynamic Work Score Tokenomics

> **Note**: This describes the testnet tokenomics. Mainnet parameters may differ based on testnet results.

## Overview

COINjecture implements an adaptive tokenomics system that responds to actual network behavior rather than using static parameters. Tokenomics emerge from measured computational work and real-world market forces.

## Core Architecture: Hardware-Class-Relative Competition

### Traditional PoW Systems
```
Competition Model: "Everyone vs Everyone"
├─ Mobile phone vs ASIC farm
├─ Result: Mobile phone loses 100% of the time
└─ Outcome: Only the biggest hardware survives
```

### COINjecture
```
Competition Model: "Mobile vs Mobile, Server vs Server"
├─ Mobile phone vs other mobile phones
├─ Server vs other servers (on optimization, not size)
└─ Outcome: Natural distribution across ALL hardware classes
```

## Key Principles

### 1. No Static Targets
- **No fixed supply limits** (like Bitcoin's 21M)
- **No fixed block times** (like Bitcoin's 10 minutes)
- **No fixed difficulty schedules**
- Everything emerges from measured work scores

### 2. Work Score Based Rewards
Rewards are calculated purely from:
- **Time asymmetry**: solve_time / verify_time
- **Space asymmetry**: solve_memory / verify_memory  
- **Problem complexity**: NP-Complete problems get higher weights
- **Energy efficiency**: lower energy per operation = higher score
- **Solution quality**: exact solutions vs approximations

### 3. Dynamic Adaptation
- **Block time** emerges from verification performance
- **Difficulty** adjusts to maintain work score distribution
- **Deflation** occurs naturally as cumulative work grows
- **Tier distribution** balances through market forces

### 4. User Submissions Integration
- **Computational proof**: Subset Sum (NP-Complete) provides verifiable asymmetry
- **Practical utility**: User submissions system allows solving real problems
- **Aggregation strategies**: ANY (first solution), BEST (quality competition), MULTIPLE (diverse solutions), STATISTICAL (sample collection)
- **Bounty system**: Users pay for solutions, miners earn from both block rewards and bounties

## Architecture Components

### DynamicWorkScoreTokenomics
```python
class DynamicWorkScoreTokenomics:
    # Track actual network behavior
    work_score_history: list[WorkScoreRecord]
    capacity_performance: dict[ProblemTier, CapacityMetrics]
    
    # Dynamic supply emerges from network growth
    cumulative_work_score: float
    total_coins_issued: float
    
    # Dynamic block time emerges from verification performance
    recent_verification_times: deque
    recent_solve_times: deque
```

### Hardware-Based Capacity Selection
```python
class MarketDrivenMining:
    def select_capacity_for_hardware(self, hardware: HardwareProfile) -> ProblemTier:
        # Miners choose capacity based on hardware capability
        # Hardware capability determines capacity category
        # No profitability-based selection - hardware matching only
        capability = hardware.computational_capability
        
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
```

### Hardware Profile System
```python
@dataclass
class HardwareProfile:
    hardware_type: HardwareType
    computational_capability: float  # 0.0 to 1.0
    cpu_cores: int
    memory_gb: float
    energy_efficiency: float
    accessibility_score: float
```

## Problem Capacities (Hardware Compatibility Categories)

### Tier 1: Mobile (8-12 elements)
- **Target**: Smartphones, tablets, IoT devices
- **Problem size**: Small subset sum problems
- **Characteristics**: Energy efficiency, fast iteration
- **Competition**: Mobile vs mobile optimization

### Tier 2: Desktop (12-16 elements)  
- **Target**: Laptops, basic desktops
- **Problem size**: Medium subset sum problems
- **Characteristics**: Balanced performance
- **Competition**: Desktop vs desktop optimization

### Tier 3: Workstation (16-20 elements)
- **Target**: Gaming PCs, development machines
- **Problem size**: Large subset sum problems
- **Characteristics**: Higher compute power
- **Competition**: Workstation vs workstation optimization

### Tier 4: Server (20-24 elements)
- **Target**: Dedicated servers, cloud instances
- **Problem size**: Very large subset sum problems
- **Characteristics**: Massive parallel processing
- **Competition**: Server vs server optimization

### Tier 5: Cluster (24-32 elements)
- **Target**: Multi-node systems, supercomputers
- **Problem size**: Extremely large subset sum problems
- **Characteristics**: Distributed computing
- **Competition**: Cluster vs cluster optimization

## Reward Calculation

### Base Formula
```python
def calculate_block_reward(block, complexity):
    # 1. Get work score from complexity
    work_score = calculate_computational_work_score(complexity)
    
    # 2. Compare to recent network average
    recent_avg = get_recent_average_work()
    work_ratio = work_score / recent_avg
    
    # 3. Logarithmic scaling to prevent extremes
    base_reward = log(1 + work_ratio)
    
    # 4. Apply natural deflation
    deflation_factor = calculate_deflation_factor()
    
    # 5. Apply diversity bonus for underrepresented capacities
    diversity_bonus = calculate_diversity_bonus(block.mining_capacity)
    
    # 6. Final reward
    return base_reward * deflation_factor * diversity_bonus
```

### Work Score Components
```python
work_score = (
    time_asymmetry_measured *           # solve_time / verify_time
    sqrt(space_asymmetry_measured) *    # sqrt(solve_memory / verify_memory)
    problem_weight *                    # NP-Complete = 100x, P = 1x
    size_factor *                       # problem_size
    quality_score *                     # 1.0 for exact, <1.0 for approximate
    energy_efficiency_score             # efficiency bonus/penalty
)
```

## Diversity Bonus Mechanism

### Purpose
The diversity bonus system provides economic incentives to promote network diversity across all capacity levels, preventing any single capacity from dominating the network.

### Bonus Structure
```python
def calculate_diversity_bonus(capacity: ProblemTier) -> float:
    market_share = get_capacity_market_share(capacity)
    
    if market_share < 0.05:      # Less than 5% market share
        return 1.5              # 50% bonus for severely underrepresented
    elif market_share < 0.1:    # Less than 10% market share  
        return 1.3              # 30% bonus for underrepresented
    elif market_share < 0.15:   # Less than 15% market share
        return 1.15             # 15% bonus for slightly underrepresented
    elif market_share > 0.4:    # More than 40% market share
        return 0.9              # 10% penalty for overrepresented
    else:
        return 1.0              # No bonus/penalty for balanced representation
```

### Economic Impact
- **Underrepresented capacities** receive bonus rewards (15-50% increase)
- **Overrepresented capacities** receive penalty rewards (10% decrease)
- **Balanced capacities** receive neutral rewards
- **Natural market equilibrium** emerges through economic incentives

## Capacity Economics

### Mobile Capacity Economics
```python
mobile_miner = {
    'capacity': ProblemTier.TIER_1_MOBILE,
    'problem_size': 10,
    'solve_time': 0.5,      # Fast (optimized for mobile)
    'energy': 2.0,          # Efficient (battery-optimized)
    'work_score': 1500,     # High (excellent efficiency)
    'base_reward': 1.2,     # Base reward
    'diversity_bonus': 1.0, # No bonus/penalty (balanced)
    'total_reward': 1.2     # Final reward
}

# Competition within capacity: mobile vs mobile
# Hardware capability determines capacity selection
# Work score determines base reward, diversity bonus adjusts final reward
```

### Cluster Capacity Economics
```python
cluster_miner_underrepresented = {
    'capacity': ProblemTier.TIER_5_CLUSTER,
    'problem_size': 28,
    'solve_time': 1000,     # Slow (bad algorithm)
    'energy': 50000,        # Expensive
    'work_score': 800,      # Low (inefficient)
    'base_reward': 0.6,     # Low base reward
    'diversity_bonus': 1.3, # 30% bonus (underrepresented)
    'total_reward': 0.78    # Final reward with bonus
}

# High-end hardware can earn more through diversity bonuses
# Work score determines base reward, diversity bonus provides additional incentive
# Hardware capability determines capacity, not profitability optimization
```

## Economic Equilibrium

### Market Dynamics
- **Capacity 1**: Energy efficiency + fast iteration = competitive
- **Capacity 2**: Balanced performance = average profitability  
- **Capacity 3**: Higher energy costs = must optimize
- **Capacity 4**: High energy costs = must optimize heavily
- **Capacity 5**: Massive problems IF optimized well = high rewards + diversity bonuses

### Hardware-Based Balancing
1. **Hardware capability matching**: Miners select capacity based on hardware capability
2. **Work score optimization**: Miners optimize within their capacity for higher base rewards
3. **Diversity incentives**: Underrepresented capacities receive bonus rewards
4. **Overrepresentation penalties**: Overrepresented capacities receive penalty rewards
5. **Natural equilibrium**: Market distributes based on hardware capability + optimization + diversity

## Implementation Requirements

### Core Functions
- `calculate_computational_work_score(complexity)` - Work score calculation
- `calculate_block_reward(block, complexity)` - Dynamic reward calculation with diversity bonus
- `get_dynamic_block_time()` - Block time from verification performance
- `get_difficulty_adjustment()` - Difficulty from work score distribution
- `select_capacity_for_hardware(hardware)` - Hardware-based capacity selection
- `calculate_diversity_bonus(capacity)` - Diversity bonus calculation

### Data Structures
- `WorkScoreRecord` - Individual block work metrics
- `CapacityMetrics` - Performance tracking per capacity
- `HardwareProfile` - Miner hardware capabilities
- `DynamicWorkScoreTokenomics` - Main tokenomics engine

### Network State Tracking
- Work score history (rolling window)
- Capacity performance metrics
- Verification time distribution
- Cumulative work score growth
- Deflation factor calculation
- Diversity bonus tracking

## Architectural Implications

### Mobile Devices
Can participate due to capacity system matching hardware capabilities. Energy efficiency and optimization matter more than raw compute power.

### Algorithm Optimization
Affects profitability more than hardware scale. Competition within capacity classes rewards efficient algorithms.

### User Submissions
Provides practical utility beyond proof-of-work. Computational work markets enable real problem solving.

### Aggregation Strategies
Enable different use cases for computational work: first solution, best solution, multiple solutions, statistical sampling.

## Comparison with Traditional PoW

### Bitcoin
```
├─ SHA-256 hashing (arbitrary work)
├─ Fixed difficulty adjustment
└─ Consensus only
```

### COINjecture
```
├─ NP-Complete solving (verifiable work)
├─ Work-score-based adjustment
└─ Consensus + computational work markets
```

## Design Principle

The architecture separates hardware capability classes from reward mechanisms. Competition occurs within capacities based on algorithmic optimization and measured performance, not across capacities based on hardware scale. Diversity bonuses ensure balanced participation across all capacity levels.

## Key Takeaway

Capacities are hardware compatibility categories. Work score measures computational complexity. User submissions provide practical utility. The architecture enables distributed participation across heterogeneous hardware through measured performance metrics and diversity incentives.
