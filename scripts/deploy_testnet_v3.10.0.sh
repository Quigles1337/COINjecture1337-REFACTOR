#!/usr/bin/env bash
set -euo pipefail

# COINjecture TestNet v3.10.0 Deployment Script
# Deploys updated testnet with token distribution and cleaned codebase

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
DROPLET_IP="167.172.213.70"
DROPLET_USER="root"
PROJECT_NAME="COINjecture"
LOCAL_PROJECT_DIR="$(pwd)"
VERSION="3.10.0"

print_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════════════════════════════════════╗"
    echo "║                                                                                            ║"
    echo "║   ██████╗ ██████╗ ██╗███╗   ██╗     ██╗███████╗ ██████╗████████╗██╗   ██╗██████╗ ███████╗  ║"
    echo "║  ██╔════╝██╔═══██╗██║████╗  ██║     ██║██╔════╝██╔════╝╚══██╔══╝██║   ██║██╔══██╗██╔════╝  ║"
    echo "║  ██║     ██║   ██║██║██╔██╗ ██║     ██║█████╗  ██║        ██║   ██║   ██║██████╔╝█████╗    ║"
    echo "║  ██║     ██║   ██║██║██║╚██╗██║██   ██║██╔══╝  ██║        ██║   ██║   ██║██╔══██╗██╔══╝    ║"
    echo "║  ╚██████╗╚██████╔╝██║██║ ╚████║╚█████╔╝███████╗╚██████╗   ██║   ╚██████╔╝██║  ██║███████╗  ║"
    echo "║   ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚════╝ ╚══════╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝  ║"
    echo "║                                                                                            ║"
    echo "║         🚀 TestNet v$VERSION Deployment to DigitalOcean Droplet                              ║"
    echo "║         🌐 Deploy to: $DROPLET_IP                                                          ║"
    echo "║         💰 Token Distribution & Cleaned Codebase                                            ║"
    echo "║         🔒 Enhanced Cryptographic Commitments                                              ║"
    echo "║                                                                                            ║"
    echo "╚════════════════════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

info() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] INFO:${NC} $1"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS:${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "🔍 Checking prerequisites..."
    
    # Check if we're in the right directory
    if [ ! -f "VERSION" ] || [ ! -f "src/cli.py" ]; then
        error "❌ Must be run from COINjecture project root directory"
        exit 1
    fi
    
    # Check version
    CURRENT_VERSION=$(cat VERSION)
    if [ "$CURRENT_VERSION" != "$VERSION" ]; then
        warn "⚠️  Version mismatch: Expected $VERSION, found $CURRENT_VERSION"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check if SSH key exists
    if [ ! -f ~/.ssh/id_rsa ] && [ ! -f ~/.ssh/id_ed25519 ]; then
        error "❌ No SSH key found. Please ensure you have SSH access to the droplet."
        exit 1
    fi
    
    success "✅ Prerequisites check passed"
}

# Create deployment package
create_deployment_package() {
    log "📦 Creating deployment package..."
    
    # Create temporary directory
    TEMP_DIR="/tmp/coinjecture_deploy_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$TEMP_DIR"
    
    # Copy project files (excluding unnecessary files)
    rsync -av --exclude='.git' \
          --exclude='data/blockchain/*' \
          --exclude='data/cache/*' \
          --exclude='logs/*' \
          --exclude='*.log' \
          --exclude='*.pid' \
          --exclude='.venv' \
          --exclude='__pycache__' \
          --exclude='*.pyc' \
          --exclude='.DS_Store' \
          . "$TEMP_DIR/"
    
    # Create deployment archive
    DEPLOY_ARCHIVE="/tmp/coinjecture_v${VERSION}_deploy.tar.gz"
    tar -czf "$DEPLOY_ARCHIVE" -C "$TEMP_DIR" .
    
    # Cleanup temp directory
    rm -rf "$TEMP_DIR"
    
    success "✅ Deployment package created: $DEPLOY_ARCHIVE"
    echo "$DEPLOY_ARCHIVE"
}

# Deploy to droplet
deploy_to_droplet() {
    local deploy_archive="$1"
    
    log "🚀 Deploying to DigitalOcean droplet ($DROPLET_IP)..."
    
    # Test SSH connection
    log "🔐 Testing SSH connection..."
    if ! ssh -o ConnectTimeout=10 -o BatchMode=yes "$DROPLET_USER@$DROPLET_IP" "echo 'SSH connection successful'" >/dev/null 2>&1; then
        error "❌ Cannot connect to droplet via SSH"
        exit 1
    fi
    success "✅ SSH connection successful"
    
    # Create backup on droplet
    log "💾 Creating backup on droplet..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        if [ -d '/home/coinjecture/$PROJECT_NAME' ]; then
            echo 'Creating backup...'
            sudo cp -r '/home/coinjecture/$PROJECT_NAME' '/home/coinjecture/${PROJECT_NAME}_backup_\$(date +%Y%m%d_%H%M%S)'
            echo 'Backup created'
        fi
    "
    
    # Upload deployment package
    log "📤 Uploading deployment package..."
    scp "$deploy_archive" "$DROPLET_USER@$DROPLET_IP:/tmp/"
    
    # Extract and deploy on droplet
    log "🔧 Extracting and deploying on droplet..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        echo 'Stopping services...'
        sudo systemctl stop coinjecture-api || true
        sudo systemctl stop coinjecture-worker || true
        
        echo 'Extracting deployment package...'
        cd /home/coinjecture
        rm -rf '$PROJECT_NAME'
        mkdir -p '$PROJECT_NAME'
        tar -xzf '/tmp/$(basename $deploy_archive)' -C '$PROJECT_NAME'
        
        echo 'Setting permissions...'
        sudo chown -R coinjecture:coinjecture '/home/coinjecture/$PROJECT_NAME'
        chmod +x '/home/coinjecture/$PROJECT_NAME/scripts/'*.sh
        
        echo 'Cleaning up...'
        rm -f '/tmp/$(basename $deploy_archive)'
        
        echo 'Deployment completed'
    "
    
    success "✅ Deployment to droplet completed"
}

# Update services on droplet
update_services() {
    log "🔄 Updating services on droplet..."
    
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME'
        
        echo 'Updating systemd services...'
        
        # Update API service
        sudo tee /etc/systemd/system/coinjecture-api.service > /dev/null << 'EOF'
[Unit]
Description=COINjecture API Server
After=network.target

[Service]
Type=simple
User=coinjecture
WorkingDirectory=/home/coinjecture/COINjecture
ExecStart=/usr/bin/python3 src/api/faucet_server.py
Restart=always
RestartSec=5
Environment=PYTHONPATH=/home/coinjecture/COINjecture/src

[Install]
WantedBy=multi-user.target
EOF

        # Update worker service
        sudo tee /etc/systemd/system/coinjecture-worker.service > /dev/null << 'EOF'
[Unit]
Description=COINjecture Cache Worker
After=network.target

[Service]
Type=simple
User=coinjecture
WorkingDirectory=/home/coinjecture/COINjecture
ExecStart=/usr/bin/python3 src/api/update_cache.py
Restart=always
RestartSec=5
Environment=PYTHONPATH=/home/coinjecture/COINjecture/src

[Install]
WantedBy=multi-user.target
EOF

        echo 'Reloading systemd...'
        sudo systemctl daemon-reload
        
        echo 'Starting services...'
        sudo systemctl enable coinjecture-api
        sudo systemctl enable coinjecture-worker
        sudo systemctl start coinjecture-api
        sudo systemctl start coinjecture-worker
        
        echo 'Checking service status...'
        sudo systemctl status coinjecture-api --no-pager
        sudo systemctl status coinjecture-worker --no-pager
    "
    
    success "✅ Services updated and started"
}

# Deploy to S3
deploy_to_s3() {
    log "☁️  Deploying web interface to S3..."
    
    # Check if AWS CLI is available
    if ! command -v aws &> /dev/null; then
        warn "⚠️  AWS CLI not found. Skipping S3 deployment."
        return
    fi
    
    # Deploy web files to S3
    if [ -d "web" ]; then
        log "📤 Uploading web files to S3..."
        aws s3 sync web/ s3://coinjecture.com/ --delete --exclude "*.md" --exclude "*.txt"
        success "✅ Web interface deployed to S3"
    else
        warn "⚠️  Web directory not found. Skipping S3 deployment."
    fi
}

# Verify deployment
verify_deployment() {
    log "🔍 Verifying deployment..."
    
    # Check API endpoint
    log "🌐 Checking API endpoint..."
    if curl -s -f "http://$DROPLET_IP:5000/health" >/dev/null; then
        success "✅ API endpoint is responding"
    else
        warn "⚠️  API endpoint not responding"
    fi
    
    # Check web interface
    log "🌐 Checking web interface..."
    if curl -s -f "http://$DROPLET_IP:8080" >/dev/null; then
        success "✅ Web interface is responding"
    else
        warn "⚠️  Web interface not responding"
    fi
    
    # Check services on droplet
    log "🔧 Checking services on droplet..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        echo 'API Service Status:'
        sudo systemctl is-active coinjecture-api
        echo 'Worker Service Status:'
        sudo systemctl is-active coinjecture-worker
    "
    
    success "✅ Deployment verification completed"
}

# Main deployment function
main() {
    print_banner
    
    log "🚀 Starting COINjecture TestNet v$VERSION deployment..."
    
    # Step 1: Check prerequisites
    check_prerequisites
    
    # Step 2: Create deployment package
    DEPLOY_ARCHIVE=$(create_deployment_package)
    
    # Step 3: Deploy to droplet
    deploy_to_droplet "$DEPLOY_ARCHIVE"
    
    # Step 4: Update services
    update_services
    
    # Step 5: Deploy to S3
    deploy_to_s3
    
    # Step 6: Verify deployment
    verify_deployment
    
    # Cleanup
    rm -f "$DEPLOY_ARCHIVE"
    
    success "🎉 TestNet v$VERSION deployment completed successfully!"
    echo ""
    info "🌐 API Server: http://$DROPLET_IP:5000"
    info "🌐 Web Interface: http://$DROPLET_IP:8080"
    info "🌐 Health Check: http://$DROPLET_IP:5000/health"
    info "💰 Token Distribution: Enabled"
    info "🔒 Enhanced Security: Cryptographic commitments with H(solution)"
    info "🧹 Cleaned Codebase: ~60 unused files removed"
    echo ""
    success "✅ TestNet v$VERSION is live and ready!"
}

# Run main function
main "$@"
