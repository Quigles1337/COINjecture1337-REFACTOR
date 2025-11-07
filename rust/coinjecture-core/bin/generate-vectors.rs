/// Golden Vector Generator for Network B
///
/// Generates deterministic test vectors for SHA-256, Merkle trees, and block headers.
/// These vectors ensure parity between Rust, Go, and Python implementations.

use coinjecture_core::hash::sha256;
use coinjecture_core::merkle::compute_merkle_root;
use coinjecture_core::codec::compute_header_hash;
use coinjecture_core::types::BlockHeader;
use serde_json::json;

fn main() {
    let mut vectors = vec![];

    // ==================== SHA-256 Test Vectors ====================

    // Vector 1: Empty input
    vectors.push(json!({
        "test_name": "sha256_empty_input",
        "operation": "SHA256",
        "input_hex": "",
        "expected_hash": hex::encode(sha256(b""))
    }));

    // Vector 2: "hello world"
    let hello_world = b"hello world";
    vectors.push(json!({
        "test_name": "sha256_hello_world",
        "operation": "SHA256",
        "input_hex": hex::encode(hello_world),
        "expected_hash": hex::encode(sha256(hello_world))
    }));

    // Vector 3: "COINjecture"
    let coinjecture = b"COINjecture";
    vectors.push(json!({
        "test_name": "sha256_coinjecture",
        "operation": "SHA256",
        "input_hex": hex::encode(coinjecture),
        "expected_hash": hex::encode(sha256(coinjecture))
    }));

    // Vector 4: All zeros (32 bytes)
    let zeros = vec![0u8; 32];
    vectors.push(json!({
        "test_name": "sha256_zeros_32",
        "operation": "SHA256",
        "input_hex": hex::encode(&zeros),
        "expected_hash": hex::encode(sha256(&zeros))
    }));

    // Vector 5: All ones (32 bytes)
    let ones = vec![0xFFu8; 32];
    vectors.push(json!({
        "test_name": "sha256_ones_32",
        "operation": "SHA256",
        "input_hex": hex::encode(&ones),
        "expected_hash": hex::encode(sha256(&ones))
    }));

    // Vector 6: Sequential bytes 0-255
    let sequential: Vec<u8> = (0..=255).collect();
    vectors.push(json!({
        "test_name": "sha256_sequential_256",
        "operation": "SHA256",
        "input_hex": hex::encode(&sequential),
        "expected_hash": hex::encode(sha256(&sequential))
    }));

    // Vector 7: Large input (10KB)
    let large_input = vec![0xAAu8; 10240];
    vectors.push(json!({
        "test_name": "sha256_large_10kb",
        "operation": "SHA256",
        "input_hex": hex::encode(&large_input[..64]), // First 64 bytes for readability
        "input_size": large_input.len(),
        "expected_hash": hex::encode(sha256(&large_input))
    }));

    // Vector 8: JSON data
    let json_data = br#"{"block_number":1337,"validator":"alice","amount":1000000}"#;
    vectors.push(json!({
        "test_name": "sha256_json_data",
        "operation": "SHA256",
        "input_hex": hex::encode(json_data),
        "expected_hash": hex::encode(sha256(json_data))
    }));

    // Vector 9: Bitcoin genesis block message
    let btc_genesis = b"The Times 03/Jan/2009 Chancellor on brink of second bailout for banks";
    vectors.push(json!({
        "test_name": "sha256_btc_genesis",
        "operation": "SHA256",
        "input_hex": hex::encode(btc_genesis),
        "expected_hash": hex::encode(sha256(btc_genesis))
    }));

    // Vector 10: Unicode string
    let unicode = "Hello 世界 🚀".as_bytes();
    vectors.push(json!({
        "test_name": "sha256_unicode",
        "operation": "SHA256",
        "input_hex": hex::encode(unicode),
        "expected_hash": hex::encode(sha256(unicode))
    }));

    // ==================== Merkle Root Test Vectors ====================

    // Vector 11: Empty merkle tree
    vectors.push(json!({
        "test_name": "merkle_empty",
        "operation": "MERKLE",
        "tx_hashes": [],
        "expected_root": hex::encode(compute_merkle_root(&[]))
    }));

    // Vector 12: Single transaction
    let single_hash = [[0x42u8; 32]];
    vectors.push(json!({
        "test_name": "merkle_single_tx",
        "operation": "MERKLE",
        "tx_hashes": vec![hex::encode(single_hash[0])],
        "expected_root": hex::encode(compute_merkle_root(&single_hash))
    }));

    // Vector 13: Two transactions
    let two_hashes = [
        [0x11u8; 32],
        [0x22u8; 32],
    ];
    vectors.push(json!({
        "test_name": "merkle_two_txs",
        "operation": "MERKLE",
        "tx_hashes": two_hashes.iter().map(|h| hex::encode(h)).collect::<Vec<_>>(),
        "expected_root": hex::encode(compute_merkle_root(&two_hashes))
    }));

    // Vector 14: Three transactions (odd count)
    let three_hashes = [
        [0xAAu8; 32],
        [0xBBu8; 32],
        [0xCCu8; 32],
    ];
    vectors.push(json!({
        "test_name": "merkle_three_txs",
        "operation": "MERKLE",
        "tx_hashes": three_hashes.iter().map(|h| hex::encode(h)).collect::<Vec<_>>(),
        "expected_root": hex::encode(compute_merkle_root(&three_hashes))
    }));

    // Vector 15: Four transactions (power of 2)
    let four_hashes = [
        sha256(b"tx1"),
        sha256(b"tx2"),
        sha256(b"tx3"),
        sha256(b"tx4"),
    ];
    vectors.push(json!({
        "test_name": "merkle_four_txs",
        "operation": "MERKLE",
        "tx_hashes": four_hashes.iter().map(|h| hex::encode(h)).collect::<Vec<_>>(),
        "expected_root": hex::encode(compute_merkle_root(&four_hashes))
    }));

    // Vector 16: Eight transactions
    let eight_hashes = [
        sha256(b"tx1"), sha256(b"tx2"), sha256(b"tx3"), sha256(b"tx4"),
        sha256(b"tx5"), sha256(b"tx6"), sha256(b"tx7"), sha256(b"tx8"),
    ];
    vectors.push(json!({
        "test_name": "merkle_eight_txs",
        "operation": "MERKLE",
        "tx_hashes": eight_hashes.iter().map(|h| hex::encode(h)).collect::<Vec<_>>(),
        "expected_root": hex::encode(compute_merkle_root(&eight_hashes))
    }));

    // Vector 17: 100 transactions (realistic block)
    let hundred_hashes: Vec<[u8; 32]> = (0..100)
        .map(|i| sha256(format!("transaction_{}", i).as_bytes()))
        .collect();
    vectors.push(json!({
        "test_name": "merkle_hundred_txs",
        "operation": "MERKLE",
        "tx_count": 100,
        "first_tx_hash": hex::encode(hundred_hashes[0]),
        "last_tx_hash": hex::encode(hundred_hashes[99]),
        "expected_root": hex::encode(compute_merkle_root(&hundred_hashes))
    }));

    // Vector 18: 1000 transactions (large block)
    let thousand_hashes: Vec<[u8; 32]> = (0..1000)
        .map(|i| sha256(format!("tx_{:04}", i).as_bytes()))
        .collect();
    vectors.push(json!({
        "test_name": "merkle_thousand_txs",
        "operation": "MERKLE",
        "tx_count": 1000,
        "first_tx_hash": hex::encode(thousand_hashes[0]),
        "last_tx_hash": hex::encode(thousand_hashes[999]),
        "expected_root": hex::encode(compute_merkle_root(&thousand_hashes))
    }));

    // ==================== Block Header Test Vectors ====================

    // Vector 19: Genesis block header
    let genesis_header = BlockHeader {
        codec_version: 1,
        block_index: 0,
        timestamp: 1704067200, // 2024-01-01 00:00:00 UTC
        parent_hash: [0u8; 32],
        merkle_root: [0u8; 32],
        miner_address: [0u8; 32],
        commitment: [0u8; 32],
        difficulty_target: 100,
        nonce: 0,
        extra_data: vec![],
    };
    let genesis_hash = compute_header_hash(&genesis_header).unwrap();
    vectors.push(json!({
        "test_name": "block_header_genesis",
        "operation": "BLOCK_HEADER",
        "header": {
            "codec_version": genesis_header.codec_version,
            "block_index": genesis_header.block_index,
            "timestamp": genesis_header.timestamp,
            "parent_hash": hex::encode(genesis_header.parent_hash),
            "merkle_root": hex::encode(genesis_header.merkle_root),
            "miner_address": hex::encode(genesis_header.miner_address),
            "commitment": hex::encode(genesis_header.commitment),
            "difficulty_target": genesis_header.difficulty_target,
            "nonce": genesis_header.nonce,
            "extra_data": hex::encode(&genesis_header.extra_data),
        },
        "expected_hash": hex::encode(genesis_hash)
    }));

    // Vector 20: Block #1 with merkle root
    let block1_merkle = compute_merkle_root(&[sha256(b"tx1"), sha256(b"tx2")]);
    let block1_miner = sha256(b"validator1_pubkey");
    let block1_header = BlockHeader {
        codec_version: 1,
        block_index: 1,
        timestamp: 1704067202,
        parent_hash: genesis_hash,
        merkle_root: block1_merkle,
        miner_address: block1_miner,
        commitment: [0xFFu8; 32],
        difficulty_target: 100,
        nonce: 42,
        extra_data: vec![],
    };
    let block1_hash = compute_header_hash(&block1_header).unwrap();
    vectors.push(json!({
        "test_name": "block_header_1",
        "operation": "BLOCK_HEADER",
        "header": {
            "codec_version": block1_header.codec_version,
            "block_index": block1_header.block_index,
            "timestamp": block1_header.timestamp,
            "parent_hash": hex::encode(block1_header.parent_hash),
            "merkle_root": hex::encode(block1_header.merkle_root),
            "miner_address": hex::encode(block1_header.miner_address),
            "commitment": hex::encode(block1_header.commitment),
            "difficulty_target": block1_header.difficulty_target,
            "nonce": block1_header.nonce,
            "extra_data": hex::encode(&block1_header.extra_data),
        },
        "expected_hash": hex::encode(block1_hash)
    }));

    // Vector 21: Block with extra data
    let block_with_extra = BlockHeader {
        codec_version: 1,
        block_index: 100,
        timestamp: 1704067400,
        parent_hash: sha256(b"parent_block_99"),
        merkle_root: sha256(b"merkle_root_100"),
        miner_address: sha256(b"miner_alice"),
        commitment: sha256(b"commitment_100"),
        difficulty_target: 1000,
        nonce: 1337,
        extra_data: b"Network B Migration - v4.5.0+".to_vec(),
    };
    let block_extra_hash = compute_header_hash(&block_with_extra).unwrap();
    vectors.push(json!({
        "test_name": "block_header_with_extra_data",
        "operation": "BLOCK_HEADER",
        "header": {
            "codec_version": block_with_extra.codec_version,
            "block_index": block_with_extra.block_index,
            "timestamp": block_with_extra.timestamp,
            "parent_hash": hex::encode(block_with_extra.parent_hash),
            "merkle_root": hex::encode(block_with_extra.merkle_root),
            "miner_address": hex::encode(block_with_extra.miner_address),
            "commitment": hex::encode(block_with_extra.commitment),
            "difficulty_target": block_with_extra.difficulty_target,
            "nonce": block_with_extra.nonce,
            "extra_data": hex::encode(&block_with_extra.extra_data),
        },
        "expected_hash": hex::encode(block_extra_hash)
    }));

    // Vector 22: Block #1000 (checkpoint)
    let checkpoint_header = BlockHeader {
        codec_version: 1,
        block_index: 1000,
        timestamp: 1704069200,
        parent_hash: sha256(b"block_999"),
        merkle_root: compute_merkle_root(&(0..50).map(|i| sha256(format!("tx_{}", i).as_bytes())).collect::<Vec<_>>()),
        miner_address: sha256(b"validator_checkpoint"),
        commitment: sha256(b"checkpoint_1000"),
        difficulty_target: 10000,
        nonce: 999999,
        extra_data: b"CHECKPOINT".to_vec(),
    };
    let checkpoint_hash = compute_header_hash(&checkpoint_header).unwrap();
    vectors.push(json!({
        "test_name": "block_header_checkpoint_1000",
        "operation": "BLOCK_HEADER",
        "header": {
            "codec_version": checkpoint_header.codec_version,
            "block_index": checkpoint_header.block_index,
            "timestamp": checkpoint_header.timestamp,
            "parent_hash": hex::encode(checkpoint_header.parent_hash),
            "merkle_root": hex::encode(checkpoint_header.merkle_root),
            "miner_address": hex::encode(checkpoint_header.miner_address),
            "commitment": hex::encode(checkpoint_header.commitment),
            "difficulty_target": checkpoint_header.difficulty_target,
            "nonce": checkpoint_header.nonce,
            "extra_data": hex::encode(&checkpoint_header.extra_data),
        },
        "expected_hash": hex::encode(checkpoint_hash)
    }));

    // Vector 23-50: Randomized stress test vectors
    for i in 23..=50 {
        let nonce_val = (i * 12345) % 100000;
        let block_idx = (i * 7) % 10000;

        let stress_header = BlockHeader {
            codec_version: 1,
            block_index: block_idx,
            timestamp: 1704067200 + (i as i64 * 2),
            parent_hash: sha256(format!("parent_{}", i).as_bytes()),
            merkle_root: sha256(format!("merkle_{}", i).as_bytes()),
            miner_address: sha256(format!("miner_{}", i).as_bytes()),
            commitment: sha256(format!("commit_{}", i).as_bytes()),
            difficulty_target: (i * 100) as u64,
            nonce: nonce_val,
            extra_data: if i % 3 == 0 {
                format!("extra_data_{}", i).into_bytes()
            } else {
                vec![]
            },
        };
        let stress_hash = compute_header_hash(&stress_header).unwrap();

        vectors.push(json!({
            "test_name": format!("stress_test_vector_{}", i),
            "operation": "BLOCK_HEADER",
            "header": {
                "codec_version": stress_header.codec_version,
                "block_index": stress_header.block_index,
                "timestamp": stress_header.timestamp,
                "parent_hash": hex::encode(stress_header.parent_hash),
                "merkle_root": hex::encode(stress_header.merkle_root),
                "miner_address": hex::encode(stress_header.miner_address),
                "commitment": hex::encode(stress_header.commitment),
                "difficulty_target": stress_header.difficulty_target,
                "nonce": stress_header.nonce,
                "extra_data": hex::encode(&stress_header.extra_data),
            },
            "expected_hash": hex::encode(stress_hash)
        }));
    }

    // ==================== Output JSON ====================

    let output = json!({
        "version": "4.5.0+",
        "generated_at": chrono::Utc::now().to_rfc3339(),
        "total_vectors": vectors.len(),
        "description": "Golden test vectors for Network B (Rust-integrated) consensus",
        "purpose": "Ensure cryptographic parity between Rust, Go, and Python implementations",
        "vectors": vectors
    });

    println!("{}", serde_json::to_string_pretty(&output).unwrap());

    eprintln!("\n✅ Generated {} golden test vectors for Network B", vectors.len());
    eprintln!("   - SHA-256: 10 vectors");
    eprintln!("   - Merkle roots: 8 vectors");
    eprintln!("   - Block headers: 32 vectors");
    eprintln!("   Total: 50 vectors\n");
}
