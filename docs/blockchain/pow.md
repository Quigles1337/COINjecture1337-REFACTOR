COINjecture PoW and problems module spec (language-agnostic)

Responsibilities
- ProblemRegistry: register/generate/solve/verify problems
- Commit–reveal helpers and salt derivation
- Work score function and difficulty mapping to score target

Interfaces
- ProblemRegistry
  - generate(problem_type, seed, tier) -> problem:dict
  - solve(problem) -> solution:any
  - verify(problem, solution) -> bool

- Commit–reveal
  - derive_epoch_salt(parent_hash:[32]) -> epoch_salt:[32]
  - create_commitment(problem_params_bytes, miner_salt:[32], solution_hash:[32]) -> [32]
  - verify_commitment(problem_params_bytes, miner_salt, solution_hash, commitment) -> bool
  - compute_solution_hash(solution) -> solution_hash:[32]

Supported problems (initial)
- subset_sum: exact DP solver; verify sum(solution)==target
- factorization: naive scaffold; verify p*q==n (not secure)
- tsp: scaffold tour; verify node coverage and basic structure
- lattice (placeholder): stub with interface only; verifier returns False until implemented

Work score (baseline)
Inputs from `ComputationalComplexity`:
- measured_solve_time, measured_verify_time, measured_solve_space, measured_verify_space
- energy_metrics.{solve_energy_joules, verify_energy_joules}
- problem_class weight; problem_size; solution_quality
Score composition (example):
- time_asymmetry * sqrt(space_asymmetry) * problem_weight * size_factor * quality_score * energy_efficiency

Difficulty mapping
- EWMA of observed scores to maintain target block interval (e.g., 30s)
- next_target = clamp(alpha*prev_target + (1-alpha)*median_score, bounds)

Anti-grinding & Commitment Binding
- miner_salt must be unique per header
- epoch_salt = H(parent_hash||round(timestamp/epoch))
- solution_hash = H(solution)
- commitment = H(encode(problem_params)||miner_salt||epoch_salt||solution_hash)

Security Properties:
1. Binding: Valid commitment can only come from valid proof (collision resistance)
2. Hiding: Commitment reveals nothing about proof (solution hash hides actual solution)
3. Anti-grinding: Epoch salt prevents pre-mining many problems

Serialization of problem params
- Each problem defines `encode_params(problem)->bytes` and `decode_params(bytes)->problem`
- Encoding must be deterministic and versioned

Cross-language notes
- Use fixed width integers for sizes and counts
- Avoid floats in consensus-critical scoring if possible; use scaled integers

Non-goals
- Network broadcasting, storage, and DB schemas


