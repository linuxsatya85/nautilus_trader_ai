"""
Unified Memory Interface for AI Nautilus Trader
Provides single API for both CrewAI and Nautilus Trader storage systems
"""

import asyncio
import threading
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from dataclasses import dataclass
from enum import Enum

from .shared_memory import SharedMemoryStorage, SharedMemoryEntry
from .redis_shared_cache import SharedRedisCache


class MemoryType(Enum):
    """Types of memory storage"""
    PERSISTENT = "persistent"  # SQLite storage
    CACHE = "cache"           # Redis/In-memory cache
    BOTH = "both"            # Store in both systems


class DataSource(Enum):
    """Data source frameworks"""
    CREWAI = "crewai"
    NAUTILUS = "nautilus"
    SHARED = "shared"


@dataclass
class MemoryConfig:
    """Configuration for unified memory system"""
    # SQLite configuration
    sqlite_db_path: Optional[str] = None
    
    # Redis configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: Optional[str] = None
    redis_db: int = 0
    
    # Cache TTL settings (seconds)
    market_data_ttl: int = 3600      # 1 hour
    agent_decision_ttl: int = 1800   # 30 minutes
    trading_signal_ttl: int = 900    # 15 minutes
    system_state_ttl: int = 300      # 5 minutes
    
    # Cleanup settings
    cleanup_interval: int = 3600     # 1 hour
    days_to_keep: int = 7           # 7 days
    
    # Performance settings
    enable_async: bool = True
    max_cache_size: int = 10000


class UnifiedMemorySystem:
    """
    Unified memory system that provides a single interface for both
    CrewAI and Nautilus Trader storage and caching needs
    """
    
    def __init__(self, config: Optional[MemoryConfig] = None):
        self.config = config or MemoryConfig()
        self._lock = threading.RLock()
        self._cleanup_thread = None
        self._running = False
        
        # Initialize storage systems
        self.persistent_storage = SharedMemoryStorage(self.config.sqlite_db_path)
        self.cache_storage = SharedRedisCache(
            redis_host=self.config.redis_host,
            redis_port=self.config.redis_port,
            redis_password=self.config.redis_password,
            redis_db=self.config.redis_db
        )
        
        # Event callbacks
        self._event_callbacks: Dict[str, List[Callable]] = {}
        
        print("✅ Unified Memory System initialized")
    
    def start(self):
        """Start the unified memory system"""
        if self._running:
            return
        
        self._running = True
        
        # Start cleanup thread
        if self.config.cleanup_interval > 0:
            self._cleanup_thread = threading.Thread(
                target=self._cleanup_worker,
                daemon=True
            )
            self._cleanup_thread.start()
        
        print("🚀 Unified Memory System started")
    
    def stop(self):
        """Stop the unified memory system"""
        self._running = False
        
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
        
        print("🛑 Unified Memory System stopped")
    
    def _cleanup_worker(self):
        """Background cleanup worker"""
        while self._running:
            try:
                # Clean up old persistent data
                self.persistent_storage.cleanup_old_data(self.config.days_to_keep)
                
                # Sleep until next cleanup
                time.sleep(self.config.cleanup_interval)
                
            except Exception as e:
                print(f"Error in cleanup worker: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    # Market Data Methods
    def save_market_data(self, instrument_id: str, data_type: str, 
                        data: Dict[str, Any], memory_type: MemoryType = MemoryType.BOTH,
                        source: DataSource = DataSource.NAUTILUS) -> bool:
        """Save market data to specified memory type"""
        success = True
        
        try:
            if memory_type in [MemoryType.PERSISTENT, MemoryType.BOTH]:
                # Save to persistent storage
                persistent_success = self.persistent_storage.save_market_data(
                    instrument_id, data_type, data
                )
                success = success and persistent_success
                
                # Also save as shared memory entry
                entry = SharedMemoryEntry(
                    source=source.value,
                    data_type=f"market_data_{data_type}",
                    content=data,
                    metadata={
                        "instrument_id": instrument_id,
                        "data_type": data_type
                    },
                    tags=["market_data", instrument_id, data_type]
                )
                self.persistent_storage.save_shared_memory(entry)
            
            if memory_type in [MemoryType.CACHE, MemoryType.BOTH]:
                # Save to cache
                cache_success = self.cache_storage.set_market_data(
                    instrument_id, data_type, data, self.config.market_data_ttl
                )
                success = success and cache_success
            
            # Trigger event callbacks
            self._trigger_event("market_data_saved", {
                "instrument_id": instrument_id,
                "data_type": data_type,
                "source": source.value,
                "memory_type": memory_type.value
            })
            
            return success
            
        except Exception as e:
            print(f"Error saving market data: {e}")
            return False
    
    def get_market_data(self, instrument_id: str, data_type: Optional[str] = None,
                       memory_type: MemoryType = MemoryType.CACHE,
                       limit: int = 100) -> Optional[Dict[str, Any]]:
        """Get market data from specified memory type"""
        try:
            if memory_type == MemoryType.CACHE:
                return self.cache_storage.get_market_data(instrument_id, data_type)
            
            elif memory_type == MemoryType.PERSISTENT:
                data_list = self.persistent_storage.get_market_data(
                    instrument_id, data_type, limit
                )
                return data_list[0] if data_list else None
            
            elif memory_type == MemoryType.BOTH:
                # Try cache first, fallback to persistent
                cached_data = self.cache_storage.get_market_data(instrument_id, data_type)
                if cached_data:
                    return cached_data
                
                data_list = self.persistent_storage.get_market_data(
                    instrument_id, data_type, 1
                )
                return data_list[0] if data_list else None
            
            return None
            
        except Exception as e:
            print(f"Error getting market data: {e}")
            return None
    
    # Agent Decision Methods
    def save_agent_decision(self, agent_id: str, decision_type: str,
                          decision_data: Dict[str, Any], confidence: float = 0.0,
                          task_id: Optional[str] = None,
                          memory_type: MemoryType = MemoryType.BOTH,
                          source: DataSource = DataSource.CREWAI) -> bool:
        """Save agent decision to specified memory type"""
        success = True
        
        try:
            if memory_type in [MemoryType.PERSISTENT, MemoryType.BOTH]:
                # Save to persistent storage
                persistent_success = self.persistent_storage.save_agent_decision(
                    agent_id, decision_type, decision_data, confidence, task_id
                )
                success = success and persistent_success
                
                # Also save as shared memory entry
                entry = SharedMemoryEntry(
                    source=source.value,
                    data_type=f"agent_decision_{decision_type}",
                    content=decision_data,
                    metadata={
                        "agent_id": agent_id,
                        "decision_type": decision_type,
                        "confidence": confidence,
                        "task_id": task_id
                    },
                    score=confidence,
                    tags=["agent_decision", agent_id, decision_type]
                )
                self.persistent_storage.save_shared_memory(entry)
            
            if memory_type in [MemoryType.CACHE, MemoryType.BOTH]:
                # Save to cache
                cache_success = self.cache_storage.set_agent_decision(
                    agent_id, decision_type, decision_data, confidence,
                    self.config.agent_decision_ttl
                )
                success = success and cache_success
            
            # Trigger event callbacks
            self._trigger_event("agent_decision_saved", {
                "agent_id": agent_id,
                "decision_type": decision_type,
                "confidence": confidence,
                "source": source.value,
                "memory_type": memory_type.value
            })
            
            return success
            
        except Exception as e:
            print(f"Error saving agent decision: {e}")
            return False
    
    def get_agent_decision(self, agent_id: str, decision_type: Optional[str] = None,
                          memory_type: MemoryType = MemoryType.CACHE,
                          limit: int = 100) -> Optional[Dict[str, Any]]:
        """Get agent decision from specified memory type"""
        try:
            if memory_type == MemoryType.CACHE:
                return self.cache_storage.get_agent_decision(agent_id, decision_type)
            
            elif memory_type == MemoryType.PERSISTENT:
                data_list = self.persistent_storage.get_agent_decisions(
                    agent_id, decision_type, limit
                )
                return data_list[0] if data_list else None
            
            elif memory_type == MemoryType.BOTH:
                # Try cache first, fallback to persistent
                cached_data = self.cache_storage.get_agent_decision(agent_id, decision_type)
                if cached_data:
                    return cached_data
                
                data_list = self.persistent_storage.get_agent_decisions(
                    agent_id, decision_type, 1
                )
                return data_list[0] if data_list else None
            
            return None
            
        except Exception as e:
            print(f"Error getting agent decision: {e}")
            return None
    
    # Trading Signal Methods
    def save_trading_signal(self, signal_id: str, signal_data: Dict[str, Any],
                          source: DataSource = DataSource.SHARED,
                          memory_type: MemoryType = MemoryType.BOTH) -> bool:
        """Save trading signal"""
        success = True
        
        try:
            if memory_type in [MemoryType.PERSISTENT, MemoryType.BOTH]:
                # Save as shared memory entry
                entry = SharedMemoryEntry(
                    id=signal_id,
                    source=source.value,
                    data_type="trading_signal",
                    content=signal_data,
                    metadata={"signal_id": signal_id},
                    score=signal_data.get("confidence", 0.0),
                    tags=["trading_signal", signal_data.get("action", "unknown")]
                )
                persistent_success = self.persistent_storage.save_shared_memory(entry)
                success = success and persistent_success
            
            if memory_type in [MemoryType.CACHE, MemoryType.BOTH]:
                # Save to cache
                cache_success = self.cache_storage.set_trading_signal(
                    signal_id, signal_data, source.value, self.config.trading_signal_ttl
                )
                success = success and cache_success
            
            # Trigger event callbacks
            self._trigger_event("trading_signal_saved", {
                "signal_id": signal_id,
                "action": signal_data.get("action", "unknown"),
                "source": source.value,
                "memory_type": memory_type.value
            })
            
            return success
            
        except Exception as e:
            print(f"Error saving trading signal: {e}")
            return False
    
    def get_trading_signal(self, signal_id: str,
                          memory_type: MemoryType = MemoryType.CACHE) -> Optional[Dict[str, Any]]:
        """Get trading signal"""
        try:
            if memory_type == MemoryType.CACHE:
                return self.cache_storage.get_trading_signal(signal_id)
            
            elif memory_type in [MemoryType.PERSISTENT, MemoryType.BOTH]:
                entries = self.persistent_storage.load_shared_memories(
                    data_type="trading_signal", limit=1000
                )
                
                for entry in entries:
                    if entry.id == signal_id:
                        return {
                            "signal_data": entry.content,
                            "source": entry.source,
                            "timestamp": entry.timestamp
                        }
            
            return None
            
        except Exception as e:
            print(f"Error getting trading signal: {e}")
            return None
    
    def get_active_signals(self) -> List[str]:
        """Get list of active trading signals"""
        return self.cache_storage.get_active_signals()
    
    # System State Methods
    def set_system_state(self, component: str, state_data: Dict[str, Any],
                        source: DataSource = DataSource.SHARED) -> bool:
        """Set system component state"""
        try:
            # Always use cache for system state (real-time data)
            success = self.cache_storage.set_system_state(
                component, state_data, self.config.system_state_ttl
            )
            
            # Trigger event callbacks
            self._trigger_event("system_state_updated", {
                "component": component,
                "source": source.value
            })
            
            return success
            
        except Exception as e:
            print(f"Error setting system state: {e}")
            return False
    
    def get_system_state(self, component: str) -> Optional[Dict[str, Any]]:
        """Get system component state"""
        return self.cache_storage.get_system_state(component)

    # Event System Methods
    def publish_event(self, event_type: str, event_data: Dict[str, Any],
                     source: DataSource, target: Optional[DataSource] = None) -> bool:
        """Publish real-time event"""
        try:
            target_str = target.value if target else None
            success = self.cache_storage.publish_event(
                event_type, event_data, source.value, target_str
            )

            # Also save as cross-framework event in persistent storage
            self.persistent_storage.create_cross_framework_event(
                event_type, source.value, event_data, target_str
            )

            return success

        except Exception as e:
            print(f"Error publishing event: {e}")
            return False

    def get_events(self, target: Optional[DataSource] = None) -> List[Dict[str, Any]]:
        """Get events for target framework"""
        try:
            target_str = target.value if target else None

            # Get from cache (real-time events)
            event_ids = self.cache_storage.get_event_queue(target_str)
            events = []

            for event_id in event_ids:
                event = self.cache_storage.get_event(event_id)
                if event:
                    events.append(event)

            return events

        except Exception as e:
            print(f"Error getting events: {e}")
            return []

    def get_unprocessed_events(self, target: Optional[DataSource] = None) -> List[Dict[str, Any]]:
        """Get unprocessed events from persistent storage"""
        target_str = target.value if target else None
        return self.persistent_storage.get_unprocessed_events(target_str)

    def mark_event_processed(self, event_id: str) -> bool:
        """Mark event as processed"""
        return self.persistent_storage.mark_event_processed(event_id)

    # Shared Memory Methods
    def save_shared_memory(self, entry: SharedMemoryEntry,
                          memory_type: MemoryType = MemoryType.PERSISTENT) -> bool:
        """Save shared memory entry"""
        try:
            if memory_type in [MemoryType.PERSISTENT, MemoryType.BOTH]:
                success = self.persistent_storage.save_shared_memory(entry)
                if not success:
                    return False

            if memory_type in [MemoryType.CACHE, MemoryType.BOTH]:
                # Convert to cache format based on data type
                if "market_data" in entry.data_type:
                    instrument_id = entry.metadata.get("instrument_id", "unknown")
                    data_type = entry.metadata.get("data_type", "unknown")
                    self.cache_storage.set_market_data(
                        instrument_id, data_type, entry.content
                    )
                elif "agent_decision" in entry.data_type:
                    agent_id = entry.metadata.get("agent_id", "unknown")
                    decision_type = entry.metadata.get("decision_type", "unknown")
                    confidence = entry.metadata.get("confidence", entry.score)
                    self.cache_storage.set_agent_decision(
                        agent_id, decision_type, entry.content, confidence
                    )

            return True

        except Exception as e:
            print(f"Error saving shared memory: {e}")
            return False

    def load_shared_memories(self, source: Optional[DataSource] = None,
                           data_type: Optional[str] = None,
                           limit: int = 100,
                           min_score: float = 0.0) -> List[SharedMemoryEntry]:
        """Load shared memories with filtering"""
        source_str = source.value if source else None
        return self.persistent_storage.load_shared_memories(
            source_str, data_type, limit, min_score
        )

    # Event Callback System
    def register_event_callback(self, event_type: str, callback: Callable):
        """Register callback for specific event type"""
        if event_type not in self._event_callbacks:
            self._event_callbacks[event_type] = []
        self._event_callbacks[event_type].append(callback)

    def unregister_event_callback(self, event_type: str, callback: Callable):
        """Unregister event callback"""
        if event_type in self._event_callbacks:
            try:
                self._event_callbacks[event_type].remove(callback)
            except ValueError:
                pass

    def _trigger_event(self, event_type: str, event_data: Dict[str, Any]):
        """Trigger event callbacks"""
        if event_type in self._event_callbacks:
            for callback in self._event_callbacks[event_type]:
                try:
                    callback(event_data)
                except Exception as e:
                    print(f"Error in event callback: {e}")

    # Utility Methods
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        try:
            cache_stats = self.cache_storage.get_cache_stats()

            # Get persistent storage stats
            persistent_stats = {}
            try:
                with self.persistent_storage._lock:
                    import sqlite3
                    with sqlite3.connect(self.persistent_storage.db_path) as conn:
                        cursor = conn.cursor()

                        # Count records in each table
                        tables = [
                            "shared_memories",
                            "market_data_cache",
                            "agent_decisions_cache",
                            "cross_framework_events"
                        ]

                        for table in tables:
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cursor.fetchone()[0]
                            persistent_stats[f"{table}_count"] = count

                        # Get database size
                        cursor.execute("PRAGMA page_count")
                        page_count = cursor.fetchone()[0]
                        cursor.execute("PRAGMA page_size")
                        page_size = cursor.fetchone()[0]
                        persistent_stats["db_size_bytes"] = page_count * page_size

            except Exception as e:
                persistent_stats["error"] = str(e)

            return {
                "cache": cache_stats,
                "persistent": persistent_stats,
                "config": {
                    "cleanup_interval": self.config.cleanup_interval,
                    "days_to_keep": self.config.days_to_keep,
                    "running": self._running
                },
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            return {"error": str(e)}

    def clear_all_memory(self, confirm: bool = False) -> bool:
        """Clear all memory (use with caution)"""
        if not confirm:
            print("⚠️ Use clear_all_memory(confirm=True) to actually clear memory")
            return False

        try:
            # Clear cache
            self.cache_storage.clear_namespace()

            # Clear persistent storage
            with self.persistent_storage._lock:
                import sqlite3
                with sqlite3.connect(self.persistent_storage.db_path) as conn:
                    cursor = conn.cursor()

                    tables = [
                        "shared_memories",
                        "market_data_cache",
                        "agent_decisions_cache",
                        "cross_framework_events"
                    ]

                    for table in tables:
                        cursor.execute(f"DELETE FROM {table}")

                    conn.commit()

            print("🗑️ All memory cleared")
            return True

        except Exception as e:
            print(f"Error clearing memory: {e}")
            return False

    # Context Manager Support
    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# Global instance for easy access
_global_memory_system: Optional[UnifiedMemorySystem] = None


def get_memory_system(config: Optional[MemoryConfig] = None) -> UnifiedMemorySystem:
    """Get global memory system instance"""
    global _global_memory_system

    if _global_memory_system is None:
        _global_memory_system = UnifiedMemorySystem(config)

    return _global_memory_system


def initialize_memory_system(config: Optional[MemoryConfig] = None) -> UnifiedMemorySystem:
    """Initialize and start global memory system"""
    memory_system = get_memory_system(config)
    memory_system.start()
    return memory_system
