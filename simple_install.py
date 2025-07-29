#!/usr/bin/env python3
"""
Simple AI Nautilus Trader Installation Script
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(cmd):
    """Run command and check result."""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(f"Success: {result.stdout}")
    return True

def main():
    print("🚀 AI Nautilus Trader - Simple Installation")
    print("=" * 50)
    
    # Check Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Create virtual environment
    print("📦 Creating virtual environment...")
    if not run_command(f'"{sys.executable}" -m venv ai_trading_env'):
        print("❌ Failed to create virtual environment")
        return False
    
    # Determine pip path
    if os.name == 'nt':  # Windows
        pip_path = "ai_trading_env\\Scripts\\pip"
        python_path = "ai_trading_env\\Scripts\\python"
    else:  # Unix/Linux/macOS
        pip_path = "ai_trading_env/bin/pip"
        python_path = "ai_trading_env/bin/python"
    
    # Upgrade pip
    print("📚 Upgrading pip...")
    if not run_command(f'"{python_path}" -m pip install --upgrade pip'):
        print("❌ Failed to upgrade pip")
        return False
    
    # Install requirements
    print("📦 Installing requirements...")
    if not run_command(f'"{pip_path}" install -r requirements.txt'):
        print("❌ Failed to install requirements")
        return False
    
    # Install package
    print("📦 Installing AI Nautilus Trader package...")
    if not run_command(f'"{pip_path}" install -e .'):
        print("❌ Failed to install package")
        return False
    
    # Test installation
    print("🧪 Testing installation...")
    test_cmd = f'"{python_path}" -c "import ai_nautilus_trader; print(\\"✅ Package imported successfully\\"); ai_nautilus_trader.check_installation()"'
    if not run_command(test_cmd):
        print("❌ Installation test failed")
        return False
    
    print("🎉 Installation completed successfully!")
    print("\nNext steps:")
    print("1. Set your API keys:")
    print("   export OPENAI_API_KEY='your-api-key'")
    print("2. Activate virtual environment:")
    print(f"   source {pip_path.replace('/pip', '/activate')}")
    print("3. Start using the system!")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
