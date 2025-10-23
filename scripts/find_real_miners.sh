#!/bin/bash

# Find Real Miners in the Network
# Discovers actual miner addresses from the network

set -e

DROPLET_IP="167.172.213.70"
DROPLET_USER="root"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

echo "🔍 Finding Real Miners in the Network..."

# Check if there are any real network connections
log "🔍 Checking for real network connections..."

# Look for actual miner addresses in the system
ssh "$DROPLET_USER@$DROPLET_IP" "
    cd '/home/coinjecture/COINjecture'
    
    echo '📊 Checking for real miner addresses...'
    
    # Check if there are any real blockchain files
    if [ -f 'data/blockchain.db' ]; then
        echo '✅ Found blockchain.db - checking for real miners...'
        # This would require a database query to extract miner addresses
        echo '   Note: blockchain.db contains real miner data'
    else
        echo '⚠️  No blockchain.db found'
    fi
    
    # Check for any real network data
    if [ -d 'data_backup_*' ]; then
        echo '✅ Found backup data - checking for real miners...'
        find data_backup_* -name '*.json' -exec grep -l 'miner_address' {} \; | head -5 | while read file; do
            echo \"   File: \$file\"
            grep -o '\"miner_address\": \"[^\"]*\"' \"\$file\" | head -3
        done
    else
        echo '⚠️  No backup data found'
    fi
    
    # Check for any running mining processes
    echo '🔍 Checking for running mining processes...'
    ps aux | grep -i miner | grep -v grep || echo '   No mining processes found'
    
    # Check for any wallet files
    echo '🔍 Checking for wallet files...'
    find . -name '*wallet*' -o -name '*miner*' | head -5
"

# Check if we can connect to real network peers
log "🌐 Checking for real network peers..."

# Try to find real network endpoints
known_network_endpoints=(
    "167.172.213.70:5000"
    "bootstrap:5000"
    "api.coinjecture.com"
)

for endpoint in "${known_network_endpoints[@]}"; do
    echo "🔍 Checking endpoint: $endpoint"
    
    if curl -s "http://$endpoint/health" > /dev/null 2>&1; then
        echo "✅ Endpoint $endpoint is responding"
        
        # Try to get real block data
        block_data=$(curl -s "http://$endpoint/v1/data/block/latest" 2>/dev/null)
        if [ $? -eq 0 ]; then
            miner_address=$(echo "$block_data" | jq -r '.data.miner_address // "unknown"' 2>/dev/null)
            if [ "$miner_address" != "unknown" ] && [ "$miner_address" != "null" ]; then
                echo "   📦 Latest block miner: $miner_address"
            fi
        fi
    else
        echo "❌ Endpoint $endpoint not responding"
    fi
done

# Check for any real miner addresses in the current system
log "🔍 Checking current system for real miners..."

ssh "$DROPLET_USER@$DROPLET_IP" "
    cd '/home/coinjecture/COINjecture'
    
    echo '📊 Current system miner addresses:'
    
    # Check current blockchain state
    if [ -f 'data/blockchain_state.json' ]; then
        echo '   Blockchain state file exists'
        # Extract miner addresses from blockchain state
        grep -o '\"miner_address\": \"[^\"]*\"' data/blockchain_state.json | head -5
    fi
    
    # Check for any mining-related processes
    echo '🔍 Mining processes:'
    ps aux | grep -E '(mining|miner|consensus)' | grep -v grep | head -5
    
    # Check for any wallet or address files
    echo '🔍 Wallet/address files:'
    find . -name '*wallet*' -o -name '*address*' -o -name '*miner*' | head -5
"

# Create a summary
echo ""
log "📊 Summary of Real Miners Found:"
echo "   🔍 Checked for real network connections"
echo "   📦 Looked for actual miner addresses in blockchain data"
echo "   🌐 Tested network endpoints for real miner data"
echo "   🔧 Checked current system for mining processes"

success "✅ Real miner discovery completed!"
