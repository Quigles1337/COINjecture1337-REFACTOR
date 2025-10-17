COINjecture core module spec (language-agnostic)

Responsibilities
- Define canonical on-chain structures: BlockHeader, Block, CommitmentLeaf
- Provide deterministic hashing, serialization, and Merkle tree construction
- Validate Merkle proofs and commitment bindings

Public types (logical schema)
- BlockHeader
  - version:u16
  - parent_hash:[32]
  - height:u32
  - timestamp:u64 (unix seconds)
  - commitments_root:[32]
  - tx_root:[32] (optional; zero for none)
  - difficulty_target:u32 (score target windowed)
  - cumulative_work:u128
  - miner_pubkey:[33] (compressed)
  - commit_nonce:u64
  - problem_type:u8
  - tier:u8
  - commit_epoch:u32
  - proof_commitment:[32] (binds off-chain proof bundle)
  - header_hash:[32] (computed)

- CommitmentLeaf (64 bytes)
  - left:[32]  // e.g., H(problem_params||salt)
  - right:[32] // e.g., H(solution_claim||meta) or H(CID)

- Block
  - header: BlockHeader
  - txs: bytes or opaque list (optional)

Serialization rules
- Field order is canonical as listed above
- Integers are little-endian for on-wire messages unless underlying stack requires big-endian (must be consistent network-wide)
- Hash inputs are byte sequences exactly equal to serialization of fields with no extra whitespace/newlines
- All Merkle tree leaves are 32-byte hashes; internal nodes: H(left||right)

Hashing
- Default: SHA-256 (single round) for commitments and merkle nodes; header_hash = SHA-256(serialize(header_without_hash))
- If an alternative hash is used, include `version` gating to preserve consensus

Merkle construction
- Pad to next power of two by duplicating last leaf
- Root = iterative pairwise H(left||right)
- Proof: list of sibling nodes with left/right position flags

Proof verification (pseudocode)
verify_merkle_proof(leaf, proof[]) -> root
- Start with h = H(leaf)
- For each (sibling, dir):
  - If dir == LEFT: h = H(sibling||h)
  - Else: h = H(h||sibling)
- Return h and compare to commitments_root

Commitment rules
- proof_commitment = H(serialize(problem_params)||salt)
- A CommitmentLeaf may store H(CID) in the right half to bind the off-chain bundle reference
- Byte ordering and encoding of params must be fixed by `pow.README.md`

Cross-language mapping
- Prefer fixed-size arrays for hashes and keys
- Use explicit endianness helpers
- Avoid language-specific floating serialization in headers; use integers only

Non-goals
- Networking, storage, and problem solving belong to other modules


