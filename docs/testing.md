COINjecture tests spec (language-agnostic)

Integration scenarios
- Header-first sync across 3 nodes
- Commit–reveal success path; bundle retrievable by CID; archive pinning
- Invalid reveal rejected (mismatched commitment)
- Reorg: longer cumulative-work branch overtakes current tip

Invariants
- Commitment binding/hiding holds for all accepted blocks
- Fork-choice picks max cumulative work deterministically
- Light nodes never accept blocks without valid commitments

Running tests
- python -m pytest tests -q
- or go/rust equivalents following the same scenarios and fixtures

Determinism
- Use fixed seeds for problem generation where appropriate


