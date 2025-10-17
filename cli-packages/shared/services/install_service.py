#!/usr/bin/env python3
"""
COINjecture Background Service Installer

Installs COINjecture as a background service on macOS, Windows, and Linux.
Provides automatic mining and network submission capabilities.
"""

import os
import sys
import platform
import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional

class ServiceInstaller:
    """Cross-platform service installer for COINjecture."""
    
    def __init__(self):
        self.system = platform.system()
        self.home_dir = Path.home()
        self.app_name = "COINjecture"
        self.service_name = "coinjecture-miner"
        
        # Platform-specific paths
        if self.system == "Darwin":  # macOS
            self.service_dir = self.home_dir / "Library" / "LaunchAgents"
            self.config_dir = self.home_dir / ".coinjecture"
        elif self.system == "Windows":
            self.service_dir = Path("C:/ProgramData/COINjecture")
            self.config_dir = self.home_dir / "AppData" / "Roaming" / "COINjecture"
        else:  # Linux
            self.service_dir = self.home_dir / ".config" / "systemd" / "user"
            self.config_dir = self.home_dir / ".coinjecture"
    
    def install_background_service(self) -> bool:
        """Install background service for the current platform."""
        try:
            print(f"🔧 Installing {self.app_name} background service...")
            print(f"   Platform: {self.system}")
            print(f"   Service: {self.service_name}")
            
            # Create directories
            self.service_dir.mkdir(parents=True, exist_ok=True)
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Create configuration
            self._create_config()
            
            # Install platform-specific service
            if self.system == "Darwin":
                return self._install_macos_service()
            elif self.system == "Windows":
                return self._install_windows_service()
            else:
                return self._install_linux_service()
                
        except Exception as e:
            print(f"❌ Failed to install background service: {e}")
            return False
    
    def _create_config(self):
        """Create service configuration file."""
        config = {
            "service": {
                "name": self.service_name,
                "description": f"{self.app_name} Background Mining Service",
                "version": "3.6.0"
            },
            "mining": {
                "enabled": True,
                "capacity": "TIER_2_DESKTOP",
                "auto_submit": True,
                "interval_seconds": 30
            },
            "network": {
                "api_url": "http://167.172.213.70:5000",
                "timeout_seconds": 30,
                "retry_attempts": 3
            },
            "logging": {
                "enabled": True,
                "level": "INFO",
                "max_size_mb": 10,
                "max_files": 5
            }
        }
        
        config_file = self.config_dir / "service_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Configuration created: {config_file}")
    
    def _install_macos_service(self) -> bool:
        """Install macOS LaunchAgent service."""
        try:
            plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.coinjecture.miner</string>
    <key>ProgramArguments</key>
    <array>
        <string>python3</string>
        <string>-c</string>
        <string>import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli._mine_single_block('TIER_2_DESKTOP')</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{self.config_dir}/miner.log</string>
    <key>StandardErrorPath</key>
    <string>{self.config_dir}/miner_error.log</string>
    <key>WorkingDirectory</key>
    <string>{os.getcwd()}</string>
    <key>StartInterval</key>
    <integer>30</integer>
</dict>
</plist>"""
            
            plist_file = self.service_dir / "com.coinjecture.miner.plist"
            with open(plist_file, 'w') as f:
                f.write(plist_content)
            
            # Load the service
            subprocess.run(["launchctl", "load", str(plist_file)], check=True)
            
            print(f"✅ macOS LaunchAgent installed: {plist_file}")
            print("   Service will start automatically on login")
            return True
            
        except Exception as e:
            print(f"❌ Failed to install macOS service: {e}")
            return False
    
    def _install_windows_service(self) -> bool:
        """Install Windows Task Scheduler service."""
        try:
            # Create batch script
            batch_script = f"""@echo off
cd /d "{os.getcwd()}"
python -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli._mine_single_block('TIER_2_DESKTOP')"
"""
            
            script_file = self.service_dir / "miner.bat"
            with open(script_file, 'w') as f:
                f.write(batch_script)
            
            # Create Task Scheduler entry
            task_name = "COINjectureMiner"
            task_command = f"""schtasks /create /tn "{task_name}" /tr "{script_file}" /sc minute /mo 1 /ru SYSTEM /f"""
            
            subprocess.run(task_command, shell=True, check=True)
            
            print(f"✅ Windows Task Scheduler entry created: {task_name}")
            print("   Service will run every minute")
            return True
            
        except Exception as e:
            print(f"❌ Failed to install Windows service: {e}")
            return False
    
    def _install_linux_service(self) -> bool:
        """Install Linux systemd user service."""
        try:
            service_content = f"""[Unit]
Description=COINjecture Background Mining Service
After=network.target

[Service]
Type=simple
User=%i
WorkingDirectory={os.getcwd()}
ExecStart=/usr/bin/python3 -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli._mine_single_block('TIER_2_DESKTOP')"
Restart=always
RestartSec=30
StandardOutput=append:{self.config_dir}/miner.log
StandardError=append:{self.config_dir}/miner_error.log

[Install]
WantedBy=default.target
"""
            
            service_file = self.service_dir / f"{self.service_name}.service"
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            # Enable and start the service
            subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "--user", "enable", f"{self.service_name}.service"], check=True)
            subprocess.run(["systemctl", "--user", "start", f"{self.service_name}.service"], check=True)
            
            print(f"✅ Linux systemd service installed: {service_file}")
            print("   Service will start automatically on login")
            return True
            
        except Exception as e:
            print(f"❌ Failed to install Linux service: {e}")
            return False
    
    def uninstall_service(self) -> bool:
        """Uninstall the background service."""
        try:
            print(f"🗑️  Uninstalling {self.app_name} background service...")
            
            if self.system == "Darwin":
                return self._uninstall_macos_service()
            elif self.system == "Windows":
                return self._uninstall_windows_service()
            else:
                return self._uninstall_linux_service()
                
        except Exception as e:
            print(f"❌ Failed to uninstall service: {e}")
            return False
    
    def _uninstall_macos_service(self) -> bool:
        """Uninstall macOS LaunchAgent service."""
        try:
            plist_file = self.service_dir / "com.coinjecture.miner.plist"
            if plist_file.exists():
                subprocess.run(["launchctl", "unload", str(plist_file)], check=True)
                plist_file.unlink()
                print("✅ macOS LaunchAgent uninstalled")
            return True
        except Exception as e:
            print(f"❌ Failed to uninstall macOS service: {e}")
            return False
    
    def _uninstall_windows_service(self) -> bool:
        """Uninstall Windows Task Scheduler service."""
        try:
            task_name = "COINjectureMiner"
            subprocess.run(f'schtasks /delete /tn "{task_name}" /f', shell=True, check=True)
            print("✅ Windows Task Scheduler entry removed")
            return True
        except Exception as e:
            print(f"❌ Failed to uninstall Windows service: {e}")
            return False
    
    def _uninstall_linux_service(self) -> bool:
        """Uninstall Linux systemd service."""
        try:
            subprocess.run(["systemctl", "--user", "stop", f"{self.service_name}.service"], check=True)
            subprocess.run(["systemctl", "--user", "disable", f"{self.service_name}.service"], check=True)
            
            service_file = self.service_dir / f"{self.service_name}.service"
            if service_file.exists():
                service_file.unlink()
            
            print("✅ Linux systemd service uninstalled")
            return True
        except Exception as e:
            print(f"❌ Failed to uninstall Linux service: {e}")
            return False
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get current service status."""
        status = {
            "platform": self.system,
            "service_name": self.service_name,
            "installed": False,
            "running": False,
            "config_file": str(self.config_dir / "service_config.json")
        }
        
        try:
            if self.system == "Darwin":
                result = subprocess.run(["launchctl", "list", "com.coinjecture.miner"], 
                                      capture_output=True, text=True)
                status["installed"] = result.returncode == 0
                status["running"] = "com.coinjecture.miner" in result.stdout
                
            elif self.system == "Windows":
                result = subprocess.run(['schtasks', '/query', '/tn', 'COINjectureMiner'], 
                                      capture_output=True, text=True)
                status["installed"] = result.returncode == 0
                status["running"] = "Ready" in result.stdout
                
            else:  # Linux
                result = subprocess.run(["systemctl", "--user", "is-active", f"{self.service_name}.service"], 
                                      capture_output=True, text=True)
                status["installed"] = True  # Assume installed if we can check status
                status["running"] = result.stdout.strip() == "active"
                
        except Exception as e:
            status["error"] = str(e)
        
        return status


def install_background_service() -> bool:
    """Main function to install background service."""
    installer = ServiceInstaller()
    return installer.install_background_service()


def uninstall_background_service() -> bool:
    """Main function to uninstall background service."""
    installer = ServiceInstaller()
    return installer.uninstall_service()


def get_service_status() -> Dict[str, Any]:
    """Get service status."""
    installer = ServiceInstaller()
    return installer.get_service_status()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "install":
            success = install_background_service()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "uninstall":
            success = uninstall_background_service()
            sys.exit(0 if success else 1)
        elif sys.argv[1] == "status":
            status = get_service_status()
            print(json.dumps(status, indent=2))
            sys.exit(0)
        else:
            print("Usage: python install_service.py [install|uninstall|status]")
            sys.exit(1)
    else:
        # Default to install
        success = install_background_service()
        sys.exit(0 if success else 1)
