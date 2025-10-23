#!/usr/bin/env bash
set -euo pipefail

# COINjecture TestNet Isolation Script
# Completely isolates the testnet from the old network

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DROPLET_IP="167.172.213.70"
DROPLET_USER="root"
PROJECT_NAME="COINjecture"

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

# Stop all services and processes
stop_all_services() {
    log "⏹️  Stopping all services and processes..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        # Stop systemd services
        sudo systemctl stop coinjecture-api || true
        sudo systemctl stop coinjecture-worker || true
        
        # Kill all Python processes
        pkill -f python || true
        
        # Kill any other COINjecture processes
        pkill -f coinjecture || true
        
        # Wait for processes to stop
        sleep 3
        
        echo 'All services stopped'
    "
    success "✅ All services stopped"
}

# Clear all data completely
clear_all_data() {
    log "🧹 Clearing all blockchain data..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME'
        
        # Remove all data
        rm -rf data/*
        rm -f *.log *.pid
        
        # Remove any temporary files
        rm -f /tmp/coinjecture*
        
        # Clear system logs
        sudo journalctl --vacuum-time=1s || true
        
        echo 'All data cleared'
    "
    success "✅ All data cleared"
}

# Create isolated testnet configuration
create_isolated_config() {
    log "🔧 Creating isolated testnet configuration..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME'
        
        # Create isolated testnet config
        cat > testnet_config.json << 'EOF'
{
  \"network_id\": \"coinjecture-testnet-v1\",
  \"genesis_hash\": \"d1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358\",
  \"bootstrap_peers\": [],
  \"max_peers\": 0,
  \"isolated\": true,
  \"genesis_block\": {
    \"index\": 0,
    \"block_hash\": \"d1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358\",
    \"timestamp\": 1700000000.0,
    \"previous_hash\": \"0000000000000000000000000000000000000000000000000000000000000000\",
    \"miner_address\": \"GENESIS\",
    \"work_score\": 0.0
  }
}
EOF

        echo 'Isolated testnet configuration created'
    "
    success "✅ Isolated testnet configuration created"
}

# Initialize fresh blockchain state
initialize_fresh_chain() {
    log "🏗️  Initializing fresh blockchain state..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME'
        
        # Create fresh blockchain state
        python3 -c \"
import sys
sys.path.append('src')
from tokenomics.blockchain_state import BlockchainState
import json
import os

# Create data directory
os.makedirs('data', exist_ok=True)
os.makedirs('data/cache', exist_ok=True)

# Initialize fresh blockchain state
blockchain_state = BlockchainState()
blockchain_state.save_state('data/blockchain_state.json')

# Create genesis block info
genesis_info = {
    'index': 0,
    'block_hash': 'd1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358',
    'timestamp': 1700000000.0,
    'previous_hash': '0000000000000000000000000000000000000000000000000000000000000000',
    'miner_address': 'GENESIS',
    'work_score': 0.0
}

# Save genesis block
with open('data/cache/latest_block.json', 'w') as f:
    json.dump(genesis_info, f, indent=2)

# Create empty blocks history
with open('data/cache/blocks_history.json', 'w') as f:
    json.dump([genesis_info], f, indent=2)

print('Fresh blockchain state initialized')
print('Genesis block:', genesis_info['block_hash'])
\"
    "
    success "✅ Fresh blockchain state initialized"
}

# Start isolated services
start_isolated_services() {
    log "🚀 Starting isolated testnet services..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME'
        
        # Start services
        sudo systemctl start coinjecture-api
        sudo systemctl start coinjecture-worker
        
        # Check status
        echo 'Service Status:'
        sudo systemctl is-active coinjecture-api
        sudo systemctl is-active coinjecture-worker
    "
    success "✅ Isolated services started"
}

# Verify isolated testnet
verify_isolated_testnet() {
    log "🔍 Verifying isolated testnet..."
    
    # Wait for services to start
    sleep 10
    
    # Check API health
    if curl -s -f "http://$DROPLET_IP:5000/health" >/dev/null; then
        success "✅ API is responding"
    else
        error "❌ API not responding"
        return 1
    fi
    
    # Check latest block (should be genesis or very low index)
    LATEST_BLOCK=$(curl -s "http://$DROPLET_IP:5000/v1/data/block/latest" | jq -r '.data.index // "unknown"')
    
    if [ "$LATEST_BLOCK" = "0" ] || [ "$LATEST_BLOCK" = "1" ]; then
        success "✅ Isolated testnet started correctly (block index: $LATEST_BLOCK)"
    else
        warn "⚠️  Block index is $LATEST_BLOCK (expected 0 or 1 for isolated testnet)"
    fi
    
    success "✅ Isolated testnet verification completed"
}

# Main function
main() {
    echo -e "${BLUE}"
    echo "🔄 COINjecture TestNet Isolation"
    echo "🌐 Deploy to: $DROPLET_IP"
    echo "🔒 Isolated: No external network connections"
    echo "🏗️  Fresh: Starting from genesis block"
    echo -e "${NC}"
    
    log "🔄 Starting COINjecture testnet isolation..."
    
    # Step 1: Stop all services
    stop_all_services
    
    # Step 2: Clear all data
    clear_all_data
    
    # Step 3: Create isolated config
    create_isolated_config
    
    # Step 4: Initialize fresh chain
    initialize_fresh_chain
    
    # Step 5: Start isolated services
    start_isolated_services
    
    # Step 6: Verify isolated testnet
    verify_isolated_testnet
    
    success "🎉 Isolated testnet setup completed!"
    echo ""
    info "🌐 API Server: http://$DROPLET_IP:5000"
    info "🌐 Health Check: http://$DROPLET_IP:5000/health"
    info "🌐 Latest Block: http://$DROPLET_IP:5000/v1/data/block/latest"
    info "🔒 Isolated: No external network connections"
    info "🏗️  Fresh: Starting from genesis block"
    info "💰 Tokenomics: Real token distribution enabled"
    echo ""
    success "✅ Isolated testnet is ready for development!"
}

# Run main function
main "$@"
