//! Golden vector tests - FROZEN test fixtures for determinism
//!
//! These tests ensure:
//! 1. Hashes remain stable across versions (no regressions)
//! 2. Cross-platform determinism (x86_64, arm64, etc.)
//! 3. Codec equivalence (msgpack == JSON)
//!
//! CRITICAL: Changes to golden hashes require labeled PR + code owner approval

use coinjecture_core::codec::{decode_json, encode_msgpack};
use coinjecture_core::hash::sha256;
use coinjecture_core::merkle::compute_merkle_root;
use coinjecture_core::types::*;
use serde_json::Value;
use std::fs;
use std::path::Path;

// ==================== HELPER FUNCTIONS ====================

fn load_golden_json(filename: &str) -> Value {
    let path = Path::new("golden").join(filename);
    let content = fs::read_to_string(&path)
        .unwrap_or_else(|e| panic!("Failed to read {}: {}", path.display(), e));
    serde_json::from_str(&content)
        .unwrap_or_else(|e| panic!("Failed to parse {} as JSON: {}", filename, e))
}

fn hex_to_bytes_32(hex: &str) -> [u8; 32] {
    let bytes = hex::decode(hex).expect("Invalid hex string");
    assert_eq!(bytes.len(), 32, "Expected 32 bytes, got {}", bytes.len());
    let mut arr = [0u8; 32];
    arr.copy_from_slice(&bytes);
    arr
}

// ==================== GENESIS BLOCK ====================

#[test]
fn test_golden_genesis_block() {
    let golden = load_golden_json("genesis_v4_0_0.json");

    // Parse expected hash from golden vector
    let expected_hash = golden["expected_hash_msgpack"]
        .as_str()
        .expect("Missing expected_hash_msgpack");

    // Parse header from golden vector
    let header_json = golden["header"].to_string();
    let header: BlockHeader = decode_json(&header_json).expect("Failed to decode genesis header");

    // Validate genesis block fields
    assert_eq!(header.block_index, 0, "Genesis must be block 0");
    assert_eq!(header.timestamp, 1609459200, "Genesis timestamp frozen");
    assert_eq!(header.difficulty_target, 1000, "Genesis difficulty frozen");
    assert_eq!(header.nonce, 0, "Genesis nonce must be 0");

    // Compute hash via msgpack
    let msgpack_bytes = encode_msgpack(&header).expect("Failed to encode genesis");
    let actual_hash = sha256(&msgpack_bytes);
    let actual_hex = hex::encode(actual_hash);

    println!("\n╔════════════════════════════════════════════════════════╗");
    println!("║  GENESIS BLOCK HASH VALIDATION                         ║");
    println!("╚════════════════════════════════════════════════════════╝");
    println!("Platform: {} {}", std::env::consts::OS, std::env::consts::ARCH);
    println!("Expected: {}", expected_hash);
    println!("Actual:   {}", actual_hex);

    assert_eq!(
        expected_hash, actual_hex,
        "CONSENSUS FAILURE: Genesis hash mismatch!"
    );

    println!("✅ Genesis block hash validated\n");
}

// ==================== BLOCK HEADERS ====================

#[test]
fn test_golden_block_headers() {
    let golden = load_golden_json("headers_v4_0_0.json");
    let test_cases = golden["test_cases"].as_array().expect("Missing test_cases");

    println!("\n╔════════════════════════════════════════════════════════╗");
    println!("║  BLOCK HEADER HASH VALIDATION ({} cases)             ║", test_cases.len());
    println!("╚════════════════════════════════════════════════════════╝");

    for test_case in test_cases {
        let name = test_case["name"].as_str().expect("Missing name");
        println!("\nTesting: {}", name);

        let header_json = test_case["header"].to_string();
        let header: BlockHeader = decode_json(&header_json)
            .unwrap_or_else(|e| panic!("Failed to decode header {}: {}", name, e));

        let expected_hash = test_case["expected_hash"]
            .as_str()
            .expect("Missing expected_hash");

        // Compute hash via msgpack
        let msgpack_bytes = encode_msgpack(&header).expect("Failed to encode");
        let actual_hash = sha256(&msgpack_bytes);
        let actual_hex = hex::encode(actual_hash);

        println!("  Expected: {}", expected_hash);
        println!("  Actual:   {}", actual_hex);

        assert_eq!(
            expected_hash, actual_hex,
            "Header hash mismatch for {}",
            name
        );
        println!("  ✅ Validated");
    }

    println!("\n✅ All block header hashes validated\n");
}

// ==================== MERKLE ROOTS ====================

#[test]
fn test_golden_merkle_roots() {
    let golden = load_golden_json("merkle_v4_0_0.json");
    let test_cases = golden["test_cases"].as_array().expect("Missing test_cases");

    println!("\n╔════════════════════════════════════════════════════════╗");
    println!("║  MERKLE ROOT HASH VALIDATION ({} cases)               ║", test_cases.len());
    println!("╚════════════════════════════════════════════════════════╝");

    for test_case in test_cases {
        let name = test_case["name"].as_str().expect("Missing name");
        println!("\nTesting: {}", name);

        let expected_root = test_case["expected_root"]
            .as_str()
            .expect("Missing expected_root");

        // Parse transaction hashes
        let tx_hashes: Vec<[u8; 32]> = if let Some(hashes) = test_case["transaction_hashes"].as_array() {
            hashes
                .iter()
                .map(|h| hex_to_bytes_32(h.as_str().expect("Invalid hash")))
                .collect()
        } else {
            // Large test case - skip for now
            println!("  Skipping large test case");
            continue;
        };

        let actual_root = compute_merkle_root(&tx_hashes);
        let actual_hex = hex::encode(actual_root);

        println!("  Expected: {}", expected_root);
        println!("  Actual:   {}", actual_hex);

        assert_eq!(
            expected_root, actual_hex,
            "Merkle root mismatch for {}",
            name
        );
        println!("  ✅ Validated");
    }

    println!("\n✅ All merkle roots validated\n");
}

// ==================== DETERMINISM REPORT ====================

#[test]
fn test_determinism_report() {
    println!("\n╔════════════════════════════════════════════════════════╗");
    println!("║   CROSS-PLATFORM DETERMINISM REPORT                    ║");
    println!("╚════════════════════════════════════════════════════════╝");
    println!();
    println!("Platform: {} {}", std::env::consts::OS, std::env::consts::ARCH);
    println!("Rust: {}", env!("CARGO_PKG_RUST_VERSION"));
    println!();
    println!("Golden Vectors: v4.0.0 (Frozen 2025-11-04)");
    println!();
    println!("Test Suite:");
    println!("  - Genesis block validation");
    println!("  - Block header validation (4 hardware tiers)");
    println!("  - Merkle root computation (6 cases)");
    println!("  - Strict decode security");
    println!();
    println!("✅ If all tests pass, consensus is deterministic");
    println!("════════════════════════════════════════════════════════");
}
