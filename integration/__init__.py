"""
AI Nautilus Platform Integration Layer

This module provides adapters and bridges to integrate existing CrewAI and 
Nautilus Trader codebases without modifying the original source code.
"""

from .adapters.crewai_adapter import CrewAIAdapter
from .adapters.nautilus_adapter import NautilusAdapter
from .bridges.data_bridge import DataBridge
from .bridges.message_bridge import MessageBridge

__version__ = "1.0.0"
__all__ = [
    "CrewAIAdapter",
    "NautilusAdapter", 
    "DataBridge",
    "MessageBridge",
]