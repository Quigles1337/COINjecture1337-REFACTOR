# COINjecture API Specifications

## Overview

Language-agnostic API specifications for COINjecture's utility-based computational work system. These APIs enable interaction with the tokenomics engine, user submissions system, and network state management.

## Tokenomics APIs

### Core Work Score Calculation

```
calculate_work_score(complexity_metrics) -> float
```

**Input Parameters:**
- `complexity_metrics`: Object containing measured performance data
  - `measured_solve_time`: float (seconds)
  - `measured_verify_time`: float (seconds)
  - `measured_solve_memory`: int (bytes)
  - `measured_verify_memory`: int (bytes)
  - `energy_metrics`: Object with energy consumption data
  - `problem_class`: string (P, NP, NP-Complete, NP-Hard, PSPACE, EXPTIME)
  - `problem_size`: int (number of elements)
  - `solution_quality`: float (0.0 to 1.0)

**Output:**
- `float`: Calculated work score based on measured complexity

**Formula:**
```
work_score = 
    time_asymmetry_measured *           // measured_solve_time / measured_verify_time
    sqrt(space_asymmetry_measured) *    // sqrt(measured_solve_memory / measured_verify_memory)
    problem_class_weight *              // NP-Complete = 100, P = 1
    problem_size *                      // n (number of elements)
    solution_quality *                  // 1.0 for exact, <1.0 for approximate
    energy_efficiency                   // reference_energy / actual_energy
```

### Block Reward Calculation

```
calculate_block_reward(work_score, network_state) -> float
```

**Input Parameters:**
- `work_score`: float (from calculate_work_score)
- `network_state`: Object containing network metrics
  - `recent_avg_work`: float (rolling average of recent work scores)
  - `cumulative_work_score`: float (total network work)

**Output:**
- `float`: Block reward amount

**Formula:**
```
reward = log(1 + work_score/network_avg) * deflation_factor

where:
  deflation_factor = 1 / (2^(log2(cumulative_work)/10))
```

### Deflation Factor

```
get_deflation_factor(cumulative_work) -> float
```

**Input Parameters:**
- `cumulative_work`: float (total cumulative work score)

**Output:**
- `float`: Deflation factor (0.01 to 1.0)

### Tier Selection

```
select_optimal_tier(hardware_profile, tier_metrics) -> tier_id
```

**Input Parameters:**
- `hardware_profile`: Object containing hardware capabilities
  - `hardware_type`: enum (MOBILE, DESKTOP, WORKSTATION, SERVER, CLUSTER)
  - `computational_capability`: float (0.0 to 1.0)
  - `energy_efficiency`: float (0.0 to 1.0)
- `tier_metrics`: Object containing tier performance data
  - `avg_work_score`: float
  - `avg_solve_time`: float
  - `market_share`: float

**Output:**
- `tier_id`: enum (TIER_1_MOBILE, TIER_2_DESKTOP, TIER_3_WORKSTATION, TIER_4_SERVER, TIER_5_CLUSTER)

## User Submissions APIs

### Problem Submission

```
submit_problem(problem_spec, bounty, aggregation_strategy) -> submission_id
```

**Input Parameters:**
- `problem_spec`: Object containing problem definition
  - `problem_type`: string (subset_sum, factorization, tsp, etc.)
  - `problem_template`: object (problem-specific parameters)
  - `seeding_strategy`: string (how to generate problem instances)
- `bounty`: float (reward amount for solutions)
- `aggregation_strategy`: enum (ANY, BEST, MULTIPLE, STATISTICAL)
- `aggregation_params`: object (strategy-specific parameters)

**Output:**
- `submission_id`: string (unique identifier for the submission)

### Get Eligible Problems

```
get_eligible_problems(solver_tier) -> list[submission]
```

**Input Parameters:**
- `solver_tier`: enum (TIER_1_MOBILE, TIER_2_DESKTOP, etc.)

**Output:**
- `list[submission]`: Array of problem submissions available for solving

### Record Solution

```
record_solution(submission_id, solution_record) -> bool
```

**Input Parameters:**
- `submission_id`: string (from submit_problem)
- `solution_record`: Object containing solution data
  - `block_number`: int
  - `block_hash`: string
  - `miner_address`: string
  - `problem_instance`: object (specific problem instance solved)
  - `solution`: any (solution data)
  - `solution_quality`: float (0.0 to 1.0)
  - `work_score`: float
  - `solve_time`: float (seconds)
  - `energy_used`: float (joules)
  - `verified`: bool
  - `verification_time`: float (seconds)

**Output:**
- `bool`: Success status

### Aggregate Solutions

```
aggregate_solutions(submission_id, strategy) -> result
```

**Input Parameters:**
- `submission_id`: string
- `strategy`: enum (ANY, BEST, MULTIPLE, STATISTICAL)

**Output:**
- `result`: Object containing aggregated solution data

## Network State APIs

### Tier Metrics

```
get_tier_metrics(tier_id) -> tier_metrics
```

**Input Parameters:**
- `tier_id`: enum (TIER_1_MOBILE, TIER_2_DESKTOP, etc.)

**Output:**
- `tier_metrics`: Object containing tier performance data
  - `blocks_mined`: int
  - `total_work_score`: float
  - `avg_work_score`: float
  - `avg_solve_time`: float
  - `avg_asymmetry`: float
  - `market_share`: float

### Network State

```
get_network_state() -> network_state
```

**Output:**
- `network_state`: Object containing global network metrics
  - `cumulative_work_score`: float
  - `total_coins_issued`: float
  - `coins_per_work_unit`: float
  - `current_deflation_factor`: float
  - `blocks_mined`: int
  - `dynamic_block_time`: float (seconds)
  - `difficulty_adjustment`: float
  - `recent_avg_work`: float
  - `work_score_trend`: object

### Profitability Estimation

```
estimate_profitability(hardware_profile, tier_id) -> float
```

**Input Parameters:**
- `hardware_profile`: Object (same as select_optimal_tier)
- `tier_id`: enum (tier to estimate for)

**Output:**
- `float`: Estimated profitability (work_score per second)

## Aggregation Strategies

### ANY
- **Purpose**: First valid solution wins
- **Parameters**: None
- **Use case**: Urgent problems needing quick solutions

### BEST
- **Purpose**: Highest quality solution wins
- **Parameters**: 
  - `max_blocks`: int (maximum blocks to wait)
  - `early_bonus_decay`: float (decay factor for early solutions)
- **Use case**: Problems where solution quality matters

### MULTIPLE
- **Purpose**: Collect multiple diverse solutions
- **Parameters**:
  - `target_count`: int (number of solutions to collect)
- **Use case**: Problems with multiple valid approaches

### STATISTICAL
- **Purpose**: Collect statistical sample of solutions
- **Parameters**:
  - `sample_size`: int (number of solutions for statistical analysis)
- **Use case**: Research problems needing solution distribution analysis

## Error Handling

All APIs should return structured error responses:

```
{
  "error": true,
  "error_code": "INVALID_PARAMETERS",
  "message": "Detailed error description",
  "details": {} // Additional error context
}
```

Common error codes:
- `INVALID_PARAMETERS`: Invalid input parameters
- `SUBMISSION_NOT_FOUND`: Submission ID not found
- `TIER_NOT_SUPPORTED`: Hardware tier not supported
- `INSUFFICIENT_DATA`: Not enough data for calculation
- `VERIFICATION_FAILED`: Solution verification failed

## Rate Limiting

APIs should implement appropriate rate limiting:
- **Read operations**: 100 requests per minute
- **Write operations**: 10 requests per minute
- **Heavy computations**: 1 request per minute

## Authentication

For user submissions and solution recording:
- **Method**: Cryptographic signatures
- **Required**: Wallet address and signature
- **Optional**: API keys for higher rate limits

## Data Formats

### Timestamps
- **Format**: Unix timestamp (float)
- **Precision**: Seconds with decimal places

### Monetary Values
- **Format**: Float with appropriate decimal precision
- **Unit**: Native token units

### Problem Data
- **Format**: JSON object
- **Validation**: Schema validation required

### Solution Data
- **Format**: JSON object
- **Validation**: Solution-specific validation required



