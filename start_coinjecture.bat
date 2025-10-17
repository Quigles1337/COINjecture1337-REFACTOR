@echo off
title COINjecture Blockchain
color 0A

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║                                                              ║
echo  ║  🔬 Mathematical Proof-of-Work Mining                        ║
echo  ║  🌟 Transform blockchain mining into meaningful discovery    ║
echo  ║  💎 Every proof counts. Every discovery pays.                ║
echo  ║                                                              ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

echo 🚀 Starting COINjecture Interactive Menu...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "setup.py" (
    echo ❌ Please run this script from the COINjecture directory
    pause
    exit /b 1
)

REM Run setup if needed
if not exist "src\cli.py" (
    echo 📦 Running initial setup...
    python setup.py --quick-start
)

REM Start the interactive CLI
python -c "import sys; sys.path.append('src'); from cli import COINjectureCLI; cli = COINjectureCLI(); cli.run(['interactive'])"

echo.
echo 👋 Thank you for using COINjecture!
pause
