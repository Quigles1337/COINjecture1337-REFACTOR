#!/usr/bin/env python3
"""
COINjecture Package Signing Script

Handles code signing for macOS (notarization) and Windows (Authenticode).
Provides GPG signing for Linux packages.
"""

import os
import sys
import subprocess
import platform
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

class PackageSigner:
    """Cross-platform package signing utility."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.system = platform.system()
        self.version = "3.9.16"
        
        # Signing configuration
        self.config = {
            "macos": {
                "developer_id": os.getenv("COINJECTURE_DEVELOPER_ID", "Developer ID Application: YOUR_NAME"),
                "team_id": os.getenv("COINJECTURE_TEAM_ID", "YOUR_TEAM_ID"),
                "apple_id": os.getenv("COINJECTURE_APPLE_ID", "your@email.com"),
                "app_password": os.getenv("COINJECTURE_APP_PASSWORD", "your-app-password"),
                "bundle_id": "com.coinjecture.app"
            },
            "windows": {
                "certificate_file": os.getenv("COINJECTURE_CERT_FILE", "certificate.pfx"),
                "certificate_password": os.getenv("COINJECTURE_CERT_PASSWORD", "your-password"),
                "timestamp_url": "http://timestamp.digicert.com"
            },
            "linux": {
                "gpg_key_id": os.getenv("COINJECTURE_GPG_KEY_ID", "your-gpg-key-id"),
                "gpg_passphrase": os.getenv("COINJECTURE_GPG_PASSPHRASE", "your-passphrase")
            }
        }
    
    def sign_package(self, package_path: Path) -> bool:
        """Sign a package based on platform."""
        try:
            print(f"🔐 Signing package: {package_path}")
            print(f"   Platform: {self.system}")
            
            if self.system == "Darwin":
                return self._sign_macos_package(package_path)
            elif self.system == "Windows":
                return self._sign_windows_package(package_path)
            else:
                return self._sign_linux_package(package_path)
                
        except Exception as e:
            print(f"❌ Failed to sign package: {e}")
            return False
    
    def _sign_macos_package(self, package_path: Path) -> bool:
        """Sign and notarize macOS package."""
        try:
            print("🍎 Signing macOS package...")
            
            # Check if it's a .app bundle or .dmg
            if package_path.suffix == ".app":
                return self._sign_macos_app(package_path)
            elif package_path.suffix == ".dmg":
                return self._sign_macos_dmg(package_path)
            else:
                print(f"❌ Unsupported macOS package format: {package_path.suffix}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to sign macOS package: {e}")
            return False
    
    def _sign_macos_app(self, app_path: Path) -> bool:
        """Sign macOS .app bundle."""
        try:
            print(f"📱 Signing .app bundle: {app_path}")
            
            # Sign the app bundle
            sign_command = [
                "codesign",
                "--deep",
                "--force",
                "--verify",
                "--verbose",
                "--sign", self.config["macos"]["developer_id"],
                "--options", "runtime",
                "--entitlements", str(self.project_root / "cli-packages" / "shared" / "signing" / "entitlements.plist"),
                str(app_path)
            ]
            
            result = subprocess.run(sign_command, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Code signing failed: {result.stderr}")
                return False
            
            print("✅ App bundle signed successfully")
            
            # Verify signature
            verify_command = ["codesign", "--verify", "--verbose", str(app_path)]
            result = subprocess.run(verify_command, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Signature verification failed: {result.stderr}")
                return False
            
            print("✅ Signature verified")
            return True
            
        except Exception as e:
            print(f"❌ Failed to sign app bundle: {e}")
            return False
    
    def _sign_macos_dmg(self, dmg_path: Path) -> bool:
        """Sign and notarize macOS DMG."""
        try:
            print(f"💿 Signing DMG: {dmg_path}")
            
            # Sign the DMG
            sign_command = [
                "codesign",
                "--force",
                "--sign", self.config["macos"]["developer_id"],
                str(dmg_path)
            ]
            
            result = subprocess.run(sign_command, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ DMG signing failed: {result.stderr}")
                return False
            
            print("✅ DMG signed successfully")
            
            # Submit for notarization
            print("📤 Submitting for notarization...")
            notarize_command = [
                "xcrun", "notarytool", "submit",
                str(dmg_path),
                "--apple-id", self.config["macos"]["apple_id"],
                "--password", self.config["macos"]["app_password"],
                "--team-id", self.config["macos"]["team_id"],
                "--wait"
            ]
            
            result = subprocess.run(notarize_command, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Notarization failed: {result.stderr}")
                return False
            
            print("✅ Notarization successful")
            
            # Staple the notarization
            staple_command = ["xcrun", "stapler", "staple", str(dmg_path)]
            result = subprocess.run(staple_command, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"⚠️  Stapling failed: {result.stderr}")
                # Not critical, continue
            
            print("✅ DMG notarized and stapled")
            return True
            
        except Exception as e:
            print(f"❌ Failed to sign DMG: {e}")
            return False
    
    def _sign_windows_package(self, package_path: Path) -> bool:
        """Sign Windows package with Authenticode."""
        try:
            print(f"🪟 Signing Windows package: {package_path}")
            
            # Check if signtool is available
            try:
                subprocess.run(["signtool", "/?"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("❌ signtool not found. Install Windows SDK or Visual Studio")
                return False
            
            # Sign the executable
            sign_command = [
                "signtool", "sign",
                "/f", self.config["windows"]["certificate_file"],
                "/p", self.config["windows"]["certificate_password"],
                "/tr", self.config["windows"]["timestamp_url"],
                "/td", "sha256",
                "/fd", "sha256",
                str(package_path)
            ]
            
            result = subprocess.run(sign_command, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Windows signing failed: {result.stderr}")
                return False
            
            print("✅ Windows package signed successfully")
            
            # Verify signature
            verify_command = ["signtool", "verify", "/pa", str(package_path)]
            result = subprocess.run(verify_command, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Signature verification failed: {result.stderr}")
                return False
            
            print("✅ Signature verified")
            return True
            
        except Exception as e:
            print(f"❌ Failed to sign Windows package: {e}")
            return False
    
    def _sign_linux_package(self, package_path: Path) -> bool:
        """Sign Linux package with GPG."""
        try:
            print(f"🐧 Signing Linux package: {package_path}")
            
            # Check if GPG is available
            try:
                subprocess.run(["gpg", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("❌ GPG not found. Install GPG to sign packages")
                return False
            
            # Create detached signature
            signature_path = package_path.with_suffix(package_path.suffix + ".sig")
            sign_command = [
                "gpg",
                "--detach-sign",
                "--armor",
                "--local-user", self.config["linux"]["gpg_key_id"],
                "--output", str(signature_path),
                str(package_path)
            ]
            
            # Set passphrase if provided
            env = os.environ.copy()
            if self.config["linux"]["gpg_passphrase"]:
                env["GPG_TTY"] = "/dev/tty"
            
            result = subprocess.run(sign_command, capture_output=True, text=True, env=env)
            if result.returncode != 0:
                print(f"❌ GPG signing failed: {result.stderr}")
                return False
            
            print(f"✅ Linux package signed: {signature_path}")
            
            # Verify signature
            verify_command = ["gpg", "--verify", str(signature_path), str(package_path)]
            result = subprocess.run(verify_command, capture_output=True, text=True)
            if result.returncode != 0:
                print(f"❌ Signature verification failed: {result.stderr}")
                return False
            
            print("✅ Signature verified")
            return True
            
        except Exception as e:
            print(f"❌ Failed to sign Linux package: {e}")
            return False
    
    def create_entitlements(self) -> bool:
        """Create macOS entitlements file."""
        try:
            entitlements_content = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.cs.allow-jit</key>
    <true/>
    <key>com.apple.security.cs.allow-unsigned-executable-memory</key>
    <true/>
    <key>com.apple.security.cs.disable-executable-page-protection</key>
    <true/>
    <key>com.apple.security.cs.disable-library-validation</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.network.server</key>
    <true/>
</dict>
</plist>"""
            
            entitlements_file = self.project_root / "cli-packages" / "shared" / "signing" / "entitlements.plist"
            entitlements_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(entitlements_file, 'w') as f:
                f.write(entitlements_content)
            
            print(f"✅ Entitlements file created: {entitlements_file}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to create entitlements: {e}")
            return False
    
    def verify_signature(self, package_path: Path) -> bool:
        """Verify package signature."""
        try:
            print(f"🔍 Verifying signature: {package_path}")
            
            if self.system == "Darwin":
                return self._verify_macos_signature(package_path)
            elif self.system == "Windows":
                return self._verify_windows_signature(package_path)
            else:
                return self._verify_linux_signature(package_path)
                
        except Exception as e:
            print(f"❌ Failed to verify signature: {e}")
            return False
    
    def _verify_macos_signature(self, package_path: Path) -> bool:
        """Verify macOS signature."""
        try:
            verify_command = ["codesign", "--verify", "--verbose", str(package_path)]
            result = subprocess.run(verify_command, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ macOS signature verification failed: {e}")
            return False
    
    def _verify_windows_signature(self, package_path: Path) -> bool:
        """Verify Windows signature."""
        try:
            verify_command = ["signtool", "verify", "/pa", str(package_path)]
            result = subprocess.run(verify_command, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Windows signature verification failed: {e}")
            return False
    
    def _verify_linux_signature(self, package_path: Path) -> bool:
        """Verify Linux signature."""
        try:
            signature_path = package_path.with_suffix(package_path.suffix + ".sig")
            if not signature_path.exists():
                print(f"❌ Signature file not found: {signature_path}")
                return False
            
            verify_command = ["gpg", "--verify", str(signature_path), str(package_path)]
            result = subprocess.run(verify_command, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            print(f"❌ Linux signature verification failed: {e}")
            return False


def sign_package(package_path: str) -> bool:
    """Sign a package."""
    signer = PackageSigner(Path.cwd())
    return signer.sign_package(Path(package_path))


def verify_package(package_path: str) -> bool:
    """Verify a package signature."""
    signer = PackageSigner(Path.cwd())
    return signer.verify_signature(Path(package_path))


def create_entitlements() -> bool:
    """Create macOS entitlements file."""
    signer = PackageSigner(Path.cwd())
    return signer.create_entitlements()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python sign_packages.py <command> [package_path]")
        print("Commands:")
        print("  sign <package_path>     - Sign a package")
        print("  verify <package_path>   - Verify package signature")
        print("  entitlements           - Create macOS entitlements file")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "sign":
        if len(sys.argv) < 3:
            print("❌ Package path required for signing")
            sys.exit(1)
        success = sign_package(sys.argv[2])
        sys.exit(0 if success else 1)
    
    elif command == "verify":
        if len(sys.argv) < 3:
            print("❌ Package path required for verification")
            sys.exit(1)
        success = verify_package(sys.argv[2])
        sys.exit(0 if success else 1)
    
    elif command == "entitlements":
        success = create_entitlements()
        sys.exit(0 if success else 1)
    
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)
