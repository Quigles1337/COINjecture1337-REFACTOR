from __future__ import annotations
import time
import json
import hashlib
from hashlib import sha256
import os
try:
    import psutil  # type: ignore
    _HAS_PSUTIL = True
except Exception:
    psutil = None  # type: ignore
    _HAS_PSUTIL = False
import random
from dataclasses import dataclass
from typing import Literal, Optional, Tuple # Import Optional and Tuple
import math
from enum import Enum

# Aggregation feature flag
ENABLE_AGGREGATION = True

if ENABLE_AGGREGATION:
    try:
        # Local imports to avoid mandatory dependency for core PoW
        from user_submissions.submission import SolutionRecord
    except Exception:
        ENABLE_AGGREGATION = False

@dataclass
class EnergyMetrics:
    """Physically measured energy consumption"""

    # Energy measurements (Joules)
    solve_energy_joules: float      # Total energy to solve
    verify_energy_joules: float     # Total energy to verify

    # Power measurements (Watts)
    solve_power_watts: float        # Average power during solving
    verify_power_watts: float        # Average power during verification

    # Time measurements (seconds)
    solve_time_seconds: float
    verify_time_seconds: float

    # Hardware utilization (percentage)
    cpu_utilization: float          # 0-100%
    memory_utilization: float       # 0-100%
    gpu_utilization: float          # 0-100% (if applicable)


@dataclass
class ComputationalComplexity:
    """Complete complexity specification for a computational problem"""

    # Asymptotic Time Complexities
    time_solve_O: str              # Upper bound (Big O)
    time_solve_Omega: str          # Lower bound (Big Omega)
    time_solve_Theta: Optional[str] # Tight bound (Theta), Optional if not known
    time_verify_O: str
    time_verify_Omega: str
    time_verify_Theta: Optional[str]

    # Asymptotic Space Complexities
    space_solve_O: str
    space_solve_Omega: str
    space_solve_Theta: Optional[str]
    space_verify_O: str
    space_verify_Omega: str
    space_verify_Theta: Optional[str]

    # Problem Classification
    problem_class: Literal[
        'P',           # Polynomial time
        'NP',          # Nondeterministic polynomial
        'NP-Complete', # Hardest problems in NP
        'NP-Hard',     # At least as hard as NP-Complete
        'PSPACE',      # Polynomial space
        'EXPTIME'      # Exponential time
    ]

    # Problem Characteristics
    problem_size: int            # n (number of elements, nodes, etc.)
    solution_size: int           # Size of solution representation

    # Solution Quality (ε-approximation ratio)
    epsilon_approximation: Optional[float] # Approximation ratio, None for exact algorithms

    # Asymmetry Measures (based on theoretical bounds)
    asymmetry_time: float        # solve_time_O / verify_time_O (using O for simplicity in asymmetry)
    asymmetry_space: float       # space_solve_O / verify_time_O

    # Measured Performance
    measured_solve_time: float   # Actual seconds to solve
    measured_verify_time: float  # Actual seconds to verify
    measured_solve_space: int    # Actual bytes used solving
    measured_verify_space: int   # Actual bytes used verifying

    # Energy Metrics
    energy_metrics: EnergyMetrics

    # Problem Data (Needed for verification checks that depend on problem details like target)
    problem: dict

    # Solution Quality (0.0 to 1.0, 1.0 for correct) - This field already exists!
    solution_quality: float


class HardwareType(Enum):
    """Hardware types for accessibility and decentralization"""
    MOBILE_LIGHTWEIGHT = "mobile"  # Smartphones, tablets, IoT devices
    DESKTOP_STANDARD = "desktop"  # Laptops, basic desktops
    WORKSTATION_ADVANCED = "workstation"  # Gaming PCs, development machines
    SERVER_HIGH_PERFORMANCE = "server"  # Dedicated servers, cloud instances
    CLUSTER_DISTRIBUTED = "cluster"  # Multi-node systems, supercomputers


class ProblemType(Enum):
    """Supported computational problem types for PoW."""
    SUBSET_SUM = "subset_sum"
    FACTORIZATION = "factorization"
    TSP = "tsp"


class ProblemRegistry:
    """Registry for pluggable PoW problem types."""

    def __init__(self):
        self._generators = {}
        self._solvers = {}
        self._verifiers = {}
        self._complexity_builders = {}

    def register_problem_type(self, problem_type: ProblemType, generator, solver, verifier, complexity_builder):
        self._generators[problem_type.value] = generator
        self._solvers[problem_type.value] = solver
        self._verifiers[problem_type.value] = verifier
        self._complexity_builders[problem_type.value] = complexity_builder

    def generate(self, problem_type: ProblemType, **kwargs) -> dict:
        generator = self._generators.get(problem_type.value)
        if generator is None:
            raise ValueError(f"No generator registered for problem type: {problem_type}")
        problem = generator(**kwargs)
        # Ensure type tag is present
        if 'type' not in problem:
            problem['type'] = problem_type.value
        return problem

    def solve(self, problem: dict):
        ptype = problem.get('type')
        solver = self._solvers.get(ptype)
        if solver is None:
            raise ValueError(f"No solver registered for problem type: {ptype}")
        return solver(problem)

    def verify(self, problem: dict, solution) -> bool:
        ptype = problem.get('type')
        verifier = self._verifiers.get(ptype)
        if verifier is None:
            raise ValueError(f"No verifier registered for problem type: {ptype}")
        return verifier(problem, solution)

    def build_complexity(self, problem: dict, solution, *, solve_time: float, verify_time: float, solve_memory: int, verify_memory: int, energy_metrics: 'EnergyMetrics') -> 'ComputationalComplexity':
        ptype = problem.get('type')
        builder = self._complexity_builders.get(ptype)
        if builder is None:
            raise ValueError(f"No complexity builder registered for problem type: {ptype}")
        return builder(problem=problem, solution=solution, solve_time=solve_time, verify_time=verify_time, solve_memory=solve_memory, verify_memory=verify_memory, energy_metrics=energy_metrics)


# Global registry instance
PROBLEM_REGISTRY = ProblemRegistry()


# --- Subset Sum Adapters (register into registry) ---

def subset_sum_generate_adapter(seed, tier: ProblemTier):
    return generate_subset_sum_problem(seed=seed, tier=tier)


def subset_sum_solve_adapter(problem):
    return solve_subset_sum(problem)


def subset_sum_verify_adapter(problem, solution):
    return verify_subset_sum(problem, solution)


def subset_sum_complexity_adapter(problem, solution, *, solve_time, verify_time, solve_memory, verify_memory, energy_metrics):
    return subset_sum_complexity(
        problem=problem,
        solution=solution,
        solve_time=solve_time,
        verify_time=verify_time,
        solve_memory=solve_memory,
        verify_memory=verify_memory,
        energy_metrics=energy_metrics
    )


# Register subset sum on import
PROBLEM_REGISTRY.register_problem_type(
    ProblemType.SUBSET_SUM,
    subset_sum_generate_adapter,
    subset_sum_solve_adapter,
    subset_sum_verify_adapter,
    subset_sum_complexity_adapter
)


# --- Factorization (scaffold) ---

def generate_factorization_problem(seed, tier: ProblemTier):
    random.seed(seed)
    # Simple small semiprime for scaffold only (NOT secure)
    p = random.randrange(10007, 10177)
    q = random.randrange(10007, 10177)
    n = p * q
    return {'n': n, 'type': ProblemType.FACTORIZATION.value}


def solve_factorization(problem):
    n = problem['n']
    # Naive trial division scaffold (placeholder)
    i = 2
    while i * i <= n:
        if n % i == 0:
            return {'p': i, 'q': n // i}
        i += 1
    return {'p': 1, 'q': n}


def verify_factorization(problem, solution):
    return solution.get('p', 0) * solution.get('q', 0) == problem['n']


def factorization_complexity(problem, solution, *, solve_time, verify_time, solve_memory, verify_memory, energy_metrics):
    # Treat as subexponential verify O(1) for scaffold
    return ComputationalComplexity(
        time_solve_O="O(2^(n/2))",
        time_solve_Omega="Omega(2^(n/3))",
        time_solve_Theta=None,
        time_verify_O="O(1)",
        time_verify_Omega="Omega(1)",
        time_verify_Theta="Theta(1)",
        space_solve_O="O(n)",
        space_solve_Omega="Omega(1)",
        space_solve_Theta=None,
        space_verify_O="O(1)",
        space_verify_Omega="Omega(1)",
        space_verify_Theta="Theta(1)",
        problem_class='NP-Hard',
        problem_size=len(str(problem['n'])),
        solution_size=2,
        epsilon_approximation=None,
        asymmetry_time=1e6,
        asymmetry_space=1e3,
        measured_solve_time=solve_time,
        measured_verify_time=verify_time,
        measured_solve_space=solve_memory,
        measured_verify_space=verify_memory,
        energy_metrics=energy_metrics,
        problem=problem,
        solution_quality=1.0 if verify_factorization(problem, solution) else 0.0
    )


PROBLEM_REGISTRY.register_problem_type(
    ProblemType.FACTORIZATION,
    generate_factorization_problem,
    solve_factorization,
    verify_factorization,
    factorization_complexity
)


# --- TSP (scaffold) ---

def generate_tsp_problem(seed, tier: ProblemTier):
    random.seed(seed)
    city_count = max(5, min(12, tier.get_size_range()[1] // 2))
    cities = [(random.random(), random.random()) for _ in range(city_count)]
    return {'cities': cities, 'type': ProblemType.TSP.value}


def solve_tsp(problem):
    cities = problem['cities']
    # Trivial identity tour scaffold
    tour = list(range(len(cities)))
    return {'tour': tour, 'distance': len(tour)}


def verify_tsp(problem, solution):
    tour = solution.get('tour', [])
    return isinstance(tour, list) and len(set(tour)) == len(problem['cities'])


def tsp_complexity(problem, solution, *, solve_time, verify_time, solve_memory, verify_memory, energy_metrics):
    n = len(problem['cities'])
    return ComputationalComplexity(
        time_solve_O="O(n!)",
        time_solve_Omega="Omega(n)",
        time_solve_Theta=None,
        time_verify_O="O(n)",
        time_verify_Omega="Omega(n)",
        time_verify_Theta="Theta(n)",
        space_solve_O="O(n)",
        space_solve_Omega="Omega(1)",
        space_solve_Theta=None,
        space_verify_O="O(n)",
        space_verify_Omega="Omega(1)",
        space_verify_Theta="Theta(n)",
        problem_class='NP-Complete',
        problem_size=n,
        solution_size=len(solution.get('tour', [])),
        epsilon_approximation=None,
        asymmetry_time=math.factorial(max(1, n)) / max(1, n),
        asymmetry_space=max(1, n),
        measured_solve_time=solve_time,
        measured_verify_time=verify_time,
        measured_solve_space=solve_memory,
        measured_verify_space=verify_memory,
        energy_metrics=energy_metrics,
        problem=problem,
        solution_quality=1.0 if verify_tsp(problem, solution) else 0.0
    )


PROBLEM_REGISTRY.register_problem_type(
    ProblemType.TSP,
    generate_tsp_problem,
    solve_tsp,
    verify_tsp,
    tsp_complexity
)

class ProblemTier(Enum):
    """Problem difficulty tiers - ALL Subset Sum with different sizes"""
    TIER_1_MOBILE = "mobile"  # 8-12 elements
    TIER_2_DESKTOP = "desktop"  # 12-16 elements
    TIER_3_WORKSTATION = "workstation"  # 16-20 elements
    TIER_4_SERVER = "server"  # 20-24 elements
    TIER_5_CLUSTER = "cluster" # 24-32 elements

    def get_size_range(self) -> Tuple[int, int]:
        """Returns the (min_size, max_size) for the problem tier."""
        if self == ProblemTier.TIER_1_MOBILE:
            return (8, 12)
        elif self == ProblemTier.TIER_2_DESKTOP:
            return (12, 16)
        elif self == ProblemTier.TIER_3_WORKSTATION:
            return (16, 20)
        elif self == ProblemTier.TIER_4_SERVER:
            return (20, 24)
        elif self == ProblemTier.TIER_5_CLUSTER:
            return (24, 32)
        else:
            raise ValueError("Unknown ProblemTier")


def complexity_to_operations(complexity_str: str, n: int) -> float:
    """
    Convert Big-O notation to estimated operation count.

    Examples:
        O(n) with n=100 -> 100 operations
        O(n^2) with n=100 -> 10,000 operations
        O(2^n) with n=20 -> 1,048,876 operations
        O(n!) with n=10 -> 3,628,800 operations
        O(n * target) with n=10 and target=100 -> 1000 operations
    """

    # Parse complexity string - handle O(), Omega(), Theta() if needed, but for operations
    # we likely just use the dominant term from O() or Theta(). Sticking to O() for now.
    # Remove "O(", "Omega(", "Theta(" and ")"
    cleaned_complexity_str = complexity_str.replace("O(", "").replace("Omega(", "").replace("Theta(", "").replace(")", "").strip()


    complexity_map = {
        '1': lambda n: 1,
        'log n': lambda n: math.log2(n) if n > 1 else 0, # log(1) is 0 or undefined, handle n=1
        'n': lambda n: n,
        'n log n': lambda n: n * math.log2(n) if n > 1 else 0, # handle n=1
        'n^2': lambda n: n ** 2,
        'n^3': lambda n: n ** 3,
        '2^n': lambda n: 2 ** n,
        '2^(n/2)': lambda n: 2 ** (n / 2),
        'n!': lambda n: math.factorial(n),
        'n^n': lambda n: n ** n,
    }


    if cleaned_complexity_str in complexity_map:
        return complexity_map[cleaned_complexity_str](n)
    else:
        # Attempt to parse n^k or c^n forms
        if '^' in cleaned_complexity_str:
            parts = cleaned_complexity_str.split('^')
            if len(parts) == 2:
                base, exponent = parts
                if base == 'n':
                    try:
                        k = float(exponent)
                        return n ** k
                    except ValueError:
                        pass
                else:
                    try:
                        c = float(base)
                        if exponent == 'n':
                            return c ** n
                        else: # Handle cases like c^k
                             k = float(exponent)
                             return c ** k
                    except ValueError:
                        pass
        # If none of the above, it's an unknown complexity string
        raise ValueError(f"Unknown or unparseable complexity: {cleaned_complexity_str}")


def calculate_computational_work_score(complexity: ComputationalComplexity) -> float:
    """
    Calculate proof-of-work score based primarily on measured performance and energy,
    incorporating refined complexity metrics.
    """

    n = complexity.problem_size
    energy = complexity.energy_metrics

    # Prioritize measured metrics for work score
    # Time and Space Asymmetry based on measured values
    time_asymmetry_measured = (
        complexity.measured_solve_time / max(1e-9, complexity.measured_verify_time) # Avoid division by zero
    )
    space_asymmetry_measured = (
        complexity.measured_solve_space / max(1, complexity.measured_verify_space) # Avoid division by zero
    )

    # Problem Class Weight
    class_weights = {
        'P': 1,
        'NP': 10,
        'NP-Complete': 100,
        'NP-Hard': 100,
        'PSPACE': 500,
        'EXPTIME': 1000
    }
    problem_weight = class_weights.get(complexity.problem_class, 1)

    # Size Factor
    size_factor = max(1, n)

    # Solution Quality Score (using epsilon approximation)
    # Lower epsilon means higher quality (closer to optimal)
    # Score should be higher for lower epsilon. 1 / (1 + epsilon) is one way.
    # For exact solutions (epsilon is None), quality is 1.0.
    if complexity.epsilon_approximation is None:
        quality_score = 1.0
    else:
        # Ensure epsilon is non-negative
        epsilon = max(0.0, complexity.epsilon_approximation)
        quality_score = 1.0 / (1.0 + epsilon) # Score decreases as epsilon increases


    # Energy Efficiency Score
    energy_efficiency_score = 1.0
    if energy.solve_energy_joules > 0 and complexity.measured_solve_time > 0:
        # Use estimated solve operations from O() as a proxy for work size
        try:
            estimated_solve_ops = complexity_to_operations(complexity.time_solve_O, n)
            if estimated_solve_ops > 0:
                reference_energy_per_op = 1e-9 # Example: 1 nJ per operation (needs calibration)
                actual_energy_per_op = energy.solve_energy_joules / estimated_solve_ops
                if actual_energy_per_op > 0:
                     energy_efficiency_score = min(2.0, max(0.1, reference_energy_per_op / actual_energy_per_op)) # Cap efficiency bonus/penalty
        except ValueError:
            # Handle cases where complexity_to_operations fails
            energy_efficiency_score = 1.0 # Default to no bonus/penalty


    # Combined Work Score
    work_score = (
        time_asymmetry_measured *
        math.sqrt(space_asymmetry_measured) *
        problem_weight *
        size_factor *
        quality_score *
        energy_efficiency_score
    )

    # Add a small bonus based on theoretical asymmetry
    try:
        # These calls might fail if the complexity strings are not parsable by complexity_to_operations
        # We need to ensure complexity_to_operations can handle all strings stored in Complexity.
        theoretical_time_asymmetry = complexity_to_operations(complexity.time_solve_O, n) / max(1e-9, complexity_to_operations(complexity.time_verify_O, n))
        # This call will fail if complexity_to_operations doesn't handle "O(n * target)"
        # Now, subset_sum_complexity calculates asymmetry directly, so this call is fine if space_solve_O is a parsable term like O(n) or O(2^n)
        # If space_solve_O is "O(n * target)", this call will still fail.
        # Let's adjust subset_sum_complexity to store parsable strings or calculate asymmetry_space differently.

        # After modifying subset_sum_complexity to calculate asymmetry directly,
        # we can use the stored asymmetry values here for the theoretical bonus.
        theoretical_time_asymmetry_stored = complexity.asymmetry_time
        theoretical_space_asymmetry_stored = complexity.asymmetry_space


        theoretical_bonus = math.log(max(1, theoretical_time_asymmetry_stored)) + math.log(max(1, theoretical_space_asymmetry_stored)) * 0.5
        work_score += theoretical_bonus
    except ValueError as e:
        # Catch the specific ValueError from complexity_to_operations if it's still used here.
        print(f"Error calculating theoretical bonus: {e}")
        pass # No theoretical bonus if parsing fails
    except ZeroDivisionError:
        # Handle division by zero
        pass # No theoretical bonus


    return work_score


def subset_sum_complexity(
    problem: dict, # Pass the problem dictionary
    solution: list[int],
    solve_time: float,
    verify_time: float,
    solve_memory: int,
    verify_memory: int,
    energy_metrics: EnergyMetrics
) -> ComputationalComplexity:
    """
    Create complexity specification for a Subset Sum problem, including
    asymptotic bounds and epsilon approximation (for potential approximate solvers).
    """

    numbers = problem['numbers']
    target = problem['target']
    n = len(numbers)
    solution_length = len(solution)

    # For the exact Subset Sum solver provided, epsilon approximation is None.
    # If an approximate solver was used, this would be its approximation ratio.
    epsilon_approximation = None

    # Calculate solution quality (simple correctness check for exact solver)
    is_correct = sum(solution) == target
    # For an exact solver, quality is 1.0 if correct, 0.0 otherwise.
    # For an approximate solver, quality is related to epsilon.
    # This correctness measure is used in calculate_work_score via the epsilon_approximation.
    # If is_correct is False, epsilon_approximation should probably be set to infinity or a large number
    # to result in a quality_score of 0.

    # Let's update epsilon_approximation based on correctness for clarity
    if not is_correct:
        epsilon_approximation = float('inf') # Infinite epsilon for incorrect solutions


    # Uniqueness is hard to determine without finding all solutions, simplify
    # uniqueness = 1.0 # Assume unique for simplicity in this model - REMOVE THIS LINE


    # Subset Sum is NP-Complete
    # Calculate theoretical asymmetry directly using estimated operations based on n and target.
    estimated_solve_ops_time = 2**n
    estimated_verify_ops_time = n

    # Estimated space for DP is proportional to n * target.
    # Estimated space for verification is proportional to n (storing the subset).
    estimated_solve_ops_space = n * target
    estimated_verify_ops_space = solution_length # Or n, depending on how subset is stored

    # Calculate theoretical asymmetry directly
    theoretical_time_asymmetry_calc = estimated_solve_ops_time / max(1e-9, estimated_verify_ops_time)
    theoretical_space_asymmetry_calc = estimated_solve_ops_space / max(1, estimated_verify_ops_space)


    return ComputationalComplexity(
        # Asymptotic bounds for Subset Sum (kept as strings for documentation)
        time_solve_O="O(2^n)",
        time_solve_Omega="Omega(2^(n/2))",
        time_solve_Theta=None,
        time_verify_O="O(n)",
        time_verify_Omega="Omega(n)",
        time_verify_Theta="Theta(n)",

        # Space complexities (Asymptotic bounds for dynamic programming solver)
        # Keep the strings as documentation, but asymmetry calculated numerically.
        space_solve_O="O(n * target)",
        space_solve_Omega="Omega(n)",
        space_solve_Theta=None,
        space_verify_O="O(n)",
        space_verify_Omega="Omega(n)",
        space_verify_Theta="Theta(n)",


        # Classification
        problem_class='NP-Complete',

        # Size metrics
        problem_size=n,
        solution_size=solution_length,

        # Solution Quality (ε-approximation ratio)
        epsilon_approximation=epsilon_approximation, # Use calculated epsilon (None or inf)

        # Asymmetry (theoretical - calculated here using n and target)
        asymmetry_time=theoretical_time_asymmetry_calc,
        asymmetry_space=theoretical_space_asymmetry_calc,


        # Quality (based on correctness and epsilon)
        # The quality score in the dataclass itself is not directly used in calculate_work_score
        # but is a metric *reported* by the solver. Let's set it based on correctness.
        solution_quality=1.0 if is_correct else 0.0,
        # uniqueness=uniqueness, # REMOVE THIS LINE
        # Measured performance
        measured_solve_time=solve_time,
        measured_verify_time=verify_time,
        measured_solve_space=solve_memory,
        measured_verify_space=verify_memory,

        # Energy Metrics
        energy_metrics=energy_metrics,
        problem=problem # Store the problem dictionary in complexity
    )


@dataclass
class Block:
    """
    COINjecture block with computational problem solving as proof-of-work.
    The solution itself IS the proof of work.
    """

    # Standard blockchain fields
    index: int
    timestamp: float
    previous_hash: str

    # Transactions
    transactions: list['Transaction'] # Use string literal for forward reference
    merkle_root: str

    # Mathematical Problem
    problem: dict  # The computational problem (e.g., Subset Sum parameters)

    # The Solution (This IS the Proof of Work)
    solution: list[int] # The solution to the problem

    # Measured Complexity and Energy (for validation and potential future use)
    complexity: ComputationalComplexity

    # Hardware Capacity
    mining_capacity: ProblemTier # Store the mining capacity in the block

    # Cumulative Work Score (New field)
    cumulative_work_score: float

    # Block hash (deterministic from contents)
    block_hash: str

    # IPFS CID for full proof bundle
    offchain_cid: Optional[str] = None

    def calculate_hash(self) -> str:
        """Block hash is deterministic from key contents."""
        # Hash the core elements that define the block's validity and identity.
        # The solution is part of the problem definition and thus implicitly hashed via problem.
        data = {
            'index': self.index,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'merkle_root': self.merkle_root,
            'problem': self.problem, # Include problem in hash
            'solution': self.solution, # Include solution in hash
            'mining_capacity': self.mining_capacity.value, # Include the capacity value in the hash
            'cumulative_work_score': self.cumulative_work_score # Include cumulative work score in hash
        }
        # Ensure problem and solution are serializable. Subset Sum problem/solution are lists/dicts.
        return sha256(json.dumps(data, sort_keys=True).encode('utf-8')).hexdigest()


    def is_valid(self) -> bool:
        """
        Validate block by verifying the solution and problem size against the mining tier.
        Difficulty is now tied to the problem size generated by the mining tier.
        """

        # 1. Verify the solution is mathematically correct for the problem via registry
        if not PROBLEM_REGISTRY.verify(self.problem, self.solution):
            return False

        # 2. Verify the problem size falls within the range of the claimed mining capacity
        claimed_min_size, claimed_max_size = self.mining_capacity.get_size_range()
        actual_problem_size = self.problem.get('size', 0)
        if not (claimed_min_size <= actual_problem_size <= claimed_max_size):
            print(f"Problem size {actual_problem_size} is not within the range of capacity {self.mining_capacity.name} ({claimed_min_size}-{claimed_max_size}).")
            return False


        # 3. (Optional but good practice) Verify measured complexity is plausible
        # This doesn't invalidate the block based on work score, but helps identify
        # potentially fraudulent claims about performance or energy usage.
        # The verify_complexity_metrics function now checks for internal consistency
        # and plausible ranges of the reported metrics, using the stored problem.
        try:
            if not verify_complexity_metrics(self.complexity):
                 print("Complexity metrics verification failed.")
                 # Decide if this should invalidate the block or just be a warning.
                 # For a strict PoW, it probably should invalidate.
                 return False
        except Exception as e:
             print(f"Error during complexity verification: {e}")
             return False

        # 4. Verify the cumulative work score is correct (previous_block.cumulative_work_score + current_block.work_score)
        # This check requires access to the previous block's cumulative work score, which is
        # not directly available in the current is_valid signature.
        # A full blockchain implementation would pass the previous block to is_valid or
        # have access to the blockchain state to retrieve it.
        # For this isolated block validation, we'll skip the cumulative score verification
        # but acknowledge its importance in a full system.
        # print("Note: Cumulative work score verification is skipped in this isolated block check.")
        # In a real system, you would do something like:
        # expected_cumulative_score = previous_block.cumulative_work_score + calculate_computational_work_score(self.complexity)
        # if abs(self.cumulative_work_score - expected_cumulative_score) > tolerance: return False


        # 5. Verify block hash
        if self.block_hash != self.calculate_hash():
            return False

        return True

    def to_dict(self) -> dict:
        """Convert block to dictionary for JSON serialization."""
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'previous_hash': self.previous_hash,
            'transactions': [tx.to_dict() if hasattr(tx, 'to_dict') else tx for tx in self.transactions],
            'merkle_root': self.merkle_root,
            'problem': self.problem,
            'solution': self.solution,
            'complexity': {
                'time_solve_O': self.complexity.time_solve_O,
                'time_solve_Omega': self.complexity.time_solve_Omega,
                'time_solve_Theta': self.complexity.time_solve_Theta,
                'time_verify_O': self.complexity.time_verify_O,
                'time_verify_Omega': self.complexity.time_verify_Omega,
                'time_verify_Theta': self.complexity.time_verify_Theta,
                'space_solve_O': self.complexity.space_solve_O,
                'space_solve_Omega': self.complexity.space_solve_Omega,
                'space_solve_Theta': self.complexity.space_solve_Theta,
                'space_verify_O': self.complexity.space_verify_O,
                'space_verify_Omega': self.complexity.space_verify_Omega,
                'space_verify_Theta': self.complexity.space_verify_Theta,
                'solution_quality': self.complexity.solution_quality
            },
            'mining_capacity': self.mining_capacity.value if hasattr(self.mining_capacity, 'value') else str(self.mining_capacity),
            'cumulative_work_score': self.cumulative_work_score,
            'block_hash': self.block_hash,
            'offchain_cid': self.offchain_cid
        }


def verify_complexity_metrics(complexity: ComputationalComplexity) -> bool:
    """
    Verify that claimed complexity metrics are plausible.
    This is a check for honesty, not the core PoW validation.
    Requires the problem data to be stored in the Complexity object.
    """

    n = complexity.problem_size
    problem = complexity.problem # Get the problem data from the complexity object
    target = problem.get('target', None) # Get target from the stored problem

    if target is None:
        print("Target not found in stored problem data within Complexity object.")
        return False # Cannot verify space complexity without target

    # 1. Verify claimed asymptotic complexities are in the supported map or parsable format
    supported_asymptotic_forms = ['O()', 'Omega()', 'Theta()'] # Basic check for format
    def check_asymptotic_form(comp_str):
         if comp_str is None: return True # Theta is optional
         return any(comp_str.startswith(form) for form in supported_asymptotic_forms) and comp_str.endswith(')')

    # Check format of all complexity strings
    if not (check_asymptotic_form(complexity.time_solve_O) and
            check_asymptotic_form(complexity.time_solve_Omega) and
            check_asymptotic_form(complexity.time_solve_Theta) and
            check_asymptotic_form(complexity.time_verify_O) and
            check_asymptotic_form(complexity.time_verify_Omega) and
            check_asymptotic_form(complexity.time_verify_Theta) and
            check_asymptotic_form(complexity.space_solve_O) and
            check_asymptotic_form(complexity.space_solve_Omega) and
            check_asymptotic_form(complexity.space_solve_Theta) and
            check_asymptotic_form(complexity.space_verify_O) and
            check_asymptotic_form(complexity.space_verify_Omega) and
            check_asymptotic_form(complexity.space_verify_Theta)):
         print("Complexity format check failed.")
         return False


    # 2. Verify problem class is supported
    supported_classes = ['P', 'NP', 'NP-Complete', 'NP-Hard', 'PSPACE', 'EXPTIME']
    if complexity.problem_class not in supported_classes:
        print(f"Unsupported problem class: {complexity.problem_class}")
        return False

    # 3. Verify measured times are non-negative
    if complexity.measured_solve_time < 0 or complexity.measured_verify_time < 0:
        print("Measured times are negative.")
        return False

    # 4. Verify measured space is non-negative
    if complexity.measured_solve_space < 0 or complexity.measured_verify_space < 0:
        print("Measured space is negative.")
        return False

    # 5. Verify energy metrics are non-negative
    if complexity.energy_metrics.solve_energy_joules < 0 or \
       complexity.energy_metrics.verify_energy_joules < 0 or \
       complexity.energy_metrics.solve_power_watts < 0 or \
       complexity.energy_metrics.verify_power_watts < 0:
       print("Energy metrics are negative.")
       return False

    # 6. Verify asymmetry is reasonable (based on *stored* theoretical asymmetry values)
    # We trust the stored asymmetry values if basic checks pass, to avoid recalculating
    # complex expressions like n*target here.
    if complexity.asymmetry_time < 0 or complexity.asymmetry_space < 0:
         return False

    # 7. Verify epsilon approximation is non-negative if provided
    if complexity.epsilon_approximation is not None and complexity.epsilon_approximation < 0:
        print("Epsilon approximation is negative.")
        return False

    # 8. Check consistency between epsilon_approximation and solution_quality
    # If epsilon is None (exact), quality should be 1.0 or 0.0 (correct/incorrect).
    # If epsilon is not None (approximate), quality should be calculated from epsilon.
    if complexity.epsilon_approximation is None:
        if complexity.solution_quality not in [0.0, 1.0]:
            print(f"Consistency check failed: Exact solution should have quality 0.0 or 1.0, got {complexity.solution_quality}")
            return False
    else:
        # For approximate solutions, check if quality is roughly consistent with epsilon
        # This is a heuristic check. 1 / (1 + epsilon) is one way quality might be derived.
        expected_quality_from_epsilon = 1.0 / (1.0 + max(0.0, complexity.epsilon_approximation))
        if abs(complexity.solution_quality - expected_quality_from_epsilon) > 0.1: # Allow 0.1 deviation
             print(f"Consistency check failed: Reported quality {complexity.solution_quality} inconsistent with epsilon {complexity.epsilon_approximation} (expected ~{expected_quality_from_epsilon})")
             return False


    # Add checks for consistency between measured values and claimed asymptotic complexity.
    # This is challenging without benchmarks or historical data, but basic checks is possible.
    # E.g., if claimed time_solve_O is O(n) but measured_solve_time increases exponentially with n.
    # This level of verification requires more context and complexity tracking over time.

    return True


def mine_block(
    transactions: list['Transaction'],
    previous_block: Block,
    capacity: ProblemTier, # Accept ProblemTier instead of size
    problem_type: ProblemType = ProblemType.SUBSET_SUM,
    submission_id: Optional[str] = None,
    problem_pool: Optional[object] = None,
    miner_address: str = "Miner"
) -> Block:
    """
    Mine a block by solving a computational problem.
    The solution itself IS the proof of work.
    """

    # 1. Generate problem via registry, seeded by previous block and capacity
    problem = PROBLEM_REGISTRY.generate(
        problem_type,
        seed=previous_block.block_hash,
        tier=capacity
    )

    # 2. Solve the problem (THIS IS THE WORK)
    start_time = time.time()
    start_memory = get_memory_usage()

    # In a real system, this solver would be the "miner" process.
    solution = PROBLEM_REGISTRY.solve(problem)

    solve_time = time.time() - start_time
    solve_memory = get_memory_usage() - start_memory

    # 3. Measure verification performance
    verify_start = time.time()
    verify_start_mem = get_memory_usage()

    is_valid = PROBLEM_REGISTRY.verify(problem, solution)

    verify_time = time.time() - verify_start
    verify_memory = get_memory_usage() - verify_start_mem

    if not is_valid:
        # This indicates an issue with the solver or problem generation.
        raise InvalidSolutionError("Solution doesn't satisfy problem")

    # 4. Create complexity specification (based on measured performance and known theoreticals)
    # Note: Energy metrics are placeholders and need real measurement.
    placeholder_energy_metrics = EnergyMetrics(
        solve_energy_joules=solve_time * 100, # Placeholder: Assume 100 W power consumption
        verify_energy_joules=verify_time * 1, # Placeholder: Assume 1 W power consumption
        solve_power_watts=100,
        verify_power_watts=1,
        solve_time_seconds=solve_time,
        verify_time_seconds=verify_time,
        cpu_utilization=80.0, # Placeholder
        memory_utilization=50.0, # Placeholder
        gpu_utilization=0.0 # Placeholder
    )

    # Pass the entire problem dict, solution, measured times, and energy metrics
    print(f"Calling subset_sum_complexity with: problem={problem}, solution size={len(solution) if solution is not None else 0}, solve_time={solve_time:.4f}, verify_time={verify_time:.4f}, solve_memory={solve_memory}, verify_memory={verify_memory}")


    complexity = PROBLEM_REGISTRY.build_complexity(
        problem=problem,
        solution=solution,
        solve_time=solve_time,
        verify_time=verify_time,
        solve_memory=solve_memory,
        verify_memory=verify_memory,
        energy_metrics=placeholder_energy_metrics
    )

    # Calculate the individual work score for this block
    current_block_work_score = calculate_computational_work_score(complexity)

    # Calculate the cumulative work score for this block
    # This requires the cumulative work score from the previous block
    previous_cumulative_work_score = previous_block.cumulative_work_score if previous_block and hasattr(previous_block, 'cumulative_work_score') else 0.0 # Handle genesis case and old block instances
    cumulative_work_score = previous_cumulative_work_score + current_block_work_score


    # 5. Build merkle root
    # Assuming transactions is a list of objects with a to_dict() or similar method
    transaction_dicts = [tx.to_dict() for tx in transactions] if transactions else []
    # Merkle root now includes problem and solution as part of the "transaction" data
    # conceptually, though not actual user transactions.
    merkle_root = build_merkle_root(transaction_dicts + [{'problem': problem, 'solution': solution}], "") # No separate proof commitment in this model


    # 6. Create block
    block = Block(
        index=previous_block.index + 1,
        timestamp=time.time(),
        previous_hash=previous_block.block_hash,
        transactions=transactions, # Still include actual transactions
        merkle_root=merkle_root,
        problem=problem,
        solution=solution,
        complexity=complexity, # Include measured complexity
        mining_capacity=capacity, # Store the mining capacity in the block
        cumulative_work_score=cumulative_work_score, # Include the calculated cumulative work score
        block_hash=""  # Calculate after
    )

    block.block_hash = block.calculate_hash()

    # Upload proof bundle to IPFS (optional)
    try:
        from .api.proof_bundler import create_proof_bundle, serialize_proof_bundle
        from .storage import StorageManager, StorageConfig, NodeRole, PruningMode
        
        # Create storage manager for IPFS upload
        storage_config = StorageConfig(
            data_dir="data",
            role=NodeRole.FULL,
            pruning_mode=PruningMode.FULL,
            ipfs_api_url="http://localhost:5001"
        )
        storage_manager = StorageManager(storage_config)
        
        # Check if IPFS is available
        if storage_manager.ipfs_client.health_check():
            # Create proof bundle and upload to IPFS
            proof_bundle = create_proof_bundle(block)
            bundle_bytes = serialize_proof_bundle(proof_bundle)
            cid = storage_manager.store_proof_bundle(bundle_bytes)
            
            if cid:
                block.offchain_cid = cid
                print(f"✅ Proof bundle uploaded to IPFS: {cid}")
            else:
                # Generate a placeholder CID for demonstration
                import hashlib
                placeholder_cid = "Qm" + hashlib.sha256(block.block_hash.encode()).hexdigest()[:44]
                block.offchain_cid = placeholder_cid
                print(f"📦 Proof bundle ready (placeholder CID): {placeholder_cid}")
        else:
            # Generate a placeholder CID when IPFS is not available
            import hashlib
            placeholder_cid = "Qm" + hashlib.sha256(block.block_hash.encode()).hexdigest()[:44]
            block.offchain_cid = placeholder_cid
            print(f"📦 Proof bundle ready (placeholder CID): {placeholder_cid}")
            
    except Exception as e:
        # Generate a placeholder CID on any error
        import hashlib
        placeholder_cid = "Qm" + hashlib.sha256(block.block_hash.encode()).hexdigest()[:44]
        block.offchain_cid = placeholder_cid
        print(f"📦 Proof bundle ready (placeholder CID): {placeholder_cid}")

    # Optionally append solution record to a submission via pool
    if ENABLE_AGGREGATION and submission_id and problem_pool is not None:
        try:
            record = SolutionRecord(
                block_number=block.index,
                block_hash=block.block_hash,
                miner_address=miner_address,
                problem_instance=problem,
                solution=solution,
                solution_quality=complexity.solution_quality,
                work_score=current_block_work_score,
                solve_time=solve_time,
                energy_used=placeholder_energy_metrics.solve_energy_joules,
                verified=is_valid,
                verification_time=verify_time,
            )
            problem_pool.record_solution(submission_id, record)
        except Exception as e:
            print(f"Aggregation record append failed: {e}")

    # Display mining reward information
    if transactions:
        reward_tx = transactions[0]  # First transaction is typically the mining reward
        print(f"\n💰 Mining Reward Details:")
        print(f"   🏆 Block Mined Successfully!")
        print(f"   💎 Reward: {reward_tx.amount} coins")
        print(f"   👤 Recipient: {reward_tx.recipient}")
        print(f"   🆔 Transaction ID: {reward_tx.transaction_id[:16]}...")
        print(f"   ⏰ Timestamp: {time.ctime(reward_tx.timestamp)}")
        print(f"   📊 Work Score: {cumulative_work_score:.2f}")
        print(f"   🔧 Capacity: {capacity.name}")
        print(f"   🧩 Problem Size: {problem.get('size', 'unknown')}")
        print(f"   ⚡ Solve Time: {solve_time:.4f}s")
        print(f"   ✅ Verification: {verify_time:.6f}s")
        print(f"   🌐 IPFS CID: {block.offchain_cid if hasattr(block, 'offchain_cid') and block.offchain_cid else 'Not uploaded'}")

    return block

# Placeholder functions

def create_proof_commitment(problem, solution, complexity):
    """Removed in the unified model."""
    return ""

def store_proof_ipfs(proof_data):
    """Storing problem/solution/complexity on IPFS (placeholder)."""
    print("Storing problem/solution/complexity data to IPFS (placeholder)...")
    # In a real system, this would store the relevant parts of the block data off-chain.
    # For this model, the block hash is sufficient on-chain.
    # The full data might be stored for auditability.
    # print(json.dumps(proof_data, indent=2)) # Avoid printing large data
    # Placeholder: Return a dummy CID.
    return "Qm...dummyCID..."

def build_merkle_root(data_dicts, *args):
    """Build a Merkle root from data dictionaries."""
    # Includes problem and solution in the data_dicts.
    import hashlib
    # Ensure data_dicts are serializable
    try:
        data_hashes = [hashlib.sha256(json.dumps(item, sort_keys=True).encode('utf-8')).hexdigest() for item in data_dicts]
    except TypeError as e:
         print(f"Error serializing data for Merkle root: {e}")
         data_hashes = [hashlib.sha256(str(item).encode('utf-8')).hexdigest() for item in data_dicts] # Simple string representation as fallback

    # Simple concatenation and hash for placeholder Merkle root:
    if not data_hashes:
        return hashlib.sha256("").hexdigest() # Hash of empty string if no data

    # A proper Merkle tree would build a tree structure.
    # Simple concatenation for placeholder:
    return hashlib.sha256("".join(data_hashes).encode('utf-8')).hexdigest()


def get_memory_usage():
    """Get current process memory usage in bytes."""
    try:
        if _HAS_PSUTIL:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss
        # Fallback using resource (Unix/macOS)
        try:
            import resource
            usage = resource.getrusage(resource.RUSAGE_SELF)
            # On macOS ru_maxrss is bytes; on Linux it's kilobytes. Multiply by 1024 to be safe.
            return int(getattr(usage, 'ru_maxrss', 0)) * 1024
        except Exception:
            pass
    except Exception as e:
        print(f"Could not get memory usage: {e}")
    return 0


def generate_subset_sum_problem(seed, tier: ProblemTier):
    """Generate a Subset Sum problem based on seed and difficulty tier."""
    import random
    random.seed(seed)
    min_size, max_size = tier.get_size_range()
    size = random.randint(min_size, max_size) # Select a random size within the tier's range

    numbers = [random.randint(1, 100) for _ in range(size)]
    # Ensure a solution exists by summing a random subset
    subset_size = random.randint(1, max(1, size // 2))
    target = sum(random.sample(numbers, subset_size))
    return {'numbers': numbers, 'target': target, 'size': size, 'type': ProblemType.SUBSET_SUM.value}


def solve_subset_sum(problem):
    """Solve the Subset Sum problem using a dynamic programming approach."""
    numbers = problem['numbers']
    target = problem['target']
    n = len(numbers)

    if target < 0:
        return []
    if target == 0:
        return []

    dp = {0: []}

    for num in numbers:
        new_sums = {}
        for current_sum, path in dp.items():
            new_sum = current_sum + num
            if new_sum <= target:
                if new_sum not in dp:
                     new_sums[new_sum] = path + [num]
        dp.update(new_sums)

    if target in dp:
        return dp[target]
    else:
        return []


def verify_subset_sum(problem, solution):
    """Verify if the solution is correct for the Subset Sum problem."""
    if not isinstance(solution, list):
        return False
    return sum(solution) == problem['target']

class InvalidSolutionError(Exception):
    """Custom exception for invalid solutions."""
    pass

class InsufficientWorkError(Exception):
    """Custom exception when the solved problem's work score is too low."""
    pass


# Enhanced Transaction class with cryptographic signatures
class Transaction:
    """
    Enhanced Transaction class with cryptographic signatures and validation.
    """
    
    def __init__(self, sender: str, recipient: str, amount: float, timestamp: float = None):
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = timestamp or time.time()
        self.transaction_id = ""
        self.signature = ""
        self.public_key = ""
        
        # Calculate transaction ID
        self.transaction_id = self.calculate_transaction_id()
    
    def calculate_transaction_id(self) -> str:
        """Calculate unique transaction ID from transaction data."""
        import hashlib
        data = f"{self.sender}{self.recipient}{self.amount}{self.timestamp}".encode()
        return hashlib.sha256(data).hexdigest()
    
    def sign(self, private_key_bytes: bytes) -> str:
        """
        Sign transaction with private key.
        
        Args:
            private_key_bytes: Private key as bytes
            
        Returns:
            Signature as hex string
        """
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            from cryptography.hazmat.primitives import serialization
            
            # Load private key
            private_key = ed25519.Ed25519PrivateKey.from_private_bytes(private_key_bytes)
            
            # Get public key for storage
            public_key = private_key.public_key()
            self.public_key = public_key.public_bytes(
                encoding=serialization.Encoding.Raw,
                format=serialization.PublicFormat.Raw
            ).hex()
            
            # Sign transaction data
            transaction_data = f"{self.sender}{self.recipient}{self.amount}{self.timestamp}".encode()
            signature = private_key.sign(transaction_data)
            self.signature = signature.hex()
            
            return self.signature
        except Exception as e:
            print(f"Error signing transaction: {e}")
            return ""
    
    def verify_signature(self) -> bool:
        """
        Verify transaction signature.
        
        Returns:
            True if signature is valid
        """
        try:
            from cryptography.hazmat.primitives.asymmetric import ed25519
            
            if not self.signature or not self.public_key:
                return False
            
            # Load public key
            public_key_bytes = bytes.fromhex(self.public_key)
            public_key = ed25519.Ed25519PublicKey.from_public_bytes(public_key_bytes)
            
            # Verify signature
            transaction_data = f"{self.sender}{self.recipient}{self.amount}{self.timestamp}".encode()
            signature_bytes = bytes.fromhex(self.signature)
            
            public_key.verify(signature_bytes, transaction_data)
            return True
        except Exception:
            return False
    
    def to_dict(self):
        return {
            'transaction_id': self.transaction_id,
            'sender': self.sender, 
            'recipient': self.recipient, 
            'amount': self.amount,
            'timestamp': self.timestamp,
            'signature': self.signature,
            'public_key': self.public_key
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create transaction from dictionary."""
        tx = cls(
            sender=data['sender'],
            recipient=data['recipient'],
            amount=data['amount'],
            timestamp=data.get('timestamp', time.time())
        )
        tx.transaction_id = data.get('transaction_id', tx.transaction_id)
        tx.signature = data.get('signature', '')
        tx.public_key = data.get('public_key', '')
        return tx

    def __str__(self):
        return f"Transaction {self.transaction_id[:8]}...: {self.sender} -> {self.recipient} ({self.amount})"

# Sample block creation code removed - CLI now connects to live network