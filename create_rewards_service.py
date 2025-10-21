#!/usr/bin/env python3
"""
Simple Rewards Service
Reads mining rewards from blockchain state and serves them via API
"""

import json
import os
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

def get_mining_rewards(address):
    """Get mining rewards for a specific address from blockchain state."""
    try:
        blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"
        
        if not os.path.exists(blockchain_state_path):
            return {
                "status": "error",
                "error": "Blockchain state not found",
                "message": "Blockchain state file not available"
            }
        
        with open(blockchain_state_path, 'r') as f:
            blockchain_state = json.load(f)
        
        # Get blocks mined by this address
        all_blocks = blockchain_state.get('blocks', [])
        miner_blocks = [block for block in all_blocks if block.get('miner_address') == address]
        
        if not miner_blocks:
            return {
                "status": "success",
                "data": {
                    "miner_address": address,
                    "total_rewards": 0.0,
                    "blocks_mined": 0,
                    "rewards_breakdown": [],
                    "total_work_score": 0.0
                }
            }
        
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
        
        return {
            "status": "success",
            "data": {
                "miner_address": address,
                "total_rewards": round(total_rewards, 2),
                "blocks_mined": len(miner_blocks),
                "rewards_breakdown": rewards_breakdown,
                "total_work_score": round(total_work_score, 2),
                "average_work_score": round(total_work_score / len(miner_blocks), 2) if miner_blocks else 0.0
            }
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": "Failed to get mining rewards",
            "message": str(e)
        }

@app.route('/v1/rewards/<address>', methods=['GET'])
def get_rewards(address):
    """Get mining rewards for an address."""
    result = get_mining_rewards(address)
    return jsonify(result)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "service": "rewards"})

if __name__ == '__main__':
    print("🚀 Starting Rewards Service...")
    print("📊 Reading from blockchain state: /opt/coinjecture-consensus/data/blockchain_state.json")
    app.run(host='0.0.0.0', port=5001, debug=False)
