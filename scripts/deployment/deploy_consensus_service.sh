#!/bin/bash

# COINjecture Consensus Service Deployment Script
# Processes block events into actual blockchain blocks

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." &>/dev/null && pwd)"
VENV_DIR="$PROJECT_ROOT/.venv"
LOGS_DIR="$PROJECT_ROOT/logs"
PID_FILE="$PROJECT_ROOT/consensus_service.pid"
LOG_FILE="$LOGS_DIR/consensus_service.log"

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
    echo "║         🔄 Consensus Service Deployment                                                    ║"
    echo "║         📊 Process block events into blockchain blocks                                   ║"
    echo "║         ⛏️  Enable blockchain growth and consensus                                         ║"
    echo "║                                                                                            ║"
    echo "╚════════════════════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

check_requirements() {
    log "Checking system requirements..."
    
    # Check Python version
    if ! command -v python3 &> /dev/null; then
        error "Python 3 is required but not installed"
        exit 1
    fi
    
    python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ $(echo "$python_version < 3.9" | bc -l) -eq 1 ]]; then
        error "Python 3.9+ is required, found $python_version"
        exit 1
    fi
    
    log "✅ Python $python_version detected"
}

setup_environment() {
    log "Setting up Python virtual environment..."
    
    if [ ! -d "$VENV_DIR" ]; then
        python3 -m venv "$VENV_DIR"
        log "✅ Virtual environment created"
    else
        log "✅ Virtual environment already exists"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    log "✅ Virtual environment activated"
    
    # Install dependencies
    log "Installing Python dependencies..."
    pip install -q -r "$PROJECT_ROOT/requirements.txt"
    log "✅ Dependencies installed from requirements.txt"
}

create_directories() {
    log "Creating data directories..."
    mkdir -p "$LOGS_DIR"
    mkdir -p "$PROJECT_ROOT/data"
    log "✅ Directories created: data, logs"
}

start_consensus_service() {
    log "Starting consensus service..."
    
    # Change to project root
    cd "$PROJECT_ROOT"
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Start consensus service
    nohup python3 scripts/consensus/start_consensus_service.py > "$LOG_FILE" 2>&1 &
    
    # Save PID
    echo $! > "$PID_FILE"
    
    # Wait a moment for startup
    sleep 3
    
    # Check if process is running
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        log "✅ Consensus service started (PID: $(cat "$PID_FILE"))"
        log "📊 View logs: tail -f $LOG_FILE"
        log "🔄 Processing block events into blockchain blocks"
    else
        error "Failed to start consensus service"
        return 1
    fi
}

stop_consensus_service() {
    log "Stopping consensus service..."
    
    if [ -f "$PID_FILE" ]; then
        pid=$(cat "$PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                kill -9 "$pid"
            fi
        fi
        rm -f "$PID_FILE"
    fi
    
    log "✅ Consensus service stopped"
}

status_consensus_service() {
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
        log "✅ Consensus service is running (PID: $(cat "$PID_FILE"))"
        return 0
    else
        log "❌ Consensus service is not running"
        return 1
    fi
}

show_logs() {
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        error "Log file not found: $LOG_FILE"
        exit 1
    fi
}

# Main script logic
case "${1:-start}" in
    start)
        print_banner
        check_requirements
        setup_environment
        create_directories
        start_consensus_service
        log "🚀 Consensus service deployment complete!"
        log "💡 Run '$0 status' to check status"
        log "💡 Run '$0 logs' to view activity"
        ;;
    stop)
        stop_consensus_service
        ;;
    restart)
        stop_consensus_service
        sleep 2
        start_consensus_service
        ;;
    status)
        status_consensus_service
        ;;
    logs)
        show_logs
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs}"
        exit 1
        ;;
esac
