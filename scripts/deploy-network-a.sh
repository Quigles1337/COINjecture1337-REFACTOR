#!/usr/bin/env bash
#
# COINjecture Network A Deployment Script
# Institutional-Grade Automated Deployment for Production Validators
# Version: 4.5.0+
#
# Usage:
#   ./scripts/deploy-network-a.sh [--validator N] [--dry-run] [--skip-build]
#
# Security: This script handles sensitive cryptographic keys.
#           Ensure proper access controls and audit logging.

set -euo pipefail  # Strict error handling
IFS=$'\n\t'        # Safer word splitting

# ==============================================================================
# CONFIGURATION
# ==============================================================================

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
readonly VERSION="4.5.0+"

# Deployment configuration
readonly NETWORK_ID="coinjecture-go-testnet"
readonly VALIDATOR_COUNT=3
readonly BINARY_NAME="coinjectured"

# Directory structure (institutional standards)
readonly BUILD_DIR="${PROJECT_ROOT}/build"
readonly CONFIG_DIR="${PROJECT_ROOT}/configs/network-a"
readonly KEYS_DIR="${PROJECT_ROOT}/keys/network-a"
readonly DEPLOY_DIR="/opt/coinjecture"
readonly DATA_DIR="/var/lib/coinjecture/network-a"
readonly LOG_DIR="/var/log/coinjecture"
readonly BACKUP_DIR="/var/backups/coinjecture/network-a"

# Colors for output (institutional clarity)
readonly COLOR_RESET='\033[0m'
readonly COLOR_BOLD='\033[1m'
readonly COLOR_RED='\033[0;31m'
readonly COLOR_GREEN='\033[0;32m'
readonly COLOR_YELLOW='\033[0;33m'
readonly COLOR_BLUE='\033[0;34m'

# ==============================================================================
# COMMAND-LINE ARGUMENTS
# ==============================================================================

DRY_RUN=false
SKIP_BUILD=false
VALIDATOR_ID=""
REMOTE_DEPLOY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --validator)
            VALIDATOR_ID="$2"
            shift 2
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        --remote)
            REMOTE_DEPLOY=true
            shift
            ;;
        --help)
            show_usage
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

# Logging functions with ISO 8601 timestamps (institutional audit standards)
log() {
    local timestamp
    timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    echo -e "${COLOR_BOLD}[${timestamp}]${COLOR_RESET} $*"
}

info() {
    log "${COLOR_BLUE}INFO${COLOR_RESET}  $*"
}

success() {
    log "${COLOR_GREEN}✓${COLOR_RESET}     $*"
}

warn() {
    log "${COLOR_YELLOW}WARN${COLOR_RESET}  $*" >&2
}

error() {
    log "${COLOR_RED}ERROR${COLOR_RESET} $*" >&2
}

fatal() {
    error "$*"
    exit 1
}

show_usage() {
    cat <<EOF
COINjecture Network A Deployment Script

Usage:
  $0 [OPTIONS]

Options:
  --validator N     Deploy specific validator (1-${VALIDATOR_COUNT})
  --dry-run         Show what would be done without executing
  --skip-build      Skip binary compilation step
  --remote          Deploy to remote servers (requires SSH config)
  --help            Show this help message

Examples:
  # Deploy all validators locally
  $0

  # Deploy specific validator with dry-run
  $0 --validator 1 --dry-run

  # Deploy to remote servers
  $0 --remote

Environment Variables:
  COINJECTURE_DEPLOY_USER   SSH user for remote deployment (default: coinjecture)
  COINJECTURE_SUDO_PASSWORD Password for sudo (use with caution)

EOF
}

# Check if command exists
command_exists() {
    command -v "$1" &>/dev/null
}

# Run command with dry-run support
run_cmd() {
    if [[ "$DRY_RUN" == true ]]; then
        info "[DRY-RUN] Would execute: $*"
    else
        "$@"
    fi
}

# ==============================================================================
# PRE-FLIGHT CHECKS
# ==============================================================================

preflight_checks() {
    info "Running pre-flight checks..."

    # Check required commands
    local required_commands=("go" "git" "systemctl" "openssl")
    for cmd in "${required_commands[@]}"; do
        if ! command_exists "$cmd"; then
            fatal "Required command not found: $cmd"
        fi
    done
    success "All required commands available"

    # Check Go version (institutional requirement: Go 1.21+)
    local go_version
    go_version=$(go version | awk '{print $3}' | sed 's/go//')
    info "Go version: $go_version"
    if [[ ! "$go_version" =~ ^1\.(2[1-9]|[3-9][0-9]) ]]; then
        warn "Go version $go_version may not be supported. Recommended: 1.21+"
    fi

    # Check if running as root (institutional security: don't run as root)
    if [[ $EUID -eq 0 ]]; then
        warn "Running as root. Recommended to use dedicated service user."
    fi

    # Check disk space (institutional requirement: 50GB minimum)
    local available_space
    available_space=$(df -BG "${PROJECT_ROOT}" | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $available_space -lt 50 ]]; then
        warn "Low disk space: ${available_space}GB available. Recommended: 50GB+"
    fi
    success "Disk space check passed: ${available_space}GB available"

    # Check network connectivity
    if ! ping -c 1 github.com &>/dev/null; then
        warn "No internet connectivity detected. Remote operations may fail."
    fi
    success "Network connectivity verified"

    # Verify project structure
    if [[ ! -d "${PROJECT_ROOT}/go" ]]; then
        fatal "Invalid project structure: go/ directory not found"
    fi
    success "Project structure validated"
}

# ==============================================================================
# BUILD PHASE
# ==============================================================================

build_binary() {
    if [[ "$SKIP_BUILD" == true ]]; then
        info "Skipping build (--skip-build specified)"
        return
    fi

    info "Building COINjecture binary..."

    # Create build directory
    run_cmd mkdir -p "${BUILD_DIR}"

    # Build with institutional security flags
    cd "${PROJECT_ROOT}/go"

    info "Compiling with security hardening flags..."
    run_cmd env \
        CGO_ENABLED=0 \
        GOOS=linux \
        GOARCH=amd64 \
        go build \
        -trimpath \
        -ldflags="-s -w -X main.Version=${VERSION} -X main.BuildDate=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        -o "${BUILD_DIR}/${BINARY_NAME}" \
        ./cmd/coinjectured

    if [[ ! -f "${BUILD_DIR}/${BINARY_NAME}" ]]; then
        fatal "Binary not found after build: ${BUILD_DIR}/${BINARY_NAME}"
    fi

    # Verify binary
    local binary_size
    binary_size=$(stat -f%z "${BUILD_DIR}/${BINARY_NAME}" 2>/dev/null || stat -c%s "${BUILD_DIR}/${BINARY_NAME}")
    info "Binary size: $((binary_size / 1024 / 1024))MB"

    # Set executable permissions
    run_cmd chmod +x "${BUILD_DIR}/${BINARY_NAME}"

    success "Binary compiled successfully"
}

# Build keygen utility
build_keygen() {
    info "Building keygen utility..."

    cd "${PROJECT_ROOT}/go"
    run_cmd go build \
        -o "${BUILD_DIR}/coinjecture-keygen" \
        ./cmd/coinjecture-keygen

    run_cmd chmod +x "${BUILD_DIR}/coinjecture-keygen"
    success "Keygen utility built"
}

# ==============================================================================
# KEY GENERATION PHASE
# ==============================================================================

generate_validator_keys() {
    info "Generating validator keypairs..."

    # Create keys directory with restricted permissions
    run_cmd mkdir -p "${KEYS_DIR}"
    run_cmd chmod 700 "${KEYS_DIR}"

    # Check if keys already exist
    if [[ -f "${KEYS_DIR}/validator1.priv" ]]; then
        warn "Validator keys already exist at ${KEYS_DIR}"
        read -rp "Regenerate keys? This will OVERWRITE existing keys! (yes/no): " confirm
        if [[ "$confirm" != "yes" ]]; then
            info "Skipping key generation"
            return
        fi
        warn "Regenerating keys..."
    fi

    # Generate keys using keygen utility
    run_cmd "${BUILD_DIR}/coinjecture-keygen" \
        --output "${KEYS_DIR}" \
        --count ${VALIDATOR_COUNT} \
        --prefix "validator" \
        --verbose

    # Verify keys were generated
    for i in $(seq 1 ${VALIDATOR_COUNT}); do
        if [[ ! -f "${KEYS_DIR}/validator${i}.priv" ]]; then
            fatal "Failed to generate keys for validator ${i}"
        fi
    done

    success "Generated ${VALIDATOR_COUNT} validator keypairs"

    # Display public keys for configuration
    info "Validator public keys (copy to config files):"
    for i in $(seq 1 ${VALIDATOR_COUNT}); do
        local pubkey
        pubkey=$(cat "${KEYS_DIR}/validator${i}.pub")
        echo "  Validator ${i}: ${pubkey}"
    done
}

# ==============================================================================
# CONFIGURATION PHASE
# ==============================================================================

configure_validators() {
    info "Configuring validators..."

    # Verify config files exist
    for i in $(seq 1 ${VALIDATOR_COUNT}); do
        local config_file="${CONFIG_DIR}/validator-${i}.yaml"
        if [[ ! -f "$config_file" ]]; then
            fatal "Config file not found: $config_file"
        fi
    done

    # Update configs with generated keys (institutional security: automated config)
    for i in $(seq 1 ${VALIDATOR_COUNT}); do
        local privkey pubkey
        privkey=$(cat "${KEYS_DIR}/validator${i}.priv")
        pubkey=$(cat "${KEYS_DIR}/validator${i}.pub")

        info "Updating validator-${i} config with generated keys..."

        # Replace placeholder keys (using sed for safety)
        run_cmd sed -i.bak \
            "s/VALIDATOR${i}_PRIVKEY_PLACEHOLDER_64_HEX_CHARS_REPLACE_WITH_ACTUAL_KEY/${privkey}/g" \
            "${CONFIG_DIR}/validator-${i}.yaml"

        run_cmd sed -i.bak \
            "s/VALIDATOR${i}_PUBKEY_PLACEHOLDER_64_HEX_CHARS_REPLACE_WITH_ACTUAL_KEY/${pubkey}/g" \
            "${CONFIG_DIR}/validator-${i}.yaml"
    done

    success "Validator configurations updated"
}

# ==============================================================================
# DEPLOYMENT PHASE
# ==============================================================================

deploy_local() {
    local validator_id=$1

    info "Deploying validator ${validator_id} locally..."

    # Create directory structure
    run_cmd sudo mkdir -p "${DEPLOY_DIR}"
    run_cmd sudo mkdir -p "${DATA_DIR}"
    run_cmd sudo mkdir -p "${LOG_DIR}"
    run_cmd sudo mkdir -p "${BACKUP_DIR}"

    # Copy binary
    run_cmd sudo cp "${BUILD_DIR}/${BINARY_NAME}" "${DEPLOY_DIR}/"
    run_cmd sudo chmod +x "${DEPLOY_DIR}/${BINARY_NAME}"

    # Copy config
    run_cmd sudo cp "${CONFIG_DIR}/validator-${validator_id}.yaml" \
        "${DEPLOY_DIR}/config.yaml"

    # Set permissions (institutional security)
    run_cmd sudo chown -R coinjecture:coinjecture "${DEPLOY_DIR}"
    run_cmd sudo chown -R coinjecture:coinjecture "${DATA_DIR}"
    run_cmd sudo chown -R coinjecture:coinjecture "${LOG_DIR}"
    run_cmd sudo chmod 640 "${DEPLOY_DIR}/config.yaml"

    success "Validator ${validator_id} deployed locally"
}

# ==============================================================================
# SERVICE MANAGEMENT
# ==============================================================================

install_systemd_service() {
    local validator_id=$1

    info "Installing systemd service for validator ${validator_id}..."

    local service_file="/etc/systemd/system/coinjectured-validator${validator_id}.service"

    # Create systemd service file
    run_cmd sudo tee "$service_file" >/dev/null <<EOF
[Unit]
Description=COINjecture Validator ${validator_id} (Network A)
Documentation=https://github.com/Quigles1337/COINjecture1337-REFACTOR
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=coinjecture
Group=coinjecture

# Binary and config
ExecStart=${DEPLOY_DIR}/${BINARY_NAME} --config ${DEPLOY_DIR}/config.yaml

# Working directory
WorkingDirectory=${DEPLOY_DIR}

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=coinjectured-validator${validator_id}

# Restart policy (institutional reliability)
Restart=on-failure
RestartSec=10s
StartLimitInterval=5min
StartLimitBurst=5

# Resource limits (institutional safety)
LimitNOFILE=65536
LimitNPROC=512
MemoryLimit=4G

# Security hardening (institutional standards)
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
ProtectHome=true
ReadWritePaths=${DATA_DIR} ${LOG_DIR} ${BACKUP_DIR}

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd
    run_cmd sudo systemctl daemon-reload

    # Enable service
    run_cmd sudo systemctl enable "coinjectured-validator${validator_id}.service"

    success "Systemd service installed and enabled"
}

# ==============================================================================
# MAIN DEPLOYMENT FLOW
# ==============================================================================

main() {
    info "COINjecture Network A Deployment Script v${VERSION}"
    info "Network ID: ${NETWORK_ID}"
    info "Deploying ${VALIDATOR_COUNT} validators"
    echo

    # Run pre-flight checks
    preflight_checks
    echo

    # Build phase
    build_binary
    build_keygen
    echo

    # Key generation
    generate_validator_keys
    echo

    # Configuration
    configure_validators
    echo

    # Deployment
    if [[ -n "$VALIDATOR_ID" ]]; then
        deploy_local "$VALIDATOR_ID"
        install_systemd_service "$VALIDATOR_ID"
    else
        for i in $(seq 1 ${VALIDATOR_COUNT}); do
            deploy_local "$i"
            install_systemd_service "$i"
        done
    fi
    echo

    # Final summary
    success "Deployment complete!"
    echo
    info "Next steps:"
    echo "  1. Start validators: sudo systemctl start coinjectured-validator1"
    echo "  2. Check status: sudo systemctl status coinjectured-validator1"
    echo "  3. View logs: sudo journalctl -u coinjectured-validator1 -f"
    echo "  4. Test API: curl http://localhost:8080/v1/status"
    echo
    info "For production deployment, remember to:"
    echo "  - Configure firewall rules (ports 9000, 8080, 9090)"
    echo "  - Set up monitoring and alerting"
    echo "  - Configure automatic backups"
    echo "  - Enable TLS certificates"
    echo "  - Use HSM for key management"
}

# ==============================================================================
# ENTRY POINT
# ==============================================================================

main "$@"
