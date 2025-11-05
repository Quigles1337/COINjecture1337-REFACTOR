"""
Tests for dual-run parity validator

These tests verify the legacy_compat module correctly:
1. Runs both implementations in parallel
2. Detects drift
3. Tracks metrics
4. Respects feature flags
"""

import os
import pytest
from unittest.mock import Mock, patch

from coinjecture.legacy_compat import (
    CODEC_MODE,
    ParityError,
    dual_run,
    get_parity_stats,
    PARITY_MATCHES,
    PARITY_DRIFTS,
)


class TestDualRun:
    """Test the dual_run() function"""

    def setup_method(self):
        """Reset metrics before each test"""
        # Reset Prometheus counters (simplified)
        PARITY_MATCHES._value._value = 0.0
        for metric in PARITY_DRIFTS._metrics.values():
            if hasattr(metric, '_value'):
                metric._value._value = 0.0

    def test_legacy_only_mode(self, monkeypatch):
        """Test legacy_only mode uses only legacy implementation"""
        monkeypatch.setenv("CODEC_MODE", "legacy_only")

        legacy_called = False
        refactored_called = False

        def legacy_fn():
            nonlocal legacy_called
            legacy_called = True
            return "legacy_result"

        def refactored_fn():
            nonlocal refactored_called
            refactored_called = True
            return "refactored_result"

        # Need to reload module to pick up env var
        import importlib
        import coinjecture.legacy_compat as lc
        importlib.reload(lc)

        result = lc.dual_run("test_func", legacy_fn, refactored_fn)

        assert result == "legacy_result"
        assert legacy_called
        assert not refactored_called

    def test_refactored_only_mode(self, monkeypatch):
        """Test refactored_only mode uses only refactored implementation"""
        monkeypatch.setenv("CODEC_MODE", "refactored_only")
        monkeypatch.setenv("RUST_AVAILABLE", "1")

        legacy_called = False
        refactored_called = False

        def legacy_fn():
            nonlocal legacy_called
            legacy_called = True
            return "legacy_result"

        def refactored_fn():
            nonlocal refactored_called
            refactored_called = True
            return "refactored_result"

        import importlib
        import coinjecture.legacy_compat as lc
        importlib.reload(lc)

        result = lc.dual_run("test_func", legacy_fn, refactored_fn)

        assert result == "refactored_result"
        assert not legacy_called
        assert refactored_called

    def test_shadow_mode_match(self, monkeypatch):
        """Test shadow mode with matching results"""
        monkeypatch.setenv("CODEC_MODE", "shadow")

        legacy_called = False
        refactored_called = False

        def legacy_fn():
            nonlocal legacy_called
            legacy_called = True
            return "matching_result"

        def refactored_fn():
            nonlocal refactored_called
            refactored_called = True
            return "matching_result"

        import importlib
        import coinjecture.legacy_compat as lc
        importlib.reload(lc)

        result = lc.dual_run("test_func", legacy_fn, refactored_fn)

        # Shadow mode returns refactored result
        assert result == "matching_result"
        assert legacy_called
        assert refactored_called

        # Check metrics
        stats = lc.get_parity_stats()
        assert stats['parity_matches'] > 0

    def test_shadow_mode_drift(self, monkeypatch, caplog):
        """Test shadow mode detects drift"""
        monkeypatch.setenv("CODEC_MODE", "shadow")

        def legacy_fn():
            return "legacy_result"

        def refactored_fn():
            return "refactored_result"

        import importlib
        import coinjecture.legacy_compat as lc
        importlib.reload(lc)

        result = lc.dual_run("test_func", legacy_fn, refactored_fn)

        # Shadow mode still returns refactored (logs drift)
        assert result == "refactored_result"

        # Check drift was logged
        assert "PARITY DRIFT" in caplog.text

    def test_refactored_primary_fallback(self, monkeypatch):
        """Test refactored_primary falls back to legacy on error"""
        monkeypatch.setenv("CODEC_MODE", "refactored_primary")

        def legacy_fn():
            return "legacy_result"

        def refactored_fn():
            raise RuntimeError("Refactored failed")

        import importlib
        import coinjecture.legacy_compat as lc
        importlib.reload(lc)

        result = lc.dual_run("test_func", legacy_fn, refactored_fn)

        # Should fallback to legacy
        assert result == "legacy_result"

    def test_custom_compare_fn(self, monkeypatch):
        """Test custom comparison function"""
        monkeypatch.setenv("CODEC_MODE", "shadow")

        def legacy_fn():
            return [1, 2, 3]

        def refactored_fn():
            return [3, 2, 1]  # Different order

        def compare_fn(a, b):
            # Compare as sets (order doesn't matter)
            return set(a) == set(b)

        import importlib
        import coinjecture.legacy_compat as lc
        importlib.reload(lc)

        result = lc.dual_run("test_func", legacy_fn, refactored_fn, compare_fn)

        # Should match with custom comparison
        assert result == [3, 2, 1]
        stats = lc.get_parity_stats()
        assert stats['parity_matches'] > 0


class TestHeaderHashing:
    """Test block header hashing parity"""

    def test_compute_header_hash_deterministic(self):
        """Test that header hashing is deterministic"""
        from coinjecture.types import BlockHeader
        from coinjecture.legacy_compat import legacy_compute_header_hash

        header = BlockHeader(
            codec_version=1,
            block_index=1,
            timestamp=1609459200,
            parent_hash=b"\x00" * 32,
            merkle_root=b"\x00" * 32,
            miner_address=b"\x00" * 32,
            commitment=b"\x00" * 32,
            difficulty_target=1000,
            nonce=42,
            extra_data=b"",
        )

        # Compute twice
        hash1 = legacy_compute_header_hash(header)
        hash2 = legacy_compute_header_hash(header)

        # Must be identical
        assert hash1 == hash2
        assert len(hash1) == 32  # SHA-256

    def test_header_hash_changes_with_nonce(self):
        """Test that changing nonce changes hash"""
        from coinjecture.types import BlockHeader
        from coinjecture.legacy_compat import legacy_compute_header_hash

        header1 = BlockHeader(
            codec_version=1,
            block_index=1,
            timestamp=1609459200,
            parent_hash=b"\x00" * 32,
            merkle_root=b"\x00" * 32,
            miner_address=b"\x00" * 32,
            commitment=b"\x00" * 32,
            difficulty_target=1000,
            nonce=42,
            extra_data=b"",
        )

        header2 = BlockHeader(
            codec_version=1,
            block_index=1,
            timestamp=1609459200,
            parent_hash=b"\x00" * 32,
            merkle_root=b"\x00" * 32,
            miner_address=b"\x00" * 32,
            commitment=b"\x00" * 32,
            difficulty_target=1000,
            nonce=99,  # Different nonce
            extra_data=b"",
        )

        hash1 = legacy_compute_header_hash(header1)
        hash2 = legacy_compute_header_hash(header2)

        # Hashes must be different
        assert hash1 != hash2


class TestSubsetSumVerification:
    """Test subset sum verification parity"""

    def test_verify_valid_solution(self):
        """Test verification of valid subset sum solution"""
        from coinjecture.types import Problem, Solution, VerifyBudget, HardwareTier, ProblemType
        from coinjecture.legacy_compat import legacy_verify_subset_sum

        problem = Problem(
            problem_type=ProblemType.SUBSET_SUM,
            tier=HardwareTier.DESKTOP,
            elements=[1, 2, 3, 4, 5, 6, 7, 8],
            target=15,
            timestamp=1000,
        )

        # Valid solution: [0,1,2,4] = 1+2+3+5 = 11... wait
        # Let me fix: [1,3,4,6] = 2+4+5+7 = 18... no
        # [0,2,4] = 1+3+5 = 9... no
        # [4,5,6,7] = 5+6+7+8 = 26... no
        # [1,4,7] = 2+5+8 = 15 ✓
        solution = Solution(
            indices=[1, 4, 7],
            timestamp=1001,
        )

        budget = VerifyBudget.from_tier(HardwareTier.DESKTOP)

        result = legacy_verify_subset_sum(problem, solution, budget)
        assert result is True

    def test_verify_invalid_solution_wrong_sum(self):
        """Test verification rejects wrong sum"""
        from coinjecture.types import Problem, Solution, VerifyBudget, HardwareTier, ProblemType
        from coinjecture.legacy_compat import legacy_verify_subset_sum

        problem = Problem(
            problem_type=ProblemType.SUBSET_SUM,
            tier=HardwareTier.DESKTOP,
            elements=[1, 2, 3, 4, 5],
            target=10,
            timestamp=1000,
        )

        # Invalid: [0,1] = 1+2 = 3, not 10
        solution = Solution(
            indices=[0, 1],
            timestamp=1001,
        )

        budget = VerifyBudget.from_tier(HardwareTier.DESKTOP)

        result = legacy_verify_subset_sum(problem, solution, budget)
        assert result is False

    def test_verify_rejects_out_of_bounds(self):
        """Test verification rejects out-of-bounds indices"""
        from coinjecture.types import Problem, Solution, VerifyBudget, HardwareTier, ProblemType
        from coinjecture.legacy_compat import legacy_verify_subset_sum

        problem = Problem(
            problem_type=ProblemType.SUBSET_SUM,
            tier=HardwareTier.DESKTOP,
            elements=[1, 2, 3],
            target=6,
            timestamp=1000,
        )

        # Out of bounds: index 10 doesn't exist
        solution = Solution(
            indices=[0, 1, 10],
            timestamp=1001,
        )

        budget = VerifyBudget.from_tier(HardwareTier.DESKTOP)

        result = legacy_verify_subset_sum(problem, solution, budget)
        assert result is False


class TestParityStats:
    """Test parity statistics tracking"""

    def test_get_parity_stats_structure(self):
        """Test get_parity_stats returns expected structure"""
        stats = get_parity_stats()

        assert isinstance(stats, dict)
        assert "codec_mode" in stats
        assert "rust_available" in stats
        assert "parity_matches" in stats
        assert "parity_drifts" in stats

    def test_codec_mode_from_env(self):
        """Test CODEC_MODE is read from environment"""
        stats = get_parity_stats()
        mode = stats["codec_mode"]

        # Should be one of the valid modes
        assert mode in ["legacy_only", "shadow", "refactored_primary", "refactored_only"]
