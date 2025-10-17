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
cd "$SCRIPT_DIR"

VENV_DIR=".venv"
DATA_DIR="data"
LOGS_DIR="logs"
PID_FILE="mining_node.pid"
LOG_FILE="$LOGS_DIR/mining.log"

# Network configuration
NETWORK_API_URL="http://167.172.213.70:5000"
BOOTSTRAP_PEERS=("167.172.213.70:8080")

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
    echo "║         🌐 Connect to existing network: $NETWORK_API_URL ║"
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
    "bootstrap_peers": ["167.172.213.70:8080"],
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
}

check_network_connectivity() {
    log "Checking network connectivity..."
    
    if curl -s --connect-timeout 10 "$NETWORK_API_URL/health" > /dev/null; then
        log "✅ Network API is accessible at $NETWORK_API_URL"
    else
        warn "Network API not accessible, mining will start in offline mode"
    fi
}

start_mining_node() {
    log "Starting mining node..."
    
    source "$VENV_DIR/bin/activate"
    
    # Start mining node in background with tier parameter
    nohup python3 -c "
import sys
sys.path.append('src')
from cli import COINjectureCLI
cli = COINjectureCLI()
cli.run(['mine', '--config', 'miner_config.json', '--tier', 'desktop', '--problem-type', 'subset_sum'])
" > "$LOG_FILE" 2>&1 &
    
    # Save PID
    echo $! > "$PID_FILE"
    
    # Wait a moment for startup
    sleep 3
    
    if is_running; then
        log "✅ Mining node started (PID: $(cat $PID_FILE))"
        log "📊 View logs: tail -f $LOG_FILE"
        log "🌐 Network API: $NETWORK_API_URL"
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
        echo "Network API: $NETWORK_API_URL"
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
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start    # Start mining"
    echo "  $0 status   # Check if running"
    echo "  $0 logs     # View recent activity"
    echo "  $0 stop     # Stop mining"
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
    help|--help|-h)
        show_help
        ;;
    *)
        error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
