"""
Redis-based Shared Cache for Real-time Data Sharing
Uses LiteLLM's existing Redis infrastructure for high-performance caching
"""

import json
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import threading

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from litellm.caching.redis_cache import RedisCache
from litellm.caching.dual_cache import DualCache
from litellm.caching.in_memory_cache import InMemoryCache


class SharedRedisCache:
    """
    Redis-based shared cache that extends LiteLLM's existing Redis infrastructure
    for real-time data sharing between CrewAI and Nautilus Trader
    """
    
    def __init__(self, 
                 redis_host: str = "localhost",
                 redis_port: int = 6379,
                 redis_password: Optional[str] = None,
                 redis_db: int = 0,
                 namespace: str = "ai_nautilus_shared"):
        
        self.namespace = namespace
        self._lock = threading.RLock()
        
        # Try to use Redis if available, fallback to in-memory
        if REDIS_AVAILABLE:
            try:
                # Use LiteLLM's Redis cache infrastructure
                self.redis_cache = RedisCache(
                    host=redis_host,
                    port=redis_port,
                    password=redis_password,
                    db=redis_db
                )
                
                # Create dual cache (Redis + In-Memory) for best performance
                self.cache = DualCache(
                    redis_cache=self.redis_cache,
                    in_memory_cache=InMemoryCache()
                )
                
                self.redis_available = True
                print(f"✅ Redis shared cache initialized: {redis_host}:{redis_port}")
                
            except Exception as e:
                print(f"⚠️ Redis connection failed, using in-memory cache: {e}")
                self.cache = InMemoryCache()
                self.redis_available = False
        else:
            print("⚠️ Redis not available, using in-memory cache")
            self.cache = InMemoryCache()
            self.redis_available = False
    
    def _make_key(self, category: str, key: str) -> str:
        """Create namespaced key"""
        return f"{self.namespace}:{category}:{key}"
    
    def set_market_data(self, instrument_id: str, data_type: str, 
                       data: Dict[str, Any], ttl: int = 3600) -> bool:
        """Set market data with TTL"""
        try:
            key = self._make_key("market", f"{instrument_id}:{data_type}")
            
            cache_data = {
                "data": data,
                "timestamp": datetime.now().isoformat(),
                "instrument_id": instrument_id,
                "data_type": data_type
            }
            
            # Use LiteLLM's cache interface
            self.cache.set_cache(key, json.dumps(cache_data), ttl=ttl)
            
            # Also set latest data pointer
            latest_key = self._make_key("latest", f"market:{instrument_id}")
            self.cache.set_cache(latest_key, key, ttl=ttl)
            
            return True
            
        except Exception as e:
            print(f"Error setting market data: {e}")
            return False
    
    def get_market_data(self, instrument_id: str, 
                       data_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get latest market data"""
        try:
            if data_type:
                key = self._make_key("market", f"{instrument_id}:{data_type}")
            else:
                # Get latest data for instrument
                latest_key = self._make_key("latest", f"market:{instrument_id}")
                key = self.cache.get_cache(latest_key)
                if not key:
                    return None
            
            cached_data = self.cache.get_cache(key)
            if cached_data:
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            print(f"Error getting market data: {e}")
            return None
    
    def set_agent_decision(self, agent_id: str, decision_type: str,
                          decision_data: Dict[str, Any], confidence: float = 0.0,
                          ttl: int = 1800) -> bool:
        """Set agent decision with TTL"""
        try:
            key = self._make_key("agent", f"{agent_id}:{decision_type}")
            
            cache_data = {
                "decision_data": decision_data,
                "confidence": confidence,
                "timestamp": datetime.now().isoformat(),
                "agent_id": agent_id,
                "decision_type": decision_type
            }
            
            self.cache.set_cache(key, json.dumps(cache_data), ttl=ttl)
            
            # Set latest decision pointer
            latest_key = self._make_key("latest", f"agent:{agent_id}")
            self.cache.set_cache(latest_key, key, ttl=ttl)
            
            return True
            
        except Exception as e:
            print(f"Error setting agent decision: {e}")
            return False
    
    def get_agent_decision(self, agent_id: str, 
                          decision_type: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Get latest agent decision"""
        try:
            if decision_type:
                key = self._make_key("agent", f"{agent_id}:{decision_type}")
            else:
                # Get latest decision for agent
                latest_key = self._make_key("latest", f"agent:{agent_id}")
                key = self.cache.get_cache(latest_key)
                if not key:
                    return None
            
            cached_data = self.cache.get_cache(key)
            if cached_data:
                return json.loads(cached_data)
            
            return None
            
        except Exception as e:
            print(f"Error getting agent decision: {e}")
            return None
    
    def set_trading_signal(self, signal_id: str, signal_data: Dict[str, Any],
                          source: str = "ai", ttl: int = 900) -> bool:
        """Set trading signal"""
        try:
            key = self._make_key("signal", signal_id)
            
            cache_data = {
                "signal_data": signal_data,
                "source": source,
                "timestamp": datetime.now().isoformat(),
                "signal_id": signal_id
            }
            
            self.cache.set_cache(key, json.dumps(cache_data), ttl=ttl)
            
            # Add to active signals list
            signals_key = self._make_key("active", "signals")
            active_signals = self.get_active_signals()
            active_signals.append(signal_id)
            
            # Keep only last 100 signals
            if len(active_signals) > 100:
                active_signals = active_signals[-100:]
            
            self.cache.set_cache(signals_key, json.dumps(active_signals), ttl=3600)
            
            return True
            
        except Exception as e:
            print(f"Error setting trading signal: {e}")
            return False
    
    def get_trading_signal(self, signal_id: str) -> Optional[Dict[str, Any]]:
        """Get specific trading signal"""
        try:
            key = self._make_key("signal", signal_id)
            cached_data = self.cache.get_cache(key)
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            print(f"Error getting trading signal: {e}")
            return None
    
    def get_active_signals(self) -> List[str]:
        """Get list of active signal IDs"""
        try:
            signals_key = self._make_key("active", "signals")
            cached_data = self.cache.get_cache(signals_key)
            if cached_data:
                return json.loads(cached_data)
            return []
            
        except Exception as e:
            print(f"Error getting active signals: {e}")
            return []
    
    def set_system_state(self, component: str, state_data: Dict[str, Any],
                        ttl: int = 300) -> bool:
        """Set system component state"""
        try:
            key = self._make_key("state", component)
            
            cache_data = {
                "state_data": state_data,
                "timestamp": datetime.now().isoformat(),
                "component": component
            }
            
            self.cache.set_cache(key, json.dumps(cache_data), ttl=ttl)
            return True
            
        except Exception as e:
            print(f"Error setting system state: {e}")
            return False
    
    def get_system_state(self, component: str) -> Optional[Dict[str, Any]]:
        """Get system component state"""
        try:
            key = self._make_key("state", component)
            cached_data = self.cache.get_cache(key)
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            print(f"Error getting system state: {e}")
            return None
    
    def publish_event(self, event_type: str, event_data: Dict[str, Any],
                     source: str, target: Optional[str] = None) -> bool:
        """Publish real-time event"""
        try:
            event_id = f"{source}_{event_type}_{int(time.time() * 1000)}"
            key = self._make_key("event", event_id)
            
            cache_data = {
                "event_type": event_type,
                "event_data": event_data,
                "source": source,
                "target": target,
                "timestamp": datetime.now().isoformat(),
                "event_id": event_id,
                "processed": False
            }
            
            # Store event with short TTL
            self.cache.set_cache(key, json.dumps(cache_data), ttl=300)
            
            # Add to events queue
            queue_key = self._make_key("queue", f"events:{target or 'all'}")
            event_queue = self.get_event_queue(target)
            event_queue.append(event_id)
            
            # Keep only last 50 events in queue
            if len(event_queue) > 50:
                event_queue = event_queue[-50:]
            
            self.cache.set_cache(queue_key, json.dumps(event_queue), ttl=600)
            
            return True
            
        except Exception as e:
            print(f"Error publishing event: {e}")
            return False
    
    def get_event_queue(self, target: Optional[str] = None) -> List[str]:
        """Get event queue for target"""
        try:
            queue_key = self._make_key("queue", f"events:{target or 'all'}")
            cached_data = self.cache.get_cache(queue_key)
            if cached_data:
                return json.loads(cached_data)
            return []
            
        except Exception as e:
            print(f"Error getting event queue: {e}")
            return []
    
    def get_event(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Get specific event"""
        try:
            key = self._make_key("event", event_id)
            cached_data = self.cache.get_cache(key)
            if cached_data:
                return json.loads(cached_data)
            return None
            
        except Exception as e:
            print(f"Error getting event: {e}")
            return None
    
    def clear_namespace(self, category: Optional[str] = None) -> bool:
        """Clear cache namespace or category"""
        try:
            if self.redis_available and hasattr(self.redis_cache, 'redis_client'):
                # Use Redis pattern matching for efficient clearing
                pattern = f"{self.namespace}:{category}:*" if category else f"{self.namespace}:*"
                
                # Get Redis client from LiteLLM's cache
                redis_client = self.redis_cache.redis_client
                keys = redis_client.keys(pattern)
                
                if keys:
                    redis_client.delete(*keys)
                    
            return True
            
        except Exception as e:
            print(f"Error clearing cache: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            stats = {
                "redis_available": self.redis_available,
                "namespace": self.namespace,
                "timestamp": datetime.now().isoformat()
            }
            
            if self.redis_available and hasattr(self.redis_cache, 'redis_client'):
                redis_client = self.redis_cache.redis_client
                info = redis_client.info()
                stats.update({
                    "redis_memory_used": info.get("used_memory_human", "unknown"),
                    "redis_connected_clients": info.get("connected_clients", 0),
                    "redis_total_commands": info.get("total_commands_processed", 0)
                })
            
            return stats
            
        except Exception as e:
            print(f"Error getting cache stats: {e}")
            return {"error": str(e)}
