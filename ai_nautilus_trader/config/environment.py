"""
Environment Configuration Management
===================================

This module provides environment variable management and configuration utilities.
"""

import os
from typing import Dict, Any, Optional
from pathlib import Path

from ..utils.logger import get_logger

logger = get_logger(__name__)


class Environment:
    """
    Environment configuration manager.
    
    Handles loading and managing environment variables for the AI Nautilus Trader system.
    """
    
    def __init__(self):
        """Initialize environment manager."""
        self._env_vars: Dict[str, str] = {}
        self._load_environment()
        logger.info("🌍 Environment manager initialized")
    
    def _load_environment(self):
        """Load environment variables."""
        # Load from .env file if it exists
        env_file = Path(".env")
        if env_file.exists():
            self._load_env_file(env_file)
        
        # Load from system environment
        self._load_system_env()
    
    def _load_env_file(self, env_file: Path):
        """Load environment variables from .env file."""
        try:
            with open(env_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        self._env_vars[key] = value
            
            logger.info(f"📁 Loaded environment from {env_file}")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to load .env file: {e}")
    
    def _load_system_env(self):
        """Load relevant environment variables from system."""
        relevant_vars = [
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY", 
            "GOOGLE_API_KEY",
            "ENVIRONMENT",
            "API_HOST",
            "API_PORT",
            "TRADING_ENABLED",
            "LOG_LEVEL",
        ]
        
        for var in relevant_vars:
            value = os.getenv(var)
            if value:
                self._env_vars[var] = value
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get environment variable value.
        
        Args:
            key: Environment variable key
            default: Default value if key not found
            
        Returns:
            Environment variable value or default
        """
        return self._env_vars.get(key, default)
    
    def set(self, key: str, value: str):
        """
        Set environment variable.
        
        Args:
            key: Environment variable key
            value: Environment variable value
        """
        self._env_vars[key] = value
        os.environ[key] = value
        logger.debug(f"🌍 Set environment variable: {key}")
    
    def get_all(self) -> Dict[str, str]:
        """Get all environment variables."""
        return self._env_vars.copy()
    
    def has_api_keys(self) -> Dict[str, bool]:
        """Check which API keys are available."""
        return {
            "openai": bool(self.get("OPENAI_API_KEY")),
            "anthropic": bool(self.get("ANTHROPIC_API_KEY")),
            "google": bool(self.get("GOOGLE_API_KEY")),
        }
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        env = self.get("ENVIRONMENT", "development").lower()
        return env in ["production", "prod"]
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        env = self.get("ENVIRONMENT", "development").lower()
        return env in ["development", "dev"]


def get_env_config() -> Dict[str, Any]:
    """
    Get environment-based configuration.
    
    Returns:
        Configuration dictionary based on environment variables
    """
    env = Environment()
    
    config = {
        "system": {
            "environment": env.get("ENVIRONMENT", "development"),
            "debug": env.is_development(),
        },
        "api": {
            "host": env.get("API_HOST", "0.0.0.0"),
            "port": int(env.get("API_PORT", "8000")),
        },
        "crewai": {
            "api_key": env.get("OPENAI_API_KEY"),
            "anthropic_api_key": env.get("ANTHROPIC_API_KEY"),
            "google_api_key": env.get("GOOGLE_API_KEY"),
        },
        "trading": {
            "enabled": env.get("TRADING_ENABLED", "true").lower() == "true",
        },
        "logging": {
            "level": env.get("LOG_LEVEL", "INFO"),
        },
    }
    
    return config
