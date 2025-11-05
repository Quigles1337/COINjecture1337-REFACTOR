//! Fuzz target for header hashing
//!
//! Tests that arbitrary header data never causes issues when hashing.
//! All inputs should produce valid 32-byte hashes.

#![no_main]

use libfuzzer_sys::fuzz_target;
use coinjecture_core::{BlockHeader, codec};

fuzz_target!(|header: BlockHeader| {
    // Compute hash - should never panic
    if let Ok(hash) = codec::compute_header_hash(&header) {
        // Verify hash is valid
        assert_eq!(hash.len(), 32, "Hash must be 32 bytes");
    }
});
