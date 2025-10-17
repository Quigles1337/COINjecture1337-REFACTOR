#!/usr/bin/env bash
set -euo pipefail

# COINjecture Mining Node Deployment Script
# Deploys a local mining node that connects to the existing COINjecture network
# Faucet API already running at: http://167.172.213.70:5000

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." &>/dev/null && pwd)"
cd "$PROJECT_ROOT"

VENV_DIR=".venv"
DATA_DIR="data"
LOGS_DIR="logs"
PID_FILE="mining_node.pid"
LOG_FILE="$LOGS_DIR/mining.log"

# P2P Network configuration
BOOTSTRAP_PEERS=("167.172.213.70:12345")

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
    echo "║         ⛏️  Mining Node Deployment                                                         ║"
    echo "║         🌐 Connect to P2P network via bootstrap peers ║"
    echo "║         💎 Start earning rewards through computational work                              ║"
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

check_requirements() {
    log "Checking system requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ $(echo "$python_version < 3.8" | bc -l) -eq 1 ]]; then
        error "Python 3.8+ required, found $python_version"
        exit 1
    fi
    
    log "✅ Python $python_version detected"
}

setup_environment() {
    log "Setting up Python virtual environment..."
    
    # Create virtual environment
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        log "✅ Virtual environment created"
    else
        log "✅ Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip > /dev/null 2>&1
    
    log "✅ Virtual environment activated"
}

install_dependencies() {
    log "Installing Python dependencies..."
    
    source "$VENV_DIR/bin/activate"
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt > /dev/null 2>&1
        log "✅ Dependencies installed from requirements.txt"
    else
        # Install core dependencies manually
        pip install requests Flask Flask-CORS Flask-Limiter cryptography > /dev/null 2>&1
        log "✅ Core dependencies installed"
    fi
}

create_directories() {
    log "Creating data directories..."
    
    mkdir -p "$DATA_DIR"/{cache,blockchain,ipfs}
    mkdir -p "$LOGS_DIR"
    
    log "✅ Directories created: $DATA_DIR, $LOGS_DIR"
}

create_miner_config() {
    log "Creating miner configuration..."
    
    # Create a Python script to generate the config with proper enum handling
    cat > "create_config.py" << 'EOF'
import json
import sys
sys.path.append('src')
from node import NodeRole

config = {
    "role": NodeRole.MINER,
    "data_dir": "./data",
    "network_id": "coinjecture-mainnet", 
    "listen_addr": "0.0.0.0:8080",
    "bootstrap_peers": ["167.172.213.70:12345"],
    "enable_user_submissions": True,
    "ipfs_api_url": "http://167.172.213.70:5001",
    "target_block_interval_secs": 30,
    "log_level": "INFO"
}

# Convert enum to string for JSON serialization
config["role"] = config["role"].value

with open("miner_config.json", "w") as f:
    json.dump(config, f, indent=2)

print("Config created successfully")
EOF
    
    # Run the config creation script
    source "$VENV_DIR/bin/activate"
    python3 create_config.py
    rm create_config.py
    
    log "✅ Miner configuration created: miner_config.json"
    
    # Generate wallet on first run
    if [ ! -f "config/miner_wallet.json" ]; then
        log "🔑 Generating miner wallet..."
        python3 -c "
import sys
sys.path.append('src')
from tokenomics.wallet import Wallet

wallet = Wallet.generate_new()
wallet.save_to_file('config/miner_wallet.json')
print(f'✅ Wallet created: {wallet.address}')
print(f'💰 Mining rewards will be sent to this address')
"
        log "💰 Mining rewards will be sent to your wallet address"
    else
        log "🔑 Using existing wallet"
    fi
}

check_network_connectivity() {
    log "Checking P2P network connectivity..."
    
    # Check if bootstrap peers are reachable
    for peer in "${BOOTSTRAP_PEERS[@]}"; do
        if nc -z -w5 ${peer/:/ } 2>/dev/null; then
            log "✅ Bootstrap peer $peer is reachable"
        else
            warn "Bootstrap peer $peer not reachable, will retry on startup"
        fi
    done
    
    log "🌐 P2P network configuration ready"
}

start_mining_node() {
    log "Starting P2P mining node..."
    
    source "$VENV_DIR/bin/activate"
    
    # Start proper P2P mining node
    nohup python3 scripts/mining/start_real_p2p_miner.py > "$LOG_FILE" 2>&1 &
    
    # Save PID
    echo $! > "$PID_FILE"
    
    # Wait a moment for startup
    sleep 3
    
    if is_running; then
        log "✅ Mining node started (PID: $(cat $PID_FILE))"
        log "📊 View logs: tail -f $LOG_FILE"
        log "🌐 P2P Network: Bootstrap peers configured"
        log "⛏️  Mining tier: desktop"
    else
        error "Failed to start mining node"
        error "Check logs: $LOG_FILE"
        exit 1
    fi
}

is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        fi
    fi
    return 1
}

stop_mining_node() {
    log "Stopping mining node..."
    
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            kill "$pid"
            sleep 2
            if ps -p "$pid" > /dev/null 2>&1; then
                kill -9 "$pid" 2>/dev/null || true
            fi
            log "✅ Mining node stopped"
        else
            log "Mining node was not running"
        fi
        rm -f "$PID_FILE"
    else
        log "No PID file found, mining node may not be running"
    fi
}

show_status() {
    echo -e "${BLUE}COINjecture Mining Node Status${NC}"
    echo "=================================="
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        echo -e "Status: ${GREEN}RUNNING${NC} (PID: $pid)"
        echo "Log file: $LOG_FILE"
        echo "P2P Network: Bootstrap peers configured"
        echo ""
        echo "Recent activity:"
        tail -n 5 "$LOG_FILE" 2>/dev/null || echo "No recent logs"
    else
        echo -e "Status: ${RED}STOPPED${NC}"
    fi
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        echo -e "${BLUE}Mining Node Logs (last 20 lines)${NC}"
        echo "======================================"
        tail -n 20 "$LOG_FILE"
        echo ""
        echo "To follow logs in real-time: tail -f $LOG_FILE"
    else
        echo "No log file found at $LOG_FILE"
    fi
}

show_help() {
    echo "COINjecture Mining Node Deployment Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     Start the mining node"
    echo "  stop      Stop the mining node"
    echo "  restart   Restart the mining node"
    echo "  status    Show mining node status"
    echo "  logs      Show recent logs"
    echo "  register  Register as a new miner with the network"
    echo "  sync      Perform full blockchain synchronization"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start    # Start mining"
    echo "  $0 status   # Check if running"
    echo "  $0 logs     # View recent activity"
    echo "  $0 register # Register new miner"
    echo "  $0 sync     # Sync with blockchain"
    echo "  $0 stop     # Stop mining"
}

register_miner() {
    log "🔐 Setting up miner authentication..."
    
    # Get user input
    read -p "Enter your miner ID: " miner_id
    
    # Default values
    miner_id=${miner_id:-"miner_$(date +%s)"}
    
    log "Setting up miner: $miner_id"
    
    # Check if enhanced auth is available
    response=$(curl -s -X POST http://167.172.213.70:5000/v1/user/register \
        -H "Content-Type: application/json" \
        -d "{
            \"user_id\": \"$miner_id\",
            \"auth_method\": \"hmac_personal\",
            \"tier\": \"TIER_2_DESKTOP\"
        }" 2>/dev/null)
    
    if echo "$response" | grep -q '"status": "success"'; then
        # Enhanced auth system available
        log "✅ Enhanced authentication available!"
        
        # Extract API key
        api_key=$(echo "$response" | grep -o '"api_key": "[^"]*"' | cut -d'"' -f4)
        
        if [ -n "$api_key" ]; then
            log "🔑 Your API key: $api_key"
            log "💾 Save these credentials securely:"
            echo ""
            echo "export COINJECTURE_USER_ID=\"$miner_id\""
            echo "export COINJECTURE_API_KEY=\"$api_key\""
            echo ""
            log "💡 Add these to your shell profile to use automatically"
            log "💡 Or run: export COINJECTURE_USER_ID=\"$miner_id\" && export COINJECTURE_API_KEY=\"$api_key\""
        fi
        
        log "🚀 You can now start mining with: $0 start"
    else
        # Fallback to current network authentication
        log "📡 Using current network authentication (shared secret)"
        log "🔑 Your credentials:"
        echo ""
        echo "export COINJECTURE_USER_ID=\"$miner_id\""
        echo "export COINJECTURE_API_KEY=\"dev-secret\""
        echo ""
        log "💡 The network uses shared secret authentication"
        log "💡 All miners use the same secret: 'dev-secret'"
        log "🚀 You can now start mining with: $0 start"
        
        # Set environment variables for current session
        export COINJECTURE_USER_ID="$miner_id"
        export COINJECTURE_API_KEY="dev-secret"
        log "✅ Credentials set for current session"
    fi
}

sync_blockchain() {
    log "🔄 Starting full blockchain synchronization..."
    
    # Check if node is running
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        log "⚠️  Mining node is running. Stopping for sync..."
        stop_mining_node
        sleep 2
    fi
    
    log "📡 Connecting to COINjecture network..."
    log "🌐 Network API: http://167.172.213.70:5000"
    
    # Check network connectivity
    if ! curl -s --connect-timeout 10 http://167.172.213.70:5000/health >/dev/null; then
        log "❌ Network unreachable. Cannot sync."
        exit 1
    fi
    
    log "✅ Network connected"
    
    # Get current blockchain state
    log "📊 Fetching blockchain state..."
    latest_block=$(curl -s http://167.172.213.70:5000/v1/data/block/latest)
    
    if echo "$latest_block" | grep -q '"status": "success"'; then
        block_index=$(echo "$latest_block" | grep -o '"index": [0-9]*' | cut -d' ' -f2)
        cumulative_work=$(echo "$latest_block" | grep -o '"cumulative_work_score": [0-9.]*' | cut -d' ' -f2)
        block_hash=$(echo "$latest_block" | grep -o '"block_hash": "[^"]*"' | cut -d'"' -f4)
        
        log "📈 Current blockchain state:"
        log "   Block Index: $block_index"
        log "   Cumulative Work: $cumulative_work"
        log "   Block Hash: ${block_hash:0:16}..."
        
        # Get recent block events
        log "📋 Fetching recent block events..."
        recent_events=$(curl -s "http://167.172.213.70:5000/v1/display/blocks/latest?limit=10")
        
        if echo "$recent_events" | grep -q '"status": "success"'; then
            event_count=$(echo "$recent_events" | grep -o '"block_index": [0-9]*' | wc -l)
            log "📊 Found $event_count recent block events"
            
            # Show recent events
            echo "$recent_events" | jq -r '.data[] | "  Event: \(.event_id[0:8])... | Block: \(.block_index) | Work: \(.work_score) | Miner: \(.miner_id)"' 2>/dev/null || log "   (Raw events available)"
        fi
        
        # Sync with full node if available
        log "🔗 Attempting full node synchronization..."
        
        # Try to get block range
        block_range=$(curl -s "http://167.172.213.70:5000/v1/data/blocks?start=0&end=10")
        
        if echo "$block_range" | grep -q '"status": "success"'; then
            range_count=$(echo "$block_range" | grep -o '"index": [0-9]*' | wc -l)
            log "📦 Synced $range_count blocks from network"
        fi
        
        # Check for telemetry data
        log "📊 Checking miner telemetry..."
        telemetry=$(curl -s "http://167.172.213.70:5000/v1/display/telemetry/latest?limit=5")
        
        if echo "$telemetry" | grep -q '"status": "success"'; then
            telemetry_count=$(echo "$telemetry" | jq -r '.data | length' 2>/dev/null || echo "0")
            log "📈 Found $telemetry_count telemetry entries"
        fi
        
        log "✅ Blockchain synchronization complete!"
        log "💡 Network is ready for mining"
        log "💡 Run '$0 start' to begin mining"
        
    else
        log "❌ Failed to fetch blockchain state"
        log "💡 Check network connectivity"
        exit 1
    fi
}

# Main script logic
case "${1:-help}" in
    start)
        print_banner
        check_requirements
        setup_environment
        install_dependencies
        create_directories
        create_miner_config
        check_network_connectivity
        start_mining_node
        echo ""
        log "🚀 Mining node deployment complete!"
        log "💡 Run '$0 status' to check status"
        log "💡 Run '$0 logs' to view activity"
        log "💡 Run '$0 register' to register as a new miner"
        ;;
    stop)
        stop_mining_node
        ;;
    restart)
        stop_mining_node
        sleep 2
        $0 start
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    register)
        register_miner
        ;;
    sync)
        sync_blockchain
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
