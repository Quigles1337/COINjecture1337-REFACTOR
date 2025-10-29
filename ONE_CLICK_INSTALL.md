# 🚀 COINjecture One-Click Installation

**The easiest way to install and run COINjecture CLI!**

## 🎯 Quick Start

### **macOS & Linux:**
```bash
curl -s https://raw.githubusercontent.com/beanapologist/COINjecture/main/install_coinjecture.sh | bash
```

### **Windows:**
```cmd
curl -s https://raw.githubusercontent.com/beanapologist/COINjecture/main/install_coinjecture.bat -o install.bat && install.bat
```

## ✨ What It Does

The one-click installer automatically:

1. **✅ Checks Python 3.7+** - Verifies Python installation
2. **📥 Downloads v3.16.0** - Gets the latest package for your platform
3. **🔧 Installs Dependencies** - Automatically installs required packages
4. **⚙️ Creates Configuration** - Sets up optimal mining configuration
5. **🚀 Creates Launchers** - Generates easy-to-use startup scripts
6. **🖥️ Desktop Shortcuts** - Creates desktop shortcuts (if possible)
7. **🧪 Tests Installation** - Verifies everything works correctly

## 📁 Installation Location

- **macOS/Linux**: `~/coinjecture/`
- **Windows**: `%USERPROFILE%\coinjecture\`

## 🎮 After Installation

### **Start COINjecture:**
```bash
cd ~/coinjecture
./start_coinjecture.sh
```

### **Start Mining:**
```bash
./start_mining.sh
```

### **Generate Wallet:**
```bash
./generate_wallet.sh
```

## 🔧 Manual Installation

If you prefer manual installation:

1. **Download** the package for your platform from [GitHub Releases](https://github.com/beanapologist/COINjecture/releases/tag/v3.16.0)
2. **Extract** to your desired location
3. **Install dependencies**: `pip install requests cryptography pycryptodome ipfshttpclient`
4. **Run**: `python3 src/cli.py interactive`

## 🆘 Troubleshooting

### **Python Not Found:**
- **macOS**: `brew install python3`
- **Ubuntu/Debian**: `sudo apt install python3 python3-pip`
- **CentOS/RHEL**: `sudo yum install python3 python3-pip`
- **Windows**: Download from [python.org](https://python.org)

### **Permission Denied:**
```bash
chmod +x install_coinjecture.sh
./install_coinjecture.sh
```

### **Dependencies Issues:**
```bash
pip install --upgrade pip
pip install requests cryptography pycryptodome ipfshttpclient
```

## 🌐 Live Network

- **🌍 Website**: [https://coinjecture.com](https://coinjecture.com)
- **📊 Data Marketplace**: [https://coinjecture.com](https://coinjecture.com) (Marketplace tab)
- **🔗 API Server**: [http://167.172.213.70:12346](http://167.172.213.70:12346)

## 📚 Documentation

- **📖 User Guide**: [GitHub Repository](https://github.com/beanapologist/COINjecture)
- **🔧 API Docs**: [https://coinjecture.com/api-docs](https://coinjecture.com/api-docs)
- **💬 Support**: [GitHub Issues](https://github.com/beanapologist/COINjecture/issues)

---

**Ready to mine $BEANS? Install now and start earning! 🚀**
