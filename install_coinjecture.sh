#!/bin/bash
# COINjecture One-Click Installer
# ===============================

set -e

echo "🚀 COINjecture One-Click Installer"
echo "=================================="
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.7+ first:"
    echo "  macOS: brew install python3"
    echo "  Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "  CentOS/RHEL: sudo yum install python3 python3-pip"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.7"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.7+ is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Download and run the installer
echo "📥 Downloading installer..."
curl -s https://raw.githubusercontent.com/beanapologist/COINjecture/main/one_click_install.py -o one_click_install.py

echo "🔧 Running installer..."
python3 one_click_install.py

# Clean up
rm -f one_click_install.py

echo ""
echo "🎉 Installation complete!"
echo "Run: ~/coinjecture/start_coinjecture.sh"
