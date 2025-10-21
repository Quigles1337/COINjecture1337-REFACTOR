#!/bin/bash

# Fix Rewards Data Source
# This script updates the rewards endpoint to read from blockchain state instead of ingest database

set -e

echo "🔧 Fixing Rewards Data Source"
echo "============================="

# Configuration
DROPLET_IP="167.172.213.70"
SSH_KEY="$HOME/.ssh/coinjecture_droplet_key"
USER="root"

echo "🔑 Using SSH key: $SSH_KEY"
echo "🌐 Connecting to droplet: $DROPLET_IP"
echo ""

# Create a comprehensive fix script for the droplet
cat > /tmp/fix_rewards_data_source_droplet.sh << 'EOF'
#!/bin/bash

echo "🔧 Fixing Rewards Data Source on Droplet"
echo "========================================="

# 1. Check current mining activity in blockchain state
echo "📊 Checking mining activity in blockchain state..."
BLOCKS_MINED=$(jq '.blocks[] | select(.miner_address == "BEANSa93eefd297ae59e963d0977319690ffbc55e2b33") | .index' /opt/coinjecture-consensus/data/blockchain_state.json | wc -l)
echo "   Blocks mined by user: $BLOCKS_MINED"

if [ "$BLOCKS_MINED" -gt 0 ]; then
    echo "   ✅ Found mining activity in blockchain state"
    echo "   📋 Mining details:"
    jq '.blocks[] | select(.miner_address == "BEANSa93eefd297ae59e963d0977319690ffbc55e2b33") | {index: .index, work_score: .cumulative_work_score, timestamp: .timestamp}' /opt/coinjecture-consensus/data/blockchain_state.json | head -5
else
    echo "   ❌ No mining activity found"
fi

# 2. Update the rewards endpoint to read from blockchain state
echo "📝 Updating rewards endpoint to read from blockchain state..."

# Create the updated rewards endpoint code
cat > /tmp/rewards_endpoint_fixed.py << 'REWARDS_FIXED'
        @self.app.route('/v1/rewards/<address>', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_mining_rewards(address: str):
            """Get mining rewards earned by a specific address."""
            try:
                # Read from blockchain state instead of ingest database
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
REWARDS_FIXED

# Replace the rewards endpoint in faucet_server.py
echo "📝 Updating faucet_server.py with fixed rewards endpoint..."

# Remove the old rewards endpoint
sed -i '/@self.app.route.*rewards.*address/,/^        @self.app.route.*leaderboard/d' /home/coinjecture/COINjecture/src/api/faucet_server.py

# Add the new rewards endpoint
sed -i '/@self.app.errorhandler(404)/i\
        @self.app.route('\''/v1/rewards/<address>'\'', methods=['\''GET'\''])\
        @self.limiter.limit("100 per minute")\
        def get_mining_rewards(address: str):\
            """Get mining rewards earned by a specific address."""\
            try:\
                # Read from blockchain state instead of ingest database\
                blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"\
                \
                if not os.path.exists(blockchain_state_path):\
                    return jsonify({\
                        "status": "error",\
                        "error": "Blockchain state not found",\
                        "message": "Blockchain state file not available"\
                    }), 500\
                \
                with open(blockchain_state_path, '\''r'\'') as f:\
                    blockchain_state = json.load(f)\
                \
                # Get blocks mined by this address\
                all_blocks = blockchain_state.get('\''blocks'\'', [])\
                miner_blocks = [block for block in all_blocks if block.get('\''miner_address'\'') == address]\
                \
                if not miner_blocks:\
                    return jsonify({\
                        "status": "success",\
                        "data": {\
                            "miner_address": address,\
                            "total_rewards": 0.0,\
                            "blocks_mined": 0,\
                            "rewards_breakdown": [],\
                            "total_work_score": 0.0\
                        }\
                    }), 200\
                \
                # Calculate rewards (50 COIN per block + work score bonus)\
                rewards_breakdown = []\
                total_rewards = 0.0\
                total_work_score = 0.0\
                \
                for block in miner_blocks:\
                    work_score = block.get('\''cumulative_work_score'\'', 0.0)\
                    base_reward = 50.0  # Base mining reward\
                    work_bonus = work_score * 0.1  # 0.1 COIN per work score point\
                    block_reward = base_reward + work_bonus\
                    \
                    rewards_breakdown.append({\
                        "block_index": block.get('\''index'\''),\
                        "block_hash": block.get('\''block_hash'\''),\
                        "work_score": work_score,\
                        "base_reward": base_reward,\
                        "work_bonus": work_bonus,\
                        "total_reward": block_reward,\
                        "timestamp": block.get('\''timestamp'\''),\
                        "cid": block.get('\''offchain_cid'\'', '\'''\'')\
                    })\
                    \
                    total_rewards += block_reward\
                    total_work_score += work_score\
                \
                return jsonify({\
                    "status": "success",\
                    "data": {\
                        "miner_address": address,\
                        "total_rewards": round(total_rewards, 2),\
                        "blocks_mined": len(miner_blocks),\
                        "rewards_breakdown": rewards_breakdown,\
                        "total_work_score": round(total_work_score, 2),\
                        "average_work_score": round(total_work_score / len(miner_blocks), 2) if miner_blocks else 0.0\
                    }\
                }), 200\
                \
            except Exception as e:\
                return jsonify({\
                    "status": "error",\
                    "error": "Failed to get mining rewards",\
                    "message": str(e)\
                }), 500' /home/coinjecture/COINjecture/src/api/faucet_server.py

echo "✅ Rewards endpoint updated to read from blockchain state"

# 3. Restart the API service
echo "🔄 Restarting API service..."
systemctl restart coinjecture-api
echo "✅ API service restarted"

# 4. Test the fixed rewards endpoint
echo "🧪 Testing fixed rewards endpoint..."
sleep 3

echo "Testing rewards for user address:"
curl -s "https://api.coinjecture.com/v1/rewards/BEANSa93eefd297ae59e963d0977319690ffbc55e2b33" | jq '.'

echo ""
echo "✅ Rewards data source fix completed!"
echo "===================================="
echo ""
echo "🎯 What was fixed:"
echo "   ✅ Rewards endpoint now reads from blockchain state"
echo "   ✅ Found $BLOCKS_MINED blocks mined by user"
echo "   ✅ API service restarted"
echo ""
echo "🧪 Test the rewards command now:"
echo "   https://coinjecture.com"
echo ""
echo "Users should now see their actual mining rewards!"

# Clean up
rm -f /tmp/rewards_endpoint_fixed.py

EOF

# Make the script executable
chmod +x /tmp/fix_rewards_data_source_droplet.sh

echo "📤 Copying rewards data source fix script to droplet..."
scp -i "$SSH_KEY" /tmp/fix_rewards_data_source_droplet.sh "$USER@$DROPLET_IP:/tmp/"

echo "🚀 Running rewards data source fix on droplet..."
ssh -i "$SSH_KEY" "$USER@$DROPLET_IP" "chmod +x /tmp/fix_rewards_data_source_droplet.sh && /tmp/fix_rewards_data_source_droplet.sh"

# Clean up
rm -f /tmp/fix_rewards_data_source_droplet.sh

echo ""
echo "🎉 Rewards data source fix completed!"
echo "===================================="
echo ""
echo "🧪 Test the rewards command now:"
echo "   https://coinjecture.com"
echo ""
echo "Users should now see their actual mining rewards!"
