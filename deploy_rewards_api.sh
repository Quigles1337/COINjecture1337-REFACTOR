#!/bin/bash

# Deploy Rewards API Endpoint to Droplet
# This script deploys the rewards endpoint so users can access their mining rewards

set -e

echo "🔧 Deploying Rewards API Endpoint to Droplet"
echo "============================================="

# Configuration
DROPLET_IP="167.172.213.70"
SSH_KEY="$HOME/.ssh/coinjecture_droplet_key"
USER="root"

echo "🔑 Using SSH key: $SSH_KEY"
echo "🌐 Connecting to droplet: $DROPLET_IP"
echo ""

# Create a comprehensive rewards API deployment script for the droplet
cat > /tmp/deploy_rewards_droplet.sh << 'EOF'
#!/bin/bash

echo "🔧 Deploying Rewards API Endpoint on Droplet"
echo "============================================="

# 1. Backup current faucet_server.py
echo "📝 Backing up current API server..."
cp /home/coinjecture/COINjecture/src/api/faucet_server.py /home/coinjecture/COINjecture/src/api/faucet_server.py.backup
echo "✅ Backup created"

# 2. Update faucet_server.py with rewards endpoint
echo "📝 Adding rewards endpoint to API server..."

# Create the rewards endpoint code
cat > /tmp/rewards_endpoint.py << 'REWARDS_ENDPOINT'
        @self.app.route('/v1/rewards/<address>', methods=['GET'])
        @self.limiter.limit("100 per minute")
        def get_mining_rewards(address: str):
            """Get mining rewards earned by a specific address."""
            try:
                # Get block events for this miner
                block_events = self.ingest_store.latest_blocks(limit=1000)
                miner_events = [event for event in block_events if event.get('miner_address') == address]
                
                if not miner_events:
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
                
                for event in miner_events:
                    work_score = event.get('work_score', 0.0)
                    base_reward = 50.0  # Base mining reward
                    work_bonus = work_score * 0.1  # 0.1 COIN per work score point
                    block_reward = base_reward + work_bonus
                    
                    rewards_breakdown.append({
                        "block_index": event.get('block_index'),
                        "block_hash": event.get('block_hash'),
                        "work_score": work_score,
                        "base_reward": base_reward,
                        "work_bonus": work_bonus,
                        "total_reward": block_reward,
                        "timestamp": event.get('ts'),
                        "cid": event.get('cid')
                    })
                    
                    total_rewards += block_reward
                    total_work_score += work_score
                
                return jsonify({
                    "status": "success",
                    "data": {
                        "miner_address": address,
                        "total_rewards": round(total_rewards, 2),
                        "blocks_mined": len(miner_events),
                        "rewards_breakdown": rewards_breakdown,
                        "total_work_score": round(total_work_score, 2),
                        "average_work_score": round(total_work_score / len(miner_events), 2) if miner_events else 0.0
                    }
                }), 200
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Failed to get mining rewards",
                    "message": str(e)
                }), 500
        
        @self.app.route('/v1/rewards/leaderboard', methods=['GET'])
        @self.limiter.limit("50 per minute")
        def get_mining_leaderboard():
            """Get mining leaderboard showing top miners by rewards."""
            try:
                # Get all block events
                block_events = self.ingest_store.latest_blocks(limit=10000)
                
                # Group by miner address
                miner_stats = {}
                for event in block_events:
                    miner_address = event.get('miner_address')
                    if not miner_address:
                        continue
                    
                    if miner_address not in miner_stats:
                        miner_stats[miner_address] = {
                            'address': miner_address,
                            'blocks_mined': 0,
                            'total_work_score': 0.0,
                            'total_rewards': 0.0
                        }
                    
                    work_score = event.get('work_score', 0.0)
                    base_reward = 50.0
                    work_bonus = work_score * 0.1
                    block_reward = base_reward + work_bonus
                    
                    miner_stats[miner_address]['blocks_mined'] += 1
                    miner_stats[miner_address]['total_work_score'] += work_score
                    miner_stats[miner_address]['total_rewards'] += block_reward
                
                # Sort by total rewards
                leaderboard = sorted(
                    miner_stats.values(),
                    key=lambda x: x['total_rewards'],
                    reverse=True
                )
                
                # Round values for display
                for miner in leaderboard:
                    miner['total_rewards'] = round(miner['total_rewards'], 2)
                    miner['total_work_score'] = round(miner['total_work_score'], 2)
                    miner['average_work_score'] = round(
                        miner['total_work_score'] / miner['blocks_mined'], 2
                    ) if miner['blocks_mined'] > 0 else 0.0
                
                return jsonify({
                    "status": "success",
                    "data": {
                        "leaderboard": leaderboard[:50],  # Top 50 miners
                        "total_miners": len(leaderboard),
                        "total_blocks": sum(m['blocks_mined'] for m in leaderboard),
                        "total_rewards_distributed": round(sum(m['total_rewards'] for m in leaderboard), 2)
                    }
                }), 200
                
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": "Failed to get mining leaderboard",
                    "message": str(e)
                }), 500
REWARDS_ENDPOINT

# Add the rewards endpoint to the faucet_server.py
echo "📝 Adding rewards endpoint to faucet_server.py..."
# Find the line with the last route and add the rewards endpoint before it
sed -i '/@self.app.errorhandler(404)/i\
        @self.app.route('\''/v1/rewards/<address>'\'', methods=['\''GET'\''])\
        @self.limiter.limit("100 per minute")\
        def get_mining_rewards(address: str):\
            """Get mining rewards earned by a specific address."""\
            try:\
                # Get block events for this miner\
                block_events = self.ingest_store.latest_blocks(limit=1000)\
                miner_events = [event for event in block_events if event.get('\''miner_address'\'') == address]\
                \
                if not miner_events:\
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
                for event in miner_events:\
                    work_score = event.get('\''work_score'\'', 0.0)\
                    base_reward = 50.0  # Base mining reward\
                    work_bonus = work_score * 0.1  # 0.1 COIN per work score point\
                    block_reward = base_reward + work_bonus\
                    \
                    rewards_breakdown.append({\
                        "block_index": event.get('\''block_index'\''),\
                        "block_hash": event.get('\''block_hash'\''),\
                        "work_score": work_score,\
                        "base_reward": base_reward,\
                        "work_bonus": work_bonus,\
                        "total_reward": block_reward,\
                        "timestamp": event.get('\''ts'\''),\
                        "cid": event.get('\''cid'\'')\
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
                        "blocks_mined": len(miner_events),\
                        "rewards_breakdown": rewards_breakdown,\
                        "total_work_score": round(total_work_score, 2),\
                        "average_work_score": round(total_work_score / len(miner_events), 2) if miner_events else 0.0\
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

echo "Testing rewards endpoint for test address:"
curl -s "https://api.coinjecture.com/v1/rewards/BEANSa93eefd297ae59e963d0977319690ffbc55e2b33" | jq '.'

echo ""
echo "✅ Rewards API deployment completed!"
echo "=================================="
echo ""
echo "🎯 What was deployed:"
echo "   ✅ Rewards endpoint: /v1/rewards/<address>"
echo "   ✅ Leaderboard endpoint: /v1/rewards/leaderboard"
echo "   ✅ API service restarted"
echo ""
echo "🧪 Test the rewards command now:"
echo "   https://coinjecture.com"
echo ""
echo "Users can now access their mining rewards!"

# Clean up
rm -f /tmp/rewards_endpoint.py

EOF

# Make the script executable
chmod +x /tmp/deploy_rewards_droplet.sh

echo "📤 Copying rewards API deployment script to droplet..."
scp -i "$SSH_KEY" /tmp/deploy_rewards_droplet.sh "$USER@$DROPLET_IP:/tmp/"

echo "🚀 Running rewards API deployment on droplet..."
ssh -i "$SSH_KEY" "$USER@$DROPLET_IP" "chmod +x /tmp/deploy_rewards_droplet.sh && /tmp/deploy_rewards_droplet.sh"

# Clean up
rm -f /tmp/deploy_rewards_droplet.sh

echo ""
echo "🎉 Rewards API deployment completed!"
echo "==================================="
echo ""
echo "🧪 Test the rewards command now:"
echo "   https://coinjecture.com"
echo ""
echo "Users who have mined can now access their rewards!"
