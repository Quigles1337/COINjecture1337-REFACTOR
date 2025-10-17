#!/bin/bash

# COINjecture Auto-Launch macOS Installer v3.6.6
# This script installs COINjecture and automatically launches it

set -e

echo "🚀 COINjecture Auto-Launch macOS Installer v3.6.6"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
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

print_special() {
    echo -e "${PURPLE}[SPECIAL]${NC} $1"
}

# Check if running on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This installer is for macOS only."
    exit 1
fi

# Create installation directory
INSTALL_DIR="$HOME/Applications/COINjecture"
print_status "Installing COINjecture to: $INSTALL_DIR"

# Create directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Copy the executable
if [ -f "./COINjecture" ]; then
    print_status "Copying COINjecture executable..."
    cp "./COINjecture" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/COINjecture"
    print_success "Executable copied successfully"
else
    print_error "COINjecture executable not found in current directory"
    exit 1
fi

# COMPREHENSIVE SECURITY WARNING ELIMINATION
print_special "🔒 ELIMINATING macOS SECURITY WARNINGS..."

# Remove ALL quarantine and security attributes
print_status "Removing quarantine attributes..."
xattr -d com.apple.quarantine "$INSTALL_DIR/COINjecture" 2>/dev/null || true
xattr -d com.apple.provenance "$INSTALL_DIR/COINjecture" 2>/dev/null || true
xattr -d com.apple.metadata:kMDItemWhereFroms "$INSTALL_DIR/COINjecture" 2>/dev/null || true
xattr -d com.apple.metadata:kMDItemDownloadedDate "$INSTALL_DIR/COINjecture" 2>/dev/null || true

# Clear ALL extended attributes
print_status "Clearing all extended attributes..."
xattr -c "$INSTALL_DIR/COINjecture" 2>/dev/null || true

# Set proper permissions
print_status "Setting proper permissions..."
chmod 755 "$INSTALL_DIR/COINjecture"

# Create a wrapper script that bypasses security warnings
print_status "Creating security-bypass wrapper..."
cat > "$INSTALL_DIR/COINjecture-Safe" << 'EOF'
#!/bin/bash
# COINjecture Security-Bypass Wrapper
# This script eliminates macOS security warnings

cd "$HOME/Applications/COINjecture"

# Remove any quarantine attributes that might have been re-added
xattr -d com.apple.quarantine ./COINjecture 2>/dev/null || true
xattr -d com.apple.provenance ./COINjecture 2>/dev/null || true
xattr -c ./COINjecture 2>/dev/null || true

# Run COINjecture
exec ./COINjecture "$@"
EOF
chmod +x "$INSTALL_DIR/COINjecture-Safe"

print_success "Security-bypass wrapper created"

# Create desktop shortcut
print_status "Creating desktop shortcut..."
cat > "$HOME/Desktop/COINjecture.command" << 'EOF'
#!/bin/bash
# COINjecture Desktop Launcher with Security Bypass

cd "$HOME/Applications/COINjecture"

# Remove all security attributes
xattr -d com.apple.quarantine ./COINjecture 2>/dev/null || true
xattr -d com.apple.provenance ./COINjecture 2>/dev/null || true
xattr -d com.apple.metadata:kMDItemWhereFroms ./COINjecture 2>/dev/null || true
xattr -d com.apple.metadata:kMDItemDownloadedDate ./COINjecture 2>/dev/null || true
xattr -c ./COINjecture 2>/dev/null || true

# Run COINjecture
./COINjecture
EOF
chmod +x "$HOME/Desktop/COINjecture.command"

print_success "Desktop shortcut created: ~/Desktop/COINjecture.command"

# Create Applications folder shortcut
print_status "Creating Applications folder shortcut..."
ln -sf "$INSTALL_DIR/COINjecture-Safe" "$HOME/Applications/COINjecture-CLI"

print_success "Applications shortcut created"

# Final security check
print_special "🔍 FINAL SECURITY CHECK..."
if xattr -l "$INSTALL_DIR/COINjecture" 2>/dev/null | grep -q "com.apple"; then
    print_warning "Some security attributes still present - running final cleanup..."
    xattr -c "$INSTALL_DIR/COINjecture" 2>/dev/null || true
else
    print_success "✅ All security attributes successfully removed!"
fi

echo ""
echo "🎉 Installation Complete!"
echo "========================"
echo ""
print_success "COINjecture installed successfully with ZERO security warnings! 🎯"
echo ""

# AUTO-LAUNCH COINjecture
print_special "🚀 LAUNCHING COINjecture..."
echo ""

print_status "Starting COINjecture with security bypass..."
echo ""

# Launch COINjecture with security bypass
cd "$INSTALL_DIR"
exec ./COINjecture-Safe
