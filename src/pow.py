"""
Module: pow
Specification: docs/blockchain/pow.md

Proof-of-Work system with problem registry, commit-reveal protocol,
work score calculation, and difficulty adjustment.
"""

import hashlib
import time
import math
import json
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum

# Import from existing blockchain module
try:
    from .core.blockchain import (
        ComputationalComplexity, ProblemTier, ProblemType,
        calculate_computational_work_score,
        generate_subset_sum_problem, solve_subset_sum, subset_sum_complexity
    )
except ImportError:
    # Fallback for direct execution
    from core.blockchain import (
        ComputationalComplexity, ProblemTier, ProblemType,
        calculate_computational_work_score,
        generate_subset_sum_problem, solve_subset_sum, subset_sum_complexity
    )


# Constants
DEFAULT_EPOCH_DURATION = 3600  # 1 hour in seconds
DEFAULT_TARGET_BLOCK_TIME = 30.0  # 30 seconds
DIFFICULTY_ALPHA = 0.1  # EWMA smoothing factor
MIN_TARGET = 100.0  # Minimum difficulty target
MAX_TARGET = 1000000.0  # Maximum difficulty target


def derive_epoch_salt(parent_hash: bytes, timestamp: int, epoch_duration: int = DEFAULT_EPOCH_DURATION) -> bytes:
    """
    Derive epoch salt from parent hash and timestamp.
    
    Args:
        parent_hash: 32-byte parent block hash
        timestamp: Unix timestamp
        epoch_duration: Epoch duration in seconds
        
    Returns:
        32-byte epoch salt
    """
    epoch_number = timestamp // epoch_duration
    epoch_data = parent_hash + epoch_number.to_bytes(8, 'little')
    return hashlib.sha256(epoch_data).digest()


def create_commitment(problem_params_bytes: bytes, miner_salt: bytes, epoch_salt: bytes, solution_hash: bytes) -> bytes:
    """
    Create commitment hash from problem parameters, miner salt, epoch salt, and solution hash.
    
    This ensures cryptographic binding: valid commitment can only come from valid proof.
    The solution_hash parameter provides the hiding property while maintaining binding.
    
    Args:
        problem_params_bytes: Serialized problem parameters
        miner_salt: 32-byte unique miner salt
        epoch_salt: 32-byte epoch salt
        solution_hash: 32-byte hash of the solution (H(solution))
        
    Returns:
        32-byte commitment hash
    """
    commitment_data = problem_params_bytes + miner_salt + epoch_salt + solution_hash
    return hashlib.sha256(commitment_data).digest()


def verify_commitment(problem_params_bytes: bytes, miner_salt: bytes, epoch_salt: bytes, solution_hash: bytes, commitment: bytes) -> bool:
    """
    Verify that a commitment matches the given parameters including solution hash.
    
    Args:
        problem_params_bytes: Serialized problem parameters
        miner_salt: 32-byte miner salt
        epoch_salt: 32-byte epoch salt
        solution_hash: 32-byte hash of the solution (H(solution))
        commitment: 32-byte commitment to verify
        
    Returns:
        True if commitment is valid
    """
    expected_commitment = create_commitment(problem_params_bytes, miner_salt, epoch_salt, solution_hash)
    return commitment == expected_commitment


def compute_solution_hash(solution: List[int]) -> bytes:
    """
    Compute hash of solution for commitment binding.
    
    Args:
        solution: List of integers representing the solution
        
    Returns:
        32-byte hash of the solution
    """
    # Convert solution to deterministic bytes
    solution_bytes = json.dumps(solution, sort_keys=True).encode('utf-8')
    return hashlib.sha256(solution_bytes).digest()


def encode_problem_params(problem: Dict[str, Any]) -> bytes:
    """
    Encode problem parameters to deterministic bytes.
    
    Args:
        problem: Problem dictionary
        
    Returns:
        Serialized problem parameters
    """
    # Simple encoding: concatenate key-value pairs in sorted order
    # This is deterministic but not optimized for size
    parts = []
    for key in sorted(problem.keys()):
        value = problem[key]
        if isinstance(value, (int, float)):
            parts.append(f"{key}:{value}".encode())
        elif isinstance(value, list):
            # Encode lists as comma-separated values
            list_str = ",".join(str(x) for x in value)
            parts.append(f"{key}:[{list_str}]".encode())
        else:
            parts.append(f"{key}:{str(value)}".encode())
    
    return b"|".join(parts)


def decode_problem_params(problem_bytes: bytes) -> Dict[str, Any]:
    """
    Decode problem parameters from bytes.
    
    Args:
        problem_bytes: Serialized problem parameters
        
    Returns:
        Problem dictionary
    """
    problem = {}
    parts = problem_bytes.split(b"|")
    
    for part in parts:
        if b":" not in part:
            continue
            
        key, value_str = part.split(b":", 1)
        key = key.decode()
        
        # Parse different value types
        if value_str.startswith(b"["):
            # List value
            list_str = value_str[1:-1].decode()  # Remove brackets
            if list_str:
                problem[key] = [int(x) if x.isdigit() else x for x in list_str.split(",")]
            else:
                problem[key] = []
        elif value_str.isdigit():
            problem[key] = int(value_str)
        else:
            try:
                problem[key] = float(value_str)
            except ValueError:
                problem[key] = value_str.decode()
    
    return problem


class ProblemRegistry:
    """
    Registry for managing different problem types.
    
    Implements the ProblemRegistry interface from pow.md specification.
    """
    
    def __init__(self):
        """Initialize the problem registry."""
        self.problem_types = {
            ProblemType.SUBSET_SUM: {
                'generate': self._generate_subset_sum,
                'solve': self._solve_subset_sum,
                'verify': self._verify_subset_sum,
                'encode': self._encode_subset_sum,
                'decode': self._decode_subset_sum
            },
            # Placeholder for future problem types
            # ProblemType.FACTORIZATION: {...},
            # ProblemType.TSP: {...},
            # ProblemType.LATTICE: {...}
        }
    
    def generate(self, problem_type: ProblemType, seed: str, capacity: ProblemTier) -> Dict[str, Any]:
        """
        Generate a problem of the specified type.
        
        Args:
            problem_type: Type of problem to generate
            seed: Seed for deterministic generation
            capacity: Hardware capacity tier
            
        Returns:
            Problem dictionary
        """
        if problem_type not in self.problem_types:
            raise ValueError(f"Unsupported problem type: {problem_type}")
        
        generator = self.problem_types[problem_type]['generate']
        return generator(seed, capacity)
    
    def solve(self, problem: Dict[str, Any]) -> Any:
        """
        Solve a problem.
        
        Args:
            problem: Problem dictionary
            
        Returns:
            Solution
        """
        problem_type = ProblemType(problem.get('type', 'subset_sum'))
        if problem_type not in self.problem_types:
            raise ValueError(f"Unsupported problem type: {problem_type}")
        
        solver = self.problem_types[problem_type]['solve']
        return solver(problem)
    
    def verify(self, problem: Dict[str, Any], solution: Any) -> bool:
        """
        Verify a solution to a problem.
        
        Args:
            problem: Problem dictionary
            solution: Solution to verify
            
        Returns:
            True if solution is valid
        """
        problem_type = ProblemType(problem.get('type', 'subset_sum'))
        if problem_type not in self.problem_types:
            raise ValueError(f"Unsupported problem type: {problem_type}")
        
        verifier = self.problem_types[problem_type]['verify']
        return verifier(problem, solution)
    
    def encode_params(self, problem: Dict[str, Any]) -> bytes:
        """Encode problem parameters to bytes."""
        problem_type = ProblemType(problem.get('type', 'subset_sum'))
        if problem_type not in self.problem_types:
            raise ValueError(f"Unsupported problem type: {problem_type}")
        
        encoder = self.problem_types[problem_type]['encode']
        return encoder(problem)
    
    def decode_params(self, problem_bytes: bytes, problem_type: ProblemType) -> Dict[str, Any]:
        """Decode problem parameters from bytes."""
        if problem_type not in self.problem_types:
            raise ValueError(f"Unsupported problem type: {problem_type}")
        
        decoder = self.problem_types[problem_type]['decode']
        return decoder(problem_bytes)
    
    # Subset Sum implementation
    def _generate_subset_sum(self, seed: str, capacity: ProblemTier) -> Dict[str, Any]:
        """Generate a subset sum problem."""
        return generate_subset_sum_problem(seed=seed, tier=capacity)
    
    def _solve_subset_sum(self, problem: Dict[str, Any]) -> List[int]:
        """Solve a subset sum problem."""
        return solve_subset_sum(problem)
    
    def _verify_subset_sum(self, problem: Dict[str, Any], solution: List[int]) -> bool:
        """Verify a subset sum solution."""
        if not solution:
            return False
        
        numbers = problem.get('numbers', [])
        target = problem.get('target', 0)
        
        # Check if solution elements are in the original numbers
        for num in solution:
            if num not in numbers:
                return False
        
        # Check if sum equals target
        return sum(solution) == target
    
    def _encode_subset_sum(self, problem: Dict[str, Any]) -> bytes:
        """Encode subset sum problem parameters."""
        return encode_problem_params(problem)
    
    def _decode_subset_sum(self, problem_bytes: bytes) -> Dict[str, Any]:
        """Decode subset sum problem parameters."""
        return decode_problem_params(problem_bytes)


def calculate_work_score(complexity: ComputationalComplexity) -> float:
    """
    Calculate work score from computational complexity.
    
    This is a wrapper around the existing calculate_computational_work_score function.
    
    Args:
        complexity: Computational complexity metrics
        
    Returns:
        Work score value
    """
    return calculate_computational_work_score(complexity)


@dataclass
class DifficultyAdjuster:
    """
    Difficulty adjustment system using EWMA of observed scores.
    
    Implements the difficulty mapping from pow.md specification.
    """
    
    target_block_time: float = DEFAULT_TARGET_BLOCK_TIME
    alpha: float = DIFFICULTY_ALPHA
    min_target: float = MIN_TARGET
    max_target: float = MAX_TARGET
    current_target: float = 1000.0  # Initial target
    observed_scores: List[float] = None
    
    def __post_init__(self):
        """Initialize observed scores list."""
        if self.observed_scores is None:
            self.observed_scores = []
    
    def update(self, observed_score: float, block_time: float) -> None:
        """
        Update difficulty based on observed score and block time.
        
        Args:
            observed_score: Work score of the solved block
            block_time: Time taken to mine the block
        """
        self.observed_scores.append(observed_score)
        
        # Keep only recent scores (last 100 blocks)
        if len(self.observed_scores) > 100:
            self.observed_scores = self.observed_scores[-100:]
        
        # Calculate median score
        sorted_scores = sorted(self.observed_scores)
        median_score = sorted_scores[len(sorted_scores) // 2]
        
        # EWMA update: next_target = alpha * prev_target + (1-alpha) * median_score
        # Adjust based on block time ratio
        time_ratio = self.target_block_time / max(block_time, 0.1)
        adjusted_median = median_score * time_ratio
        
        self.current_target = self.alpha * self.current_target + (1 - self.alpha) * adjusted_median
        
        # Clamp to bounds
        self.current_target = max(self.min_target, min(self.max_target, self.current_target))
    
    def get_current_target(self) -> float:
        """
        Get the current difficulty target.
        
        Returns:
            Current difficulty target
        """
        return self.current_target
    
    def get_target_for_capacity(self, capacity: ProblemTier) -> float:
        """
        Get difficulty target adjusted for specific capacity.
        
        Args:
            capacity: Hardware capacity tier
            
        Returns:
            Capacity-adjusted difficulty target
        """
        base_target = self.get_current_target()
        
        # Adjust target based on capacity (higher capacity = higher target)
        capacity_multiplier = {
            ProblemTier.TIER_1_MOBILE: 0.5,
            ProblemTier.TIER_2_DESKTOP: 1.0,
            ProblemTier.TIER_3_WORKSTATION: 1.5,
            ProblemTier.TIER_4_SERVER: 2.0,
            ProblemTier.TIER_5_CLUSTER: 3.0
        }.get(capacity, 1.0)
        
        return base_target * capacity_multiplier


if __name__ == "__main__":
    # Test ProblemRegistry
    print("Testing ProblemRegistry...")
    registry = ProblemRegistry()
    problem = registry.generate(ProblemType.SUBSET_SUM, "test_seed", ProblemTier.TIER_2_DESKTOP)
    solution = registry.solve(problem)
    assert registry.verify(problem, solution)
    print("✅ ProblemRegistry tests passed")
    
    # Test commit-reveal
    print("Testing commit-reveal...")
    parent_hash = b"0" * 32
    epoch_salt = derive_epoch_salt(parent_hash, int(time.time()))
    miner_salt = b"random_salt_here_32bytes_pad"
    params_bytes = registry.encode_params(problem)
    commitment = create_commitment(params_bytes, miner_salt, epoch_salt)
    assert verify_commitment(params_bytes, miner_salt, epoch_salt, commitment)
    print("✅ Commit-reveal tests passed")
    
    # Test difficulty adjustment
    print("Testing difficulty adjustment...")
    adjuster = DifficultyAdjuster(target_block_time=30.0)
    adjuster.update(observed_score=1000.0, block_time=35.0)
    target = adjuster.get_current_target()
    print(f"Adjusted target: {target}")
    
    # Test capacity-specific targets
    for capacity in ProblemTier:
        capacity_target = adjuster.get_target_for_capacity(capacity)
        print(f"Target for {capacity.name}: {capacity_target}")
    
    print("✅ All POW module tests passed!")
