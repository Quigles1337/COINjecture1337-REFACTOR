#!/usr/bin/env python3
"""
COINjecture Package Builder

Automated build script for creating cross-platform distribution packages.
Builds standalone executables for macOS, Windows, and Linux.
"""

import os
import sys
import subprocess
import platform
import shutil
import argparse
from pathlib import Path

class PackageBuilder:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.cli_packages_dir = self.project_root / "cli-packages"
        self.dist_dir = self.project_root / "dist"
        self.packages_dir = self.dist_dir / "packages"
        self.version = "3.6.0"
        
        # Create directories
        self.dist_dir.mkdir(exist_ok=True)
        self.packages_dir.mkdir(exist_ok=True)
    
    def log(self, message, level="INFO"):
        """Log a message with timestamp."""
        timestamp = subprocess.check_output(['date'], text=True).strip()
        print(f"[{timestamp}] {level}: {message}")
    
    def run_command(self, command, description, cwd=None):
        """Run a command and handle errors."""
        self.log(f"Running: {description}")
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                check=True, 
                capture_output=True, 
                text=True,
                cwd=cwd or self.project_root
            )
            self.log(f"✅ {description} completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            self.log(f"❌ {description} failed: {e.stderr}", "ERROR")
            return False
    
    def check_dependencies(self):
        """Check if required dependencies are installed."""
        self.log("Checking dependencies...")
        
        # Check PyInstaller
        try:
            subprocess.run(['pyinstaller', '--version'], check=True, capture_output=True)
            self.log("✅ PyInstaller is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("❌ PyInstaller not found. Installing...", "ERROR")
            if not self.run_command("pip3 install pyinstaller", "Installing PyInstaller"):
                return False
        
        # Check Python version
        if sys.version_info < (3, 8):
            self.log(f"❌ Python 3.8+ required, found {sys.version}", "ERROR")
            return False
        
        self.log(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} is compatible")
        return True
    
    def create_icons(self):
        """Create application icons for all platforms."""
        self.log("Creating application icons...")
        
        assets_dir = self.cli_packages_dir / "shared" / "launcher"
        assets_dir.mkdir(exist_ok=True)
        
        # Create a simple text-based icon as placeholder
        # In a real implementation, you'd use proper icon files
        icon_content = """# COINjecture Icon Placeholder
# This would be replaced with actual icon files:
# - icon.ico (Windows)
# - icon.icns (macOS) 
# - icon.png (Linux)
"""
        
        for icon_file in ["icon.ico", "icon.icns", "icon.png"]:
            icon_path = assets_dir / icon_file
            if not icon_path.exists():
                with open(icon_path, 'w') as f:
                    f.write(icon_content)
                self.log(f"Created placeholder: {icon_file}")
        
        return True
    
    def create_version_info(self):
        """Create version info file for Windows."""
        self.log("Creating version info...")
        
        version_info = f"""# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    # filevers and prodvers should be always a tuple with four items: (1, 2, 3, 4)
    # Set not needed items to zero 0.
    filevers=(3,4,0,0),
    prodvers=(3,4,0,0),
    # Contains a bitmask that specifies the valid bits 'flags'r
    mask=0x3f,
    # Contains a bitmask that specifies the Boolean attributes of the file.
    flags=0x0,
    # The operating system for which this file was designed.
    # 0x4 - NT and there is no need to change it.
    OS=0x4,
    # The general type of file.
    # 0x1 - the file is an application.
    fileType=0x1,
    # The function of the file.
    # 0x0 - the function is not defined for this fileType
    subtype=0x0,
    # Creation date and time stamp.
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'COINjecture'),
        StringStruct(u'FileDescription', u'COINjecture - Proof-of-Work Blockchain'),
        StringStruct(u'FileVersion', u'{self.version}'),
        StringStruct(u'InternalName', u'COINjecture'),
        StringStruct(u'LegalCopyright', u'Copyright (C) 2025 COINjecture'),
        StringStruct(u'OriginalFilename', u'COINjecture.exe'),
        StringStruct(u'ProductName', u'COINjecture'),
        StringStruct(u'ProductVersion', u'{self.version}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
        
        version_file = self.cli_packages_dir / "shared" / "launcher" / "version_info.txt"
        with open(version_file, 'w') as f:
            f.write(version_info)
        
        self.log("✅ Version info created")
        return True
    
    def build_executable(self, platform_name):
        """Build executable for specified platform."""
        self.log(f"Building executable for {platform_name}...")
        
        # Clean previous builds
        build_dir = self.project_root / "build"
        dist_executable_dir = self.dist_dir / "COINjecture"
        
        if build_dir.exists():
            shutil.rmtree(build_dir)
        if dist_executable_dir.exists():
            shutil.rmtree(dist_executable_dir)
        
        # Run PyInstaller
        spec_file = self.cli_packages_dir / "shared" / "specs" / "coinjecture.spec"
        if not self.run_command(f"pyinstaller {spec_file}", f"Building {platform_name} executable"):
            return False
        
        # Move executable to packages directory
        executable_name = f"COINjecture-{self.version}-{platform_name}"
        if platform_name == "Windows":
            executable_name += ".exe"
        elif platform_name == "macOS":
            executable_name += ".app"
        elif platform_name == "Linux":
            executable_name += ".AppImage"
        
        source_path = self.dist_dir / "COINjecture"
        target_path = self.packages_dir / executable_name
        
        if source_path.exists():
            if target_path.exists():
                shutil.rmtree(target_path)
            shutil.move(str(source_path), str(target_path))
            self.log(f"✅ {platform_name} executable created: {executable_name}")
            return True
        else:
            self.log(f"❌ Executable not found at {source_path}", "ERROR")
            return False
    
    def create_dmg(self):
        """Create DMG installer for macOS."""
        self.log("Creating macOS DMG installer...")
        
        app_path = self.packages_dir / f"COINjecture-{self.version}-macOS.app"
        dmg_path = self.packages_dir / f"COINjecture-{self.version}-macOS.dmg"
        
        if not app_path.exists():
            self.log("❌ macOS app not found", "ERROR")
            return False
        
        # Create DMG using hdiutil
        dmg_command = f"""
        hdiutil create -volname "COINjecture {self.version}" -srcfolder "{app_path}" -ov -format UDZO "{dmg_path}"
        """
        
        if self.run_command(dmg_command, "Creating DMG installer"):
            # Remove the app directory since we now have the DMG
            shutil.rmtree(app_path)
            self.log("✅ macOS DMG created successfully")
            return True
        else:
            return False
    
    def create_windows_installer(self):
        """Create Windows installer using NSIS."""
        self.log("Creating Windows installer...")
        
        exe_path = self.packages_dir / f"COINjecture-{self.version}-Windows.exe"
        installer_path = self.packages_dir / f"COINjecture-{self.version}-Windows-Installer.exe"
        
        if not exe_path.exists():
            self.log("❌ Windows executable not found", "ERROR")
            return False
        
        # Create NSIS script
        nsis_script = f"""
!define APPNAME "COINjecture"
!define COMPANYNAME "COINjecture"
!define DESCRIPTION "Proof-of-Work Blockchain"
!define VERSIONMAJOR 3
!define VERSIONMINOR 4
!define VERSIONBUILD 0
!define HELPURL "https://github.com/beanapologist/COINjecture"
!define UPDATEURL "https://github.com/beanapologist/COINjecture"
!define ABOUTURL "https://github.com/beanapologist/COINjecture"
!define INSTALLSIZE 100000

RequestExecutionLevel admin
InstallDir "$PROGRAMFILES\\${{APPNAME}}"
Name "${{COMPANYNAME}} - ${{APPNAME}}"
outFile "{installer_path}"
icon "icon.ico"
installDirRegKey HKLM "Software\\${{COMPANYNAME}}\\${{APPNAME}}" ""
page directory
page instfiles

section "install"
    setOutPath $INSTDIR
    file "{exe_path}"
    writeUninstaller "$INSTDIR\\uninstall.exe"
    createDirectory "$SMPROGRAMS\\${{COMPANYNAME}}"
    createShortCut "$SMPROGRAMS\\${{COMPANYNAME}}\\${{APPNAME}}.lnk" "$INSTDIR\\COINjecture-{self.version}-Windows.exe" "" "$INSTDIR\\COINjecture-{self.version}-Windows.exe"
    createShortCut "$DESKTOP\\${{APPNAME}}.lnk" "$INSTDIR\\COINjecture-{self.version}-Windows.exe" "" "$INSTDIR\\COINjecture-{self.version}-Windows.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "DisplayName" "${{COMPANYNAME}} - ${{APPNAME}} - ${{DESCRIPTION}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "UninstallString" "$\\"$INSTDIR\\uninstall.exe$\\""
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "InstallLocation" "$\\"$INSTDIR$\\""
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "DisplayIcon" "$\\"$INSTDIR\\COINjecture-{self.version}-Windows.exe$\\""
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "Publisher" "${{COMPANYNAME}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "HelpLink" "${{HELPURL}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "URLUpdateInfo" "${{UPDATEURL}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "URLInfoAbout" "${{ABOUTURL}}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "DisplayVersion" "${{VERSIONMAJOR}}.${{VERSIONMINOR}}.${{VERSIONBUILD}}"
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "VersionMajor" ${{VERSIONMAJOR}}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "VersionMinor" ${{VERSIONMINOR}}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "NoModify" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "NoRepair" 1
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}" "EstimatedSize" ${{INSTALLSIZE}}
sectionEnd

section "uninstall"
    delete "$INSTDIR\\COINjecture-{self.version}-Windows.exe"
    delete "$INSTDIR\\uninstall.exe"
    rmDir $INSTDIR
    delete "$SMPROGRAMS\\${{COMPANYNAME}}\\${{APPNAME}}.lnk"
    rmDir "$SMPROGRAMS\\${{COMPANYNAME}}"
    delete "$DESKTOP\\${{APPNAME}}.lnk"
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${{COMPANYNAME}} ${{APPNAME}}"
    DeleteRegKey /ifempty HKLM "Software\\${{COMPANYNAME}}"
sectionEnd
"""
        
        nsis_file = self.packaging_dir / "installers" / "windows_installer.nsi"
        nsis_file.parent.mkdir(exist_ok=True)
        
        with open(nsis_file, 'w') as f:
            f.write(nsis_script)
        
        # Check if NSIS is available
        try:
            subprocess.run(['makensis', '/VERSION'], check=True, capture_output=True)
            if self.run_command(f'makensis "{nsis_file}"', "Creating Windows installer"):
                self.log("✅ Windows installer created successfully")
                return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("⚠️ NSIS not found, skipping Windows installer creation", "WARNING")
            return True  # Not a failure, just skip installer
        
        return False
    
    def create_appimage(self):
        """Create AppImage for Linux."""
        self.log("Creating Linux AppImage...")
        
        # For now, just rename the executable to .AppImage
        # In a real implementation, you'd use appimagetool
        exe_path = self.packages_dir / f"COINjecture-{self.version}-Linux"
        appimage_path = self.packages_dir / f"COINjecture-{self.version}-Linux.AppImage"
        
        if exe_path.exists():
            shutil.move(str(exe_path), str(appimage_path))
            # Make executable
            os.chmod(appimage_path, 0o755)
            self.log("✅ Linux AppImage created successfully")
            return True
        else:
            self.log("❌ Linux executable not found", "ERROR")
            return False
    
    def build_all(self):
        """Build packages for all platforms."""
        self.log("Starting build process for all platforms...")
        
        # Check dependencies
        if not self.check_dependencies():
            return False
        
        # Create assets
        if not self.create_icons():
            return False
        
        if not self.create_version_info():
            return False
        
        # Build for current platform
        current_platform = platform.system()
        if current_platform == "Darwin":
            platform_name = "macOS"
        elif current_platform == "Windows":
            platform_name = "Windows"
        else:
            platform_name = "Linux"
        
        self.log(f"Building for current platform: {platform_name}")
        
        if not self.build_executable(platform_name):
            return False
        
        # Create platform-specific packages
        if platform_name == "macOS":
            if not self.create_dmg():
                return False
        elif platform_name == "Windows":
            if not self.create_windows_installer():
                return False
        elif platform_name == "Linux":
            if not self.create_appimage():
                return False
        
        self.log("🎉 All packages built successfully!")
        self.show_summary()
        return True
    
    def show_summary(self):
        """Show build summary."""
        self.log("Build Summary:")
        print("\n" + "="*60)
        print("📦 COINjecture Package Build Complete!")
        print("="*60)
        
        if self.packages_dir.exists():
            packages = list(self.packages_dir.iterdir())
            if packages:
                print(f"\n📁 Packages created in: {self.packages_dir}")
                for package in packages:
                    size = package.stat().st_size / (1024 * 1024)  # MB
                    print(f"   • {package.name} ({size:.1f} MB)")
            else:
                print("\n❌ No packages found")
        
        print("\n🚀 Next Steps:")
        print("1. Test packages on target platforms")
        print("2. Upload to GitHub Releases")
        print("3. Update download links in documentation")
        print("4. Share with users!")
        print("\n" + "="*60)

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Build COINjecture packages")
    parser.add_argument("--all", action="store_true", help="Build for all platforms")
    parser.add_argument("--platform", choices=["macOS", "Windows", "Linux"], help="Build for specific platform")
    parser.add_argument("--clean", action="store_true", help="Clean build directories")
    
    args = parser.parse_args()
    
    builder = PackageBuilder()
    
    if args.clean:
        builder.log("Cleaning build directories...")
        for dir_path in [builder.project_root / "build", builder.dist_dir]:
            if dir_path.exists():
                shutil.rmtree(dir_path)
                builder.log(f"Cleaned: {dir_path}")
        return
    
    if args.platform:
        # Build for specific platform
        if not builder.check_dependencies():
            sys.exit(1)
        if not builder.create_icons():
            sys.exit(1)
        if not builder.create_version_info():
            sys.exit(1)
        if not builder.build_executable(args.platform):
            sys.exit(1)
    else:
        # Build for current platform
        if not builder.build_all():
            sys.exit(1)

if __name__ == "__main__":
    main()
