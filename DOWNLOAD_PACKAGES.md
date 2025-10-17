# COINjecture Download Packages

This document describes the different ways to download and install COINjecture for various platforms and use cases.

## 🌐 Live Server Status

**COINjecture is now LIVE and operational!**

- **🌍 Live API Server:** http://167.172.213.70:5000
- **✅ Health Check:** http://167.172.213.70:5000/health
- **📊 Latest Block:** http://167.172.213.70:5000/v1/data/block/latest
- **🔗 Public Access:** Available to anyone worldwide
- **📡 Telemetry Ready:** CLI can connect and send data

## 🚀 Quick Start Options

### Option 1: Standalone Applications (Recommended for Non-Developers)
**For:** All platforms, zero technical setup required

**Download and run:**
- **macOS**: `COINjecture-3.6.0-macOS.dmg` - Double-click to install
- **Windows**: `COINjecture-3.6.0-Windows-Installer.exe` - Run installer
- **Linux**: `COINjecture-3.6.0-Linux.AppImage` - Make executable and run

**Features:**
- ✅ No Python installation required
- ✅ Beautiful interactive menu for beginners
- ✅ Direct CLI access for advanced users
- ✅ Automatic wallet and mining setup
- ✅ Live network integration

### Option 2: One-Click Installer (For Developers)
**For:** All platforms, Python-based installation

```bash
# Download and run the installer
python3 install_coinjecture.py
```

**What it does:**
- ✅ Checks Python version compatibility
- ✅ Installs all dependencies automatically
- ✅ Creates necessary directories
- ✅ Generates platform-specific startup scripts
- ✅ Tests the installation
- ✅ Provides clear next steps

### Option 3: Platform-Specific Startup Scripts

#### Windows Users
```cmd
# Double-click or run:
start_coinjecture.bat
```

**Features:**
- 🎨 Beautiful ASCII logo display
- 🔍 Automatic Python version checking
- 📦 Auto-setup if needed
- 🚀 Launches interactive menu directly

#### macOS/Linux Users
```bash
# Make executable and run:
chmod +x start_coinjecture.sh
./start_coinjecture.sh
```

**Features:**
- 🔍 Python 3.9+ version validation
- 📦 Automatic dependency installation
- 🚀 Direct launch to interactive menu
- ✅ Error handling and guidance

### Option 4: Python Wheel Package
**For:** Developers, system administrators

```bash
# Build wheel package
python3 setup_dist.py bdist_wheel

# Install from wheel
pip install dist/coinjecture-3.3.1-py3-none-any.whl

# Use globally
coinjectured interactive
```

**Features:**
- 📦 Professional Python package
- 🔧 Console script entry points
- 📚 Full documentation included
- 🏷️ Proper versioning and metadata

## 📋 System Requirements

### Minimum Requirements
- **Python:** 3.9 or higher
- **RAM:** 512 MB minimum
- **Storage:** 100 MB free space
- **OS:** Windows 10+, macOS 10.14+, Linux (any modern distro)

### Recommended
- **Python:** 3.11 or higher
- **RAM:** 2 GB or more
- **Storage:** 1 GB free space
- **Network:** Internet connection for telemetry

## 🎯 Installation Methods by Use Case

### For End Users (Non-Technical) - RECOMMENDED
1. **Download** the standalone application for your platform:
   - **macOS**: `COINjecture-3.6.0-macOS.dmg`
   - **Windows**: `COINjecture-3.6.0-Windows-Installer.exe`
   - **Linux**: `COINjecture-3.6.0-Linux.AppImage`
2. **Install** using the platform-specific installer
3. **Launch** COINjecture from Applications/Start Menu
4. **Choose** "Interactive Menu" for guided experience
5. **Start** mining, creating wallets, or exploring blockchain

### For End Users (Alternative)
1. **Download** the COINjecture folder
2. **Run** `install_coinjecture.py` (double-click on Windows)
3. **Follow** the on-screen instructions
4. **Launch** using the generated startup script
5. **Connect** to live server at http://167.172.213.70:5000

### For Developers
1. **Clone** the repository: `git clone https://github.com/beanapologist/COINjecture.git`
2. **Install** dependencies: `pip install -r requirements.txt`
3. **Build** wheel: `python setup_dist.py bdist_wheel`
4. **Install** package: `pip install dist/coinjecture-*.whl`

### For System Administrators
1. **Use** the standalone applications for easy deployment
2. **Or use** the wheel package for clean installation
3. **Configure** systemd services (Linux) or Windows services
4. **Set up** monitoring and logging
5. **Deploy** across multiple machines

### For Package Builders
1. **Navigate** to `cli-packages/` directory
2. **Run** `python3 build_packages.py` for current platform
3. **Or run** platform-specific build scripts:
   - **macOS**: `./macos/builders/build_macos.sh`
   - **Windows**: `windows\builders\build_windows.bat`
   - **Linux**: `./linux/builders/build_linux.sh`
4. **Find** built packages in `dist/packages/`
5. **Test** packages on clean systems

## 🔧 Advanced Installation

### Manual Installation
```bash
# 1. Download/clone COINjecture
git clone https://github.com/beanapologist/COINjecture.git
cd COINjecture

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create directories
mkdir -p data/cache logs

# 4. Test installation
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['--help'])"
```

### Docker Installation (Coming Soon)
```bash
# Build Docker image
docker build -t coinjecture .

# Run container
docker run -it coinjecture interactive
```

## 📦 Package Contents

### Core Files
- `src/` - Main source code
- `setup.py` - Development setup
- `setup_dist.py` - Distribution setup
- `requirements.txt` - Python dependencies
- `README.md` - Project documentation
- `USER_GUIDE.md` - User instructions

### CLI Packages (New!)
- `cli-packages/` - Standalone application build system
- `cli-packages/shared/` - Shared components across platforms
- `cli-packages/macos/` - macOS-specific build tools
- `cli-packages/windows/` - Windows-specific build tools
- `cli-packages/linux/` - Linux-specific build tools
- `DISTRIBUTION.md` - Complete distribution guide

### Startup Scripts
- `start_coinjecture.bat` - Windows launcher
- `start_coinjecture.sh` - Unix launcher
- `install_coinjecture.py` - Cross-platform installer

### Configuration
- `config.json` - Node configuration (generated)
- `data/` - Blockchain data directory
- `logs/` - Application logs

## 🚀 First Run Experience

### Interactive Menu
After installation, users are greeted with:

```
🚀 COINjecture Interactive Menu
============================================================
1. 🏗️  Setup & Configuration
2. ⛏️  Mining Operations
3. 💰 Problem Submissions
4. 🔍 Blockchain Explorer
5. 🌐 Network Management
6. 📊 Telemetry & Monitoring
7. ❓ Help & Documentation
8. 🚪 Exit
============================================================
```

### Guided Setup
- **Step 1:** Choose node type (miner/full/light/archive)
- **Step 2:** Configure data directory
- **Step 3:** Enable telemetry (optional)
- **Step 4:** Start mining or exploring

## 🔍 Troubleshooting

### Common Issues

#### Python Not Found
```bash
# Windows: Install from python.org
# macOS: brew install python3
# Linux: sudo apt install python3 python3-pip
```

#### Permission Denied (Unix)
```bash
chmod +x start_coinjecture.sh
chmod +x install_coinjecture.py
```

#### Import Errors
```bash
# Ensure you're in the COINjecture directory
cd /path/to/COINjecture

# Check Python path
python3 -c "import sys; print(sys.path)"
```

#### Dependencies Missing
```bash
pip install -r requirements.txt
# or
python3 -m pip install --upgrade pip
pip install requests flask flask-cors flask-limiter
```

## 📞 Support

### Getting Help
1. **Check** USER_GUIDE.md for detailed instructions
2. **Run** `coinjectured --help` for command reference
3. **Use** the interactive help system (option 7 in menu)
4. **Visit** GitHub issues for bug reports

### Community
- **GitHub:** https://github.com/beanapologist/COINjecture
- **Issues:** https://github.com/beanapologist/COINjecture/issues
- **Discussions:** GitHub Discussions (coming soon)

## 🎉 What's Next?

After installation, you can:

1. **Start Mining** - Solve NP-complete problems and earn rewards
2. **Submit Problems** - Pay others to solve your computational challenges
3. **Explore Blockchain** - View blocks, proofs, and network activity
4. **Connect to Network** - Join the COINjecture peer-to-peer network
5. **Monitor Telemetry** - Track your mining performance and network stats
6. **Access Live API** - Connect to the live server at http://167.172.213.70:5000

## 🌐 Live Server Endpoints

**Your COINjecture server is now live and accessible worldwide:**

- **Health Check:** http://167.172.213.70:5000/health
- **Latest Block:** http://167.172.213.70:5000/v1/data/block/latest
- **Block by Index:** http://167.172.213.70:5000/v1/data/block/{index}
- **Block Range:** http://167.172.213.70:5000/v1/data/blocks?start={start}&end={end}
- **IPFS Data:** http://167.172.213.70:5000/v1/data/ipfs/{cid}

**Welcome to COINjecture - where every proof counts!** 🚀
