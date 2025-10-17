# COINjecture Distribution Guide

This document provides comprehensive instructions for distributing COINjecture packages across all platforms with proper code signing and notarization.

## 📦 Package Overview

COINjecture v3.6.0 provides production-ready standalone applications for:
- **macOS**: DMG installer with notarization
- **Windows**: EXE installer with Authenticode signing
- **Linux**: AppImage with GPG signature

## 🔐 Code Signing Requirements

### macOS Notarization

**Required:**
- Apple Developer Account ($99/year)
- Developer ID Application certificate
- App-specific password for notarization

**Environment Variables:**
```bash
export COINJECTURE_DEVELOPER_ID="Developer ID Application: YOUR_NAME"
export COINJECTURE_TEAM_ID="YOUR_TEAM_ID"
export COINJECTURE_APPLE_ID="your@email.com"
export COINJECTURE_APP_PASSWORD="your-app-password"
```

**Process:**
1. Sign the app bundle with Developer ID
2. Submit to Apple for notarization
3. Staple the notarization to the DMG
4. Verify with `spctl --assess --verbose`

### Windows Authenticode

**Required:**
- Code signing certificate (.pfx file)
- Windows SDK (includes signtool)

**Environment Variables:**
```bash
set COINJECTURE_CERT_FILE=certificate.pfx
set COINJECTURE_CERT_PASSWORD=your-password
```

**Process:**
1. Sign executable with signtool
2. Verify with `signtool verify /pa executable.exe`
3. Test on Windows Defender

### Linux GPG Signing

**Required:**
- GPG key pair
- GPG installed on build system

**Environment Variables:**
```bash
export COINJECTURE_GPG_KEY_ID="your-gpg-key-id"
export COINJECTURE_GPG_PASSPHRASE="your-passphrase"
```

**Process:**
1. Create detached signature with GPG
2. Verify with `gpg --verify package.sig package`
3. Distribute both package and signature

## 🏗️ Build Process

### Prerequisites

**All Platforms:**
- Python 3.8+
- PyInstaller
- Git

**macOS:**
- Xcode Command Line Tools
- codesign, xcrun notarytool

**Windows:**
- Visual Studio or Windows SDK
- signtool, makensis (optional)

**Linux:**
- appimagetool (optional)
- GPG

### Building Packages

**1. Clone Repository:**
```bash
git clone https://github.com/beanapologist/COINjecture.git
cd COINjecture
```

**2. Install Dependencies:**
```bash
pip install -r requirements.txt
pip install pyinstaller
```

**3. Build for Current Platform:**
```bash
cd cli-packages
python3 build_packages.py
```

**4. Build for Specific Platform:**
```bash
# macOS
python3 build_packages.py --platform macOS

# Windows  
python3 build_packages.py --platform Windows

# Linux
python3 build_packages.py --platform Linux
```

**5. Build All Platforms:**
```bash
python3 build_packages.py --all
```

### Platform-Specific Builds

#### macOS Build
```bash
cd cli-packages/macos/builders
./build_macos.sh
```

**Output:**
- `COINjecture-3.6.0-macOS.dmg` (signed and notarized)
- `COINjecture-3.6.0-macOS.app` (signed app bundle)

#### Windows Build
```cmd
cd cli-packages\windows\builders
build_windows.bat
```

**Output:**
- `COINjecture-3.6.0-Windows.exe` (signed executable)
- `COINjecture-3.6.0-Windows-Installer.exe` (NSIS installer)

#### Linux Build
```bash
cd cli-packages/linux/builders
./build_linux.sh
```

**Output:**
- `COINjecture-3.6.0-Linux.AppImage` (signed AppImage)
- `COINjecture-3.6.0-Linux.AppImage.sig` (GPG signature)

## 🧪 Testing Packages

### Pre-Release Testing

**1. Clean System Test:**
- Test on fresh VM/container
- No Python installation
- Verify all dependencies bundled

**2. Functionality Test:**
- Launch application
- Test network connectivity
- Test mining functionality
- Test background service installation

**3. Security Test:**
- Verify code signatures
- Test on different OS versions
- Check for malware false positives

### Cross-Platform Testing

**macOS:**
- Test on macOS 10.14+ (Mojave, Catalina, Big Sur, Monterey, Ventura, Sonoma)
- Verify notarization status
- Test Gatekeeper acceptance

**Windows:**
- Test on Windows 10/11
- Verify Authenticode signature
- Test Windows Defender compatibility

**Linux:**
- Test on Ubuntu, Fedora, Arch, Debian
- Verify AppImage execution
- Test GPG signature verification

## 📤 Distribution Methods

### GitHub Releases

**1. Create Release:**
```bash
git tag v3.6.0
git push origin v3.6.0
```

**2. Upload Artifacts:**
- Upload DMG, EXE, AppImage files
- Include GPG signatures
- Add release notes

**3. Verify Downloads:**
- Test download links
- Verify file integrity
- Check signature verification

### Alternative Distribution

**Direct Download:**
- Host on CDN (CloudFlare, AWS S3)
- Provide checksums
- Include verification instructions

**Package Managers:**
- Homebrew (macOS)
- Chocolatey (Windows)
- Snap/Flatpak (Linux)

## 🔍 Verification Instructions

### For Users

**macOS:**
```bash
# Check notarization
spctl --assess --verbose COINjecture-3.6.0-macOS.dmg

# Verify signature
codesign --verify --verbose COINjecture-3.6.0-macOS.app
```

**Windows:**
```cmd
# Verify signature
signtool verify /pa COINjecture-3.6.0-Windows.exe
```

**Linux:**
```bash
# Verify GPG signature
gpg --verify COINjecture-3.6.0-Linux.AppImage.sig COINjecture-3.6.0-Linux.AppImage

# Check AppImage
./COINjecture-3.6.0-Linux.AppImage --appimage-extract-and-run --help
```

### For Developers

**Verify Build Integrity:**
```bash
# Check file sizes
ls -lh dist/packages/

# Verify signatures
python3 cli-packages/shared/signing/sign_packages.py verify package_path

# Test functionality
./package --help
```

## 🚀 Release Checklist

### Pre-Release
- [ ] All tests passing
- [ ] Code signing configured
- [ ] Version numbers updated
- [ ] Changelog updated
- [ ] Documentation updated

### Build Process
- [ ] Clean build environment
- [ ] All dependencies installed
- [ ] Environment variables set
- [ ] Build all platforms
- [ ] Verify signatures
- [ ] Test on clean systems

### Post-Release
- [ ] Upload to GitHub Releases
- [ ] Update download links
- [ ] Announce release
- [ ] Monitor user feedback
- [ ] Track download statistics

## 🛠️ Troubleshooting

### Common Issues

**Build Failures:**
- Check Python version (3.8+ required)
- Verify PyInstaller installation
- Check file permissions
- Ensure sufficient disk space

**Signing Issues:**
- Verify certificate validity
- Check environment variables
- Test signing tools
- Verify network connectivity (notarization)

**Package Issues:**
- Test on clean system
- Check bundled dependencies
- Verify file permissions
- Test network connectivity

### Support

**Documentation:**
- README.md - Basic usage
- USER_GUIDE.md - Detailed instructions
- QUICK_REFERENCE.md - Command reference

**Community:**
- GitHub Issues - Bug reports
- GitHub Discussions - Questions
- Discord - Real-time support

## 📊 Monitoring

### Analytics
- Download statistics
- Platform distribution
- User feedback
- Error reports

### Metrics
- Package size optimization
- Build time tracking
- Test coverage
- Performance benchmarks

---

**Ready to distribute COINjecture to the world!** 🌍

The distribution process ensures that users receive trusted, signed packages that work seamlessly across all platforms while maintaining security and integrity.