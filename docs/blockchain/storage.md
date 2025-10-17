COINjecture storage module spec (language-agnostic)

Responsibilities
- Local persistent store for headers/blocks/indices
- IPFS client integration for proof bundles
- Pruning strategies per node role

DB schema (column families/keys)
- headers: key=header_hash -> header_bytes
- blocks: key=block_hash -> block_bytes (optional body)
- tips: single key -> set of tip hashes
- work_index: key=height -> cumulative_work:u128
- commit_index: key=commitment:[32] -> cid
- peer_index: key=peer_id -> meta

Pruning modes
- light: keep headers + commit_index only
- full: keep recent N epochs of bundles (configurable)
- archive: keep all; disable IPFS GC; pin bundles

IPFS client
- add(obj_bytes) -> cid
- get(cid) -> bytes
- pin(cid) -> ok
- health checks and backoff on failure

Durability and batching
- Batch writes for header sequences
- fsync on finalized ranges (k-deep)

Cross-language notes
- Prefer LevelDB/RocksDB bindings with column families
- Use deterministic byte encodings for keys


