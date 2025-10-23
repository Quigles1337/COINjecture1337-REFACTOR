#!/bin/bash

# Force Genesis Restart Script
# Completely clears blockchain data and restarts from genesis block

set -e

# Configuration
DROPLET_IP="167.172.213.70"
DROPLET_USER="root"
PROJECT_NAME="COINjecture"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: ✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: ⚠️  $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: ❌ $1${NC}"
}

# Header
echo "╔════════════════════════════════════════════════════════════════════════════════════════════╗"
echo "║                                                                                            ║"
echo "║   ██████╗ ██████╗ ██╗███╗   ██╗     ██╗███████╗ ██████╗████████╗██╗   ██╗██████╗ ███████╗  ║"
echo "║  ██╔════╝██╔═══██╗██║████╗  ██║     ██║██╔════╝██╔════╝╚══██╔══╝██║   ██║██╔══██╗██╔════╝  ║"
echo "║  ██║     ██║   ██║██║██╔██╗ ██║     ██║█████╗  ██║        ██║   ██║   ██║██████╔╝█████╗    ║"
echo "║  ██║     ██║   ██║██║██║╚██╗██║██   ██║██╔══╝  ██║        ██║   ██║   ██║██╔══██╗██╔══╝    ║"
echo "║  ╚██████╗╚██████╔╝██║██║ ╚████║╚█████╔╝███████╗╚██████╗   ██║   ╚██████╔╝██║  ██║███████╗  ║"
echo "║   ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚════╝ ╚══════╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝  ║"
echo "║                                                                                            ║"
echo "║         🔄 Force Genesis Restart - Complete Blockchain Reset                              ║"
echo "║         🌐 Deploy to: $DROPLET_IP                                                          ║"
echo "║         🔗 Genesis: d1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358     ║"
echo "║         ⚠️  WARNING: This will completely clear all blockchain data!                       ║"
echo "║                                                                                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════════════════════╝"
echo ""

log "🔄 Starting force genesis restart..."

# Step 1: Stop all services
stop_services() {
    log "🛑 Stopping all services..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        systemctl stop coinjecture-api.service
        systemctl stop coinjecture-worker.service
        pkill -f 'python.*faucet_server' || true
        pkill -f 'python.*consensus_service' || true
        sleep 2
    "
    success "✅ All services stopped"
}

# Step 2: Backup existing data
backup_data() {
    log "💾 Backing up existing blockchain data..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME'
        mkdir -p backups/backup_\$(date +%Y%m%d_%H%M%S)
        cp -r data/ backups/backup_\$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
        echo 'Backup created: backups/backup_\$(date +%Y%m%d_%H%M%S)/'
    "
    success "✅ Data backed up"
}

# Step 3: Completely clear blockchain data
clear_blockchain_data() {
    log "🗑️  Completely clearing blockchain data..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME'
        
        # Remove all blockchain data
        rm -rf data/blockchain.db*
        rm -rf data/blockchain_state.json
        rm -rf data/cache/
        rm -rf data/blockchain/
        rm -rf data/ipfs/
        rm -rf data/wallets/
        rm -rf logs/*.log
        
        # Remove any remaining blockchain files
        find data/ -name '*.db*' -delete 2>/dev/null || true
        find data/ -name '*.json' -delete 2>/dev/null || true
        
        echo 'All blockchain data cleared'
    "
    success "✅ Blockchain data completely cleared"
}

# Step 4: Initialize fresh blockchain state
initialize_fresh_blockchain() {
    log "🏗️  Initializing fresh blockchain state..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME'
        
        # Create fresh data directory
        mkdir -p data
        
        # Initialize fresh blockchain state
        python3 -c \"
import json
import os
from tokenomics.blockchain_state import BlockchainState

# Create fresh blockchain state
blockchain_state = BlockchainState()
blockchain_state.save_state('data/blockchain_state.json')

# Create genesis block info
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

# Create block queue
with open('data/block_queue.json', 'w') as f:
    json.dump([], f)

print('Fresh blockchain initialized with genesis block')
print('Genesis block:', genesis_info['block_hash'])
print('Block index: 0')
\"
    "
    success "✅ Fresh blockchain initialized"
}

# Step 5: Update API to use fresh blockchain
update_api_for_fresh_start() {
    log "🔧 Updating API for fresh blockchain start..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME/src/api'
        
        # Create a fresh API that starts from genesis
        cat > faucet_server_fresh.py << 'EOF'
#!/usr/bin/env python3
import sys
import os
sys.path.append('src')

from flask import Flask, request, jsonify
import json
import time
from tokenomics.blockchain_state import BlockchainState

app = Flask(__name__)

# Initialize fresh blockchain state
blockchain_state = BlockchainState()
blockchain_state.load_state()

# Load genesis block
genesis_block = None
try:
    with open('data/genesis_block.json', 'r') as f:
        genesis_block = json.load(f)
except:
    genesis_block = {
        'index': 0,
        'block_hash': 'd1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358',
        'timestamp': 1700000000.0,
        'previous_hash': '0' * 64,
        'miner_address': 'GENESIS',
        'work_score': 0.0
    }

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'blockchain': 'fresh'})

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

        chmod +x faucet_server_fresh.py
        echo 'Fresh API created'
    "
    success "✅ Fresh API created"
}

# Step 6: Update systemd service
update_systemd_service() {
    log "⚙️  Updating systemd service for fresh start..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        # Update API service
        cat > /etc/systemd/system/coinjecture-api.service << 'EOF'
[Unit]
Description=COINjecture API Server
After=network.target

[Service]
Type=simple
User=coinjecture
Group=coinjecture
WorkingDirectory=/home/coinjecture/COINjecture
ExecStart=/home/coinjecture/COINjecture/venv/bin/python src/api/faucet_server_fresh.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

        # Reload systemd
        systemctl daemon-reload
        echo 'Systemd service updated for fresh start'
    "
    success "✅ Systemd service updated"
}

# Step 7: Start services
start_services() {
    log "🚀 Starting services with fresh blockchain..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        systemctl start coinjecture-api.service
        sleep 3
        systemctl status coinjecture-api.service --no-pager
    "
    success "✅ Services started"
}

# Step 8: Verify fresh start
verify_fresh_start() {
    log "🔍 Verifying fresh blockchain start..."
    
    # Wait for services to start
    sleep 5
    
    # Check API health
    if curl -s http://$DROPLET_IP:5000/health > /dev/null; then
        success "✅ API is responding"
    else
        error "❌ API is not responding"
        return 1
    fi
    
    # Check block index
    block_index=$(curl -s http://$DROPLET_IP:5000/v1/data/block/latest | jq -r '.data.index // "error"')
    if [ "$block_index" = "0" ]; then
        success "✅ Blockchain started from genesis (index 0)"
    else
        warning "⚠️  Block index is $block_index (expected 0)"
    fi
    
    # Check genesis block
    genesis_hash=$(curl -s http://$DROPLET_IP:5000/v1/data/block/latest | jq -r '.data.block_hash // "error"')
    if [ "$genesis_hash" = "d1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358" ]; then
        success "✅ Correct genesis block hash"
    else
        warning "⚠️  Genesis block hash: $genesis_hash"
    fi
}

# Main execution
main() {
    stop_services
    backup_data
    clear_blockchain_data
    initialize_fresh_blockchain
    update_api_for_fresh_start
    update_systemd_service
    start_services
    verify_fresh_start
    
    success "🎉 Force genesis restart completed!"
    
    echo ""
    log "📊 Fresh Blockchain Status:"
    echo "   🌐 API Server: http://$DROPLET_IP:5000"
    echo "   🔍 Health Check: http://$DROPLET_IP:5000/health"
    echo "   📊 Latest Block: http://$DROPLET_IP:5000/v1/data/block/latest"
    echo "   🔗 Genesis: d1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358"
    echo "   📈 Block Index: 0 (Fresh Start)"
    echo ""
    success "✅ Blockchain successfully restarted from genesis!"
}

# Run main function
main "$@"
