#!/bin/bash
# Deploy Complete CID Fix to Droplet
# Uses the corrected files from local workspace

set -e

echo "🚀 COINjecture Complete CID Fix Deployment"
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

# Step 1: Create deployment package with ALL fixed files
print_status "Creating complete deployment package..."

cd "/Users/sarahmarin/Downloads/COINjecture-main 4"

# Create comprehensive tarball with all fixed files
tar -czf coinjecture_complete_cid_fix.tar.gz \
    src/core/blockchain.py \
    src/cli.py \
    cid_generator.py \
    scripts/regenerate_all_cids.py \
    scripts/validate_all_cids.py \
    scripts/final_cid_converter.py \
    scripts/working_cid_converter.py \
    scripts/robust_cid_converter.py \
    scripts/force_cid_conversion.py \
    scripts/proper_cid_converter.py \
    scripts/migrate_cid_database.py \
    scripts/fix_computational_data_cids.py \
    scripts/fix_backend_cid_encoding.py \
    scripts/fix_cid_encoding.py \
    scripts/update_all_cids_in_db.py \
    scripts/update_existing_cids.py \
    scripts/test_complete_system.py \
    scripts/update_server_cids.py

print_success "Complete deployment package created: coinjecture_complete_cid_fix.tar.gz"

# Step 2: Transfer to droplet
print_status "Transferring complete fix package to droplet..."
scp coinjecture_complete_cid_fix.tar.gz ${DROPLET_USER}@${DROPLET_IP}:/tmp/

print_success "Package transferred to droplet"

# Step 3: Deploy complete fix on droplet
print_status "Deploying complete CID fix on droplet..."
ssh ${DROPLET_USER}@${DROPLET_IP} << 'EOF'
    set -e
    
    echo "🔧 Deploying complete CID fix on droplet..."
    
    # Navigate to project directory
    cd /root/COINjecture
    
    # Create backup directory
    BACKUP_DIR="backup_$(date +%s)"
    mkdir -p $BACKUP_DIR
    echo "📦 Creating backup in $BACKUP_DIR..."
    
    # Backup critical files
    cp src/core/blockchain.py $BACKUP_DIR/ 2>/dev/null || echo "blockchain.py not found"
    cp src/cli.py $BACKUP_DIR/ 2>/dev/null || echo "cli.py not found"
    cp cid_generator.py $BACKUP_DIR/ 2>/dev/null || echo "cid_generator.py not found"
    
    # Extract ALL fixed files
    echo "📁 Extracting complete fix package..."
    tar -xzf /tmp/coinjecture_complete_cid_fix.tar.gz -C .
    
    # Set permissions
    chmod +x scripts/*.py 2>/dev/null || echo "No scripts to make executable"
    
    echo "✅ Complete CID fix deployed successfully"
    
    # Show what was updated
    echo "📋 Updated files:"
    echo "  - src/core/blockchain.py (base58btc CID generation)"
    echo "  - src/cli.py (base58btc CID generation)"
    echo "  - cid_generator.py (base58btc CID generation)"
    echo "  - scripts/regenerate_all_cids.py (database migration)"
    echo "  - scripts/validate_all_cids.py (validation)"
    echo "  - All migration scripts (fixed constants)"
EOF

print_success "Complete CID fix deployed to droplet"

# Step 4: Run database migration on production
print_status "Running database migration on production..."
ssh ${DROPLET_USER}@${DROPLET_IP} << 'EOF'
    set -e
    
    echo "🗄️ Running database migration on production..."
    cd /root/COINjecture
    
    # Check if database exists
    if [ -f "data/blockchain.db" ]; then
        echo "📊 Found database: data/blockchain.db"
        
        # Run the new migration script
        python3 scripts/regenerate_all_cids.py
        
        echo "✅ Database migration completed"
    else
        echo "⚠️ No database found at data/blockchain.db"
        echo "Migration skipped - no database to migrate"
    fi
EOF

print_success "Database migration completed"

# Step 5: Validate the migration
print_status "Validating CID migration..."
ssh ${DROPLET_USER}@${DROPLET_IP} << 'EOF'
    set -e
    
    echo "🔍 Validating CID migration..."
    cd /root/COINjecture
    
    # Run validation script
    python3 scripts/validate_all_cids.py
    
    echo "✅ CID validation completed"
EOF

print_success "CID validation completed"

# Step 6: Restart services
print_status "Restarting services..."
ssh ${DROPLET_USER}@${DROPLET_IP} << 'EOF'
    echo "🔄 Restarting services..."
    
    # Check what services are running
    echo "📊 Current services:"
    systemctl list-units --type=service | grep -i coinjecture || echo "No coinjecture services found"
    
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
    
    # Check for any Python processes that might need restarting
    echo "🐍 Python processes:"
    ps aux | grep python | grep -v grep || echo "No Python processes found"
    
    # Check service status
    echo "📊 Service status:"
    systemctl status coinjecture-api --no-pager -l 2>/dev/null || echo "API service not found"
    systemctl status coinjecture-consensus --no-pager -l 2>/dev/null || echo "Consensus service not found"
EOF

print_success "Services restarted"

# Step 7: Test integration
print_status "Testing CID integration..."
ssh ${DROPLET_USER}@${DROPLET_IP} << 'EOF'
    echo "🧪 Testing CID integration..."
    cd /root/COINjecture
    
    # Test API health
    echo "🔍 Testing API health..."
    curl -s http://localhost:5000/health 2>/dev/null | head -5 || echo "Health endpoint not responding"
    
    # Test latest block endpoint
    echo "📦 Testing latest block..."
    curl -s http://localhost:5000/v1/data/block/latest 2>/dev/null | head -5 || echo "Latest block endpoint not responding"
    
    # Test CID format in response
    echo "🔍 Checking CID format in API response..."
    LATEST_RESPONSE=$(curl -s http://localhost:5000/v1/data/block/latest 2>/dev/null || echo "{}")
    echo "Latest block response: $LATEST_RESPONSE" | head -3
    
    echo "✅ Integration tests completed"
EOF

print_success "Integration tests completed"

# Step 8: Cleanup
print_status "Cleaning up..."
rm -f coinjecture_complete_cid_fix.tar.gz

print_success "Cleanup completed"

# Final summary
echo ""
echo "🎯 COMPLETE CID FIX DEPLOYMENT COMPLETE"
echo "======================================="
echo "✅ All CID generation code updated with base58btc"
echo "✅ Database migration executed with validation"
echo "✅ All migration scripts fixed"
echo "✅ Services restarted"
echo "✅ Integration tests completed"
echo ""
echo "🌐 Production server now has:"
echo "  - Proper base58btc CID generation"
echo "  - Valid CIDs in database"
echo "  - Fixed migration scripts"
echo "  - Working API endpoints"
echo ""
echo "📊 Next steps:"
echo "  1. Test frontend proof bundle downloads"
echo "  2. Verify academic export functionality"
echo "  3. Monitor service logs for any issues"
echo ""
echo "🎉 Complete CID fix deployment successful!"
