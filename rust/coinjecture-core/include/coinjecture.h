/**
 * COINjecture Core - C FFI Header
 *
 * This header provides C-compatible bindings for Go (via cgo) to call
 * consensus-critical Rust functions.
 *
 * CRITICAL: These functions are deterministic and consensus-critical.
 * Any changes must maintain identical behavior across all platforms.
 *
 * Author: Quigles1337 <adz@alphx.io>
 * Version: 4.0.0
 */

#ifndef COINJECTURE_H
#define COINJECTURE_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// ==================== RESULT CODES ====================

/**
 * Result codes for FFI functions
 */
typedef enum {
    COINJ_OK = 0,
    COINJ_ERROR_INVALID_INPUT = 1,
    COINJ_ERROR_OUT_OF_MEMORY = 2,
    COINJ_ERROR_VERIFICATION_FAILED = 3,
    COINJ_ERROR_ENCODING = 4,
    COINJ_ERROR_INTERNAL = 5,
} CoinjResult;

// ==================== DATA STRUCTURES ====================

/**
 * Block header structure (C-compatible)
 *
 * IMPORTANT: Field order and sizes must match Rust BlockHeaderFFI exactly.
 */
typedef struct {
    uint32_t codec_version;
    uint32_t block_index;
    int64_t timestamp;
    uint8_t parent_hash[32];
    uint8_t merkle_root[32];
    uint8_t miner_address[32];
    uint8_t commitment[32];
    uint32_t difficulty_target;
    uint64_t nonce;
    uint32_t extra_data_len;
    const uint8_t *extra_data;
} BlockHeaderFFI;

/**
 * Subset sum problem structure (C-compatible)
 *
 * Tier values:
 * - 0: Mobile
 * - 1: Desktop
 * - 2: Workstation
 * - 3: Server
 * - 4: Cluster
 */
typedef struct {
    uint32_t problem_type;  // 0 = SubsetSum
    uint32_t tier;
    const int64_t *elements;
    uint32_t elements_len;
    int64_t target;
    int64_t timestamp;
} SubsetSumProblemFFI;

/**
 * Subset sum solution structure (C-compatible)
 */
typedef struct {
    const uint32_t *indices;
    uint32_t indices_len;
    int64_t timestamp;
} SubsetSumSolutionFFI;

/**
 * Verification budget structure (C-compatible)
 */
typedef struct {
    uint32_t max_ops;
    uint32_t max_duration_ms;
    uint32_t max_memory_bytes;
} VerifyBudgetFFI;

// ==================== CORE FUNCTIONS ====================

/**
 * Compute SHA-256 hash of input bytes
 *
 * @param input Input data
 * @param input_len Length of input in bytes
 * @param out_hash Output buffer (must be 32 bytes)
 * @return COINJ_OK on success, error code otherwise
 */
CoinjResult coinjecture_sha256_hash(
    const uint8_t *input,
    uint32_t input_len,
    uint8_t out_hash[32]
);

/**
 * Compute block header hash (deterministic, consensus-critical)
 *
 * @param header Pointer to block header structure
 * @param out_hash Output buffer (must be 32 bytes)
 * @return COINJ_OK on success, error code otherwise
 */
CoinjResult coinjecture_compute_header_hash(
    const BlockHeaderFFI *header,
    uint8_t out_hash[32]
);

/**
 * Compute Merkle root from transaction hashes
 *
 * @param tx_hashes Array of 32-byte transaction hashes
 * @param tx_count Number of transactions
 * @param out_root Output buffer (must be 32 bytes)
 * @return COINJ_OK on success, error code otherwise
 */
CoinjResult coinjecture_compute_merkle_root(
    const uint8_t (*tx_hashes)[32],
    uint32_t tx_count,
    uint8_t out_root[32]
);

/**
 * Verify subset sum solution (O(n) verification with budget limits)
 *
 * @param problem Pointer to problem structure
 * @param solution Pointer to solution structure
 * @param budget Pointer to budget structure
 * @param out_valid Output: 1 if valid, 0 if invalid
 * @return COINJ_OK on success, error code otherwise
 */
CoinjResult coinjecture_verify_subset_sum(
    const SubsetSumProblemFFI *problem,
    const SubsetSumSolutionFFI *solution,
    const VerifyBudgetFFI *budget,
    int32_t *out_valid
);

// ==================== ERROR HANDLING ====================

/**
 * Get last error message (thread-local)
 *
 * @return Pointer to null-terminated error string (must free with coinjecture_free_string)
 */
char *coinjecture_last_error(void);

/**
 * Free a string allocated by Rust
 *
 * @param s String pointer returned by coinjecture_* function
 */
void coinjecture_free_string(char *s);

// ==================== VERSION INFO ====================

/**
 * Get library version
 *
 * @return Pointer to static version string (do not free)
 */
const char *coinjecture_version(void);

/**
 * Get codec version
 *
 * @return Codec version number (currently 1)
 */
uint32_t coinjecture_codec_version(void);

#ifdef __cplusplus
}
#endif

#endif // COINJECTURE_H
