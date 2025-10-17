COINjecture networking module spec (language-agnostic)

Responsibilities
- libp2p host wrapper, gossipsub topics, simple RPC for sync and proof fetch
- Message encoding and compression

Topics (gossipsub)
- /coinj/headers/1.0.0         // announce new headers
- /coinj/commit-reveal/1.0.0   // reveal bundles and CIDs
- /coinj/requests/1.0.0        // fetch requests (headers/proofs)
- /coinj/responses/1.0.0       // fetch responses

RPC (request/response)
- get_headers(start_height, count) -> [headers]
- get_block_by_hash(hash) -> header or full block
- get_proof_by_cid(cid) -> bundle bytes

Message schemas (JSON/protobuf logical fields)
- HeaderMsg { header_bytes, tip_work:u128, peer_id }
- RevealMsg { cid, commitment:[32], problem_type:u8, tier:u8 }
- RequestMsg { kind, params }
- ResponseMsg { status, payload }

Compression
- Use zstd/snappy for payloads > 1KB; indicate codec in envelope

Rate limits and validation
- Per-peer quotas; drop malformed or oversized messages
- Deduplicate by header_hash/commitment

Security and identity
- Use libp2p noise; sign control RPCs if needed (out of scope for consensus)

Cross-language notes
- Avoid dynamic typing on the wire; define explicit numeric tags or field names


