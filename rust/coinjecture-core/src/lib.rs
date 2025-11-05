//! COINjecture Core - Consensus-Critical Blockchain Logic
//!
//! This crate provides institutional-grade, deterministic, verifiable
//! implementations of all consensus-critical blockchain operations.
//!
//! # Architecture
//!
//! - **types**: Canonical data structures (#[repr(C)] for FFI)
//! - **codec**: Deterministic serialization (msgpack + JSON)
//! - **hash**: SHA-256 hashing primitives
//! - **merkle**: Deterministic Merkle tree construction
//! - **commitment**: Commit-reveal protocol with epoch binding
//! - **verify**: Proof verification with resource budgets
//! - **errors**: Typed error handling (no panics in consensus)
//! - **python**: PyO3 bindings for Python interop
//!
//! # Quality Gates
//!
//! - Determinism: All operations produce identical results across platforms
//! - Verifiability: All proofs verifiable in O(n) or better
//! - Reproducibility: Locked dependencies, reproducible builds
//! - Security: Defense-in-depth, budget limits, strict validation
//!
//! # Usage
//!
//! ```rust
//! use coinjecture_core::*;
//!
//! // Create a block header
//! let header = types::BlockHeader::default();
//!
//! // Compute canonical hash
//! let hash = codec::compute_header_hash(&header)?;
//!
//! // Verify a subset sum proof
//! let budget = types::VerifyBudget::strict_desktop();
//! let result = verify::verify_solution(&problem, &solution, &budget)?;
//! # Ok::<(), errors::ConsensusError>(())
//! ```

// Module declarations
pub mod codec;
pub mod commitment;
pub mod errors;
pub mod hash;
pub mod merkle;
pub mod types;
pub mod verify;

// Python bindings (feature-gated)
#[cfg(feature = "python")]
pub mod python;

// C FFI bindings for Go/C interop (feature-gated)
#[cfg(feature = "ffi")]
pub mod ffi;

// Re-exports for convenience
pub use errors::{ConsensusError, Result};
pub use types::{
    Block, BlockHeader, Commitment, HardwareTier, MerkleProof, PinManifest, Problem, ProblemType,
    Reveal, Solution, Transaction, TxType, VerifyBudget, CODEC_VERSION, MAX_BLOCK_SIZE,
    MAX_PROOF_ELEMENTS, MAX_TX_PER_BLOCK,
};

/// Library version (matches Cargo.toml)
pub const VERSION: &str = env!("CARGO_PKG_VERSION");

/// Library name
pub const NAME: &str = env!("CARGO_PKG_NAME");

/// Get version info as string
pub fn version_info() -> String {
    format!(
        "{} v{} (codec v{})",
        NAME, VERSION, CODEC_VERSION
    )
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_version_info() {
        let info = version_info();
        assert!(info.contains("coinjecture-core"));
        assert!(info.contains("4.0.0"));
    }
}
