# COINjecture: Utility-Based Computational Work ($BEANS)

Satoshi Nakamoto's Bitcoin whitepaper was brilliant in its core insights: proof-of-work for consensus, blocks storing transactions in an immutable ledger, and decentralized participation without trusted intermediaries. These foundational ideas remain sound.

COINjecture builds on this foundation, evolving the concept: instead of arbitrary work (hashing), we prove that meaningful computational work was actually done, with practical utility built in. The native token is $BEANS.

## The Fundamental Shift

### From arbitrary work to verifiable work

- **Bitcoin**: Hash until you find a number (arbitrary computation) - brilliant for consensus, but the work itself has no inherent value
- **COINjecture**: Solve NP-Complete problems (verifiable complexity: O(2^n) solve, O(n) verify) - the work itself proves meaningful computational effort

### From predetermined schedules to real-world dynamics

- **Bitcoin**: Fixed supply (21M), fixed block time (10 min), fixed halving schedule - elegant simplicity that worked
- **COINjecture**: Supply emerges from cumulative work, block time from verification performance, deflation from network growth - parameters adapt to actual network behavior

### From mining to solving

- Not mining for coins
- Solving problems to prove computational work
- Optionally solving real problems users submit and pay for

## Utility-Based Architecture

### Two layers of utility

1. **Consensus layer**: Proof of computational work via NP-Complete problems
   - Subset Sum provides verifiable asymmetry
   - Work score measures actual complexity
   - On-chain proof that work was done

2. **Utility layer**: User-submitted computational work markets
   - Users submit problems they need solved
   - Solvers earn block rewards + user bounties
   - Aggregation strategies: ANY, BEST, MULTIPLE, STATISTICAL
   - Real economic demand drives real computational supply

## Tokenomics Dictated by Reality

### No arbitrary parameters. Everything emerges from measured events

- **Supply**: Cumulative work score determines coins issued
- **Deflation**: Natural deflation as cumulative work grows (each new unit represents smaller fraction of total)
- **Block time**: Emerges from measured verification performance
- **Difficulty**: Adjusts to maintain work score distribution
- **Rewards**: Based on work_score relative to network average

### Formula

```
reward = log(1 + work_score/network_avg) * deflation_factor

where:
  work_score = f(measured_solve_time, measured_verify_time, energy, quality)
  deflation_factor = 1 / (2^(log2(cumulative_work)/10))
```

## Tier System: Hardware Compatibility Categories

### Not reward brackets - hardware compatibility classes

- **Tier 1 (Mobile)**: 8-12 elements, optimized for energy efficiency
- **Tier 2 (Desktop)**: 12-16 elements, balanced performance
- **Tier 3 (Workstation)**: 16-20 elements, higher compute
- **Tier 4 (Server)**: 20-24 elements, must optimize algorithms
- **Tier 5 (Cluster)**: 24-32 elements, distributed computation

### Key principle

- Work score independent of tier
- Competition within tiers, not across tiers
- Profitability = work_score / (solve_time * energy_cost)
- Mobile phones compete with mobile phones, servers with servers

## API Specifications

Detailed API specifications are available in [API.README.md](API.README.md), including:

- **Tokenomics APIs**: Work score calculation, block rewards, deflation factors
- **User Submissions APIs**: Problem submission, solution recording, aggregation
- **Network State APIs**: Tier metrics, network state, profitability estimation
- **Aggregation Strategies**: ANY, BEST, MULTIPLE, STATISTICAL
- **Error Handling**: Structured error responses and common error codes

## What Makes This DeFi

### Decentralized Finance for Computation

- **Decentralized supply**: Anyone can solve problems with any hardware class
- **Market-driven demand**: Users submit problems, set bounties
- **Algorithmic pricing**: Rewards based on measured work, not arbitrary schedules
- **Transparent economics**: All metrics on-chain (work scores, solve times, energy)
- **Permissionless participation**: No gatekeepers, no minimum hardware requirements

### Real-world economic forces

- High demand for Tier 3 problems → more solvers enter Tier 3 → competition increases → work scores normalize
- Efficient algorithm discovered → solver earns more per problem → others optimize → network efficiency improves
- Energy prices rise → energy-efficient tiers become more profitable → natural rebalancing

## Comparison: Bitcoin vs COINjecture

### Bitcoin (Consensus-Only Chain)

- Proof mechanism: SHA-256 hashing (arbitrary work) - brilliant for consensus
- Tokenomics: Predetermined schedule (21M supply, 4-year halvings) - elegant simplicity
- Utility: Consensus only - achieved its goal perfectly
- Participation: Hardware arms race (ASICs dominate) - unintended consequence of success

### COINjecture (Utility-Based Chain)

- Proof mechanism: NP-Complete solving (verifiable work)
- Tokenomics: Emergent from real-world events (work scores, user demand)
- Utility: Consensus + computational work markets
- Participation: Algorithm optimization within hardware classes

## Design Principle

The architecture separates hardware capability classes from reward mechanisms. Tokenomics emerge from measured performance and market forces, not predetermined schedules. This enables distributed participation across heterogeneous hardware and creates a computational work market on-chain.

## What This Enables

- **Computational work markets**: DeFi for computation
- **Utility-driven tokenomics**: Supply/demand based on real work
- **Algorithm optimization economy**: Compete on efficiency, not hardware scale
- **Practical utility**: Solve real problems, not just maintain consensus
- **Distributed participation**: All hardware classes economically viable

## Closing

Satoshi's vision was revolutionary: decentralized consensus through proof-of-work, immutable transaction history, and permissionless participation. Bitcoin achieved this brilliantly.

COINjecture builds on this foundation, evolving the concept with complexity theory and real-world utility.

Not mining - solving.

Not arbitrary work - verifiable work.

Not predetermined schedules - emergent economics.

Not centralized - distributed by design.

**COINjecture: Utility-based computational work, built on Satoshi's foundation.**
