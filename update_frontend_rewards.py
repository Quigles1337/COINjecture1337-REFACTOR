#!/usr/bin/env python3
"""
Update Frontend Rewards Display
This script updates the frontend to show correct rewards data
"""

import os
import json

def update_frontend_rewards():
    """Update the frontend to show correct rewards data"""
    
    # Create a simple rewards API endpoint
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
                        "error": "Blockchain state not found"
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
                            "total_work_score": 0.0
                        }
                    }), 200
                
                # Calculate rewards
                total_rewards = 0.0
                total_work_score = 0.0
                
                for block in miner_blocks:
                    work_score = block.get('cumulative_work_score', 0.0)
                    base_reward = 50.0
                    work_bonus = work_score * 0.1
                    block_reward = base_reward + work_bonus
                    
                    total_rewards += block_reward
                    total_work_score += work_score
                
                return jsonify({
                    "status": "success",
                    "data": {
                        "miner_address": address,
                        "total_rewards": round(total_rewards, 2),
                        "blocks_mined": len(miner_blocks),
                        "total_work_score": round(total_work_score, 2)
                    }
                }), 200
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Failed to get mining rewards",
                    "message": str(e)
                }), 500
'''
    
    # Add to faucet_server.py
    faucet_server_path = "/home/coinjecture/COINjecture/src/api/faucet_server.py"
    
    with open(faucet_server_path, 'r') as f:
        content = f.read()
    
    # Check if already exists
    if '/v1/rewards/' in content:
        print("✅ Rewards endpoint already exists")
        return
    
    # Find insertion point
    error_handler_pos = content.find('@self.app.errorhandler(404)')
    if error_handler_pos == -1:
        print("❌ Could not find error handler position")
        return
    
    # Insert the endpoint
    new_content = content[:error_handler_pos] + rewards_endpoint + content[error_handler_pos:]
    
    with open(faucet_server_path, 'w') as f:
        f.write(new_content)
    
    print("✅ Rewards endpoint added to API server")

if __name__ == "__main__":
    update_frontend_rewards()
