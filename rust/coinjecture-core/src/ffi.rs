/// C FFI Layer for Go Bindings
///
/// This module exports Rust consensus functions via C ABI for consumption by Go.
/// Go uses cgo to call these functions directly.
///
/// CRITICAL: All functions must be deterministic and match Python PyO3 bindings.
/// Any divergence will cause consensus forks.

use std::ffi::CString;
use std::os::raw::{c_char, c_int, c_uint};
use std::ptr;
use std::slice;

use crate::codec::compute_header_hash;
use crate::hash::sha256;
use crate::merkle::compute_merkle_root;
use crate::verify::verify_solution;
use crate::types::{BlockHeader, Problem, Solution, VerifyBudget, ProblemType, HardwareTier};

/// Result codes for C FFI functions
#[repr(C)]
pub enum CoinjResult {
    Ok = 0,
    ErrorInvalidInput = 1,
    ErrorOutOfMemory = 2,
    ErrorVerificationFailed = 3,
    ErrorEncoding = 4,
    ErrorInternal = 5,
}

/// Block header structure (C-compatible)
#[repr(C)]
pub struct BlockHeaderFFI {
    pub codec_version: c_uint,
    pub block_index: c_uint,
    pub timestamp: i64,
    pub parent_hash: [u8; 32],
    pub merkle_root: [u8; 32],
    pub miner_address: [u8; 32],
    pub commitment: [u8; 32],
    pub difficulty_target: c_uint,
    pub nonce: u64,
    pub extra_data_len: c_uint,
    pub extra_data: *const u8,
}

/// Subset sum problem (C-compatible)
#[repr(C)]
pub struct SubsetSumProblemFFI {
    pub problem_type: c_uint,
    pub tier: c_uint,
    pub elements: *const i64,
    pub elements_len: c_uint,
    pub target: i64,
    pub timestamp: i64,
}

/// Subset sum solution (C-compatible)
#[repr(C)]
pub struct SubsetSumSolutionFFI {
    pub indices: *const c_uint,
    pub indices_len: c_uint,
    pub timestamp: i64,
}

/// Verification budget (C-compatible)
#[repr(C)]
pub struct VerifyBudgetFFI {
    pub max_ops: c_uint,
    pub max_duration_ms: c_uint,
    pub max_memory_bytes: c_uint,
}

// ==================== Core Functions ====================

/// Compute SHA-256 hash of input bytes
///
/// # Safety
/// - `input` must be valid for `input_len` bytes
/// - `out_hash` must point to 32-byte buffer
///
/// # Returns
/// - `CoinjResult::Ok` on success
/// - `CoinjResult::ErrorInvalidInput` if pointers are null
#[no_mangle]
pub unsafe extern "C" fn coinjecture_sha256_hash(
    input: *const u8,
    input_len: c_uint,
    out_hash: *mut [u8; 32],
) -> CoinjResult {
    if input.is_null() || out_hash.is_null() {
        return CoinjResult::ErrorInvalidInput;
    }

    let data = slice::from_raw_parts(input, input_len as usize);
    let hash = sha256(data);

    ptr::copy_nonoverlapping(hash.as_ptr(), (*out_hash).as_mut_ptr(), 32);

    CoinjResult::Ok
}

/// Compute block header hash
///
/// # Safety
/// - `header` must be valid pointer to BlockHeaderFFI
/// - `out_hash` must point to 32-byte buffer
///
/// # Returns
/// - `CoinjResult::Ok` on success
/// - `CoinjResult::ErrorInvalidInput` if pointers are null or header invalid
#[no_mangle]
pub unsafe extern "C" fn coinjecture_compute_header_hash(
    header: *const BlockHeaderFFI,
    out_hash: *mut [u8; 32],
) -> CoinjResult {
    if header.is_null() || out_hash.is_null() {
        return CoinjResult::ErrorInvalidInput;
    }

    let header_ref = &*header;

    // Validate extra_data pointer if len > 0
    if header_ref.extra_data_len > 0 && header_ref.extra_data.is_null() {
        return CoinjResult::ErrorInvalidInput;
    }

    let extra_data = if header_ref.extra_data_len > 0 {
        slice::from_raw_parts(header_ref.extra_data, header_ref.extra_data_len as usize)
    } else {
        &[]
    };

    // Convert to internal Rust type
    let internal_header = BlockHeader {
        codec_version: header_ref.codec_version as u8,
        block_index: header_ref.block_index as u64,
        timestamp: header_ref.timestamp,
        parent_hash: header_ref.parent_hash,
        merkle_root: header_ref.merkle_root,
        miner_address: header_ref.miner_address,
        commitment: header_ref.commitment,
        difficulty_target: header_ref.difficulty_target as u64,
        nonce: header_ref.nonce,
        extra_data: extra_data.to_vec(),
    };

    match compute_header_hash(&internal_header) {
        Ok(hash) => {
            ptr::copy_nonoverlapping(hash.as_ptr(), (*out_hash).as_mut_ptr(), 32);
            CoinjResult::Ok
        }
        Err(_) => CoinjResult::ErrorEncoding,
    }
}

/// Compute Merkle root from transaction hashes
///
/// # Safety
/// - `tx_hashes` must be valid array of 32-byte hashes
/// - `tx_count` must match actual array length
/// - `out_root` must point to 32-byte buffer
///
/// # Returns
/// - `CoinjResult::Ok` on success
/// - `CoinjResult::ErrorInvalidInput` if pointers are null
#[no_mangle]
pub unsafe extern "C" fn coinjecture_compute_merkle_root(
    tx_hashes: *const [u8; 32],
    tx_count: c_uint,
    out_root: *mut [u8; 32],
) -> CoinjResult {
    if out_root.is_null() {
        return CoinjResult::ErrorInvalidInput;
    }

    let hashes: Vec<[u8; 32]> = if tx_count == 0 || tx_hashes.is_null() {
        vec![]
    } else {
        slice::from_raw_parts(tx_hashes, tx_count as usize).to_vec()
    };

    let root = compute_merkle_root(&hashes);

    ptr::copy_nonoverlapping(root.as_ptr(), (*out_root).as_mut_ptr(), 32);

    CoinjResult::Ok
}

/// Verify subset sum solution
///
/// # Safety
/// - All pointers must be valid
/// - Array lengths must match actual sizes
///
/// # Returns
/// - `CoinjResult::Ok` if solution is VALID
/// - `CoinjResult::ErrorVerificationFailed` if solution is INVALID
/// - `CoinjResult::ErrorInvalidInput` if inputs are malformed
#[no_mangle]
pub unsafe extern "C" fn coinjecture_verify_subset_sum(
    problem: *const SubsetSumProblemFFI,
    solution: *const SubsetSumSolutionFFI,
    budget: *const VerifyBudgetFFI,
    out_valid: *mut c_int,
) -> CoinjResult {
    if problem.is_null() || solution.is_null() || budget.is_null() || out_valid.is_null() {
        return CoinjResult::ErrorInvalidInput;
    }

    let problem_ref = &*problem;
    let solution_ref = &*solution;
    let budget_ref = &*budget;

    // Validate pointers
    if problem_ref.elements.is_null()
        || solution_ref.indices.is_null()
        || problem_ref.elements_len == 0
    {
        return CoinjResult::ErrorInvalidInput;
    }

    // Convert to internal types
    let elements =
        slice::from_raw_parts(problem_ref.elements, problem_ref.elements_len as usize).to_vec();
    let indices =
        slice::from_raw_parts(solution_ref.indices, solution_ref.indices_len as usize).to_vec();

    let internal_problem = Problem {
        problem_type: ProblemType::SubsetSum,
        tier: match problem_ref.tier {
            0 => HardwareTier::Mobile,
            1 => HardwareTier::Desktop,
            2 => HardwareTier::Workstation,
            3 => HardwareTier::Server,
            4 => HardwareTier::Cluster,
            _ => return CoinjResult::ErrorInvalidInput,
        },
        elements,
        target: problem_ref.target,
        timestamp: problem_ref.timestamp,
    };

    let internal_solution = Solution {
        indices,
        timestamp: solution_ref.timestamp,
    };

    let internal_budget = VerifyBudget {
        max_ops: budget_ref.max_ops as u64,
        max_duration_ms: budget_ref.max_duration_ms as u64,
        max_memory_bytes: budget_ref.max_memory_bytes as u64,
    };

    match verify_solution(&internal_problem, &internal_solution, &internal_budget) {
        Ok(result) => {
            *out_valid = if result.valid { 1 } else { 0 };
            CoinjResult::Ok
        }
        Err(_) => CoinjResult::ErrorVerificationFailed,
    }
}

// ==================== Error Handling ====================

/// Get last error message (thread-local)
///
/// # Safety
/// - Caller must free the returned string with `coinjecture_free_string`
///
/// # Returns
/// - Pointer to null-terminated error string
/// - NULL if no error occurred
#[no_mangle]
pub unsafe extern "C" fn coinjecture_last_error() -> *mut c_char {
    // TODO: Implement thread-local error storage
    let error = CString::new("Not implemented").unwrap();
    error.into_raw()
}

/// Free a string allocated by Rust
///
/// # Safety
/// - `s` must be a string previously returned by a coinjecture_* function
/// - `s` must not be used after this call
#[no_mangle]
pub unsafe extern "C" fn coinjecture_free_string(s: *mut c_char) {
    if !s.is_null() {
        drop(CString::from_raw(s));
    }
}

// ==================== Version Info ====================

/// Get library version
///
/// # Returns
/// - Pointer to static string (do not free)
#[no_mangle]
pub extern "C" fn coinjecture_version() -> *const c_char {
    concat!(env!("CARGO_PKG_VERSION"), "\0").as_ptr() as *const c_char
}

/// Get codec version
///
/// # Returns
/// - Codec version number (currently 1)
#[no_mangle]
pub extern "C" fn coinjecture_codec_version() -> c_uint {
    1
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_sha256_hash_ffi() {
        let input = b"COINjecture";
        let mut output = [0u8; 32];

        unsafe {
            let result = coinjecture_sha256_hash(
                input.as_ptr(),
                input.len() as c_uint,
                &mut output as *mut [u8; 32],
            );

            assert!(matches!(result, CoinjResult::Ok));
            assert_ne!(output, [0u8; 32]); // Should have computed hash
        }
    }

    #[test]
    fn test_version_info() {
        let version = coinjecture_version();
        assert!(!version.is_null());

        let codec_version = coinjecture_codec_version();
        assert_eq!(codec_version, 1);
    }
}
