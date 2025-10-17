#!/bin/bash
# Linux Build Script for COINjecture

set -e  # Exit on any error

echo "🐧 Building COINjecture for Linux..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Check if we're on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "❌ This script must be run on Linux"
    exit 1
fi

# Check for required tools
echo "🔍 Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    echo "Install with: sudo apt install python3 python3-pip"
    exit 1
fi

if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Installing PyInstaller..."
    pip3 install pyinstaller
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install PyInstaller"
        exit 1
    fi
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p "$PROJECT_ROOT/dist/packages"
mkdir -p "$PROJECT_ROOT/packaging/assets"

# Create Linux icon (placeholder)
echo "🎨 Creating app icon..."
cat > "$PROJECT_ROOT/packaging/assets/icon.png" << 'EOF'
# Placeholder for Linux app icon
# In production, this would be a proper PNG file
EOF

# Create desktop file for AppImage
echo "📝 Creating desktop file..."
cat > "$PROJECT_ROOT/packaging/assets/coinjecture.desktop" << 'EOF'
[Desktop Entry]
Name=COINjecture
Comment=Proof-of-Work Blockchain
Exec=COINjecture
Icon=coinjecture
Terminal=true
Type=Application
Categories=Network;Finance;
StartupNotify=true
EOF

# Build the executable
echo "🔨 Building executable..."
cd "$PROJECT_ROOT"

# Clean previous builds
rm -rf build/ dist/COINjecture/

# Run PyInstaller
pyinstaller packaging/coinjecture.spec

# Check if build was successful
if [ ! -f "dist/COINjecture/COINjecture" ]; then
    echo "❌ Build failed - executable not found"
    exit 1
fi

# Create AppImage structure
echo "📦 Creating AppImage..."
APPIMAGE_NAME="COINjecture-3.6.0-Linux.AppImage"
APPIMAGE_PATH="dist/packages/$APPIMAGE_NAME"

# Create AppImage directory structure
APPIMAGE_DIR="dist/packages/COINjecture.AppDir"
rm -rf "$APPIMAGE_DIR"
mkdir -p "$APPIMAGE_DIR/usr/bin"
mkdir -p "$APPIMAGE_DIR/usr/share/applications"
mkdir -p "$APPIMAGE_DIR/usr/share/icons/hicolor/256x256/apps"

# Copy executable
cp dist/COINjecture/COINjecture "$APPIMAGE_DIR/usr/bin/"

# Copy desktop file
cp packaging/assets/coinjecture.desktop "$APPIMAGE_DIR/usr/share/applications/"

# Copy icon (if exists)
if [ -f "packaging/assets/icon.png" ]; then
    cp packaging/assets/icon.png "$APPIMAGE_DIR/usr/share/icons/hicolor/256x256/apps/coinjecture.png"
fi

# Create AppRun script
cat > "$APPIMAGE_DIR/AppRun" << 'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
exec "${HERE}/usr/bin/COINjecture" "$@"
EOF

chmod +x "$APPIMAGE_DIR/AppRun"

# Create AppImage metadata
cat > "$APPIMAGE_DIR/AppImage.yml" << 'EOF'
api-version: 1
name: COINjecture
version: 3.6.0
exec: usr/bin/COINjecture
icon: coinjecture
categories: Network;Finance;
EOF

# Make executable
chmod +x "$APPIMAGE_DIR/usr/bin/COINjecture"

echo "✅ AppImage structure created"

# Check if appimagetool is available
if command -v appimagetool &> /dev/null; then
    echo "🔧 Creating AppImage with appimagetool..."
    appimagetool "$APPIMAGE_DIR" "$APPIMAGE_PATH"
    
    if [ $? -eq 0 ]; then
        echo "✅ AppImage created: $APPIMAGE_PATH"
        rm -rf "$APPIMAGE_DIR"
    else
        echo "❌ Failed to create AppImage"
        exit 1
    fi
else
    echo "⚠️ appimagetool not found, creating portable executable instead..."
    
    # Create a simple portable executable
    PORTABLE_NAME="COINjecture-3.6.0-Linux"
    PORTABLE_PATH="dist/packages/$PORTABLE_NAME"
    
    cp dist/COINjecture/COINjecture "$PORTABLE_PATH"
    chmod +x "$PORTABLE_PATH"
    
    echo "✅ Portable executable created: $PORTABLE_PATH"
    echo "💡 Install appimagetool to create proper AppImage:"
    echo "   wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    echo "   chmod +x appimagetool-x86_64.AppImage"
    echo "   sudo mv appimagetool-x86_64.AppImage /usr/local/bin/appimagetool"
    
    # Clean up
    rm -rf "$APPIMAGE_DIR"
fi

# GPG signing (optional)
echo "🔐 GPG signing..."
if command -v gpg &> /dev/null; then
    if [ -n "$COINJECTURE_GPG_KEY_ID" ]; then
        echo "   Signing with GPG key: $COINJECTURE_GPG_KEY_ID"
        if [ -f "$APPIMAGE_PATH" ]; then
            gpg --detach-sign --armor --local-user "$COINJECTURE_GPG_KEY_ID" "$APPIMAGE_PATH"
            echo "✅ AppImage signed: ${APPIMAGE_PATH}.sig"
        elif [ -f "$PORTABLE_PATH" ]; then
            gpg --detach-sign --armor --local-user "$COINJECTURE_GPG_KEY_ID" "$PORTABLE_PATH"
            echo "✅ Executable signed: ${PORTABLE_PATH}.sig"
        fi
    else
        echo "⚠️  COINJECTURE_GPG_KEY_ID not set, skipping GPG signing"
    fi
else
    echo "⚠️  GPG not found, skipping GPG signing"
fi

# Show file size
if [ -f "$APPIMAGE_PATH" ]; then
    SIZE=$(du -h "$APPIMAGE_PATH" | cut -f1)
    echo "📊 AppImage size: $SIZE"
elif [ -f "$PORTABLE_PATH" ]; then
    SIZE=$(du -h "$PORTABLE_PATH" | cut -f1)
    echo "📊 Executable size: $SIZE"
fi

echo ""
echo "🎉 Linux build complete!"
if [ -f "$APPIMAGE_PATH" ]; then
    echo "📁 Output: $APPIMAGE_PATH"
    echo ""
    echo "🚀 To test:"
    echo "   1. Make executable: chmod +x $APPIMAGE_PATH"
    echo "   2. Run: ./$APPIMAGE_PATH"
elif [ -f "$PORTABLE_PATH" ]; then
    echo "📁 Output: $PORTABLE_PATH"
    echo ""
    echo "🚀 To test:"
    echo "   1. Make executable: chmod +x $PORTABLE_PATH"
    echo "   2. Run: ./$PORTABLE_PATH"
fi
echo ""
