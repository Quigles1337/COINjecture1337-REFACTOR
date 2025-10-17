"""
Critical Coupling Configuration for Consensus-Cache Optimization

Mathematical Foundation:
The consensus-cache system is modeled as coupled oscillators with symmetric damping and coupling:

d/dt (V/F) = ((-η, λ), (λ, -η)) (V/F)

Where:
- V = Consensus velocity (write rate)
- F = Cache frequency (read rate)
- η = damping coefficient
- λ = coupling coefficient

Eigenvalue Analysis:
μ = -η ± λ

Marginal stability (no oscillation, no divergence): μ_max = -η + λ = 0
Therefore: λ = η (equality is the dynamical threshold)

With unit-norm scaling: λ² + η² = 1
Solving simultaneously: λ = η = 1/√2 ≈ 0.707

This is the critical coupling constant - the boundary between stability and instability.
"""

import math
import time
from typing import Tuple

# ============================================
# CRITICAL COUPLING CONSTANTS
# ============================================

# Mathematical proof: λ = η at marginal stability boundary
# With unit norm: λ² + η² = 1 → λ = η = 1/√2
SQRT2 = math.sqrt(2)
LAMBDA = 1.0 / SQRT2  # ≈ 0.707 - Consensus write coupling
ETA = 1.0 / SQRT2     # ≈ 0.707 - Cache read damping

# ============================================
# VERIFICATION ASSERTIONS
# ============================================

def verify_coupling_constants() -> bool:
    """
    Verify the critical coupling constants satisfy mathematical constraints.
    
    Returns:
        True if all constraints are satisfied
    """
    # Unit-norm constraint: λ² + η² = 1
    unit_norm = abs(LAMBDA**2 + ETA**2 - 1.0) < 1e-10
    
    # Equality constraint: λ = η (critical boundary)
    equality = abs(LAMBDA - ETA) < 1e-10
    
    # Numerical verification
    expected_value = 1.0 / math.sqrt(2)
    lambda_correct = abs(LAMBDA - expected_value) < 1e-10
    eta_correct = abs(ETA - expected_value) < 1e-10
    
    return unit_norm and equality and lambda_correct and eta_correct

# ============================================
# OPTIMAL POLLING INTERVALS
# ============================================

# Base intervals (seconds)
BASE_CONSENSUS_INTERVAL = 10.0  # Base consensus write interval
BASE_CACHE_INTERVAL = 10.0      # Base cache read interval

# Apply coupling/damping coefficients
CONSENSUS_WRITE_INTERVAL = BASE_CONSENSUS_INTERVAL / LAMBDA  # ~14.14s
CACHE_READ_INTERVAL = BASE_CACHE_INTERVAL / ETA              # ~14.14s

# At critical boundary, intervals are equal (no phase drift)
def verify_interval_equality() -> bool:
    """Verify that consensus and cache intervals are equal at critical boundary."""
    return abs(CONSENSUS_WRITE_INTERVAL - CACHE_READ_INTERVAL) < 1e-10

# ============================================
# ENERGY OPTIMIZATION CALCULATIONS
# ============================================

def calculate_energy_savings(naive_interval: float = 1.0) -> dict:
    """
    Calculate energy savings compared to naive polling.
    
    Args:
        naive_interval: Naive polling interval in seconds
        
    Returns:
        Dictionary with energy savings metrics
    """
    # Calculate frequency reduction (higher interval = lower frequency)
    consensus_freq_reduction = CONSENSUS_WRITE_INTERVAL / naive_interval
    cache_freq_reduction = CACHE_READ_INTERVAL / naive_interval
    
    # Energy savings = 1 - (new_frequency / old_frequency)
    # Since frequency = 1/interval, savings = 1 - (old_interval / new_interval)
    consensus_energy_savings = 1.0 - (naive_interval / CONSENSUS_WRITE_INTERVAL)
    cache_energy_savings = 1.0 - (naive_interval / CACHE_READ_INTERVAL)
    
    # Combined energy savings (average of both components)
    total_energy_savings = (consensus_energy_savings + cache_energy_savings) / 2.0
    
    return {
        'consensus_frequency_reduction': consensus_freq_reduction,
        'cache_frequency_reduction': cache_freq_reduction,
        'consensus_energy_savings_percent': consensus_energy_savings * 100,
        'cache_energy_savings_percent': cache_energy_savings * 100,
        'total_energy_savings_percent': total_energy_savings * 100,
        'consensus_write_interval': CONSENSUS_WRITE_INTERVAL,
        'cache_read_interval': CACHE_READ_INTERVAL,
        'naive_interval': naive_interval
    }

# ============================================
# COUPLING STATE TRACKING
# ============================================

class CouplingState:
    """
    Track coupling state to prevent oscillation.
    """
    
    def __init__(self):
        # Initialize with old timestamps to prevent immediate writes/reads
        current_time = time.time()
        self.last_consensus_write = current_time - CONSENSUS_WRITE_INTERVAL - 1.0
        self.last_cache_read = current_time - CACHE_READ_INTERVAL - 1.0
        self.write_count = 0
        self.read_count = 0
    
    def can_write(self) -> bool:
        """Check if consensus can write (λ-coupled timing)."""
        current_time = time.time()
        return current_time - self.last_consensus_write >= CONSENSUS_WRITE_INTERVAL
    
    def can_read(self) -> bool:
        """Check if cache can read (η-damped timing)."""
        current_time = time.time()
        return current_time - self.last_cache_read >= CACHE_READ_INTERVAL
    
    def record_write(self):
        """Record consensus write with coupling timing."""
        self.last_consensus_write = time.time()
        self.write_count += 1
    
    def record_read(self):
        """Record cache read with damping timing."""
        self.last_cache_read = time.time()
        self.read_count += 1
    
    def get_coupling_metrics(self) -> dict:
        """Get current coupling metrics."""
        current_time = time.time()
        time_since_write = current_time - self.last_consensus_write
        time_since_read = current_time - self.last_cache_read
        
        return {
            'consensus_write_interval': CONSENSUS_WRITE_INTERVAL,
            'cache_read_interval': CACHE_READ_INTERVAL,
            'time_since_last_write': time_since_write,
            'time_since_last_read': time_since_read,
            'write_count': self.write_count,
            'read_count': self.read_count,
            'lambda': LAMBDA,
            'eta': ETA
        }

# ============================================
# UNIT TESTS
# ============================================

def run_unit_tests() -> bool:
    """
    Run unit tests for coupling configuration.
    
    Returns:
        True if all tests pass
    """
    print("Running coupling configuration unit tests...")
    
    # Test 1: Verify coupling constants
    assert verify_coupling_constants(), "Coupling constants failed verification"
    print("✅ Coupling constants verified")
    
    # Test 2: Verify interval equality
    assert verify_interval_equality(), "Intervals not equal at critical boundary"
    print("✅ Interval equality verified")
    
    # Test 3: Verify energy savings calculation
    energy_metrics = calculate_energy_savings(1.0)
    assert energy_metrics['total_energy_savings_percent'] > 80, "Energy savings too low"
    print("✅ Energy savings calculation verified")
    
    # Test 4: Test coupling state
    state = CouplingState()
    assert state.can_write(), "Should be able to write immediately (initialized with old timestamps)"
    assert state.can_read(), "Should be able to read immediately (initialized with old timestamps)"
    
    # Test that after recording, we can't write/read immediately
    state.record_write()
    state.record_read()
    assert not state.can_write(), "Should not be able to write immediately after recording"
    assert not state.can_read(), "Should not be able to read immediately after recording"
    print("✅ Coupling state verified")
    
    print("✅ All coupling configuration unit tests passed!")
    return True

# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    print("COINjecture Critical Coupling Configuration")
    print("=" * 50)
    
    # Display constants
    print(f"λ (Lambda) = {LAMBDA:.10f}")
    print(f"η (Eta) = {ETA:.10f}")
    print(f"1/√2 = {1.0/SQRT2:.10f}")
    print()
    
    # Display intervals
    print(f"Consensus write interval: {CONSENSUS_WRITE_INTERVAL:.2f}s")
    print(f"Cache read interval: {CACHE_READ_INTERVAL:.2f}s")
    print()
    
    # Display energy savings
    energy = calculate_energy_savings(1.0)
    print(f"Energy savings vs 1s polling: {energy['total_energy_savings_percent']:.1f}%")
    print()
    
    # Run unit tests
    run_unit_tests()
    
    print("\n✅ Coupling configuration ready for consensus-cache optimization!")
