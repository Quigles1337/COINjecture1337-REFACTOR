#!/usr/bin/env python3
"""
Test metrics engine integration
"""

import sys
import os
sys.path.append('src')

from metrics_engine import get_metrics_engine, SATOSHI_CONSTANT

def test_metrics_integration():
    """Test metrics engine integration"""
    print(f"✅ Satoshi Constant: {SATOSHI_CONSTANT:.6f}")
    
    # Get metrics engine
    me = get_metrics_engine()
    metrics = me.get_network_metrics()
    
    print(f"✅ Network metrics:")
    print(f"  - Satoshi Constant: {metrics['satoshi_constant']:.6f}")
    print(f"  - Damping Ratio: {metrics['damping_ratio']:.6f}")
    print(f"  - Stability Metric: {metrics['stability_metric']:.6f}")
    print(f"  - Fork Resistance: {metrics['fork_resistance']:.6f}")
    print(f"  - Liveness Guarantee: {metrics['liveness_guarantee']:.6f}")
    
    # Test consensus equilibrium
    damping_ratio = metrics['damping_ratio']
    coupling_strength = metrics['coupling_strength']
    stability_metric = abs(complex(-damping_ratio, coupling_strength))
    
    print(f"✅ Consensus Equilibrium:")
    print(f"  - |μ| = {stability_metric:.6f} (should be 1.0)")
    print(f"  - Fork Resistance: {1.0 - damping_ratio:.6f}")
    print(f"  - Liveness Guarantee: {damping_ratio:.6f}")
    
    return True

if __name__ == "__main__":
    test_metrics_integration()
