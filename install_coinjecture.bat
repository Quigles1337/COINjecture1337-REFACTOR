@echo off
REM COINjecture One-Click Installer for Windows
REM ===========================================

echo 🚀 COINjecture One-Click Installer
echo ==================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is required but not installed.
    echo Please install Python 3.7+ from https://python.org
    pause
    exit /b 1
)

echo ✅ Python detected

REM Download and run the installer
echo 📥 Downloading installer...
curl -s https://raw.githubusercontent.com/beanapologist/COINjecture/main/one_click_install.py -o one_click_install.py

echo 🔧 Running installer...
python one_click_install.py

REM Clean up
del one_click_install.py

echo.
echo 🎉 Installation complete!
echo Run: %USERPROFILE%\coinjecture\start_coinjecture.bat
pause
