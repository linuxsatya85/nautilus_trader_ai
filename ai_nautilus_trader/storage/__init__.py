"""
AI Nautilus Trader Storage Package
Unified memory and storage system for CrewAI and Nautilus Trader integration
"""

from .shared_memory import SharedMemoryStorage, SharedMemoryEntry
from .redis_shared_cache import SharedRedisCache
from .unified_memory import (
    UnifiedMemorySystem, 
    MemoryType, 
    DataSource, 
    MemoryConfig,
    get_memory_system,
    initialize_memory_system
)

__all__ = [
    # Core storage classes
    "SharedMemoryStorage",
    "SharedMemoryEntry", 
    "SharedRedisCache",
    "UnifiedMemorySystem",
    
    # Enums and configs
    "MemoryType",
    "DataSource", 
    "MemoryConfig",
    
    # Utility functions
    "get_memory_system",
    "initialize_memory_system"
]

# Version info
__version__ = "1.0.0"
__author__ = "AI Nautilus Trader Team"
__description__ = "Unified storage system for AI trading applications"

# Storage system status
def get_storage_status():
    """Get status of all storage components"""
    try:
        memory_system = get_memory_system()
        return memory_system.get_memory_stats()
    except Exception as e:
        return {"error": str(e), "status": "not_initialized"}

# Quick setup function
def setup_storage(redis_host="localhost", redis_port=6379, 
                 redis_password=None, enable_cleanup=True):
    """Quick setup for storage system"""
    config = MemoryConfig(
        redis_host=redis_host,
        redis_port=redis_port, 
        redis_password=redis_password,
        cleanup_interval=3600 if enable_cleanup else 0
    )
    
    return initialize_memory_system(config)
