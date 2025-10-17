# COINjecture Installation Guide
## Turnkey Setup - Just Run One Command!

---

## 🚀 Super Simple Installation (Recommended)

### Step 1: Download COINjecture
```bash
git clone https://github.com/your-username/COINjecture.git
cd COINjecture
```

### Step 2: Run the Setup Script
```bash
python3 setup.py
```

**That's it!** The setup script will automatically:
- ✅ Check your Python version
- ✅ Install all required dependencies
- ✅ Create necessary directories
- ✅ Set up configuration files
- ✅ Create startup scripts
- ✅ Test everything works

---

## 🎯 What Gets Installed Automatically

### Python Dependencies
- `requests` - For IPFS API communication
- `Flask` - For the web API
- `Flask-CORS` - For cross-origin requests
- `Flask-Limiter` - For rate limiting

### Directory Structure
```
COINjecture/
├── data/
│   ├── cache/          # API cache files
│   ├── blockchain/     # Blockchain data
│   └── ipfs/          # IPFS data
├── logs/              # Log files
└── src/               # Source code
```

### Configuration Files
- `default_miner_config.json` - Ready-to-use mining configuration
- `start_coinjecture.bat` - Windows startup script
- `start_coinjecture.sh` - Unix/Mac startup script

---

## 🖥️ Platform-Specific Instructions

### Windows Users
1. Download and install Python 3.8+ from [python.org](https://python.org)
2. Open Command Prompt in the COINjecture folder
3. Run: `python setup.py`
4. Use `start_coinjecture.bat` to start

### Mac Users
1. Install Python 3.8+ (usually pre-installed)
2. Open Terminal in the COINjecture folder
3. Run: `python3 setup.py`
4. Use `./start_coinjecture.sh` to start

### Linux Users
1. Install Python 3.8+: `sudo apt install python3 python3-pip` (Ubuntu/Debian)
2. Open Terminal in the COINjecture folder
3. Run: `python3 setup.py`
4. Use `./start_coinjecture.sh` to start

---

## 🔧 Manual Installation (If Needed)

### If the automatic setup doesn't work:

#### Step 1: Install Python Dependencies
```bash
pip3 install requests Flask Flask-CORS Flask-Limiter
```

#### Step 2: Create Directories
```bash
mkdir -p data/cache data/blockchain data/ipfs logs
```

#### Step 3: Test Installation
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['--help'])"
```

---

## ✅ Verification

### Test 1: Check CLI Works
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['--help'])"
```
**Expected:** Shows help menu with all commands

### Test 2: Initialize a Node
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['init', '--role', 'miner', '--config', 'default_miner_config.json'])"
```
**Expected:** Creates configuration and shows success message

### Test 3: Check Blockchain
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['get-block', '--latest'])"
```
**Expected:** Shows latest block information

---

## 🚀 Quick Start After Installation

### Option 1: Start Mining (Earn Rewards)
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['mine', '--config', 'default_miner_config.json'])"
```

### Option 2: Submit a Problem
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['submit-problem', '--type', 'subset_sum', '--template', '{\"numbers\": [1, 2, 3, 4, 5], \"target\": 7}', '--bounty', '100'])"
```

### Option 3: Check Status
```bash
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['list-submissions'])"
```

---

## 🆘 Troubleshooting

### "Python not found"
- **Windows:** Install Python from [python.org](https://python.org) and check "Add to PATH"
- **Mac:** Install via Homebrew: `brew install python3`
- **Linux:** `sudo apt install python3 python3-pip`

### "Permission denied"
- **Windows:** Run Command Prompt as Administrator
- **Mac/Linux:** Use `sudo` if needed: `sudo python3 setup.py`

### "Module not found"
- Make sure you're in the COINjecture directory
- Try: `pip3 install --user requests Flask Flask-CORS Flask-Limiter`

### "Port already in use"
- Change the port in your config file
- Or stop other services using the same port

---

## 📋 System Requirements

### Minimum Requirements
- **OS:** Windows 10, macOS 10.14, or Linux (Ubuntu 18.04+)
- **Python:** 3.8 or higher
- **RAM:** 2GB minimum, 4GB recommended
- **Storage:** 1GB free space
- **Network:** Internet connection for IPFS

### Recommended Requirements
- **RAM:** 8GB or more
- **Storage:** 10GB free space (for blockchain data)
- **CPU:** Multi-core processor
- **Network:** Stable broadband connection

---

## 🎉 You're Ready!

After running `python3 setup.py`, you'll have:
- ✅ All dependencies installed
- ✅ Configuration files ready
- ✅ Startup scripts created
- ✅ Everything tested and working

**Next Steps:**
1. Read `USER_GUIDE.md` for detailed usage instructions
2. Use `QUICK_REFERENCE.md` for copy-paste commands
3. Start mining or submitting problems!

---

*This installation is designed to be completely turnkey - just run one command and you're ready to use COINjecture!*
