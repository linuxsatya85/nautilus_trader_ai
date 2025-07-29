#!/usr/bin/env python3
"""
AI Nautilus Trader - Automated Installation Script
==================================================

This script provides automated installation and setup for the AI Nautilus Trader system.
It handles virtual environment creation, dependency installation, and system configuration.

Usage:
    python install.py [options]

Options:
    --dev          Install development dependencies
    --no-venv      Skip virtual environment creation
    --force        Force reinstallation
    --test         Run tests after installation
"""

import os
import sys
import subprocess
import argparse
import platform
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_colored(message: str, color: str = Colors.OKGREEN):
    """Print colored message to terminal."""
    print(f"{color}{message}{Colors.ENDC}")


def print_header(message: str):
    """Print header message."""
    print_colored(f"\n{'='*60}", Colors.HEADER)
    print_colored(f"{message}", Colors.HEADER)
    print_colored(f"{'='*60}", Colors.HEADER)


def print_step(step: str, message: str):
    """Print installation step."""
    print_colored(f"\n{step} {message}", Colors.OKBLUE)


def print_success(message: str):
    """Print success message."""
    print_colored(f"✅ {message}", Colors.OKGREEN)


def print_warning(message: str):
    """Print warning message."""
    print_colored(f"⚠️ {message}", Colors.WARNING)


def print_error(message: str):
    """Print error message."""
    print_colored(f"❌ {message}", Colors.FAIL)


def run_command(command: str, check: bool = True, capture_output: bool = False):
    """
    Run shell command.
    
    Args:
        command: Command to run
        check: Whether to check return code
        capture_output: Whether to capture output
        
    Returns:
        CompletedProcess result
    """
    print_colored(f"Running: {command}", Colors.OKCYAN)
    
    result = subprocess.run(
        command,
        shell=True,
        check=check,
        capture_output=capture_output,
        text=True
    )
    
    return result


def check_python_version():
    """Check if Python version is compatible."""
    print_step("🐍", "Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python 3.8+ required, found {version.major}.{version.minor}")
        sys.exit(1)
    
    print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")


def create_virtual_environment(force: bool = False):
    """Create virtual environment."""
    print_step("📦", "Setting up virtual environment...")
    
    venv_path = Path("ai_trading_env")
    
    if venv_path.exists() and not force:
        print_warning("Virtual environment already exists, skipping creation")
        return
    
    if venv_path.exists() and force:
        print_warning("Removing existing virtual environment...")
        import shutil
        shutil.rmtree(venv_path)
    
    # Create virtual environment
    run_command(f"{sys.executable} -m venv ai_trading_env")
    print_success("Virtual environment created")


def get_pip_command():
    """Get pip command for current platform."""
    if platform.system() == "Windows":
        return "ai_trading_env\\Scripts\\pip"
    else:
        return "ai_trading_env/bin/pip"


def get_python_command():
    """Get python command for current platform."""
    if platform.system() == "Windows":
        return "ai_trading_env\\Scripts\\python"
    else:
        return "ai_trading_env/bin/python"


def install_dependencies(dev: bool = False):
    """Install Python dependencies."""
    print_step("📚", "Installing dependencies...")
    
    pip_cmd = get_pip_command()
    
    # Upgrade pip
    run_command(f"{pip_cmd} install --upgrade pip")
    
    # Install requirements
    run_command(f"{pip_cmd} install -r requirements.txt")
    
    # Install development dependencies
    if dev:
        print_step("🔧", "Installing development dependencies...")
        run_command(f"{pip_cmd} install pytest pytest-asyncio black flake8 mypy")
    
    print_success("Dependencies installed successfully")


def install_package():
    """Install the AI Nautilus Trader package."""
    print_step("🚀", "Installing AI Nautilus Trader package...")
    
    pip_cmd = get_pip_command()
    
    # Install in development mode
    run_command(f"{pip_cmd} install -e .")
    
    print_success("AI Nautilus Trader package installed")


def verify_installation():
    """Verify the installation."""
    print_step("✅", "Verifying installation...")
    
    python_cmd = get_python_command()
    
    # Test basic import first
    print(f"Running: {python_cmd} -c \"import ai_nautilus_trader; print('✅ Package import successful'); print(f'✅ Version: {{ai_nautilus_trader.get_version()}}')\"")
    result = run_command(
        f'{python_cmd} -c "import ai_nautilus_trader; print(\'✅ Package import successful\'); print(f\'✅ Version: {{ai_nautilus_trader.get_version()}}\')"',
        capture_output=True
    )
    
    if result.returncode != 0:
        print_error("❌ Package import failed")
        print(result.stderr)
        return False
    
    print(result.stdout)
    
    # Test installation check
    print(f"Running: {python_cmd} -c \"import ai_nautilus_trader; ai_nautilus_trader.check_installation()\"")
    result = run_command(
        f'{python_cmd} -c "import ai_nautilus_trader; ai_nautilus_trader.check_installation()"',
        capture_output=True
    )
    
    if result.returncode == 0:
        print_success("✅ Installation verification passed")
        print(result.stdout)
    else:
        print_error("❌ Installation verification failed")
        print(result.stderr)
        return False
    
    return True
    return True


def run_tests():
    """Run the test suite."""
    print_step("🧪", "Running test suite...")
    
    python_cmd = get_python_command()
    
    # Run tests
    test_files = [
        "test_real_crewai_integration.py",
        "test_real_nautilus_integration.py", 
        "test_integration_simple.py"
    ]
    
    for test_file in test_files:
        if Path(test_file).exists():
            print_colored(f"Running {test_file}...", Colors.OKCYAN)
            result = run_command(f"{python_cmd} {test_file}", check=False)
            
            if result.returncode == 0:
                print_success(f"{test_file} passed")
            else:
                print_error(f"{test_file} failed")


def create_config_file():
    """Create default configuration file."""
    print_step("⚙️", "Creating default configuration...")
    
    config_content = """# AI Nautilus Trader Configuration
# Copy this file to config.yaml and customize as needed

system:
  environment: development
  debug: true

api:
  host: 0.0.0.0
  port: 8000

crewai:
  # Set your API key in environment variable: OPENAI_API_KEY
  default_model: gpt-3.5-turbo

nautilus:
  trader_id: AI-TRADER
  environment: simulation

trading:
  enabled: true
  default_instruments:
    - EURUSD
    - GBPUSD
    - USDJPY

risk:
  max_drawdown: 0.05
  max_daily_loss: 0.02
"""
    
    with open("config.example.yaml", "w") as f:
        f.write(config_content)
    
    print_success("Example configuration file created: config.example.yaml")


def main():
    """Main installation function."""
    parser = argparse.ArgumentParser(description="AI Nautilus Trader Installation Script")
    parser.add_argument("--dev", action="store_true", help="Install development dependencies")
    parser.add_argument("--no-venv", action="store_true", help="Skip virtual environment creation")
    parser.add_argument("--force", action="store_true", help="Force reinstallation")
    parser.add_argument("--test", action="store_true", help="Run tests after installation")
    
    args = parser.parse_args()
    
    print_header("AI Nautilus Trader - Automated Installation")
    print_colored("🚀 Complete AI-Enhanced Trading Backend", Colors.HEADER)
    
    try:
        # Check Python version
        check_python_version()
        
        # Create virtual environment
        if not args.no_venv:
            create_virtual_environment(args.force)
        
        # Install dependencies
        install_dependencies(args.dev)
        
        # Install package
        install_package()
        
        # Create config file
        create_config_file()
        
        # Verify installation
        if verify_installation():
            print_header("🎉 INSTALLATION COMPLETED SUCCESSFULLY!")
            
            print_colored("\n📋 Next Steps:", Colors.OKBLUE)
            print_colored("1. Set your API keys in environment variables:", Colors.OKGREEN)
            print_colored("   export OPENAI_API_KEY='your-api-key'", Colors.OKCYAN)
            print_colored("2. Copy and customize the configuration:", Colors.OKGREEN)
            print_colored("   cp config.example.yaml config.yaml", Colors.OKCYAN)
            print_colored("3. Start the AI trading system:", Colors.OKGREEN)
            print_colored("   ai_trading_env/bin/python -c 'import ai_nautilus_trader; ai_nautilus_trader.check_installation()'", Colors.OKCYAN)
            
            # Run tests if requested
            if args.test:
                run_tests()
        
        else:
            print_error("Installation failed verification")
            sys.exit(1)
    
    except Exception as e:
        print_error(f"Installation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
