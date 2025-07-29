"""
Configuration Validation
========================

This module provides configuration validation utilities.
"""

from typing import Dict, Any, List
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConfigError(Exception):
    """Configuration error exception."""
    pass


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration dictionary.
    
    Args:
        config: Configuration to validate
        
    Returns:
        True if valid
        
    Raises:
        ConfigError: If configuration is invalid
    """
    errors = []
    
    # Validate required sections
    required_sections = ["system", "api", "crewai", "nautilus", "trading"]
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")
    
    # Validate API configuration
    if "api" in config:
        api_config = config["api"]
        
        if "port" in api_config:
            port = api_config["port"]
            if not isinstance(port, int) or port < 1 or port > 65535:
                errors.append("API port must be an integer between 1 and 65535")
        
        if "host" in api_config:
            host = api_config["host"]
            if not isinstance(host, str) or not host.strip():
                errors.append("API host must be a non-empty string")
    
    # Validate trading configuration
    if "trading" in config:
        trading_config = config["trading"]
        
        if "enabled" in trading_config:
            enabled = trading_config["enabled"]
            if not isinstance(enabled, bool):
                errors.append("Trading enabled must be a boolean")
        
        if "default_instruments" in trading_config:
            instruments = trading_config["default_instruments"]
            if not isinstance(instruments, list):
                errors.append("Default instruments must be a list")
            elif not all(isinstance(inst, str) for inst in instruments):
                errors.append("All instruments must be strings")
    
    # Validate risk configuration
    if "risk" in config:
        risk_config = config["risk"]
        
        for key in ["max_drawdown", "max_daily_loss", "position_limit"]:
            if key in risk_config:
                value = risk_config[key]
                if not isinstance(value, (int, float)) or value < 0 or value > 1:
                    errors.append(f"Risk {key} must be a number between 0 and 1")
    
    # Validate system configuration
    if "system" in config:
        system_config = config["system"]
        
        if "environment" in system_config:
            env = system_config["environment"]
            valid_envs = ["development", "production", "testing"]
            if env not in valid_envs:
                errors.append(f"Environment must be one of: {valid_envs}")
    
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"- {error}" for error in errors)
        logger.error(error_msg)
        raise ConfigError(error_msg)
    
    logger.info("✅ Configuration validation passed")
    return True


def validate_api_key(api_key: str, provider: str = "openai") -> bool:
    """
    Validate API key format.
    
    Args:
        api_key: API key to validate
        provider: API provider (openai, anthropic, google)
        
    Returns:
        True if valid format
    """
    if not api_key or not isinstance(api_key, str):
        return False
    
    api_key = api_key.strip()
    
    if provider.lower() == "openai":
        return api_key.startswith("sk-") and len(api_key) > 20
    elif provider.lower() == "anthropic":
        return api_key.startswith("sk-ant-") and len(api_key) > 20
    elif provider.lower() == "google":
        return len(api_key) > 10  # Basic length check
    
    return len(api_key) > 10  # Generic check


def validate_instrument(instrument: str) -> bool:
    """
    Validate trading instrument format.
    
    Args:
        instrument: Instrument to validate (e.g., "EURUSD", "BTC-USD")
        
    Returns:
        True if valid format
    """
    if not instrument or not isinstance(instrument, str):
        return False
    
    instrument = instrument.strip().upper()
    
    # Basic validation - should be 3-10 characters, alphanumeric with optional separators
    if len(instrument) < 3 or len(instrument) > 10:
        return False
    
    # Allow letters, numbers, and common separators
    allowed_chars = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_./")
    return all(c in allowed_chars for c in instrument)


def validate_timeframe(timeframe: str) -> bool:
    """
    Validate timeframe format.
    
    Args:
        timeframe: Timeframe to validate (e.g., "1m", "5m", "1h", "1d")
        
    Returns:
        True if valid format
    """
    if not timeframe or not isinstance(timeframe, str):
        return False
    
    timeframe = timeframe.strip().lower()
    
    # Valid timeframe patterns
    valid_timeframes = [
        "1s", "5s", "10s", "15s", "30s",  # Seconds
        "1m", "2m", "3m", "5m", "10m", "15m", "30m",  # Minutes
        "1h", "2h", "3h", "4h", "6h", "8h", "12h",  # Hours
        "1d", "2d", "3d",  # Days
        "1w", "2w",  # Weeks
        "1M", "2M", "3M", "6M",  # Months
    ]
    
    return timeframe in valid_timeframes
