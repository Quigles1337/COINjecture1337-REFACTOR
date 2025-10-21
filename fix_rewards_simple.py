#!/usr/bin/env python3
"""
Simple fix for rewards display without breaking the file
"""

import os

def fix_rewards_display():
    """Fix the rewards display in app.js"""
    
    app_js_path = "/home/coinjecture/COINjecture/web/app.js"
    
    # Read the file
    with open(app_js_path, 'r') as f:
        content = f.read()
    
    # Fix 1: Replace the problematic slice call
    old_slice = "const recentBlocks = rewards.rewards_breakdown.slice(0, 5);"
    new_slice = "// Show mining summary instead of individual blocks"
    
    if old_slice in content:
        content = content.replace(old_slice, new_slice)
        print("✅ Fixed rewards_breakdown.slice issue")
    
    # Fix 2: Add the mining summary display
    summary_code = '''          this.addOutput(`   🎯 You have successfully mined ${rewards.blocks_mined} blocks`);
          this.addOutput(`   💰 Total earnings: ${rewards.total_rewards} BEANS`);
          this.addOutput(`   ⚡ Average work per block: ${rewards.blocks_mined > 0 ? (rewards.total_work_score / rewards.blocks_mined).toFixed(2) : 0}`);
          if (rewards.blocks_mined > 0) {
            this.addOutput(`   🏆 Great mining performance!`);
          }'''
    
    # Find the position after the comment and add the summary
    if "// Show mining summary instead of individual blocks" in content:
        insert_pos = content.find("// Show mining summary instead of individual blocks") + len("// Show mining summary instead of individual blocks")
        content = content[:insert_pos] + "\n" + summary_code + content[insert_pos:]
        print("✅ Added mining summary display")
    
    # Write the fixed file
    with open(app_js_path, 'w') as f:
        f.write(content)
    
    print("✅ Rewards display fixed successfully")

if __name__ == "__main__":
    fix_rewards_display()
