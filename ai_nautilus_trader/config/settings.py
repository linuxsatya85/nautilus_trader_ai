"""
Settings and Configuration Management
====================================

This module provides the main Settings class and configuration utilities
for the AI Nautilus Trader system.
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path

from ..utils.logger import get_logger

logger = get_logger(__name__)


class Settings:
    """
    Main configuration class for AI Nautilus Trader.
    
    Handles loading, validation, and management of all system settings.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize settings.
        
        Args:
            config: Optional configuration dictionary
        """
        # Default configuration
        self._config = self._get_default_config()
        
        # Update with provided config
        if config:
            self._config.update(config)
        
        # Load from environment variables
        self._load_from_env()
        
        logger.info("⚙️ Settings initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            # System settings
            "system": {
                "name": "AI Nautilus Trader",
                "version": "1.0.0",
                "environment": "development",
                "debug": True,
                "log_level": "INFO",
            },
            
            # API settings
            "api": {
                "host": "0.0.0.0",
                "port": 8000,
                "cors_enabled": True,
                "cors_origins": ["*"],
                "rate_limiting": True,
                "max_requests_per_minute": 100,
            },
            
            # CrewAI settings
            "crewai": {
                "default_model": "gpt-3.5-turbo",
                "api_key": None,  # Set via environment variable
                "max_agents": 10,
                "agent_timeout": 30,
                "crew_timeout": 300,
            },
            
            # Nautilus Trader settings
            "nautilus": {
                "trader_id": "AI-TRADER",
                "environment": "simulation",
                "cache_database": "redis://localhost:6379",
                "risk_engine_enabled": True,
                "max_position_size": 1000000,
            },
            
            # Trading settings
            "trading": {
                "enabled": True,
                "default_instruments": ["EURUSD", "GBPUSD", "USDJPY"],
                "default_timeframe": "1m",
                "max_orders_per_minute": 10,
                "position_sizing": "fixed",
                "default_quantity": 10000,
            },
            
            # Risk management
            "risk": {
                "max_drawdown": 0.05,  # 5%
                "max_daily_loss": 0.02,  # 2%
                "position_limit": 0.1,  # 10% of portfolio
                "stop_loss": 0.01,  # 1%
                "take_profit": 0.02,  # 2%
            },
            
            # Data settings
            "data": {
                "providers": ["simulation"],
                "cache_enabled": True,
                "cache_duration": 3600,  # 1 hour
                "real_time_enabled": True,
            },
            
            # Logging settings
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file_enabled": True,
                "file_path": "logs/ai_nautilus_trader.log",
                "max_file_size": "10MB",
                "backup_count": 5,
            },
        }
    
    def _load_from_env(self):
        """Load configuration from environment variables."""
        # API Keys
        if os.getenv("OPENAI_API_KEY"):
            self._config["crewai"]["api_key"] = os.getenv("OPENAI_API_KEY")
        
        if os.getenv("ANTHROPIC_API_KEY"):
            self._config["crewai"]["anthropic_api_key"] = os.getenv("ANTHROPIC_API_KEY")
        
        # System environment
        if os.getenv("ENVIRONMENT"):
            self._config["system"]["environment"] = os.getenv("ENVIRONMENT")
        
        # API settings
        if os.getenv("API_HOST"):
            self._config["api"]["host"] = os.getenv("API_HOST")
        
        if os.getenv("API_PORT"):
            self._config["api"]["port"] = int(os.getenv("API_PORT"))
        
        # Trading settings
        if os.getenv("TRADING_ENABLED"):
            self._config["trading"]["enabled"] = os.getenv("TRADING_ENABLED").lower() == "true"
        
        logger.info("⚙️ Environment variables loaded")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation, e.g., 'api.host')
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any):
        """
        Set configuration value by key.
        
        Args:
            key: Configuration key (supports dot notation)
            value: Value to set
        """
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
        logger.info(f"⚙️ Configuration updated: {key} = {value}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Get configuration as dictionary."""
        return self._config.copy()
    
    def save(self, filepath: Union[str, Path]):
        """
        Save configuration to file.
        
        Args:
            filepath: Path to save configuration file
        """
        filepath = Path(filepath)
        
        if filepath.suffix.lower() == '.json':
            with open(filepath, 'w') as f:
                json.dump(self._config, f, indent=2)
        elif filepath.suffix.lower() in ['.yaml', '.yml']:
            with open(filepath, 'w') as f:
                yaml.dump(self._config, f, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")
        
        logger.info(f"⚙️ Configuration saved to {filepath}")


def load_config(filepath: Union[str, Path]) -> Settings:
    """
    Load configuration from file.
    
    Args:
        filepath: Path to configuration file
        
    Returns:
        Settings instance
    """
    filepath = Path(filepath)
    
    if not filepath.exists():
        raise FileNotFoundError(f"Configuration file not found: {filepath}")
    
    if filepath.suffix.lower() == '.json':
        with open(filepath, 'r') as f:
            config = json.load(f)
    elif filepath.suffix.lower() in ['.yaml', '.yml']:
        with open(filepath, 'r') as f:
            config = yaml.safe_load(f)
    else:
        raise ValueError(f"Unsupported file format: {filepath.suffix}")
    
    logger.info(f"⚙️ Configuration loaded from {filepath}")
    return Settings(config)


def save_config(settings: Settings, filepath: Union[str, Path]):
    """
    Save settings to file.
    
    Args:
        settings: Settings instance to save
        filepath: Path to save configuration file
    """
    settings.save(filepath)
