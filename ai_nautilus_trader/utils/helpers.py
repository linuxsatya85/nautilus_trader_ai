"""
Helper Functions and Utilities
==============================

This module provides general helper functions for the AI Nautilus Trader system.
"""

import os
import sys
import importlib
from typing import Dict, Any, List, Optional
from pathlib import Path

from .logger import get_logger

logger = get_logger(__name__)


def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate configuration dictionary.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        True if valid, False otherwise
    """
    required_sections = ["system", "api", "crewai", "nautilus", "trading"]
    
    for section in required_sections:
        if section not in config:
            logger.error(f"Missing required configuration section: {section}")
            return False
    
    # Validate API configuration
    api_config = config.get("api", {})
    if not isinstance(api_config.get("port"), int):
        logger.error("API port must be an integer")
        return False
    
    if api_config.get("port", 0) < 1 or api_config.get("port", 0) > 65535:
        logger.error("API port must be between 1 and 65535")
        return False
    
    # Validate trading configuration
    trading_config = config.get("trading", {})
    if not isinstance(trading_config.get("enabled"), bool):
        logger.error("Trading enabled must be a boolean")
        return False
    
    logger.info("✅ Configuration validation passed")
    return True


def check_dependencies() -> Dict[str, bool]:
    """
    Check if all required dependencies are available.
    
    Returns:
        Dictionary with dependency status
    """
    dependencies = {
        "crewai": False,
        "nautilus_trader": False,
        "fastapi": False,
        "uvicorn": False,
        "pydantic": False,
        "asyncio": False,
    }
    
    for dep in dependencies:
        try:
            importlib.import_module(dep)
            dependencies[dep] = True
            logger.debug(f"✅ {dep} available")
        except ImportError:
            logger.warning(f"❌ {dep} not available")
    
    return dependencies


def format_currency(amount: float, currency: str = "USD", decimals: int = 2) -> str:
    """
    Format currency amount for display.
    
    Args:
        amount: Amount to format
        currency: Currency code
        decimals: Number of decimal places
        
    Returns:
        Formatted currency string
    """
    return f"{amount:,.{decimals}f} {currency}"


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format percentage value for display.
    
    Args:
        value: Percentage value (0.05 = 5%)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"


def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path to project root
    """
    return Path(__file__).parent.parent.parent


def ensure_directory(path: Path) -> Path:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        path: Directory path
        
    Returns:
        Path to directory
    """
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_system_info() -> Dict[str, Any]:
    """
    Get system information.
    
    Returns:
        Dictionary with system information
    """
    return {
        "platform": sys.platform,
        "python_version": sys.version,
        "python_executable": sys.executable,
        "working_directory": os.getcwd(),
        "project_root": str(get_project_root()),
    }


def safe_import(module_name: str, package: Optional[str] = None) -> Optional[Any]:
    """
    Safely import a module without raising exceptions.
    
    Args:
        module_name: Name of module to import
        package: Package name for relative imports
        
    Returns:
        Imported module or None if import failed
    """
    try:
        return importlib.import_module(module_name, package)
    except ImportError as e:
        logger.warning(f"Failed to import {module_name}: {e}")
        return None


def get_available_models() -> List[str]:
    """
    Get list of available AI models.
    
    Returns:
        List of available model names
    """
    models = []
    
    # OpenAI models
    if os.getenv("OPENAI_API_KEY"):
        models.extend([
            "gpt-3.5-turbo",
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-4o-mini"
        ])
    
    # Anthropic models
    if os.getenv("ANTHROPIC_API_KEY"):
        models.extend([
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229"
        ])
    
    # Google models
    if os.getenv("GOOGLE_API_KEY"):
        models.extend([
            "gemini-pro",
            "gemini-pro-vision"
        ])
    
    return models


def validate_api_keys() -> Dict[str, bool]:
    """
    Validate API keys are available.
    
    Returns:
        Dictionary with API key status
    """
    api_keys = {
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "google": bool(os.getenv("GOOGLE_API_KEY")),
    }
    
    return api_keys


def get_memory_usage() -> Dict[str, float]:
    """
    Get current memory usage.
    
    Returns:
        Dictionary with memory usage information
    """
    try:
        import psutil
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            "rss_mb": memory_info.rss / 1024 / 1024,  # Resident Set Size
            "vms_mb": memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            "percent": process.memory_percent(),
        }
    except ImportError:
        logger.warning("psutil not available, cannot get memory usage")
        return {}


def cleanup_temp_files(temp_dir: Optional[Path] = None) -> int:
    """
    Clean up temporary files.
    
    Args:
        temp_dir: Temporary directory to clean (default: system temp)
        
    Returns:
        Number of files cleaned up
    """
    if temp_dir is None:
        temp_dir = Path("/tmp") if sys.platform != "win32" else Path(os.getenv("TEMP", ""))
    
    if not temp_dir.exists():
        return 0
    
    count = 0
    pattern = "ai_nautilus_*"
    
    for file_path in temp_dir.glob(pattern):
        try:
            if file_path.is_file():
                file_path.unlink()
                count += 1
            elif file_path.is_dir():
                import shutil
                shutil.rmtree(file_path)
                count += 1
        except Exception as e:
            logger.warning(f"Failed to clean up {file_path}: {e}")
    
    if count > 0:
        logger.info(f"Cleaned up {count} temporary files")
    
    return count
