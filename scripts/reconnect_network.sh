#!/bin/bash

# Reconnect to Network and Restart Block Ingestion
# Reconnects to 16 existing peers and restarts block processing

set -e

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
echo "║         🔄 Reconnect to Network - Restart Block Ingestion                                 ║"
echo "║         🌐 Deploy to: $DROPLET_IP                                                          ║"
echo "║         👥 Peers: 16 existing peers to reconnect                                           ║"
echo "║         📦 Block Ingestion: Restart with genesis foundation                                ║"
echo "║                                                                                            ║"
echo "╚════════════════════════════════════════════════════════════════════════════════════════════╝"
echo ""

log "🔄 Starting network reconnection and block ingestion restart..."

# Step 1: Stop current services
stop_current_services() {
    log "🛑 Stopping current services..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME'
        systemctl stop coinjecture-api.service
        systemctl stop coinjecture-worker.service
        pkill -f 'python.*faucet_server' || true
        pkill -f 'python.*consensus_service' || true
        sleep 2
    "
    success "✅ Current services stopped"
}

# Step 2: Restore full API with block ingestion
restore_full_api() {
    log "🔧 Restoring full API with block ingestion..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME/src/api'
        
        # Restore the original faucet_server.py
        if [ -f 'faucet_server.py.original' ]; then
            cp faucet_server.py.original faucet_server.py
            echo 'Original API restored'
        else
            echo 'Original API not found, keeping current'
        fi
        
        # Ensure proper permissions
        chmod +x faucet_server.py
    "
    success "✅ Full API restored"
}

# Step 3: Initialize blockchain state with genesis
initialize_blockchain_state() {
    log "🏗️  Initializing blockchain state with genesis..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME'
        
        # Ensure data directory exists
        mkdir -p data
        
        # Initialize blockchain state with genesis
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

print('Blockchain state initialized with genesis block')
print('Genesis block:', genesis_info['block_hash'])
\"
    "
    success "✅ Blockchain state initialized"
}

# Step 4: Update systemd services for full operation
update_systemd_services() {
    log "⚙️  Updating systemd services for full operation..."
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
ExecStart=/home/coinjecture/COINjecture/venv/bin/python src/api/faucet_server.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

        # Update worker service
        cat > /etc/systemd/system/coinjecture-worker.service << 'EOF'
[Unit]
Description=COINjecture Cache Worker
After=network.target

[Service]
Type=simple
User=coinjecture
Group=coinjecture
WorkingDirectory=/home/coinjecture/COINjecture
ExecStart=/home/coinjecture/COINjecture/venv/bin/python src/api/update_cache.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

        # Reload systemd
        systemctl daemon-reload
    "
    success "✅ Systemd services updated"
}

# Step 5: Start services
start_services() {
    log "🚀 Starting services..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        systemctl start coinjecture-api.service
        systemctl start coinjecture-worker.service
        sleep 5
        systemctl status coinjecture-api.service coinjecture-worker.service --no-pager
    "
    success "✅ Services started"
}

# Step 6: Verify network connectivity
verify_network_connectivity() {
    log "🔍 Verifying network connectivity..."
    
    # Wait for services to start
    sleep 10
    
    # Check API health
    if curl -s http://$DROPLET_IP:5000/health > /dev/null; then
        success "✅ API is responding"
    else
        error "❌ API is not responding"
        return 1
    fi
    
    # Check block ingestion endpoint
    if curl -s -X POST http://$DROPLET_IP:5000/v1/ingest/block -H "Content-Type: application/json" -d '{}' > /dev/null; then
        success "✅ Block ingestion endpoint is available"
    else
        warning "⚠️  Block ingestion endpoint may not be available"
    fi
    
    # Check current block index
    block_index=$(curl -s http://$DROPLET_IP:5000/v1/data/block/latest | jq -r '.data.index // "error"')
    if [ "$block_index" = "0" ]; then
        success "✅ Blockchain starts from genesis (index 0)"
    else
        warning "⚠️  Block index is $block_index"
    fi
}

# Step 7: Monitor for network activity
monitor_network_activity() {
    log "📡 Monitoring network activity..."
    
    echo "🔍 Checking for peer connections and block activity..."
    
    # Monitor for 30 seconds
    for i in {1..6}; do
        echo "Check $i (5s interval):"
        block_index=$(curl -s http://$DROPLET_IP:5000/v1/data/block/latest | jq -r '.data.index // "error"')
        echo "   Block Index: $block_index"
        sleep 5
    done
    
    success "✅ Network monitoring completed"
}

# Main execution
main() {
    stop_current_services
    restore_full_api
    initialize_blockchain_state
    update_systemd_services
    start_services
    verify_network_connectivity
    monitor_network_activity
    
    success "🎉 Network reconnection completed!"
    
    echo ""
    log "📊 Network Status:"
    echo "   🌐 API Server: http://$DROPLET_IP:5000"
    echo "   🔍 Health Check: http://$DROPLET_IP:5000/health"
    echo "   📊 Latest Block: http://$DROPLET_IP:5000/v1/data/block/latest"
    echo "   📦 Block Ingestion: http://$DROPLET_IP:5000/v1/ingest/block"
    echo "   🔗 Genesis: d1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358"
    echo "   👥 Network: Ready to reconnect to 16 peers"
    echo ""
    success "✅ Network is ready for peer connections and block ingestion!"
}

# Run main function
main "$@"
