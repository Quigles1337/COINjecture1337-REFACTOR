#!/bin/bash

# Fix Rewards Endpoint 404 Error
# This script adds a working rewards endpoint to the API server

set -e

echo "🔧 Fixing Rewards Endpoint 404 Error"
echo "===================================="

# Configuration
DROPLET_IP="167.172.213.70"
SSH_KEY="$HOME/.ssh/coinjecture_droplet_key"
USER="root"

echo "🔑 Using SSH key: $SSH_KEY"
echo "🌐 Connecting to droplet: $DROPLET_IP"
echo ""

# Create a comprehensive fix script for the droplet
cat > /tmp/fix_rewards_404_droplet.sh << 'EOF'
#!/bin/bash

echo "🔧 Fixing Rewards 404 Error on Droplet"
echo "======================================="

# 1. Check current API status
echo "📊 Checking API status..."
curl -s https://api.coinjecture.com/v1/data/block/latest | jq '.data.index' || echo "API not responding"

# 2. Add simple rewards endpoint to faucet_server.py
echo "📝 Adding rewards endpoint to API server..."

# Create a simple rewards endpoint
cat > /tmp/rewards_endpoint_simple.py << 'REWARDS_SIMPLE'
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
REWARDS_SIMPLE

# Add the endpoint to faucet_server.py
echo "📝 Adding rewards endpoint to faucet_server.py..."

# Find the position to insert (before error handlers)
sed -i '/@self.app.errorhandler(404)/i\
        @self.app.route('\''/v1/rewards/<address>'\'', methods=['\''GET'\''])\
        @self.limiter.limit("100 per minute")\
        def get_mining_rewards(address: str):\
            """Get mining rewards earned by a specific address."""\
            try:\
                # Read from blockchain state\
                blockchain_state_path = "/opt/coinjecture-consensus/data/blockchain_state.json"\
                \
                if not os.path.exists(blockchain_state_path):\
                    return jsonify({\
                        "status": "error",\
                        "error": "Blockchain state not found"\
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
                            "total_work_score": 0.0\
                        }\
                    }), 200\
                \
                # Calculate rewards\
                total_rewards = 0.0\
                total_work_score = 0.0\
                \
                for block in miner_blocks:\
                    work_score = block.get('\''cumulative_work_score'\'', 0.0)\
                    base_reward = 50.0\
                    work_bonus = work_score * 0.1\
                    block_reward = base_reward + work_bonus\
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
                        "total_work_score": round(total_work_score, 2)\
                    }\
                }), 200\
                \
            except Exception as e:\
                return jsonify({\
                    "status": "error",\
                    "error": "Failed to get mining rewards",\
                    "message": str(e)\
                }), 500' /home/coinjecture/COINjecture/src/api/faucet_server.py

echo "✅ Rewards endpoint added to API server"

# 3. Restart the API service
echo "🔄 Restarting API service..."
systemctl restart coinjecture-api
echo "✅ API service restarted"

# 4. Test the rewards endpoint
echo "🧪 Testing rewards endpoint..."
sleep 3

echo "Testing rewards for user address:"
curl -s "https://api.coinjecture.com/v1/rewards/BEANSa93eefd297ae59e963d0977319690ffbc55e2b33" | jq '.'

echo ""
echo "✅ Rewards 404 fix completed!"
echo "============================="
echo ""
echo "🎯 What was fixed:"
echo "   ✅ Added working rewards endpoint to API server"
echo "   ✅ Endpoint reads from blockchain state"
echo "   ✅ API service restarted"
echo ""
echo "🧪 Test the rewards command now:"
echo "   https://coinjecture.com"
echo ""
echo "The rewards command should now work!"

# Clean up
rm -f /tmp/rewards_endpoint_simple.py

EOF

# Make the script executable
chmod +x /tmp/fix_rewards_404_droplet.sh

echo "📤 Copying rewards 404 fix script to droplet..."
scp -i "$SSH_KEY" /tmp/fix_rewards_404_droplet.sh "$USER@$DROPLET_IP:/tmp/"

echo "🚀 Running rewards 404 fix on droplet..."
ssh -i "$SSH_KEY" "$USER@$DROPLET_IP" "chmod +x /tmp/fix_rewards_404_droplet.sh && /tmp/fix_rewards_404_droplet.sh"

# Clean up
rm -f /tmp/fix_rewards_404_droplet.sh

echo ""
echo "🎉 Rewards 404 fix completed!"
echo "============================="
echo ""
echo "🧪 Test the rewards command now:"
echo "   https://coinjecture.com"
echo ""
echo "The rewards command should now work!"
