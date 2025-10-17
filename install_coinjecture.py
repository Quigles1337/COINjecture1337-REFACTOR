#!/usr/bin/env python3
"""
COINjecture One-Click Installer
Cross-platform installer for COINjecture blockchain
"""

import os
import sys
import subprocess
import platform
import urllib.request
import zipfile
import shutil
from pathlib import Path

def print_banner():
    """Print the COINjecture banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║                                                    ║
║  🔬 Mathematical Proof-of-Work Mining                        ║
║  🌟 Transform blockchain mining into meaningful discovery    ║
║  💎 Every proof counts. Every discovery pays.                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print("❌ Python 3.9+ is required. You have Python {}.{}.{}".format(
            version.major, version.minor, version.micro))
        print("Please install Python 3.9+ from https://python.org")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("📁 Creating directories...")
    directories = ["data", "data/cache", "logs"]
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    print("✅ Directories created")

def create_startup_scripts():
    """Create platform-specific startup scripts"""
    print("🚀 Creating startup scripts...")
    
    # Windows batch file
    if platform.system() == "Windows":
        batch_content = '''@echo off
title COINjecture Blockchain
echo Starting COINjecture...
python -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['interactive'])"
pause
'''
        with open("start_coinjecture.bat", "w") as f:
            f.write(batch_content)
        print("✅ Created start_coinjecture.bat")
    
    # Unix shell script
    shell_content = '''#!/bin/bash
echo "🚀 Starting COINjecture..."
python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['interactive'])"
'''
    with open("start_coinjecture.sh", "w") as f:
        f.write(shell_content)
    
    # Make executable on Unix systems
    if platform.system() != "Windows":
        os.chmod("start_coinjecture.sh", 0o755)
    
    print("✅ Created start_coinjecture.sh")

def test_installation():
    """Test the installation"""
    print("🧪 Testing installation...")
    try:
        # Test import
        sys.path.append('src')
        from cli import COINjectureCLI
        cli = COINjectureCLI()
        print("✅ CLI imports successfully")
        
        # Test help command
        cli.run(['--help'])
        print("✅ CLI help command works")
        
        return True
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False

def main():
    """Main installation function"""
    print_banner()
    print("🚀 COINjecture One-Click Installer")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Check if we're in the right directory
    if not os.path.exists("setup.py"):
        print("❌ Please run this script from the COINjecture directory")
        return 1
    
    # Install dependencies
    if not install_dependencies():
        return 1
    
    # Create directories
    create_directories()
    
    # Create startup scripts
    create_startup_scripts()
    
    # Test installation
    if not test_installation():
        return 1
    
    print("\n🎉 Installation Complete!")
    print("=" * 50)
    print("✅ COINjecture is ready to use!")
    print("\n🚀 To start COINjecture:")
    
    if platform.system() == "Windows":
        print("   Double-click: start_coinjecture.bat")
        print("   Or run: python -c \"import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['interactive'])\"")
    else:
        print("   Run: ./start_coinjecture.sh")
        print("   Or run: python3 -c \"import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['interactive'])\"")
    
    print("\n📖 For more information, see README.md and USER_GUIDE.md")
    print("🌐 Visit: https://github.com/beanapologist/COINjecture")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
