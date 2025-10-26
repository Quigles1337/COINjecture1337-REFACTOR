#!/bin/bash
# Production Deployment Script for COINjecture CID System
# Deploys updated code to droplet with IPFS integration

set -e

echo "🚀 COINjecture Production Deployment"
echo "=================================="

# Configuration
DROPLET_IP="167.172.213.70"
DROPLET_USER="root"
PROJECT_DIR="/opt/coinjecture"
BACKUP_DIR="/opt/backups/coinjecture-$(date +%Y%m%d-%H%M%S)"

echo "📋 Deployment Configuration:"
echo "  Droplet: $DROPLET_IP"
echo "  User: $DROPLET_USER"
echo "  Project Dir: $PROJECT_DIR"
echo "  Backup Dir: $BACKUP_DIR"

# Create backup
echo "📦 Creating backup..."
ssh $DROPLET_USER@$DROPLET_IP "mkdir -p $BACKUP_DIR"
ssh $DROPLET_USER@$DROPLET_IP "cp -r $PROJECT_DIR $BACKUP_DIR/"

# Stop services
echo "🛑 Stopping services..."
ssh $DROPLET_USER@$DROPLET_IP "pkill -f 'python3.*faucet_server_cors_fixed.py' || true"
ssh $DROPLET_USER@$DROPLET_IP "pkill -f 'ipfs' || true"

# Deploy updated files
echo "📤 Deploying updated files..."

# Core blockchain files
scp src/core/blockchain.py $DROPLET_USER@$DROPLET_IP:$PROJECT_DIR/src/core/blockchain.py
scp src/cli.py $DROPLET_USER@$DROPLET_IP:$PROJECT_DIR/src/cli.py
scp src/api/faucet_server_cors_fixed.py $DROPLET_USER@$DROPLET_IP:$PROJECT_DIR/src/api/faucet_server_cors_fixed.py

# Dependencies
scp requirements.txt $DROPLET_USER@$DROPLET_IP:$PROJECT_DIR/requirements.txt

# Frontend files
scp web/app.js $DROPLET_USER@$DROPLET_IP:$PROJECT_DIR/web/app.js
scp web/style.css $DROPLET_USER@$DROPLET_IP:$PROJECT_DIR/web/style.css
scp web/index.html $DROPLET_USER@$DROPLET_IP:$PROJECT_DIR/web/index.html

# Install dependencies
echo "📦 Installing dependencies..."
ssh $DROPLET_USER@$DROPLET_IP "cd $PROJECT_DIR && pip install --break-system-packages -r requirements.txt"

# Install IPFS daemon
echo "🌐 Installing IPFS daemon..."
ssh $DROPLET_USER@$DROPLET_IP "wget https://dist.ipfs.io/go-ipfs/v0.14.0/go-ipfs_v0.14.0_linux-amd64.tar.gz"
ssh $DROPLET_USER@$DROPLET_IP "tar -xzf go-ipfs_v0.14.0_linux-amd64.tar.gz"
ssh $DROPLET_USER@$DROPLET_IP "cd go-ipfs && sudo ./install.sh"
ssh $DROPLET_USER@$DROPLET_IP "rm -rf go-ipfs*"

# Initialize IPFS
echo "🔧 Initializing IPFS..."
ssh $DROPLET_USER@$DROPLET_IP "ipfs init --profile server"
ssh $DROPLET_USER@$DROPLET_IP "ipfs config Addresses.Gateway /ip4/0.0.0.0/tcp/8080"
ssh $DROPLET_USER@$DROPLET_IP "ipfs config Addresses.API /ip4/0.0.0.0/tcp/5001"

# Create systemd service for IPFS
echo "⚙️  Creating IPFS systemd service..."
ssh $DROPLET_USER@$DROPLET_IP "cat > /etc/systemd/system/ipfs.service << 'EOF'
[Unit]
Description=IPFS daemon
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/ipfs daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF"

# Create systemd service for COINjecture API
echo "⚙️  Creating COINjecture API systemd service..."
ssh $DROPLET_USER@$DROPLET_IP "cat > /etc/systemd/system/coinjecture-api.service << 'EOF'
[Unit]
Description=COINjecture API Server
After=network.target ipfs.service
Requires=ipfs.service

[Service]
Type=simple
User=root
WorkingDirectory=$PROJECT_DIR
ExecStart=/usr/bin/python3 src/api/faucet_server_cors_fixed.py
Restart=always
RestartSec=10
Environment=PYTHONPATH=$PROJECT_DIR

[Install]
WantedBy=multi-user.target
EOF"

# Enable and start services
echo "🚀 Starting services..."
ssh $DROPLET_USER@$DROPLET_IP "systemctl daemon-reload"
ssh $DROPLET_USER@$DROPLET_IP "systemctl enable ipfs"
ssh $DROPLET_USER@$DROPLET_IP "systemctl enable coinjecture-api"
ssh $DROPLET_USER@$DROPLET_IP "systemctl start ipfs"
sleep 5
ssh $DROPLET_USER@$DROPLET_IP "systemctl start coinjecture-api"

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 10

# Test services
echo "🧪 Testing services..."
if curl -s "http://$DROPLET_IP:12346/health" | grep -q "healthy"; then
    echo "✅ COINjecture API is healthy"
else
    echo "❌ COINjecture API health check failed"
    exit 1
fi

if curl -s "http://$DROPLET_IP:8080/ipfs/QmYwAPJzv5CZsnA625s3Xf2nemtYgPpHdWEz79ojWnPbdG/readme" | grep -q "Hello and Welcome to IPFS"; then
    echo "✅ IPFS gateway is working"
else
    echo "⚠️  IPFS gateway test failed (may need time to start)"
fi

# Test CID generation
echo "🔍 Testing CID generation..."
LATEST_CID=$(curl -s "http://$DROPLET_IP:12346/v1/data/block/latest" | jq -r '.data.cid')
if [[ $LATEST_CID == Qm* ]]; then
    echo "✅ CID generation working: $LATEST_CID"
else
    echo "❌ CID generation test failed"
    exit 1
fi

# Test IPFS endpoint
echo "🔗 Testing IPFS endpoint..."
if curl -s "http://$DROPLET_IP:12346/v1/ipfs/$LATEST_CID" | grep -q "status"; then
    echo "✅ IPFS endpoint working"
else
    echo "⚠️  IPFS endpoint test failed"
fi

echo "🎉 Production deployment completed successfully!"
echo "📊 Services Status:"
echo "  - COINjecture API: http://$DROPLET_IP:12346"
echo "  - IPFS Gateway: http://$DROPLET_IP:8080"
echo "  - IPFS API: http://$DROPLET_IP:5001"
echo "📁 Backup created at: $BACKUP_DIR"
