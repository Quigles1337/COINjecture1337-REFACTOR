"""
Proof bundle utility for IPFS storage.

Serializes complete proof data from COINjecture blocks for IPFS storage.
Includes problem instances, solutions, computational complexity metrics,
and energy measurements.
"""

import json
from typing import Dict, Any, Optional


def create_proof_bundle(block) -> Dict[str, Any]:
    """
    Create complete proof bundle with all data for IPFS storage.
    
    Args:
        block: COINjecture Block object with problem, solution, and complexity data
        
    Returns:
        Dictionary containing complete proof bundle data
    """
    try:
        # Extract energy metrics safely
        energy_metrics = {}
        if hasattr(block, 'complexity') and hasattr(block.complexity, 'energy_metrics'):
            energy_metrics = {
                "solve_energy_joules": getattr(block.complexity.energy_metrics, 'solve_energy_joules', 0.0),
                "verify_energy_joules": getattr(block.complexity.energy_metrics, 'verify_energy_joules', 0.0),
                "solve_power_watts": getattr(block.complexity.energy_metrics, 'solve_power_watts', 0.0),
                "verify_power_watts": getattr(block.complexity.energy_metrics, 'verify_power_watts', 0.0),
                "solve_time_seconds": getattr(block.complexity.energy_metrics, 'solve_time_seconds', 0.0),
                "verify_time_seconds": getattr(block.complexity.energy_metrics, 'verify_time_seconds', 0.0),
                "cpu_utilization": getattr(block.complexity.energy_metrics, 'cpu_utilization', 0.0),
                "memory_utilization": getattr(block.complexity.energy_metrics, 'memory_utilization', 0.0),
                "gpu_utilization": getattr(block.complexity.energy_metrics, 'gpu_utilization', 0.0),
            }
        
        # Extract complexity data safely
        complexity_data = {}
        if hasattr(block, 'complexity'):
            complexity_data = {
                "problem_class": getattr(block.complexity, 'problem_class', 'unknown'),
                "problem_size": getattr(block.complexity, 'problem_size', 0),
                "solution_size": getattr(block.complexity, 'solution_size', 0),
                "measured_solve_time": getattr(block.complexity, 'measured_solve_time', 0.0),
                "measured_verify_time": getattr(block.complexity, 'measured_verify_time', 0.0),
                "time_solve_O": getattr(block.complexity, 'time_solve_O', 'unknown'),
                "time_verify_O": getattr(block.complexity, 'time_verify_O', 'unknown'),
                "space_solve_O": getattr(block.complexity, 'space_solve_O', 'unknown'),
                "space_verify_O": getattr(block.complexity, 'space_verify_O', 'unknown'),
                "asymmetry_time": getattr(block.complexity, 'asymmetry_time', 0.0),
                "asymmetry_space": getattr(block.complexity, 'asymmetry_space', 0.0),
            }
        
        # Create complete proof bundle
        proof_bundle = {
            "block_index": getattr(block, 'index', 0),
            "block_hash": getattr(block, 'block_hash', ''),
            "timestamp": getattr(block, 'timestamp', 0.0),
            "mining_capacity": str(getattr(block, 'mining_capacity', 'unknown')),
            "cumulative_work_score": getattr(block, 'cumulative_work_score', 0.0),
            
            # Core proof data
            "problem": getattr(block, 'problem', {}),
            "solution": getattr(block, 'solution', []),
            
            # Computational complexity
            "complexity": complexity_data,
            
            # Energy measurements
            "energy_metrics": energy_metrics,
            
            # Metadata
            "bundle_version": "1.0",
            "created_at": json.dumps({"timestamp": "2025-10-15T00:00:00Z"})
        }
        
        return proof_bundle
        
    except Exception as e:
        print(f"Error creating proof bundle: {e}")
        # Return minimal bundle on error
        return {
            "block_index": getattr(block, 'index', 0),
            "block_hash": getattr(block, 'block_hash', ''),
            "error": str(e),
            "bundle_version": "1.0"
        }


def serialize_proof_bundle(proof_bundle: Dict[str, Any]) -> bytes:
    """
    Serialize proof bundle to bytes for IPFS storage.
    
    Args:
        proof_bundle: Proof bundle dictionary
        
    Returns:
        JSON-encoded bytes ready for IPFS
    """
    return json.dumps(proof_bundle, indent=2).encode('utf-8')


def deserialize_proof_bundle(bundle_bytes: bytes) -> Dict[str, Any]:
    """
    Deserialize proof bundle from IPFS bytes.
    
    Args:
        bundle_bytes: JSON-encoded bytes from IPFS
        
    Returns:
        Proof bundle dictionary
    """
    return json.loads(bundle_bytes.decode('utf-8'))


if __name__ == "__main__":
    # Test the proof bundler
    print("Testing proof bundler...")
    
    # Create a mock block for testing
    class MockBlock:
        def __init__(self):
            self.index = 0
            self.block_hash = "test_hash_123"
            self.timestamp = 1609459200.0
            self.mining_capacity = "mobile"
            self.cumulative_work_score = 1807.18
            self.problem = {
                "type": "subset_sum",
                "numbers": [27, 4, 36, 80, 37, 32, 28, 73, 27, 78, 4, 32, 72, 51],
                "target": 215,
                "size": 14
            }
            self.solution = [0, 2, 5, 7, 11]
            
            # Mock complexity
            class MockComplexity:
                def __init__(self):
                    self.problem_class = "NP-Complete"
                    self.problem_size = 14
                    self.solution_size = 5
                    self.measured_solve_time = 0.000234
                    self.measured_verify_time = 0.000012
                    self.time_solve_O = "O(2^n)"
                    self.time_verify_O = "O(n)"
                    self.space_solve_O = "O(n)"
                    self.space_verify_O = "O(1)"
                    self.asymmetry_time = 19.5
                    self.asymmetry_space = 14.0
                    
                    # Mock energy metrics
                    class MockEnergyMetrics:
                        def __init__(self):
                            self.solve_energy_joules = 2.34
                            self.verify_energy_joules = 0.12
                            self.solve_power_watts = 10.0
                            self.verify_power_watts = 10.0
                            self.solve_time_seconds = 0.000234
                            self.verify_time_seconds = 0.000012
                            self.cpu_utilization = 85.5
                            self.memory_utilization = 45.2
                            self.gpu_utilization = 0.0
                    
                    self.energy_metrics = MockEnergyMetrics()
            
            self.complexity = MockComplexity()
    
    # Test bundle creation
    mock_block = MockBlock()
    bundle = create_proof_bundle(mock_block)
    
    print("✅ Proof bundle created successfully")
    print(f"Bundle size: {len(json.dumps(bundle))} characters")
    print(f"Problem type: {bundle['problem'].get('type', 'unknown')}")
    print(f"Solution size: {len(bundle['solution'])}")
    print(f"Energy used: {bundle['energy_metrics']['solve_energy_joules']} J")
    
    # Test serialization
    bundle_bytes = serialize_proof_bundle(bundle)
    print(f"✅ Serialized to {len(bundle_bytes)} bytes")
    
    # Test deserialization
    restored_bundle = deserialize_proof_bundle(bundle_bytes)
    print("✅ Deserialized successfully")
    print(f"Restored problem type: {restored_bundle['problem'].get('type', 'unknown')}")
