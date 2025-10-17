#!/bin/bash
# macOS Build Script for COINjecture

set -e  # Exit on any error

echo "🍎 Building COINjecture for macOS..."

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$(dirname "$SCRIPT_DIR")")")"

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This script must be run on macOS"
    exit 1
fi

# Check for required tools
echo "🔍 Checking dependencies..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    echo "Install with: brew install python3"
    exit 1
fi

if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Installing PyInstaller..."
    pip3 install pyinstaller
fi

# Create directories
echo "📁 Creating directories..."
mkdir -p "$PROJECT_ROOT/dist/packages"
mkdir -p "$PROJECT_ROOT/cli-packages/shared/launcher"

# Create macOS app icon (placeholder)
echo "🎨 Creating app icon..."
cat > "$PROJECT_ROOT/cli-packages/shared/launcher/icon.icns" << 'EOF'
# Placeholder for macOS app icon
# In production, this would be a proper .icns file
EOF

# Create Info.plist for macOS app
echo "📝 Creating Info.plist..."
cat > "$PROJECT_ROOT/cli-packages/shared/launcher/Info.plist" << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>COINjecture</string>
    <key>CFBundleDisplayName</key>
    <string>COINjecture</string>
    <key>CFBundleIdentifier</key>
    <string>com.coinjecture.app</string>
    <key>CFBundleVersion</key>
    <string>3.6.0</string>
    <key>CFBundleShortVersionString</key>
    <string>3.6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>CFBundleExecutable</key>
    <string>COINjecture</string>
    <key>CFBundleIconFile</key>
    <string>icon</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.14</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSRequiresAquaSystemAppearance</key>
    <false/>
</dict>
</plist>
EOF

# Build the executable
echo "🔨 Building executable..."
cd "$PROJECT_ROOT"

# Clean previous builds
rm -rf build/ dist/COINjecture/

# Run PyInstaller
python3 -m PyInstaller cli-packages/shared/specs/coinjecture.spec

# Check if build was successful
if [ ! -d "dist/COINjecture" ]; then
    echo "❌ Build failed - executable not found"
    exit 1
fi

# Create .app bundle
echo "📦 Creating .app bundle..."
APP_NAME="COINjecture-3.6.0-macOS.app"
APP_PATH="dist/packages/$APP_NAME"

# Create app bundle structure
mkdir -p "$APP_PATH/Contents/MacOS"
mkdir -p "$APP_PATH/Contents/Resources"

# Copy executable
cp dist/COINjecture/COINjecture "$APP_PATH/Contents/MacOS/"

# Copy Info.plist
cp cli-packages/shared/launcher/Info.plist "$APP_PATH/Contents/"

# Copy icon (if exists)
if [ -f "cli-packages/shared/launcher/icon.icns" ]; then
    cp cli-packages/shared/launcher/icon.icns "$APP_PATH/Contents/Resources/"
fi

# Make executable
chmod +x "$APP_PATH/Contents/MacOS/COINjecture"

echo "✅ macOS app bundle created: $APP_PATH"

# Create DMG
echo "💿 Creating DMG installer..."

DMG_NAME="COINjecture-3.6.0-macOS.dmg"
DMG_PATH="dist/packages/$DMG_NAME"

# Remove existing DMG
rm -f "$DMG_PATH"

# Create temporary directory for DMG contents
TEMP_DMG_DIR="dist/packages/temp_dmg"
rm -rf "$TEMP_DMG_DIR"
mkdir -p "$TEMP_DMG_DIR"

# Copy app to temp directory
cp -R "$APP_PATH" "$TEMP_DMG_DIR/"

# Create Applications symlink
ln -s /Applications "$TEMP_DMG_DIR/Applications"

# Create DMG
hdiutil create -volname "COINjecture 3.6.0" -srcfolder "$TEMP_DMG_DIR" -ov -format UDZO "$DMG_PATH"

# Clean up
rm -rf "$TEMP_DMG_DIR"
rm -rf "$APP_PATH"

echo "✅ DMG created: $DMG_PATH"

# Code signing (optional)
echo "🔐 Code signing..."
if command -v codesign &> /dev/null; then
    # Create entitlements file
    python3 "$PROJECT_ROOT/cli-packages/shared/signing/sign_packages.py" entitlements
    
    # Sign the DMG
    if [ -n "$COINJECTURE_DEVELOPER_ID" ]; then
        echo "   Signing with Developer ID: $COINJECTURE_DEVELOPER_ID"
        codesign --force --sign "$COINJECTURE_DEVELOPER_ID" "$DMG_PATH"
        
        # Notarize (if Apple ID provided)
        if [ -n "$COINJECTURE_APPLE_ID" ] && [ -n "$COINJECTURE_APP_PASSWORD" ]; then
            echo "   Submitting for notarization..."
            xcrun notarytool submit "$DMG_PATH" \
                --apple-id "$COINJECTURE_APPLE_ID" \
                --password "$COINJECTURE_APP_PASSWORD" \
                --team-id "$COINJECTURE_TEAM_ID" \
                --wait
            
            echo "   Stapling notarization..."
            xcrun stapler staple "$DMG_PATH"
        fi
        
        echo "✅ Code signing completed"
    else
        echo "⚠️  COINJECTURE_DEVELOPER_ID not set, skipping code signing"
    fi
else
    echo "⚠️  codesign not found, skipping code signing"
fi

# Show file size
SIZE=$(du -h "$DMG_PATH" | cut -f1)
echo "📊 DMG size: $SIZE"

echo ""
echo "🎉 macOS build complete!"
echo "📁 Output: $DMG_PATH"
echo ""
echo "🚀 To test:"
echo "   1. Double-click the DMG to mount it"
echo "   2. Drag COINjecture to Applications"
echo "   3. Double-click COINjecture in Applications"
echo ""
