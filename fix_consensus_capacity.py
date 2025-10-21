#!/usr/bin/env python3
"""
Fix consensus service capacity normalization
"""

import re

def fix_consensus_service():
    """Fix capacity normalization in consensus service"""
    
    # Read the current file
    with open('/opt/coinjecture-consensus/consensus_service_memory_optimized.py', 'r') as f:
        content = f.read()
    
    # Fix the _dict_to_block method to properly handle capacity
    old_dict_to_block = '''            mining_capacity=block_dict.get("mining_capacity", "mobile"),'''
    
    new_dict_to_block = '''            mining_capacity=self._normalize_capacity(block_dict.get("mining_capacity", "mobile")),'''
    
    if old_dict_to_block in content:
        content = content.replace(old_dict_to_block, new_dict_to_block)
        print("✅ Fixed _dict_to_block capacity normalization")
    else:
        print("❌ Could not find _dict_to_block capacity line")
    
    # Add the _normalize_capacity method
    normalize_method = '''
    def _normalize_capacity(self, capacity):
        """Normalize capacity string to proper tier"""
        if not capacity:
            return "mobile"
        
        capacity_str = str(capacity).upper()
        
        if "DESKTOP" in capacity_str or "TIER_2" in capacity_str:
            return "desktop"
        elif "SERVER" in capacity_str or "TIER_3" in capacity_str:
            return "server"
        elif "WORKSTATION" in capacity_str or "TIER_4" in capacity_str:
            return "workstation"
        elif "CLUSTER" in capacity_str or "TIER_5" in capacity_str:
            return "cluster"
        elif "MOBILE" in capacity_str or "TIER_1" in capacity_str:
            return "mobile"
        else:
            # Default to mobile for unknown capacities
            return "mobile"
'''
    
    # Add the method before the last class method
    if "_normalize_capacity" not in content:
        # Find the last method in the class and add before it
        lines = content.split('\n')
        insert_index = len(lines)
        
        # Find the last method (look for def that's not indented)
        for i in range(len(lines) - 1, -1, -1):
            if lines[i].strip().startswith('def ') and not lines[i].startswith('    '):
                insert_index = i
                break
        
        lines.insert(insert_index, normalize_method)
        content = '\n'.join(lines)
        print("✅ Added _normalize_capacity method")
    else:
        print("✅ _normalize_capacity method already exists")
    
    # Write the fixed file
    with open('/opt/coinjecture-consensus/consensus_service_memory_optimized.py', 'w') as f:
        f.write(content)
    
    print("✅ Consensus service capacity normalization fixed")

if __name__ == "__main__":
    fix_consensus_service()
