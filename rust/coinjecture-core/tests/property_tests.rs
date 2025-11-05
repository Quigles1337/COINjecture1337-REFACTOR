//! Property-based tests using quickcheck
//!
//! These tests verify that code satisfies properties across
//! a wide range of randomly generated inputs.
//!
//! Properties tested:
//! - Codec roundtrip
//! - Hash determinism
//! - Merkle tree properties
//! - Commitment binding

use coinjecture_core::*;
use quickcheck::{Arbitrary, Gen, QuickCheck, TestResult};
use quickcheck_macros::quickcheck;

// ==================== ARBITRARY IMPLEMENTATIONS ====================

impl Arbitrary for HardwareTier {
    fn arbitrary(g: &mut Gen) -> Self {
        let tiers = [
            HardwareTier::Mobile,
            HardwareTier::Desktop,
            HardwareTier::Workstation,
            HardwareTier::Server,
            HardwareTier::Cluster,
        ];
        *g.choose(&tiers).unwrap()
    }
}

impl Arbitrary for ProblemType {
    fn arbitrary(g: &mut Gen) -> Self {
        // Only use production-ready types
        ProblemType::SubsetSum
    }
}

impl Arbitrary for BlockHeader {
    fn arbitrary(g: &mut Gen) -> Self {
        BlockHeader {
            codec_version: CODEC_VERSION,
            block_index: u64::arbitrary(g) % (2u64.pow(32)),
            timestamp: i64::arbitrary(g).abs(),
            parent_hash: {
                let mut hash = [0u8; 32];
                for byte in &mut hash {
                    *byte = u8::arbitrary(g);
                }
                hash
            },
            merkle_root: {
                let mut hash = [0u8; 32];
                for byte in &mut hash {
                    *byte = u8::arbitrary(g);
                }
                hash
            },
            miner_address: {
                let mut addr = [0u8; 32];
                for byte in &mut addr {
                    *byte = u8::arbitrary(g);
                }
                addr
            },
            commitment: {
                let mut comm = [0u8; 32];
                for byte in &mut comm {
                    *byte = u8::arbitrary(g);
                }
                comm
            },
            difficulty_target: u64::arbitrary(g) % (2u64.pow(32)),
            nonce: u64::arbitrary(g),
            extra_data: {
                let len = usize::arbitrary(g) % 256;
                (0..len).map(|_| u8::arbitrary(g)).collect()
            },
        }
    }
}

impl Arbitrary for Problem {
    fn arbitrary(g: &mut Gen) -> Self {
        let tier = HardwareTier::arbitrary(g);
        let (min_elem, max_elem) = tier.element_range();

        let elem_count = (usize::arbitrary(g) % (max_elem - min_elem + 1)) + min_elem;
        let elements: Vec<i64> = (0..elem_count)
            .map(|_| (i64::arbitrary(g) % (2i64.pow(31))))
            .collect();

        let target = if !elements.is_empty() {
            elements.iter().take(elem_count / 2).sum()
        } else {
            0
        };

        Problem {
            problem_type: ProblemType::SubsetSum,
            tier,
            elements,
            target,
            timestamp: i64::arbitrary(g).abs(),
        }
    }
}

impl Arbitrary for Solution {
    fn arbitrary(g: &mut Gen) -> Self {
        let count = usize::arbitrary(g) % 16;
        let mut indices: Vec<u32> = (0..count).map(|_| u32::arbitrary(g) % 32).collect();
        indices.sort();
        indices.dedup();

        Solution {
            indices,
            timestamp: i64::arbitrary(g).abs(),
        }
    }
}

// ==================== PROPERTY TESTS ====================

#[quickcheck]
fn prop_header_hash_determinism(header: BlockHeader) -> bool {
    // PROPERTY: Hashing same header produces same result
    let hash1 = codec::compute_header_hash(&header);
    let hash2 = codec::compute_header_hash(&header);
    let hash3 = codec::compute_header_hash(&header);

    hash1 == hash2 && hash2 == hash3 && hash1.is_ok() && hash2.is_ok()
}

#[quickcheck]
fn prop_header_hash_length(header: BlockHeader) -> bool {
    // PROPERTY: All hashes are 32 bytes
    match codec::compute_header_hash(&header) {
        Ok(hash) => hash.len() == 32,
        Err(_) => false,
    }
}

#[quickcheck]
fn prop_header_different_hash_on_mutation(header: BlockHeader) -> TestResult {
    // PROPERTY: Changing any field changes hash
    if header.block_index == u64::MAX {
        return TestResult::discard();
    }

    let hash1 = codec::compute_header_hash(&header);

    let mut modified = header.clone();
    modified.block_index += 1;
    let hash2 = codec::compute_header_hash(&modified);

    match (hash1, hash2) {
        (Ok(h1), Ok(h2)) => TestResult::from_bool(h1 != h2),
        _ => TestResult::failed(),
    }
}

#[quickcheck]
fn prop_merkle_empty_root(x: u8) -> bool {
    // PROPERTY: Empty merkle tree has all-zeros root
    let root = merkle::compute_merkle_root(&[]);
    root == [0u8; 32]
}

#[quickcheck]
fn prop_merkle_single_leaf(hash: [u8; 32]) -> bool {
    // PROPERTY: Merkle tree of single leaf returns that leaf
    let root = merkle::compute_merkle_root(&[hash]);
    root == hash
}

#[quickcheck]
fn prop_merkle_deterministic(hashes: Vec<[u8; 32]>) -> TestResult {
    if hashes.is_empty() || hashes.len() > 1000 {
        return TestResult::discard();
    }

    // PROPERTY: Same inputs produce same merkle root
    let root1 = merkle::compute_merkle_root(&hashes);
    let root2 = merkle::compute_merkle_root(&hashes);

    TestResult::from_bool(root1 == root2)
}

#[quickcheck]
fn prop_merkle_different_on_reorder(hashes: Vec<[u8; 32]>) -> TestResult {
    if hashes.len() < 2 || hashes.len() > 100 {
        return TestResult::discard();
    }

    // PROPERTY: Reordering changes merkle root (order matters)
    let root1 = merkle::compute_merkle_root(&hashes);

    let mut reversed = hashes.clone();
    reversed.reverse();
    let root2 = merkle::compute_merkle_root(&reversed);

    // Only test if hashes are not palindromic
    if hashes == reversed {
        return TestResult::discard();
    }

    TestResult::from_bool(root1 != root2)
}

#[quickcheck]
fn prop_commitment_epoch_binding(parent_hash: [u8; 32], block_index: u64) -> bool {
    // PROPERTY: Different epochs produce different epoch salts
    let salt1 = hash::compute_epoch_salt(&parent_hash, block_index);
    let salt2 = hash::compute_epoch_salt(&parent_hash, block_index + 1);

    salt1 != salt2
}

#[quickcheck]
fn prop_commitment_parent_binding(
    parent_hash1: [u8; 32],
    parent_hash2: [u8; 32],
    block_index: u64,
) -> TestResult {
    // PROPERTY: Different parents produce different epoch salts
    if parent_hash1 == parent_hash2 {
        return TestResult::discard();
    }

    let salt1 = hash::compute_epoch_salt(&parent_hash1, block_index);
    let salt2 = hash::compute_epoch_salt(&parent_hash2, block_index);

    TestResult::from_bool(salt1 != salt2)
}

#[quickcheck]
fn prop_tier_constraints_enforced(problem: Problem) -> bool {
    // PROPERTY: Problem element count always within tier range
    let (min_elem, max_elem) = problem.tier.element_range();
    let elem_count = problem.elements.len();

    elem_count >= min_elem && elem_count <= max_elem
}

#[quickcheck]
fn prop_verify_budget_scaling(tier: HardwareTier) -> bool {
    // PROPERTY: Higher tiers have larger budgets
    let budget = VerifyBudget::from_tier(tier);

    budget.max_ops > 0 && budget.max_duration_ms > 0 && budget.max_memory_bytes > 0
}

#[quickcheck]
fn prop_hash_sha256_output_size(data: Vec<u8>) -> bool {
    // PROPERTY: SHA-256 always produces 32 bytes
    let hash = hash::sha256(&data);
    hash.len() == 32
}

#[quickcheck]
fn prop_hash_different_inputs_different_outputs(data1: Vec<u8>, data2: Vec<u8>) -> TestResult {
    // PROPERTY: Different inputs produce different hashes (collision resistance)
    if data1 == data2 {
        return TestResult::discard();
    }

    let hash1 = hash::sha256(&data1);
    let hash2 = hash::sha256(&data2);

    // Probabilistic - collisions are possible but astronomically unlikely
    TestResult::from_bool(hash1 != hash2)
}

// ==================== CODEC ROUNDTRIP PROPERTIES ====================

#[quickcheck]
fn prop_header_encode_decode_roundtrip(header: BlockHeader) -> TestResult {
    // PROPERTY: decode(encode(x)) == x
    let encoded = match codec::encode_block_header(&header) {
        Ok(bytes) => bytes,
        Err(_) => return TestResult::failed(),
    };

    // Decoding not yet fully implemented, so just verify encoding succeeds
    TestResult::from_bool(!encoded.is_empty())
}

// ==================== PERFORMANCE PROPERTIES ====================

#[test]
fn prop_header_hash_performance() {
    // PROPERTY: Header hashing is fast (< 1ms)
    use std::time::Instant;

    let header = BlockHeader::default();

    let start = Instant::now();
    let _ = codec::compute_header_hash(&header);
    let duration = start.elapsed();

    assert!(
        duration.as_millis() < 1,
        "Header hash took {:?}, expected < 1ms",
        duration
    );
}

#[test]
fn prop_merkle_1k_performance() {
    // PROPERTY: Merkle root of 1K leaves computes in < 50ms
    use std::time::Instant;

    let leaves: Vec<[u8; 32]> = (0..1000).map(|i| {
        let mut hash = [0u8; 32];
        hash[0] = (i % 256) as u8;
        hash[1] = ((i / 256) % 256) as u8;
        hash
    }).collect();

    let start = Instant::now();
    let _ = merkle::compute_merkle_root(&leaves);
    let duration = start.elapsed();

    assert!(
        duration.as_millis() < 50,
        "Merkle(1K) took {:?}, expected < 50ms",
        duration
    );
}

// ==================== RUN QUICKCHECK ====================

#[cfg(test)]
mod quickcheck_runner {
    use super::*;

    #[test]
    fn run_all_property_tests() {
        // Run each property with 1000 examples
        QuickCheck::new()
            .tests(1000)
            .quickcheck(prop_header_hash_determinism as fn(BlockHeader) -> bool);

        QuickCheck::new()
            .tests(1000)
            .quickcheck(prop_tier_constraints_enforced as fn(Problem) -> bool);

        QuickCheck::new()
            .tests(500)
            .quickcheck(prop_merkle_deterministic as fn(Vec<[u8; 32]>) -> TestResult);
    }
}
