#!/usr/bin/env python3
"""
COINjecture One-Click Installer
===============================
Automatically downloads, installs, and configures COINjecture CLI
"""

import os
import sys
import json
import shutil
import subprocess
import platform
import urllib.request
import zipfile
import tempfile
from pathlib import Path

class COINjectureInstaller:
    def __init__(self):
        self.version = "3.16.0"
        self.platform = self.detect_platform()
        self.install_dir = Path.home() / "coinjecture"
        self.package_url = f"https://github.com/beanapologist/COINjecture/releases/download/v{self.version}/COINjecture-{self.platform}-v{self.version}-Python.zip"
        
    def detect_platform(self):
        """Detect the current platform"""
        system = platform.system().lower()
        if system == "darwin":
            return "macOS"
        elif system == "windows":
            return "Windows"
        elif system == "linux":
            return "Linux"
        else:
            return "Linux"  # Default fallback
    
    def log(self, message, level="INFO"):
        """Log messages with emoji indicators"""
        emoji = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
        print(f"{emoji.get(level, 'ℹ️')} {message}")
    
    def check_python(self):
        """Check if Python 3.7+ is available"""
        self.log("Checking Python installation...")
        if sys.version_info < (3, 7):
            self.log("Python 3.7+ is required. Please install Python first.", "ERROR")
            return False
        
        self.log(f"Python {sys.version.split()[0]} detected", "SUCCESS")
        return True
    
    def check_dependencies(self):
        """Check and install required dependencies"""
        self.log("Checking dependencies...")
        
        required_packages = [
            "requests",
            "cryptography",
            "pycryptodome",
            "ipfshttpclient"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                missing_packages.append(package)
        
        if missing_packages:
            self.log(f"Installing missing packages: {', '.join(missing_packages)}")
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install"
                ] + missing_packages)
                self.log("Dependencies installed successfully", "SUCCESS")
            except subprocess.CalledProcessError:
                self.log("Failed to install dependencies. Please install manually:", "ERROR")
                self.log(f"pip install {' '.join(missing_packages)}", "WARNING")
                return False
        else:
            self.log("All dependencies are available", "SUCCESS")
        
        return True
    
    def download_package(self):
        """Download the COINjecture package"""
        self.log(f"Downloading COINjecture v{self.version} for {self.platform}...")
        
        try:
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_file:
                urllib.request.urlretrieve(self.package_url, tmp_file.name)
                self.log("Package downloaded successfully", "SUCCESS")
                return tmp_file.name
        except Exception as e:
            self.log(f"Failed to download package: {e}", "ERROR")
            return None
    
    def extract_package(self, zip_path):
        """Extract the COINjecture package"""
        self.log("Extracting package...")
        
        try:
            # Create installation directory
            self.install_dir.mkdir(exist_ok=True)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.install_dir)
            
            # Find the extracted folder
            extracted_folders = [f for f in self.install_dir.iterdir() if f.is_dir()]
            if extracted_folders:
                self.coinjecture_dir = extracted_folders[0]
            else:
                self.coinjecture_dir = self.install_dir
            
            self.log(f"Package extracted to {self.coinjecture_dir}", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"Failed to extract package: {e}", "ERROR")
            return False
        finally:
            # Clean up zip file
            if os.path.exists(zip_path):
                os.unlink(zip_path)
    
    def create_config(self):
        """Create default configuration"""
        self.log("Creating configuration...")
        
        config = {
            "role": "miner",
            "data_dir": str(self.coinjecture_dir / "data"),
            "network_id": "coinjecture-mainnet",
            "listen_addr": "0.0.0.0:8080",
            "bootstrap_peers": [
                "167.172.213.70:8080"
            ],
            "enable_user_submissions": True,
            "ipfs_api_url": "http://167.172.213.70:12346",
            "target_block_interval_secs": 30,
            "log_level": "INFO"
        }
        
        config_path = self.coinjecture_dir / "config" / "miner_config.json"
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.log("Configuration created", "SUCCESS")
        return True
    
    def create_launcher_scripts(self):
        """Create launcher scripts for easy startup"""
        self.log("Creating launcher scripts...")
        
        # Create start script
        start_script = f"""#!/bin/bash
# COINjecture v{self.version} Launcher
cd "{self.coinjecture_dir}"
python3 src/cli.py interactive
"""
        
        start_path = self.coinjecture_dir / "start_coinjecture.sh"
        with open(start_path, 'w') as f:
            f.write(start_script)
        start_path.chmod(0o755)
        
        # Create mining script
        mining_script = f"""#!/bin/bash
# COINjecture v{self.version} Mining
cd "{self.coinjecture_dir}"
python3 src/cli.py mine --config config/miner_config.json
"""
        
        mining_path = self.coinjecture_dir / "start_mining.sh"
        with open(mining_path, 'w') as f:
            f.write(mining_script)
        mining_path.chmod(0o755)
        
        # Create wallet generation script
        wallet_script = f"""#!/bin/bash
# COINjecture v{self.version} Wallet Generator
cd "{self.coinjecture_dir}"
python3 src/cli.py wallet-generate --output wallet.json
echo "Wallet generated: wallet.json"
"""
        
        wallet_path = self.coinjecture_dir / "generate_wallet.sh"
        with open(wallet_path, 'w') as f:
            f.write(wallet_script)
        wallet_path.chmod(0o755)
        
        self.log("Launcher scripts created", "SUCCESS")
        return True
    
    def create_desktop_shortcuts(self):
        """Create desktop shortcuts (if possible)"""
        self.log("Creating desktop shortcuts...")
        
        try:
            desktop = Path.home() / "Desktop"
            if desktop.exists():
                # Create desktop shortcut script
                shortcut_script = f"""#!/bin/bash
# COINjecture v{self.version} Desktop Launcher
cd "{self.coinjecture_dir}"
python3 src/cli.py interactive
"""
                
                shortcut_path = desktop / "COINjecture.sh"
                with open(shortcut_path, 'w') as f:
                    f.write(shortcut_script)
                shortcut_path.chmod(0o755)
                
                self.log("Desktop shortcut created", "SUCCESS")
            else:
                self.log("Desktop directory not found, skipping shortcut creation", "WARNING")
        except Exception as e:
            self.log(f"Could not create desktop shortcut: {e}", "WARNING")
    
    def test_installation(self):
        """Test the installation"""
        self.log("Testing installation...")
        
        try:
            # Test CLI help
            result = subprocess.run([
                sys.executable, "src/cli.py", "--help"
            ], cwd=self.coinjecture_dir, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.log("Installation test passed", "SUCCESS")
                return True
            else:
                self.log(f"Installation test failed: {result.stderr}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Installation test failed: {e}", "ERROR")
            return False
    
    def print_success_message(self):
        """Print success message with next steps"""
        print("\n" + "="*60)
        print("🎉 COINjecture Installation Complete!")
        print("="*60)
        print(f"📁 Installation Directory: {self.coinjecture_dir}")
        print(f"🌐 Version: v{self.version}")
        print(f"🖥️  Platform: {self.platform}")
        print("\n🚀 Quick Start:")
        print(f"   cd {self.coinjecture_dir}")
        print("   ./start_coinjecture.sh")
        print("\n⛏️  Start Mining:")
        print("   ./start_mining.sh")
        print("\n💰 Generate Wallet:")
        print("   ./generate_wallet.sh")
        print("\n📚 Full Documentation:")
        print("   https://coinjecture.com")
        print("\n🔗 GitHub Repository:")
        print("   https://github.com/beanapologist/COINjecture")
        print("="*60)
    
    def install(self):
        """Main installation process"""
        print("🚀 COINjecture One-Click Installer")
        print("=" * 40)
        print(f"Installing COINjecture v{self.version} for {self.platform}")
        print("=" * 40)
        
        # Check Python
        if not self.check_python():
            return False
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Download package
        zip_path = self.download_package()
        if not zip_path:
            return False
        
        # Extract package
        if not self.extract_package(zip_path):
            return False
        
        # Create configuration
        if not self.create_config():
            return False
        
        # Create launcher scripts
        if not self.create_launcher_scripts():
            return False
        
        # Create desktop shortcuts
        self.create_desktop_shortcuts()
        
        # Test installation
        if not self.test_installation():
            self.log("Installation completed but test failed. You may need to check dependencies.", "WARNING")
        
        # Print success message
        self.print_success_message()
        
        return True

def main():
    """Main entry point"""
    installer = COINjectureInstaller()
    
    try:
        success = installer.install()
        if success:
            print("\n🎉 Installation completed successfully!")
            print("Run './start_coinjecture.sh' to begin!")
        else:
            print("\n❌ Installation failed. Please check the error messages above.")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n⚠️ Installation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
