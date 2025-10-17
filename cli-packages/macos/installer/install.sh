#!/bin/bash

# COINjecture macOS Installer
# This script safely installs COINjecture and handles macOS security warnings

set -e

echo "🚀 COINjecture macOS Installer v3.6.3"
echo "======================================"
echo ""

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

# Remove quarantine attributes
print_status "Removing macOS quarantine attributes..."
xattr -d com.apple.quarantine "$INSTALL_DIR/COINjecture" 2>/dev/null || true
xattr -d com.apple.provenance "$INSTALL_DIR/COINjecture" 2>/dev/null || true
xattr -c "$INSTALL_DIR/COINjecture" 2>/dev/null || true
print_success "Quarantine attributes removed"

# Create launcher script
print_status "Creating launcher script..."
cat > "$INSTALL_DIR/launch_coinjecture.sh" << 'EOF'
#!/bin/bash
cd "$HOME/Applications/COINjecture"
./COINjecture
EOF
chmod +x "$INSTALL_DIR/launch_coinjecture.sh"

# Create desktop shortcut
print_status "Creating desktop shortcut..."
cat > "$HOME/Desktop/COINjecture.command" << 'EOF'
#!/bin/bash
cd "$HOME/Applications/COINjecture"
./COINjecture
EOF
chmod +x "$HOME/Desktop/COINjecture.command"

print_success "Desktop shortcut created: ~/Desktop/COINjecture.command"

# Create Applications folder shortcut
print_status "Creating Applications folder shortcut..."
ln -sf "$INSTALL_DIR/COINjecture" "$HOME/Applications/COINjecture-CLI"

print_success "Applications shortcut created"

# Create uninstaller
print_status "Creating uninstaller..."
cat > "$INSTALL_DIR/uninstall.sh" << 'EOF'
#!/bin/bash
echo "🗑️  Uninstalling COINjecture..."
rm -rf "$HOME/Applications/COINjecture"
rm -f "$HOME/Desktop/COINjecture.command"
rm -f "$HOME/Applications/COINjecture-CLI"
echo "✅ COINjecture uninstalled successfully"
EOF
chmod +x "$INSTALL_DIR/uninstall.sh"

print_success "Uninstaller created: $INSTALL_DIR/uninstall.sh"

echo ""
echo "🎉 Installation Complete!"
echo "========================"
echo ""
echo "📁 Installation Location: $INSTALL_DIR"
echo "🖥️  Desktop Shortcut: ~/Desktop/COINjecture.command"
echo "📱 Applications Shortcut: ~/Applications/COINjecture-CLI"
echo ""
echo "🚀 How to Run:"
echo "   • Double-click the desktop shortcut"
echo "   • Or run: $INSTALL_DIR/COINjecture"
echo "   • Or run: $INSTALL_DIR/launch_coinjecture.sh"
echo ""
echo "⚠️  macOS Security Notice:"
echo "   If you see a security warning:"
echo "   1. Right-click the executable → 'Open'"
echo "   2. Click 'Open' in the security dialog"
echo "   3. Future runs will work normally"
echo ""
echo "🗑️  To Uninstall:"
echo "   Run: $INSTALL_DIR/uninstall.sh"
echo ""
print_success "COINjecture is ready to use! 🎯"