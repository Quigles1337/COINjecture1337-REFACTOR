#!/bin/bash

# Initialize blockchain with existing genesis block
# Uses the existing genesis: d1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358

set -e

DROPLET_IP="167.172.213.70"
DROPLET_USER="root"

echo "🔄 Initializing blockchain with existing genesis block..."

# Stop services
echo "🛑 Stopping services..."
ssh "$DROPLET_USER@$DROPLET_IP" "
    cd /home/coinjecture/COINjecture
    systemctl stop coinjecture-api.service
    systemctl stop coinjecture-worker.service
    pkill -f 'python.*faucet_server' || true
    pkill -f 'python.*consensus_service' || true
"

# Clear old blockchain data
echo "🗑️  Clearing old blockchain data..."
ssh "$DROPLET_USER@$DROPLET_IP" "
    cd /home/coinjecture/COINjecture
    rm -rf data/blockchain.db*
    rm -rf data/blockchain_state.json
    rm -rf data/cache/
    rm -rf data/blockchain/
    rm -rf data/ipfs/
    rm -rf data/wallets/
    rm -rf logs/*.log
    mkdir -p data
"

# Initialize with existing genesis block
echo "🏗️  Initializing with existing genesis block..."
ssh "$DROPLET_USER@$DROPLET_IP" "
    cd /home/coinjecture/COINjecture
    
    # Create fresh blockchain state
    python3 -c \"
import json
import os
from tokenomics.blockchain_state import BlockchainState

# Create fresh blockchain state
blockchain_state = BlockchainState()
blockchain_state.save_state('data/blockchain_state.json')

# Create genesis block with existing hash
genesis_info = {
    'index': 0,
    'block_hash': 'd1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358',
    'timestamp': 1700000000.0,
    'previous_hash': '0' * 64,
    'miner_address': 'GENESIS',
    'work_score': 0.0,
    'cumulative_work_score': 0.0
}

# Save genesis block
with open('data/genesis_block.json', 'w') as f:
    json.dump(genesis_info, f, indent=2)

print('Blockchain initialized with existing genesis block')
print('Genesis block:', genesis_info['block_hash'])
print('Block index: 0')
\"
"

# Create simple API that returns genesis block
echo "🔧 Creating simple API..."
ssh "$DROPLET_USER@$DROPLET_IP" "
    cd /home/coinjecture/COINjecture/src/api
    
    cat > faucet_server_genesis.py << 'EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.append('src')

from flask import Flask, request, jsonify
import json
import time

app = Flask(__name__)

# Load genesis block
genesis_block = {
    'index': 0,
    'block_hash': 'd1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358',
    'timestamp': 1700000000.0,
    'previous_hash': '0' * 64,
    'miner_address': 'GENESIS',
    'work_score': 0.0,
    'cumulative_work_score': 0.0
}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'blockchain': 'genesis'})

@app.route('/v1/data/block/latest', methods=['GET'])
def latest_block():
    return jsonify({
        'data': genesis_block,
        'status': 'success'
    })

@app.route('/v1/data/block/<int:index>', methods=['GET'])
def get_block(index):
    if index == 0:
        return jsonify({
            'data': genesis_block,
            'status': 'success'
        })
    else:
        return jsonify({
            'error': 'Block not found',
            'status': 'error'
        }), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
EOF

    chmod +x faucet_server_genesis.py
"

# Update systemd service
echo "⚙️  Updating systemd service..."
ssh "$DROPLET_USER@$DROPLET_IP" "
    cat > /etc/systemd/system/coinjecture-api.service << 'EOF'
[Unit]
Description=COINjecture API Server
After=network.target

[Service]
Type=simple
User=coinjecture
Group=coinjecture
WorkingDirectory=/home/coinjecture/COINjecture
ExecStart=/home/coinjecture/COINjecture/venv/bin/python src/api/faucet_server_genesis.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
"

# Start services
echo "🚀 Starting services..."
ssh "$DROPLET_USER@$DROPLET_IP" "
    systemctl start coinjecture-api.service
    sleep 3
"

# Verify
echo "🔍 Verifying genesis block..."
sleep 5

block_index=$(curl -s http://$DROPLET_IP:5000/v1/data/block/latest | jq -r '.data.index // "error"')
genesis_hash=$(curl -s http://$DROPLET_IP:5000/v1/data/block/latest | jq -r '.data.block_hash // "error"')

echo "📊 Blockchain Status:"
echo "   Block Index: $block_index"
echo "   Genesis Hash: $genesis_hash"

if [ "$block_index" = "0" ] && [ "$genesis_hash" = "d1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358" ]; then
    echo "✅ SUCCESS: Blockchain initialized with existing genesis block!"
else
    echo "❌ ERROR: Genesis block not properly initialized"
    exit 1
fi

echo ""
echo "🌐 API Server: http://$DROPLET_IP:5000"
echo "🔍 Health Check: http://$DROPLET_IP:5000/health"
echo "📊 Latest Block: http://$DROPLET_IP:5000/v1/data/block/latest"
echo "🔗 Genesis: d1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358"
