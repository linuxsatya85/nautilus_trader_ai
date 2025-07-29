"""
AI Nautilus Trader - Complete AI-Enhanced Trading Backend
=========================================================

A production-ready AI trading system that integrates CrewAI and Nautilus Trader
frameworks with custom adapters for intelligent trading operations.

This package provides:
- Complete CrewAI framework for AI agent management
- Complete Nautilus Trader framework for trading operations
- Custom integration adapters connecting both systems
- REST API for frontend integration
- Configuration management system
- Comprehensive testing suite

Quick Start:
-----------
```python
from ai_nautilus_trader import AITradingSystem

# Initialize the trading system
trading_system = AITradingSystem()

# Start the AI trading backend
trading_system.start()
```

API Usage:
----------
```python
from ai_nautilus_trader.api import TradingAPI

# Create API instance
api = TradingAPI()

# Start the REST API server
api.run(host="0.0.0.0", port=8000)
```

Components:
-----------
- ai_nautilus_trader.core: Core integration layer
- ai_nautilus_trader.adapters: CrewAI and Nautilus adapters  
- ai_nautilus_trader.api: REST API endpoints
- ai_nautilus_trader.config: Configuration management
- ai_nautilus_trader.utils: Utility functions
- ai_nautilus_trader.cli: Command-line interface

Author: AI Trading Systems
License: MIT
Version: 1.0.0
"""

__version__ = "1.0.0"
__author__ = "AI Trading Systems"
__license__ = "MIT"

# Core imports
from .core.trading_system import AITradingSystem
from .core.manager import TradingManager
from .adapters.real_crewai_adapter import RealCrewAIAdapter
from .adapters.real_nautilus_adapter import RealNautilusAdapter

# API imports
from .api.server import TradingAPI
from .api.endpoints import TradingEndpoints

# Configuration imports
from .config.settings import Settings, load_config
from .config.environment import Environment

# Utility imports
from .utils.logger import setup_logging
from .utils.helpers import validate_config, check_dependencies

__all__ = [
    # Core classes
    "AITradingSystem",
    "TradingManager", 
    "RealCrewAIAdapter",
    "RealNautilusAdapter",
    
    # API classes
    "TradingAPI",
    "TradingEndpoints",
    
    # Configuration
    "Settings",
    "Environment",
    "load_config",
    
    # Utilities
    "setup_logging",
    "validate_config", 
    "check_dependencies",
]

# Package metadata
__package_info__ = {
    "name": "ai-nautilus-trader",
    "version": __version__,
    "description": "Complete AI-Enhanced Trading Backend",
    "frameworks": {
        "crewai": "0.95.0+",
        "nautilus_trader": "1.219.0+",
    },
    "features": [
        "AI Agent Management",
        "Professional Trading Infrastructure", 
        "Real-time Market Data",
        "Order Management System",
        "Risk Management",
        "Backtesting Engine",
        "REST API",
        "WebSocket Streaming",
    ],
}

def get_version():
    """Get the package version."""
    return __version__

def get_info():
    """Get package information."""
    return __package_info__

def check_installation():
    """Check if the package is properly installed."""
    try:
        # Check core dependencies
        import crewai
        import nautilus_trader
        
        # Check integration adapters
        from .adapters.real_crewai_adapter import RealCrewAIAdapter
        from .adapters.real_nautilus_adapter import RealNautilusAdapter
        
        print("✅ AI Nautilus Trader installation verified!")
        print(f"✅ Version: {__version__}")
        print(f"✅ CrewAI: {crewai.__version__}")
        print(f"✅ Nautilus Trader: Available")
        print(f"✅ Integration Adapters: Working")
        
        return True
        
    except ImportError as e:
        print(f"❌ Installation check failed: {e}")
        return False

# Initialize logging when package is imported
setup_logging()
