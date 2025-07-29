"""
Event Management System
=======================

This module provides event handling and coordination for the AI Nautilus Trader system.
"""

from typing import Dict, Any, List, Callable
from ..utils.logger import get_logger

logger = get_logger(__name__)


class EventManager:
    """
    Event manager for handling system events and coordination.
    """
    
    def __init__(self):
        """Initialize event manager."""
        self.handlers: Dict[str, List[Callable]] = {}
        logger.info("📡 Event manager initialized")
    
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe to an event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    def emit(self, event_type: str, data: Any = None):
        """Emit an event."""
        if event_type in self.handlers:
            for handler in self.handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
