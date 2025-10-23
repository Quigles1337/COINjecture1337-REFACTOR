#!/usr/bin/env bash
set -euo pipefail

# COINjecture Seamless Chain Recreation Script
# Uses existing genesis block and queues new blocks for recreation

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
GENESIS_HASH="d1700c2681b75c1d22ed08285994c202d310ff25cf40851365ca6fea22011358"

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
    echo "║         🔄 Seamless Chain Recreation with Existing Genesis                                ║"
    echo "║         🌐 Deploy to: $DROPLET_IP                                                          ║"
    echo "║         🔗 Genesis: $GENESIS_HASH                                                           ║"
    echo "║         📦 Queue: New blocks for recreation                                               ║"
    echo "║                                                                                            ║"
    echo "╚════════════════════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Create block queue system
create_block_queue_system() {
    log "📦 Creating block queue system..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME'
        
        # Create block queue directory
        mkdir -p data/block_queue
        
        # Create queue management script
        cat > block_queue_manager.py << 'EOF'
import sys
sys.path.append('src')
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any

class BlockQueueManager:
    def __init__(self, queue_dir: str = 'data/block_queue'):
        self.queue_dir = queue_dir
        os.makedirs(queue_dir, exist_ok=True)
        self.queue_file = os.path.join(queue_dir, 'pending_blocks.json')
        self.processed_file = os.path.join(queue_dir, 'processed_blocks.json')
    
    def queue_block(self, block_data: Dict[str, Any]) -> bool:
        \"\"\"Queue a new block for processing.\"\"\"
        try:
            # Load existing queue
            queue = self.load_queue()
            
            # Add block to queue
            block_data['queued_at'] = time.time()
            block_data['queued_timestamp'] = datetime.now().isoformat()
            queue.append(block_data)
            
            # Save queue
            self.save_queue(queue)
            
            print(f'Block {block_data.get(\"block_index\", \"unknown\")} queued for recreation')
            return True
        except Exception as e:
            print(f'Error queueing block: {e}')
            return False
    
    def load_queue(self) -> List[Dict[str, Any]]:
        \"\"\"Load pending blocks queue.\"\"\"
        if os.path.exists(self.queue_file):
            with open(self.queue_file, 'r') as f:
                return json.load(f)
        return []
    
    def save_queue(self, queue: List[Dict[str, Any]]) -> None:
        \"\"\"Save pending blocks queue.\"\"\"
        with open(self.queue_file, 'w') as f:
            json.dump(queue, f, indent=2)
    
    def get_queue_size(self) -> int:
        \"\"\"Get number of blocks in queue.\"\"\"
        return len(self.load_queue())
    
    def get_queue_summary(self) -> Dict[str, Any]:
        \"\"\"Get queue summary.\"\"\"
        queue = self.load_queue()
        if not queue:
            return {'size': 0, 'oldest': None, 'newest': None}
        
        return {
            'size': len(queue),
            'oldest': min(queue, key=lambda x: x.get('block_index', 0)),
            'newest': max(queue, key=lambda x: x.get('block_index', 0))
        }

# Global queue manager instance
queue_manager = BlockQueueManager()

def queue_new_block(block_data: Dict[str, Any]) -> bool:
    \"\"\"Queue a new block for recreation.\"\"\"
    return queue_manager.queue_block(block_data)

def get_queue_status() -> Dict[str, Any]:
    \"\"\"Get queue status.\"\"\"
    return queue_manager.get_queue_summary()
EOF

        echo 'Block queue system created'
    "
    success "✅ Block queue system created"
}

# Modify API to queue blocks instead of processing them
modify_api_for_queueing() {
    log "🔧 Modifying API to queue blocks instead of processing them..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME'
        
        # Create modified API that queues blocks
        cat > src/api/faucet_server_queued.py << 'EOF'
#!/usr/bin/env python3
\"\"\"
COINjecture Faucet API Server with Block Queueing
Modified to queue blocks instead of processing them for chain recreation
\"\"\"

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json
import time
import logging
from datetime import datetime

# Import our modules
from api.cache_manager import CacheManager
from api.ingest_store import IngestStore
from api.schema import BlockEvent, TelemetryEvent
from api.auth import AuthManager
from api.user_auth import UserAuthManager
from api.user_registration import UserRegistrationManager
from api.problem_endpoints import ProblemEndpoints
from api.health_monitor_api import HealthMonitorAPI

# Import block queue manager
sys.path.append('src')
from block_queue_manager import queue_new_block, get_queue_status

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class QueuedFaucetServer:
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        
        # Initialize components
        self.cache_manager = CacheManager()
        self.ingest_store = IngestStore()
        self.auth_manager = AuthManager()
        self.user_auth = UserAuthManager()
        self.user_registration = UserRegistrationManager()
        self.problem_endpoints = ProblemEndpoints()
        self.health_monitor = HealthMonitorAPI()
        
        # Rate limiting
        self.limiter = Limiter(
            self.app,
            key_func=get_remote_address,
            default_limits=['1000 per hour']
        )
        
        self.setup_routes()
    
    def setup_routes(self):
        \"\"\"Setup API routes.\"\"\"
        
        @self.app.route('/health', methods=['GET'])
        def health_check():
            \"\"\"Health check endpoint.\"\"\"
            try:
                cache_status = self.cache_manager.get_cache_status()
                queue_status = get_queue_status()
                
                return jsonify({
                    'status': 'healthy',
                    'timestamp': time.time(),
                    'cache': cache_status,
                    'queue': queue_status
                })
            except Exception as e:
                return jsonify({'status': 'unhealthy', 'error': str(e)}), 500
        
        @self.app.route('/v1/data/block/latest', methods=['GET'])
        def get_latest_block():
            \"\"\"Get latest block data (from cache).\"\"\"
            try:
                block_data = self.cache_manager.get_latest_block()
                return jsonify({
                    'status': 'success',
                    'data': block_data,
                    'meta': {
                        'api_version': 'v1',
                        'cached_at': time.time()
                    }
                })
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/v1/ingest/block', methods=['POST'])
        def ingest_block():
            \"\"\"Queue new blocks instead of processing them.\"\"\"
            try:
                payload = request.get_json(force=True, silent=False) or {}
                
                # Queue the block for recreation
                success = queue_new_block(payload)
                
                if success:
                    return jsonify({
                        'status': 'queued',
                        'message': 'Block queued for chain recreation',
                        'block_index': payload.get('block_index', 'unknown')
                    }), 202
                else:
                    return jsonify({
                        'status': 'error',
                        'message': 'Failed to queue block'
                    }), 500
                    
            except Exception as e:
                logger.error(f'Error queueing block: {e}')
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        @self.app.route('/v1/queue/status', methods=['GET'])
        def get_queue_status_endpoint():
            \"\"\"Get block queue status.\"\"\"
            try:
                status = get_queue_status()
                return jsonify({
                    'status': 'success',
                    'queue': status
                })
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
        
        # Keep other endpoints as they were
        @self.app.route('/v1/data/blocks/history', methods=['GET'])
        def get_blocks_history():
            try:
                limit = request.args.get('limit', default=100, type=int)
                data = self.cache_manager.get_blocks_history(limit=limit)
                return jsonify({
                    'status': 'success',
                    'data': data,
                    'meta': {
                        'api_version': 'v1',
                        'cached_at': time.time()
                    }
                })
            except Exception as e:
                return jsonify({'status': 'error', 'message': str(e)}), 500
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        \"\"\"Run the Flask application.\"\"\"
        logger.info(f'Starting COINjecture Faucet API Server with Block Queueing')
        logger.info(f'Server will run on {host}:{port}')
        self.app.run(host=host, port=port, debug=debug)

if __name__ == '__main__':
    server = QueuedFaucetServer()
    server.run()
EOF

        echo 'Modified API created'
    "
    success "✅ Modified API created"
}

# Initialize chain with existing genesis block
initialize_chain_with_genesis() {
    log "🏗️  Initializing chain with existing genesis block..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME'
        
        # Create chain with existing genesis block
        python3 -c \"
import sys
sys.path.append('src')
from tokenomics.blockchain_state import BlockchainState
import json
import os

# Create data directory
os.makedirs('data', exist_ok=True)
os.makedirs('data/cache', exist_ok=True)

# Initialize blockchain state
blockchain_state = BlockchainState()
blockchain_state.save_state('data/blockchain_state.json')

# Create genesis block with existing hash
genesis_info = {
    'index': 0,
    'block_hash': '$GENESIS_HASH',
    'timestamp': 1700000000.0,
    'previous_hash': '0000000000000000000000000000000000000000000000000000000000000000',
    'miner_address': 'GENESIS',
    'work_score': 0.0,
    'merkle_root': '0000000000000000000000000000000000000000000000000000000000000000',
    'capacity': 'genesis',
    'offchain_cid': 'genesis'
}

# Save genesis block
with open('data/cache/latest_block.json', 'w') as f:
    json.dump(genesis_info, f, indent=2)

# Create blocks history with genesis
with open('data/cache/blocks_history.json', 'w') as f:
    json.dump([genesis_info], f, indent=2)

print('Chain initialized with existing genesis block')
print('Genesis block:', genesis_info['block_hash'])
\"
    "
    success "✅ Chain initialized with existing genesis block"
}

# Update systemd service to use queued API
update_systemd_service() {
    log "⚙️  Updating systemd service to use queued API..."
    ssh "$DROPLET_USER@$DROPLET_IP" "
        cd '/home/coinjecture/$PROJECT_NAME'
        
        # Update systemd service
        sudo tee /etc/systemd/system/coinjecture-api.service > /dev/null << 'EOF'
[Unit]
Description=COINjecture API Server with Block Queueing
After=network.target

[Service]
Type=simple
User=coinjecture
WorkingDirectory=/home/coinjecture/COINjecture
ExecStart=/home/coinjecture/COINjecture/venv/bin/python src/api/faucet_server_queued.py
Restart=always
RestartSec=5
Environment=PYTHONPATH=/home/coinjecture/COINjecture/src

[Install]
WantedBy=multi-user.target
EOF

        # Reload systemd
        sudo systemctl daemon-reload
        
        echo 'Systemd service updated'
    "
    success "✅ Systemd service updated"
}

# Start services with queued API
start_queued_services() {
    log "🚀 Starting services with queued API..."
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
    success "✅ Services started with queued API"
}

# Verify seamless integration
verify_seamless_integration() {
    log "🔍 Verifying seamless integration..."
    
    # Wait for services to start
    sleep 10
    
    # Check API health
    if curl -s -f "http://$DROPLET_IP:5000/health" >/dev/null; then
        success "✅ API is responding"
    else
        error "❌ API not responding"
        return 1
    fi
    
    # Check latest block (should be genesis)
    LATEST_BLOCK=$(curl -s "http://$DROPLET_IP:5000/v1/data/block/latest" | jq -r '.data.index // "unknown"')
    
    if [ "$LATEST_BLOCK" = "0" ]; then
        success "✅ Chain started from genesis block (index: $LATEST_BLOCK)"
    else
        warn "⚠️  Block index is $LATEST_BLOCK (expected 0 for genesis)"
    fi
    
    # Check queue status
    QUEUE_STATUS=$(curl -s "http://$DROPLET_IP:5000/v1/queue/status" | jq -r '.queue.size // "unknown"')
    
    if [ "$QUEUE_STATUS" != "unknown" ]; then
        success "✅ Block queue is active (size: $QUEUE_STATUS)"
    else
        warn "⚠️  Could not get queue status"
    fi
    
    success "✅ Seamless integration verification completed"
}

# Main function
main() {
    print_banner
    
    log "🔄 Starting COINjecture seamless chain recreation..."
    
    # Step 1: Create block queue system
    create_block_queue_system
    
    # Step 2: Modify API to queue blocks
    modify_api_for_queueing
    
    # Step 3: Initialize chain with existing genesis
    initialize_chain_with_genesis
    
    # Step 4: Update systemd service
    update_systemd_service
    
    # Step 5: Start services with queued API
    start_queued_services
    
    # Step 6: Verify seamless integration
    verify_seamless_integration
    
    success "🎉 Seamless chain recreation completed!"
    echo ""
    info "🌐 API Server: http://$DROPLET_IP:5000"
    info "🌐 Health Check: http://$DROPLET_IP:5000/health"
    info "🌐 Queue Status: http://$DROPLET_IP:5000/v1/queue/status"
    info "🔗 Genesis: $GENESIS_HASH"
    info "📦 Queue: New blocks are being queued for recreation"
    info "🔄 Process: Chain recreation can now begin"
    echo ""
    success "✅ Seamless integration is ready!"
}

# Run main function
main "$@"
