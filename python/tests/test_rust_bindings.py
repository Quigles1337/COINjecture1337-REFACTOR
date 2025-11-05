"""
Explicit tests for Rust PyO3 bindings.

These tests ensure the Rust extension is correctly built and callable from Python.
They exercise the critical binding path between Python and Rust consensus code.

CRITICAL: These tests MUST pass for institutional-grade deployments.
If these fail, the Rust extension is not properly built/linked.
"""

import pytest
import hashlib


class TestRustExtensionAvailable:
    """Verify Rust extension is loaded"""

    def test_rust_available(self):
        """Test that Rust extension is available"""
        from coinjecture import RUST_AVAILABLE

        assert RUST_AVAILABLE, (
            "Rust extension not available. "
            "Build with: maturin develop --release"
        )

    def test_rust_version(self):
        """Test that Rust extension version is accessible"""
        try:
            from coinjecture._core import __version__
            assert __version__ is not None
            assert isinstance(__version__, str)
        except ImportError:
            pytest.fail("Rust _core module not found")

    def test_codec_version(self):
        """Test that CODEC_VERSION is exported from Rust"""
        from coinjecture import CODEC_VERSION
        assert CODEC_VERSION == 1, "CODEC_VERSION must be 1 for v4.0.0"


class TestRustHashingFunctions:
    """Test Rust hashing functions are callable"""

    def test_sha256_hash(self):
        """Test sha256_hash function from Rust"""
        from coinjecture._core import sha256_hash

        # Test empty input
        result = sha256_hash(b"")
        assert isinstance(result, bytes)
        assert len(result) == 32

        # Compare with Python hashlib
        expected = hashlib.sha256(b"").digest()
        assert result == expected

    def test_sha256_hash_with_data(self):
        """Test sha256_hash with actual data"""
        from coinjecture._core import sha256_hash

        test_data = b"COINjecture"
        result = sha256_hash(test_data)
        expected = hashlib.sha256(test_data).digest()

        assert result == expected
        assert len(result) == 32

    def test_sha256_determinism(self):
        """Test that sha256_hash is deterministic"""
        from coinjecture._core import sha256_hash

        data = b"determinism_test"
        hash1 = sha256_hash(data)
        hash2 = sha256_hash(data)
        hash3 = sha256_hash(data)

        assert hash1 == hash2 == hash3, "Rust SHA-256 must be deterministic"


class TestRustCodecFunctions:
    """Test Rust codec functions are callable"""

    def test_compute_header_hash_py(self):
        """Test compute_header_hash_py function from Rust"""
        from coinjecture._core import compute_header_hash_py

        # Genesis header
        header_dict = {
            "codec_version": 1,
            "block_index": 0,
            "timestamp": 1609459200,
            "parent_hash": b"\x00" * 32,
            "merkle_root": b"\x00" * 32,
            "miner_address": b"\x00" * 32,
            "commitment": b"\x00" * 32,
            "difficulty_target": 1000,
            "nonce": 0,
            "extra_data": b"",
        }

        result = compute_header_hash_py(header_dict)

        assert isinstance(result, bytes)
        assert len(result) == 32

    def test_compute_header_hash_determinism(self):
        """Test that compute_header_hash_py is deterministic"""
        from coinjecture._core import compute_header_hash_py

        header_dict = {
            "codec_version": 1,
            "block_index": 1,
            "timestamp": 1609459200,
            "parent_hash": b"\x00" * 32,
            "merkle_root": b"\x00" * 32,
            "miner_address": b"\x00" * 32,
            "commitment": b"\x00" * 32,
            "difficulty_target": 1000,
            "nonce": 42,
            "extra_data": b"",
        }

        hash1 = compute_header_hash_py(header_dict)
        hash2 = compute_header_hash_py(header_dict)
        hash3 = compute_header_hash_py(header_dict)

        assert hash1 == hash2 == hash3, "Rust header hash must be deterministic"

    def test_compute_header_hash_uniqueness(self):
        """Test that different headers produce different hashes"""
        from coinjecture._core import compute_header_hash_py

        header1 = {
            "codec_version": 1,
            "block_index": 0,
            "timestamp": 1609459200,
            "parent_hash": b"\x00" * 32,
            "merkle_root": b"\x00" * 32,
            "miner_address": b"\x00" * 32,
            "commitment": b"\x00" * 32,
            "difficulty_target": 1000,
            "nonce": 0,
            "extra_data": b"",
        }

        header2 = {
            "codec_version": 1,
            "block_index": 1,  # Different
            "timestamp": 1609459200,
            "parent_hash": b"\x00" * 32,
            "merkle_root": b"\x00" * 32,
            "miner_address": b"\x00" * 32,
            "commitment": b"\x00" * 32,
            "difficulty_target": 1000,
            "nonce": 0,
            "extra_data": b"",
        }

        hash1 = compute_header_hash_py(header1)
        hash2 = compute_header_hash_py(header2)

        assert hash1 != hash2, "Different headers must produce different hashes"


class TestRustMerkleFunctions:
    """Test Rust Merkle tree functions"""

    def test_compute_merkle_root_empty(self):
        """Test compute_merkle_root_py with empty transaction list"""
        from coinjecture._core import compute_merkle_root_py

        result = compute_merkle_root_py([])

        assert isinstance(result, bytes)
        assert len(result) == 32

    def test_compute_merkle_root_single(self):
        """Test compute_merkle_root_py with single transaction"""
        from coinjecture._core import compute_merkle_root_py

        tx_hash = b"\x00" * 32
        result = compute_merkle_root_py([tx_hash])

        assert isinstance(result, bytes)
        assert len(result) == 32

    def test_compute_merkle_root_multiple(self):
        """Test compute_merkle_root_py with multiple transactions"""
        from coinjecture._core import compute_merkle_root_py

        tx_hashes = [
            b"\x00" * 32,
            b"\x01" * 32,
            b"\x02" * 32,
        ]

        result = compute_merkle_root_py(tx_hashes)

        assert isinstance(result, bytes)
        assert len(result) == 32

    def test_compute_merkle_root_determinism(self):
        """Test that merkle root computation is deterministic"""
        from coinjecture._core import compute_merkle_root_py

        tx_hashes = [
            b"\xaa" * 32,
            b"\xbb" * 32,
            b"\xcc" * 32,
        ]

        root1 = compute_merkle_root_py(tx_hashes)
        root2 = compute_merkle_root_py(tx_hashes)
        root3 = compute_merkle_root_py(tx_hashes)

        assert root1 == root2 == root3, "Merkle root must be deterministic"


class TestRustVerifyFunctions:
    """Test Rust proof verification functions"""

    def test_verify_subset_sum_valid(self):
        """Test verify_subset_sum_py with valid solution"""
        from coinjecture._core import verify_subset_sum_py

        problem_dict = {
            "problem_type": 0,  # SUBSET_SUM
            "tier": 1,  # DESKTOP
            "elements": [1, 2, 3, 4, 5],
            "target": 9,
            "timestamp": 1000,
        }

        solution_dict = {
            "indices": [0, 2, 4],  # elements[0,2,4] = 1+3+5 = 9
            "timestamp": 1001,
        }

        budget_dict = {
            "max_ops": 100000,
            "max_duration_ms": 10000,
            "max_memory_bytes": 100_000_000,
        }

        result = verify_subset_sum_py(problem_dict, solution_dict, budget_dict)

        assert isinstance(result, bool)
        assert result is True, "Valid subset sum solution must verify"

    def test_verify_subset_sum_invalid_sum(self):
        """Test verify_subset_sum_py rejects wrong sum"""
        from coinjecture._core import verify_subset_sum_py

        problem_dict = {
            "problem_type": 0,  # SUBSET_SUM
            "tier": 1,  # DESKTOP
            "elements": [1, 2, 3, 4, 5],
            "target": 9,
            "timestamp": 1000,
        }

        solution_dict = {
            "indices": [0, 1],  # elements[0,1] = 1+2 = 3, not 9
            "timestamp": 1001,
        }

        budget_dict = {
            "max_ops": 100000,
            "max_duration_ms": 10000,
            "max_memory_bytes": 100_000_000,
        }

        result = verify_subset_sum_py(problem_dict, solution_dict, budget_dict)

        assert isinstance(result, bool)
        assert result is False, "Invalid subset sum solution must be rejected"

    def test_verify_subset_sum_out_of_bounds(self):
        """Test verify_subset_sum_py rejects out-of-bounds indices"""
        from coinjecture._core import verify_subset_sum_py

        problem_dict = {
            "problem_type": 0,  # SUBSET_SUM
            "tier": 1,  # DESKTOP
            "elements": [1, 2, 3],
            "target": 6,
            "timestamp": 1000,
        }

        solution_dict = {
            "indices": [0, 1, 10],  # Index 10 out of bounds
            "timestamp": 1001,
        }

        budget_dict = {
            "max_ops": 100000,
            "max_duration_ms": 10000,
            "max_memory_bytes": 100_000_000,
        }

        result = verify_subset_sum_py(problem_dict, solution_dict, budget_dict)

        assert isinstance(result, bool)
        assert result is False, "Out-of-bounds indices must be rejected"


class TestRustBindingErrorHandling:
    """Test that Rust functions handle errors gracefully"""

    def test_compute_header_hash_invalid_input(self):
        """Test that invalid header dict raises appropriate error"""
        from coinjecture._core import compute_header_hash_py

        # Missing required fields
        invalid_header = {
            "codec_version": 1,
            # Missing all other fields
        }

        with pytest.raises(Exception):  # PyValueError from Rust
            compute_header_hash_py(invalid_header)

    def test_compute_merkle_root_invalid_hash_size(self):
        """Test that invalid hash sizes are rejected"""
        from coinjecture._core import compute_merkle_root_py

        # Hash too short
        invalid_hashes = [b"\x00" * 16]  # Only 16 bytes, need 32

        with pytest.raises(Exception):
            compute_merkle_root_py(invalid_hashes)

    def test_verify_subset_sum_missing_fields(self):
        """Test that missing fields in dicts raise errors"""
        from coinjecture._core import verify_subset_sum_py

        incomplete_problem = {
            "problem_type": 0,
            # Missing tier, elements, target, timestamp
        }

        solution_dict = {
            "indices": [0],
            "timestamp": 1001,
        }

        budget_dict = {
            "max_ops": 100000,
            "max_duration_ms": 10000,
            "max_memory_bytes": 100_000_000,
        }

        with pytest.raises(Exception):
            verify_subset_sum_py(incomplete_problem, solution_dict, budget_dict)


# ==================== MARKER FOR PYTEST ====================

pytestmark = pytest.mark.bindings


if __name__ == "__main__":
    # Run with: pytest tests/test_rust_bindings.py -v
    pytest.main([__file__, "-v", "--tb=short"])
