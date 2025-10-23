#!/usr/bin/env bash
set -euo pipefail

# COINjecture TestNet v3.10.0 Simple Deployment Script
# Uses rsync for direct deployment to avoid SCP issues

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
VERSION="3.10.0"

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

# Check prerequisites
check_prerequisites() {
    log "🔍 Checking prerequisites..."
    
    if [ ! -f "VERSION" ] || [ ! -f "src/cli.py" ]; then
        error "❌ Must be run from COINjecture project root directory"
        exit 1
    fi
    
    success "✅ Prerequisites check passed"
}

# Deploy using rsync
deploy_with_rsync() {
    log "🚀 Deploying to DigitalOcean droplet using rsync..."
    
    # Create backup on droplet
    log "💾 Creating backup on droplet..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        if [ -d '/home/coinjecture/$PROJECT_NAME' ]; then
            echo 'Creating backup...'
            sudo cp -r '/home/coinjecture/$PROJECT_NAME' '/home/coinjecture/${PROJECT_NAME}_backup_\$(date +%Y%m%d_%H%M%S)'
            echo 'Backup created'
        fi
    "
    
    # Stop services
    log "⏹️  Stopping services..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        sudo systemctl stop coinjecture-api || true
        sudo systemctl stop coinjecture-worker || true
    "
    
    # Deploy files using rsync
    log "📤 Deploying files with rsync..."
    rsync -avz --delete \
        --exclude='.git' \
        --exclude='data/blockchain/*' \
        --exclude='data/cache/*' \
        --exclude='logs/*' \
        --exclude='*.log' \
        --exclude='*.pid' \
        --exclude='.venv' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='.DS_Store' \
        --exclude='node_modules' \
        ./ "$DROPLET_USER@$DROPLET_IP:/home/coinjecture/$PROJECT_NAME/"
    
    # Set permissions
    log "🔧 Setting permissions..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME'
        sudo chown -R coinjecture:coinjecture .
        chmod +x scripts/*.sh
    "
    
    success "✅ Deployment completed"
}

# Update services
update_services() {
    log "🔄 Updating services..."
    
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME'
        
        # Update systemd services
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

        # Reload and start services
        sudo systemctl daemon-reload
        sudo systemctl enable coinjecture-api
        sudo systemctl enable coinjecture-worker
        sudo systemctl start coinjecture-api
        sudo systemctl start coinjecture-worker
        
        # Check status
        echo 'Service Status:'
        sudo systemctl is-active coinjecture-api
        sudo systemctl is-active coinjecture-worker
    "
    
    success "✅ Services updated"
}

# Deploy to S3
deploy_to_s3() {
    log "☁️  Deploying web interface to S3..."
    
    if command -v aws &> /dev/null && [ -d "web" ]; then
        aws s3 sync web/ s3://coinjecture.com/ --delete --exclude "*.md" --exclude "*.txt"
        success "✅ Web interface deployed to S3"
    else
        warn "⚠️  AWS CLI not found or web directory missing. Skipping S3 deployment."
    fi
}

# Verify deployment
verify_deployment() {
    log "🔍 Verifying deployment..."
    
    # Check API endpoint
    if curl -s -f "http://$DROPLET_IP:5000/health" >/dev/null 2>&1; then
        success "✅ API endpoint is responding"
    else
        warn "⚠️  API endpoint not responding"
    fi
    
    # Check web interface
    if curl -s -f "http://$DROPLET_IP:8080" >/dev/null 2>&1; then
        success "✅ Web interface is responding"
    else
        warn "⚠️  Web interface not responding"
    fi
    
    success "✅ Deployment verification completed"
}

# Main function
main() {
    echo -e "${BLUE}"
    echo "🚀 COINjecture TestNet v$VERSION Deployment"
    echo "🌐 Deploying to: $DROPLET_IP"
    echo "💰 Token Distribution & Cleaned Codebase"
    echo -e "${NC}"
    
    check_prerequisites
    deploy_with_rsync
    update_services
    deploy_to_s3
    verify_deployment
    
    success "🎉 TestNet v$VERSION deployment completed!"
    echo ""
    info "🌐 API Server: http://$DROPLET_IP:5000"
    info "🌐 Web Interface: http://$DROPLET_IP:8080"
    info "🌐 Health Check: http://$DROPLET_IP:5000/health"
    info "💰 Token Distribution: Enabled"
    info "🔒 Enhanced Security: Cryptographic commitments"
    info "🧹 Cleaned Codebase: ~60 unused files removed"
}

main "$@"
