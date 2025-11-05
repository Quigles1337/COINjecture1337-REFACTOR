//! Fuzz target for block decoding
//!
//! This tests that malformed block data never causes:
//! - Panics
//! - Undefined behavior
//! - Memory unsafety
//! - Infinite loops
//!
//! Expected behavior: Return error gracefully

#![no_main]

use libfuzzer_sys::fuzz_target;
use coinjecture_core::codec;

fuzz_target!(|data: &[u8]| {
    // Try to decode arbitrary bytes as a block
    // Should never panic, always return Result
    let _ = codec::decode_block(data);
});
