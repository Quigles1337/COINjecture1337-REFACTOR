# 🚀 COINjecture v3.16.0 Release Announcement

**Date**: December 25, 2024  
**Version**: v3.16.0  
**Type**: Major Release - CLI Fixes & Data Marketplace

---

## 🎉 **What's New in v3.16.0**

### 🔧 **CLI Fixes & Improvements**
- **✅ 426 Error Fixed**: CLI now uses API server for IPFS access instead of direct connection
- **✅ Mining Validation Fixed**: Subset sum solver now prevents duplicate solutions
- **✅ Block Submission Fixed**: Added solution_data and problem_data to block submission payload
- **✅ Verification Updated**: Now uses ProblemRegistry for proper consensus validation
- **✅ IPFS Integration**: CLI now matches web version configuration (port 12346)

### 🏪 **Data Marketplace Integration**
- **✅ New Marketplace Page**: Integrated data marketplace into main website
- **✅ Live Statistics**: Real-time blockchain data display
- **✅ Research Products**: Computational complexity datasets and IPFS samples
- **✅ Pricing Tiers**: $BEANS and USD pricing options
- **✅ API Demo**: Interactive API testing interface
- **✅ Sample Downloads**: Free data samples for evaluation

### 🌐 **Web Interface Enhancements**
- **✅ SPA Integration**: Marketplace fully integrated into single-page application
- **✅ Responsive Design**: Mobile-optimized marketplace interface
- **✅ SEO Optimization**: Updated sitemap and meta tags
- **✅ Cache Busting**: Improved script loading and updates

---

## 📦 **Download Now**

### **GitHub Release**
🔗 **[Download v3.16.0 Packages](https://github.com/beanapologist/COINjecture/releases/tag/v3.16.0)**

### **Platform Packages**
- **🍎 macOS**: [COINjecture-macOS-v3.16.0-Python.zip](https://github.com/beanapologist/COINjecture/releases/download/v3.16.0/COINjecture-macOS-v3.16.0-Python.zip) (348K)
- **🪟 Windows**: [COINjecture-Windows-v3.16.0-Python.zip](https://github.com/beanapologist/COINjecture/releases/download/v3.16.0/COINjecture-Windows-v3.16.0-Python.zip) (348K)
- **🐧 Linux**: [COINjecture-Linux-v3.16.0-Python.zip](https://github.com/beanapologist/COINjecture/releases/download/v3.16.0/COINjecture-Linux-v3.16.0-Python.zip) (348K)

### **Web Interface**
🌐 **[Live Website](https://coinjecture.com)** - Now with integrated Data Marketplace!

---

## 🚀 **Quick Start**

### **Installation**
1. **Download** the package for your platform
2. **Extract** and run `./install.sh`
3. **Start** with `./start_coinjecture.sh` (Unix) or `start_coinjecture.bat` (Windows)
4. **Choose** "Interactive Menu" for guided experience

### **CLI Commands**
```bash
# Generate wallet
python3 src/cli.py wallet-generate --output ./my_wallet.json

# Check balance
python3 src/cli.py wallet-balance --wallet ./my_wallet.json

# Start mining (now with fixed validation!)
python3 src/cli.py mine --config ./config.json

# Interactive menu
python3 src/cli.py interactive
```

---

## 🌐 **Live Services**

- **🌍 Website**: [https://coinjecture.com](https://coinjecture.com)
- **📊 Data Marketplace**: [https://coinjecture.com](https://coinjecture.com) (Marketplace tab)
- **🔗 API Server**: [http://167.172.213.70:12346](http://167.172.213.70:12346)
- **❤️ Health Check**: [http://167.172.213.70:12346/health](http://167.172.213.70:12346/health)

---

## 🎯 **What This Means for You**

### **For Miners**
- **✅ No More 426 Errors**: CLI now works seamlessly with the API server
- **✅ Valid Mining**: Solutions are properly validated before submission
- **✅ Better Success Rate**: Mining operations now succeed consistently

### **For Researchers**
- **✅ Data Marketplace**: Access to computational complexity datasets
- **✅ Sample Data**: Free samples to evaluate data quality
- **✅ API Access**: Direct access to live blockchain data

### **For Developers**
- **✅ Consistent API**: CLI and web use the same endpoints
- **✅ Better Error Handling**: Improved debugging and error messages
- **✅ Updated Documentation**: Complete guides and references

---

## 🔗 **Community & Support**

- **📚 Documentation**: [GitHub Repository](https://github.com/beanapologist/COINjecture)
- **🐛 Issues**: [Report bugs and request features](https://github.com/beanapologist/COINjecture/issues)
- **💬 Discussions**: [Community discussions](https://github.com/beanapologist/COINjecture/discussions)
- **⭐ Star**: [Show your support](https://github.com/beanapologist/COINjecture)

---

## 🎉 **Ready to Mine!**

Your COINjecture CLI v3.16.0 is ready with:
- ✅ **CLI Fixes** - 426 error resolved, mining validation fixed
- ✅ **Data Marketplace** - Integrated research data sales platform
- ✅ **Dynamic Gas Calculation** - Real computational complexity-based gas costs
- ✅ **Enhanced CLI** - Updated commands with proper validation
- ✅ **Live Mining** - Real-time gas calculation during mining
- ✅ **API Integration** - Full integration with live server

**Start mining and experience the new CLI fixes and data marketplace!** 🚀

---

**Built with ❤️ for the COINjecture community - Version 3.16.0**

*Visit our live server: [https://coinjecture.com](https://coinjecture.com)*
