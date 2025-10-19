#!/usr/bin/env python3
"""
COINjecture Setup Script
Automatically installs all dependencies and sets up the environment
"""

__version__ = "3.9.25"

import os
import sys
import subprocess
import platform
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors gracefully"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python 3.8+ required. You have {version.major}.{version.minor}")
        print("Please install Python 3.8 or higher from https://python.org")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def install_dependencies():
    """Install all required Python packages"""
    print("📦 Installing Python dependencies...")
    
    # Core dependencies
    dependencies = [
        "requests>=2.25.0",
        "Flask>=2.0.0", 
        "Flask-CORS>=3.0.0",
        "Flask-Limiter>=2.0.0"
    ]
    
    for dep in dependencies:
        if not run_command(f"pip3 install {dep}", f"Installing {dep}"):
            return False
    
    return True

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    
    directories = [
        "data",
        "data/cache", 
        "data/blockchain",
        "data/ipfs",
        "logs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    return True

def create_config_files():
    """Create default configuration files"""
    print("⚙️ Creating configuration files...")
    
    # Default miner config
    miner_config = {
        "role": "miner",
        "data_dir": "./data",
        "network_id": "coinjecture-mainnet",
        "listen_addr": "0.0.0.0:8080",
        "enable_user_submissions": True,
        "ipfs_api_url": "http://localhost:5001",
        "target_block_interval_secs": 30,
        "log_level": "INFO"
    }
    
    import json
    with open("default_miner_config.json", "w") as f:
        json.dump(miner_config, f, indent=2)
    
    print("✅ Created default_miner_config.json")
    return True

def create_startup_scripts():
    """Create easy startup scripts"""
    print("🚀 Creating startup scripts...")
    
    # Windows batch file
    windows_script = """@echo off
echo Starting COINjecture...
python setup.py --quick-start
pause
"""
    with open("start_coinjecture.bat", "w") as f:
        f.write(windows_script)
    
    # Unix shell script
    unix_script = """#!/bin/bash
echo "Starting COINjecture..."
python3 setup.py --quick-start
"""
    with open("start_coinjecture.sh", "w") as f:
        f.write(unix_script)
    
    # Make shell script executable
    if platform.system() != "Windows":
        os.chmod("start_coinjecture.sh", 0o755)
    
    print("✅ Created startup scripts")
    return True

def test_installation():
    """Test that everything is working"""
    print("🧪 Testing installation...")
    
    # Write test script to file to avoid shell escaping issues
    test_script_content = """import sys
sys.path.append('src')
try:
    from cli import COINjectureCLI
    cli = COINjectureCLI()
    result = cli.run(['--help'])
    if result == 0:
        print("CLI test passed")
    else:
        print("CLI test failed")
        sys.exit(1)
except Exception as e:
    print(f"Import test failed: {e}")
    sys.exit(1)
"""
    
    with open("test_setup.py", "w") as f:
        f.write(test_script_content)
    
    if run_command("python3 test_setup.py", "Testing CLI functionality"):
        print("✅ All tests passed!")
        # Clean up test file
        os.remove("test_setup.py")
        return True
    else:
        print("❌ Tests failed")
        # Clean up test file
        if os.path.exists("test_setup.py"):
            os.remove("test_setup.py")
        return False

def quick_start():
    """Quick start guide for new users"""
    show_logo()
    print("\n" + "="*60)
    print("🎉 COINjecture Setup Complete!")
    print("="*60)
    print("\n📋 Quick Start Options:")
    print("\n1️⃣ Start Mining (Earn Rewards):")
    print("   python3 -c \"import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['init', '--role', 'miner', '--config', 'default_miner_config.json'])\"")
    print("   python3 -c \"import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['mine', '--config', 'default_miner_config.json'])\"")
    
    print("\n2️⃣ Submit a Problem (Pay Others to Solve):")
    print("   python3 -c \"import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['submit-problem', '--type', 'subset_sum', '--template', '{\\\"numbers\\\": [1, 2, 3, 4, 5], \\\"target\\\": 7}', '--bounty', '100'])\"")
    
    print("\n3️⃣ Check Blockchain Status:")
    print("   python3 -c \"import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['get-block', '--latest'])\"")
    
    print("\n📖 For detailed instructions, see USER_GUIDE.md")
    print("⚡ For quick commands, see QUICK_REFERENCE.md")
    print("\n🆘 Need help? Run: python3 -c \"import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['--help'])\"")

def show_logo():
    """Display the COINjecture logo"""
    logo = """
    ╔════════════════════════════════════════════════════════════════════════════════════════════╗
    ║                                                                                            ║
    ║   ██████╗ ██████╗ ██╗███╗   ██╗     ██╗███████╗ ██████╗████████╗██╗   ██╗██████╗ ███████╗  ║
    ║  ██╔════╝██╔═══██╗██║████╗  ██║     ██║██╔════╝██╔════╝╚══██╔══╝██║   ██║██╔══██╗██╔════╝  ║
    ║  ██║     ██║   ██║██║██╔██╗ ██║     ██║█████╗  ██║        ██║   ██║   ██║██████╔╝█████╗    ║
    ║  ██║     ██║   ██║██║██║╚██╗██║██   ██║██╔══╝  ██║        ██║   ██║   ██║██╔══██╗██╔══╝    ║
    ║  ╚██████╗╚██████╔╝██║██║ ╚████║╚█████╔╝███████╗╚██████╗   ██║   ╚██████╔╝██║  ██║███████╗  ║
    ║   ╚═════╝ ╚═════╝ ╚═╝╚═╝  ╚═══╝ ╚════╝ ╚══════╝ ╚═════╝   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚══════╝  ║
    ║                                                                                            ║
    ║         🔬 Mathematical Proof-of-Work Mining                                               ║
    ║         🌟 Transform blockchain mining into meaningful discovery                           ║
    ║         💎 Every proof counts. Every discovery pays.                                       ║
    ║                                                                                            ║
    ╚════════════════════════════════════════════════════════════════════════════════════════════╝
    """
    print(logo)

def main():
    """Main setup function"""
    show_logo()
    print("🚀 COINjecture Setup Script")
    print("="*40)
    
    # Check for quick start flag
    if "--quick-start" in sys.argv:
        quick_start()
        return
    
    # Run full setup
    steps = [
        ("Checking Python version", check_python_version),
        ("Installing dependencies", install_dependencies),
        ("Creating directories", create_directories),
        ("Creating config files", create_config_files),
        ("Creating startup scripts", create_startup_scripts),
        ("Testing installation", test_installation)
    ]
    
    for step_name, step_func in steps:
        if not step_func():
            print(f"\n❌ Setup failed at: {step_name}")
            print("Please check the error messages above and try again.")
            sys.exit(1)
    
    print("\n" + "="*60)
    print("🎉 COINjecture Setup Complete!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Read USER_GUIDE.md for detailed instructions")
    print("2. Use QUICK_REFERENCE.md for copy-paste commands")
    print("3. Run 'python3 setup.py --quick-start' for quick start options")
    print("\n🚀 Ready to use COINjecture!")

if __name__ == "__main__":
    main()
