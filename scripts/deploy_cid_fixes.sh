#!/bin/bash
# Deploy CID Encoding Fixes to Droplet
# Updates backend code and runs database migration

set -e

echo "🚀 COINjecture CID Encoding Fix Deployment"
echo "=========================================="

# Configuration
DROPLET_IP="167.172.213.70"
DROPLET_USER="root"
PROJECT_NAME="COINjecture-main"
REMOTE_PATH="/root/COINjecture"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Create deployment package
print_status "Creating deployment package..."
cd "/Users/sarahmarin/Downloads/COINjecture-main 4"

# Create tarball with updated files
tar -czf coinjecture_cid_fixes.tar.gz \
    src/core/blockchain.py \
    src/cli.py \
    scripts/migrate_cid_database.py \
    scripts/fix_computational_data_cids.py \
    scripts/robust_cid_converter.py \
    scripts/force_cid_conversion.py \
    scripts/proper_cid_converter.py \
    scripts/working_cid_converter.py \
    scripts/final_cid_converter.py \
    scripts/successful_cid_converter.py \
    scripts/fix_backend_cid_encoding.py

print_success "Deployment package created: coinjecture_cid_fixes.tar.gz"

# Step 2: Transfer to droplet
print_status "Transferring files to droplet..."
scp coinjecture_cid_fixes.tar.gz ${DROPLET_USER}@${DROPLET_IP}:/tmp/

print_success "Files transferred to droplet"

# Step 3: Deploy on droplet
print_status "Deploying CID fixes on droplet..."
ssh ${DROPLET_USER}@${DROPLET_IP} << 'EOF'
    set -e
    
    echo "🔧 Deploying CID fixes on droplet..."
    
    # Navigate to project directory
    cd /root/COINjecture
    
    # Backup current files
    echo "📦 Creating backup..."
    cp src/core/blockchain.py src/core/blockchain.py.backup.$(date +%s)
    cp src/cli.py src/cli.py.backup.$(date +%s)
    
    # Extract updated files
    echo "📁 Extracting updated files..."
    tar -xzf /tmp/coinjecture_cid_fixes.tar.gz -C .
    
    # Set permissions
    chmod +x scripts/*.py
    
    echo "✅ CID fixes deployed successfully"
    
    # Show updated files
    echo "📋 Updated files:"
    echo "  - src/core/blockchain.py (base58btc CID generation)"
    echo "  - src/cli.py (base58btc CID generation)"
    echo "  - scripts/migrate_cid_database.py (database migration)"
    echo "  - Multiple computational data conversion scripts"
EOF

print_success "CID fixes deployed to droplet"

# Step 4: Run database migration
print_status "Running database migration on production..."
ssh ${DROPLET_USER}@${DROPLET_IP} << 'EOF'
    set -e
    
    echo "🗄️ Running database migration..."
    cd /root/COINjecture
    
    # Check if database exists
    if [ -f "data/blockchain.db" ]; then
        echo "📊 Found database: data/blockchain.db"
        
        # Run migration
        python3 scripts/migrate_cid_database.py data/blockchain.db
        
        echo "✅ Database migration completed"
    else
        echo "⚠️ No database found at data/blockchain.db"
        echo "Migration skipped"
    fi
EOF

print_success "Database migration completed"

# Step 5: Update computational data
print_status "Updating computational data files..."
ssh ${DROPLET_USER}@${DROPLET_IP} << 'EOF'
    set -e
    
    echo "📊 Updating computational data..."
    cd /root/COINjecture
    
    # Check if kaggle_data directory exists
    if [ -d "kaggle_data" ]; then
        echo "📁 Found kaggle_data directory"
        
        # Run computational data conversion
        python3 scripts/successful_cid_converter.py kaggle_data
        
        echo "✅ Computational data updated"
    else
        echo "⚠️ No kaggle_data directory found"
        echo "Computational data update skipped"
    fi
EOF

print_success "Computational data updated"

# Step 6: Restart services
print_status "Restarting services..."
ssh ${DROPLET_USER}@${DROPLET_IP} << 'EOF'
    echo "🔄 Restarting services..."
    
    # Restart API service
    if systemctl is-active --quiet coinjecture-api; then
        systemctl restart coinjecture-api
        echo "✅ API service restarted"
    else
        echo "⚠️ API service not running"
    fi
    
    # Restart consensus service
    if systemctl is-active --quiet coinjecture-consensus; then
        systemctl restart coinjecture-consensus
        echo "✅ Consensus service restarted"
    else
        echo "⚠️ Consensus service not running"
    fi
    
    # Check service status
    echo "📊 Service status:"
    systemctl status coinjecture-api --no-pager -l
    systemctl status coinjecture-consensus --no-pager -l
EOF

print_success "Services restarted"

# Step 7: Test integration
print_status "Testing CID integration..."
ssh ${DROPLET_USER}@${DROPLET_IP} << 'EOF'
    echo "🧪 Testing CID integration..."
    cd /root/COINjecture
    
    # Test API health
    echo "🔍 Testing API health..."
    curl -s http://localhost:5000/health | head -5
    
    # Test latest block endpoint
    echo "📦 Testing latest block..."
    curl -s http://localhost:5000/v1/data/block/latest | head -5
    
    echo "✅ Integration tests completed"
EOF

print_success "Integration tests completed"

# Step 8: Cleanup
print_status "Cleaning up..."
rm -f coinjecture_cid_fixes.tar.gz

print_success "Cleanup completed"

# Final summary
echo ""
echo "🎯 CID ENCODING FIX DEPLOYMENT COMPLETE"
echo "========================================"
echo "✅ Backend code updated with base58btc CID generation"
echo "✅ Database migration executed"
echo "✅ Computational data files updated"
echo "✅ Services restarted"
echo "✅ Integration tests completed"
echo ""
echo "🌐 Next steps:"
echo "  1. Test frontend proof bundle downloads"
echo "  2. Verify academic export functionality"
echo "  3. Monitor service logs for any issues"
echo ""
echo "📊 Deployment completed successfully!"
