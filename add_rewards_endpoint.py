#!/usr/bin/env python3
"""
Add Rewards Endpoint to Main API
This script adds the rewards endpoint to the main faucet server
"""

import os
import json

def add_rewards_endpoint():
    """Add the rewards endpoint to faucet_server.py"""
    
    faucet_server_path = "/home/coinjecture/COINjecture/src/api/faucet_server.py"
    
    # Read the current file
    with open(faucet_server_path, 'r') as f:
        content = f.read()
    
    # Check if rewards endpoint already exists
    if '/v1/rewards/' in content:
        print("✅ Rewards endpoint already exists")
        return
    
    # Find the position to insert the rewards endpoint (before error handlers)
    error_handler_pos = content.find('@self.app.errorhandler(404)')
    if error_handler_pos == -1:
        print("❌ Could not find error handler position")
        return
    
    # Create the rewards endpoint code
    rewards_endpoint = '''
        @self.app.route('/v1/rewards/<address>', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_mining_rewards(address: str):
            """Get mining rewards earned by a specific address."""
            try:
                # Read from blockchain state
                blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
                
                if not os.path.exists(blockchain_state_path):
                    return jsonify({
                        "status": "error",
                        "error": "Blockchain state not found",
                        "message": "Blockchain state file not available"
                    }), 500
                
                with open(blockchain_state_path, 'r') as f:
                    blockchain_state = json.load(f)
                
                # Get blocks mined by this address
                all_blocks = blockchain_state.get('blocks', [])
                miner_blocks = [block for block in all_blocks if block.get('miner_address') == address]
                
                if not miner_blocks:
                    return jsonify({
                        "status": "success",
                        "data": {
                            "miner_address": address,
                            "total_rewards": 0.0,
                            "blocks_mined": 0,
                            "rewards_breakdown": [],
                            "total_work_score": 0.0
                        }
                    }), 200
                
                # Calculate rewards (50 COIN per block + work score bonus)
                rewards_breakdown = []
                total_rewards = 0.0
                total_work_score = 0.0
                
                for block in miner_blocks:
                    work_score = block.get('cumulative_work_score', 0.0)
                    base_reward = 50.0  # Base mining reward
                    work_bonus = work_score * 0.1  # 0.1 COIN per work score point
                    block_reward = base_reward + work_bonus
                    
                    rewards_breakdown.append({
                        "block_index": block.get('index'),
                        "block_hash": block.get('block_hash'),
                        "work_score": work_score,
                        "base_reward": base_reward,
                        "work_bonus": work_bonus,
                        "total_reward": block_reward,
                        "timestamp": block.get('timestamp'),
                        "cid": block.get('offchain_cid', '')
                    })
                    
                    total_rewards += block_reward
                    total_work_score += work_score
                
                return jsonify({
                    "status": "success",
                    "data": {
                        "miner_address": address,
                        "total_rewards": round(total_rewards, 2),
                        "blocks_mined": len(miner_blocks),
                        "rewards_breakdown": rewards_breakdown,
                        "total_work_score": round(total_work_score, 2),
                        "average_work_score": round(total_work_score / len(miner_blocks), 2) if miner_blocks else 0.0
                    }
                }), 200
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Failed to get mining rewards",
                    "message": str(e)
                }), 500
'''
    
    # Insert the rewards endpoint before the error handler
    new_content = content[:error_handler_pos] + rewards_endpoint + content[error_handler_pos:]
    
    # Write the updated content
    with open(faucet_server_path, 'w') as f:
        f.write(new_content)
    
    print("✅ Rewards endpoint added to faucet_server.py")

if __name__ == "__main__":
    add_rewards_endpoint()
