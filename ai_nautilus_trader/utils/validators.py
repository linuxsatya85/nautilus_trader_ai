"""
Validation Utilities
===================

This module provides validation utilities for the AI Nautilus Trader system.
"""

import re
from typing import Any, Dict, List, Optional
from ..utils.logger import get_logger

logger = get_logger(__name__)


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


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid format
    """
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid format
    """
    if not url or not isinstance(url, str):
        return False
    
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url.strip()))


def validate_port(port: Any) -> bool:
    """
    Validate port number.
    
    Args:
        port: Port number to validate
        
    Returns:
        True if valid port
    """
    try:
        port_int = int(port)
        return 1 <= port_int <= 65535
    except (ValueError, TypeError):
        return False


def validate_percentage(value: Any) -> bool:
    """
    Validate percentage value (0.0 to 1.0).
    
    Args:
        value: Value to validate
        
    Returns:
        True if valid percentage
    """
    try:
        float_val = float(value)
        return 0.0 <= float_val <= 1.0
    except (ValueError, TypeError):
        return False


def validate_positive_number(value: Any) -> bool:
    """
    Validate positive number.
    
    Args:
        value: Value to validate
        
    Returns:
        True if positive number
    """
    try:
        float_val = float(value)
        return float_val > 0
    except (ValueError, TypeError):
        return False


def validate_non_negative_number(value: Any) -> bool:
    """
    Validate non-negative number.
    
    Args:
        value: Value to validate
        
    Returns:
        True if non-negative number
    """
    try:
        float_val = float(value)
        return float_val >= 0
    except (ValueError, TypeError):
        return False


def validate_string_length(value: str, min_length: int = 1, max_length: int = 1000) -> bool:
    """
    Validate string length.
    
    Args:
        value: String to validate
        min_length: Minimum length
        max_length: Maximum length
        
    Returns:
        True if valid length
    """
    if not isinstance(value, str):
        return False
    
    return min_length <= len(value.strip()) <= max_length


def validate_list_of_strings(value: Any) -> bool:
    """
    Validate list of strings.
    
    Args:
        value: Value to validate
        
    Returns:
        True if valid list of strings
    """
    if not isinstance(value, list):
        return False
    
    return all(isinstance(item, str) for item in value)


def validate_dict_keys(value: Dict[str, Any], required_keys: List[str]) -> bool:
    """
    Validate dictionary has required keys.
    
    Args:
        value: Dictionary to validate
        required_keys: List of required keys
        
    Returns:
        True if all required keys present
    """
    if not isinstance(value, dict):
        return False
    
    return all(key in value for key in required_keys)
