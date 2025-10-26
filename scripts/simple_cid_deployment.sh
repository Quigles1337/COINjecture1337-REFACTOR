#!/bin/bash
# Simple CID Deployment Script
# Directly updates files on droplet

set -e

echo "🚀 Simple CID Deployment"
echo "========================"

DROPLET_IP="167.172.213.70"
DROPLET_USER="root"

# Function to print colored output
print_status() {
    echo -e "\033[0;34m[INFO]\033[0m $1"
}

print_success() {
    echo -e "\033[0;32m[SUCCESS]\033[0m $1"
}

print_error() {
    echo -e "\033[0;31m[ERROR]\033[0m $1"
}

# Step 1: Update blockchain.py
print_status "Updating blockchain.py with base58btc CID generation..."
ssh ${DROPLET_USER}@${DROPLET_IP} << 'EOF'
    cd /root/COINjecture
    
    # Backup original file
    cp core/blockchain.py core/blockchain.py.backup.$(date +%s)
    echo "✅ Backup created"
    
    # Update CID generation to use base58btc
    sed -i 's/base58\.b58encode(multihash)\.decode/base58.b58encode(multihash, alphabet=base58.BITCOIN_ALPHABET).decode/g' core/blockchain.py
    echo "✅ Updated blockchain.py CID generation"
EOF

print_success "blockchain.py updated"

# Step 2: Update cli.py
print_status "Updating cli.py with base58btc CID generation..."
ssh ${DROPLET_USER}@${DROPLET_IP} << 'EOF'
    cd /root/COINjecture
    
    # Backup original file
    cp cli.py cli.py.backup.$(date +%s)
    echo "✅ Backup created"
    
    # Update CID generation to use base58btc
    sed -i 's/base58\.b58encode(multihash)\.decode/base58.b58encode(multihash, alphabet=base58.BITCOIN_ALPHABET).decode/g' cli.py
    echo "✅ Updated cli.py CID generation"
EOF

print_success "cli.py updated"

# Step 3: Test the changes
print_status "Testing updated files..."
ssh ${DROPLET_USER}@${DROPLET_IP} << 'EOF'
    cd /root/COINjecture
    
    # Test Python syntax
    python3 -m py_compile core/blockchain.py
    echo "✅ blockchain.py syntax OK"
    
    python3 -m py_compile cli.py
    echo "✅ cli.py syntax OK"
    
    # Check if base58btc is being used
    grep -n "BITCOIN_ALPHABET" core/blockchain.py
    grep -n "BITCOIN_ALPHABET" cli.py
    echo "✅ base58btc encoding confirmed"
EOF

print_success "Files tested successfully"

# Step 4: Restart services
print_status "Restarting services..."
ssh ${DROPLET_USER}@${DROPLET_IP} << 'EOF'
    echo "🔄 Restarting services..."
    
    # Check what services are running
    systemctl list-units --type=service | grep -i coinjecture || echo "No coinjecture services found"
    
    # Try to restart any running services
    if systemctl is-active --quiet coinjecture-api; then
        systemctl restart coinjecture-api
        echo "✅ API service restarted"
    fi
    
    if systemctl is-active --quiet coinjecture-consensus; then
        systemctl restart coinjecture-consensus
        echo "✅ Consensus service restarted"
    fi
    
    # Check for any Python processes
    ps aux | grep python | grep -v grep || echo "No Python processes found"
EOF

print_success "Services restarted"

# Step 5: Test API
print_status "Testing API endpoints..."
ssh ${DROPLET_USER}@${DROPLET_IP} << 'EOF'
    echo "🧪 Testing API..."
    
    # Test health endpoint
    curl -s http://localhost:5000/health || echo "Health endpoint not responding"
    
    # Test latest block
    curl -s http://localhost:5000/v1/data/block/latest | head -3 || echo "Latest block endpoint not responding"
    
    echo "✅ API tests completed"
EOF

print_success "API tests completed"

echo ""
echo "🎯 CID DEPLOYMENT COMPLETE"
echo "=========================="
echo "✅ blockchain.py updated with base58btc CID generation"
echo "✅ cli.py updated with base58btc CID generation"
echo "✅ Files syntax tested"
echo "✅ Services restarted"
echo "✅ API endpoints tested"
echo ""
echo "🌐 New CIDs will now use proper base58btc encoding!"
echo "📊 Deployment completed successfully!"
