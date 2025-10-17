COINjecture consensus module spec (language-agnostic)

Responsibilities
- Validate headers and reveals
- Maintain block tree and choose best tip by cumulative work
- Build deterministic genesis

Header validation pipeline
1) Basic: version, timestamp (median-time-past), parent linkage
2) Commitment presence: proof_commitment non-zero; commitments_root shape
3) Difficulty: estimated_work(header) >= current_target
4) Fork-choice enqueue: insert node into tree, compute cumulative_work

Reveal validation (post-win)
1) Fetch bundle by CID (or receive inline)
2) Verify commitment: proof_commitment == H(encode(problem_params)||salt||epoch_salt)
3) Run fast verify (probabilistic) or zk proof; optional full verify
4) Update indices and persistence

Fork choice
- Tree keyed by parent_hash; node holds cumulative_work = parent.cw + block_work
- Tip = argmax(cumulative_work) with tie-breaker on earliest receipt time
- Reorg policy: apply headers along new path; bounded depth; emit events

Genesis
- Deterministic params: network_id, timestamp, fixed seed problem
- Zero difficulty gating; cumulative_work = work(genesis)

Finality
- Confirmation depth k (e.g., 20) for application-level finality hint

Safety and liveness considerations
- Orphan handling and header sync ranges
- DOS guards: max headers per peer per second; proof size caps

Cross-language notes
- Keep fork-choice math in integers
- Isolate floats in diagnostics only


