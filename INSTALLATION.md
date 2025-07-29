# 🚀 AI Nautilus Trader - Installation Guide

Complete installation guide for the AI Nautilus Trader backend system.

## 📋 Prerequisites

### **System Requirements**
- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 2GB free space
- **Internet**: Required for dependency installation

### **Required Tools**
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check pip
pip --version

# Check git
git --version
```

## 🚀 Quick Installation (Recommended)

### **Step 1: Clone Repository**
```bash
git clone https://github.com/linuxsatya85/nautilus_trader_ai.git
cd nautilus_trader_ai
```

### **Step 2: Run Automated Installer**
```bash
# Run the automated installation script
python install.py

# The installer will:
# ✅ Create virtual environment
# ✅ Install all dependencies
# ✅ Configure the package
# ✅ Run verification tests
```

### **Step 3: Set API Keys (Optional)**
```bash
# Set OpenAI API key for AI functionality
export OPENAI_API_KEY="your-openai-api-key"

# Optional: Set additional API keys
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export GOOGLE_API_KEY="your-google-api-key"
```

### **Step 4: Verify Installation**
```bash
# Activate virtual environment
source ai_trading_env/bin/activate

# Verify installation
python -c "import ai_nautilus_trader; ai_nautilus_trader.check_installation()"
```

## 🔧 Manual Installation

If you prefer manual installation or the automated installer fails:

### **Step 1: Clone Repository**
```bash
git clone https://github.com/linuxsatya85/nautilus_trader_ai.git
cd nautilus_trader_ai
```

### **Step 2: Create Virtual Environment**
```bash
# Create virtual environment
python3 -m venv ai_trading_env

# Activate virtual environment
# On Linux/macOS:
source ai_trading_env/bin/activate

# On Windows:
ai_trading_env\Scripts\activate
```

### **Step 3: Upgrade pip**
```bash
pip install --upgrade pip
```

### **Step 4: Install Dependencies**
```bash
# Install all required dependencies
pip install -r requirements.txt
```

### **Step 5: Install Package**
```bash
# Install the AI Nautilus Trader package in development mode
pip install -e .
```

### **Step 6: Verify Installation**
```bash
python -c "import ai_nautilus_trader; ai_nautilus_trader.check_installation()"
```

## 🧪 Testing Installation

### **Run Test Suite**
```bash
# Activate virtual environment
source ai_trading_env/bin/activate

# Run individual tests
python test_real_crewai_integration.py
python test_real_nautilus_integration.py
python test_integration_simple.py

# Or run all tests with installer
python install.py --test
```

### **Expected Test Results**
```
✅ AI Nautilus Trader installation verified!
✅ Version: 1.0.0
✅ CrewAI: 0.95.0
✅ Nautilus Trader: Available
✅ Integration Adapters: Working
```

## ⚙️ Configuration

### **Environment Variables**
Create a `.env` file in the project root:
```bash
# Required for AI functionality
OPENAI_API_KEY=your-openai-api-key

# Optional
ANTHROPIC_API_KEY=your-anthropic-api-key
GOOGLE_API_KEY=your-google-api-key
ENVIRONMENT=development
API_HOST=0.0.0.0
API_PORT=8000
TRADING_ENABLED=true
LOG_LEVEL=INFO
```

### **Configuration File**
Copy and customize the example configuration:
```bash
cp config.example.yaml config.yaml
# Edit config.yaml with your settings
```

## 🚀 Quick Start

### **Basic Usage**
```python
# test_basic.py
import asyncio
from ai_nautilus_trader import AITradingSystem

async def main():
    system = AITradingSystem()
    await system.start()
    print(f"Status: {system.get_status()}")
    await system.stop()

asyncio.run(main())
```

### **Run the Test**
```bash
source ai_trading_env/bin/activate
python test_basic.py
```

## 🔧 Troubleshooting

### **Common Issues**

#### **1. Python Version Error**
```
Error: Python 3.8+ required
```
**Solution**: Install Python 3.8 or higher
```bash
# Check version
python3 --version

# Install Python 3.8+ if needed
# On Ubuntu/Debian:
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-dev

# On macOS:
brew install python@3.8

# On Windows:
# Download from https://python.org
```

#### **2. Virtual Environment Issues**
```
Error: Failed to create virtual environment
```
**Solution**: Install venv module
```bash
# On Ubuntu/Debian:
sudo apt install python3-venv

# On CentOS/RHEL:
sudo yum install python3-venv
```

#### **3. Dependency Installation Failures**
```
Error: Failed to install requirements
```
**Solution**: Update pip and try again
```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

#### **4. Import Errors**
```
ImportError: No module named 'ai_nautilus_trader'
```
**Solution**: Ensure virtual environment is activated and package is installed
```bash
source ai_trading_env/bin/activate
pip install -e .
```

#### **5. API Key Issues**
```
Error: Invalid API key
```
**Solution**: Set valid API keys
```bash
export OPENAI_API_KEY="sk-your-actual-api-key"
```

### **Getting Help**

#### **Check Installation**
```bash
# Detailed installation check
source ai_trading_env/bin/activate
python -c "
import ai_nautilus_trader
print('Package Info:', ai_nautilus_trader.get_info())
ai_nautilus_trader.check_installation()
"
```

#### **Check Dependencies**
```bash
# List installed packages
pip list

# Check specific packages
pip show crewai
pip show nautilus-trader
```

#### **Check System Info**
```bash
python -c "
from ai_nautilus_trader.utils import get_system_info
import json
print(json.dumps(get_system_info(), indent=2))
"
```

## 🔄 Updating

### **Update from Git**
```bash
# Pull latest changes
git pull origin main

# Reinstall dependencies
source ai_trading_env/bin/activate
pip install -r requirements.txt
pip install -e .

# Verify update
python -c "import ai_nautilus_trader; ai_nautilus_trader.check_installation()"
```

## 🗑️ Uninstallation

### **Remove Installation**
```bash
# Remove virtual environment
rm -rf ai_trading_env

# Remove package (if installed globally)
pip uninstall ai-nautilus-trader

# Remove project directory
cd ..
rm -rf nautilus_trader_ai
```

## 📞 Support

If you encounter issues:

1. **Check this guide** for common solutions
2. **Run diagnostics**: `python install.py --test`
3. **Check logs**: Look in `logs/` directory
4. **Create issue**: [GitHub Issues](https://github.com/linuxsatya85/nautilus_trader_ai/issues)
5. **Join discussions**: [GitHub Discussions](https://github.com/linuxsatya85/nautilus_trader_ai/discussions)

## 📝 Next Steps

After successful installation:

1. **Configure API keys** for AI functionality
2. **Customize configuration** in `config.yaml`
3. **Run tests** to verify everything works
4. **Start developing** your AI trading strategies
5. **Deploy** for production use

---

**🎉 You're ready to build AI-powered trading systems!**
