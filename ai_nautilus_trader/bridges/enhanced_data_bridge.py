"""
Enhanced Data Bridge with Unified Memory System
Extends the original DataBridge with persistent and cached storage
"""

import sys
import os
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add both codebases to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'nautilus_trader'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'crewai', 'src'))

# Import existing classes - NO MODIFICATIONS NEEDED!
from nautilus_trader.model.data import Bar, QuoteTick, TradeTick, OrderBookDeltas
from nautilus_trader.model.identifiers import InstrumentId
from crewai.utilities.events import default_emitter

# Import original data bridge
from .data_bridge import DataBridge

# Import unified memory system
try:
    from ..storage.unified_memory import (
        UnifiedMemorySystem, MemoryType, DataSource, MemoryConfig,
        get_memory_system, SharedMemoryEntry
    )
    UNIFIED_MEMORY_AVAILABLE = True
except ImportError:
    UNIFIED_MEMORY_AVAILABLE = False
    print("⚠️ Unified Memory System not available, using legacy in-memory storage")

logger = logging.getLogger(__name__)


class EnhancedDataBridge(DataBridge):
    """
    Enhanced Data Bridge that extends the original DataBridge with:
    - Unified Memory System for persistent storage
    - Redis caching for real-time data
    - Cross-framework event publishing
    - Advanced data analytics and aggregation
    """
    
    def __init__(self, crewai_adapter=None, nautilus_engine=None, 
                 memory_config: Optional[MemoryConfig] = None,
                 enable_unified_memory: bool = True):
        
        # Initialize parent class
        super().__init__(crewai_adapter, nautilus_engine)
        
        # Initialize unified memory system
        self.unified_memory = None
        self.memory_enabled = enable_unified_memory and UNIFIED_MEMORY_AVAILABLE
        
        if self.memory_enabled:
            try:
                if memory_config:
                    self.unified_memory = UnifiedMemorySystem(memory_config)
                else:
                    self.unified_memory = get_memory_system()
                
                self.unified_memory.start()
                logger.info("✅ Enhanced Data Bridge with Unified Memory initialized")
                
                # Register event callbacks
                self.unified_memory.register_event_callback(
                    "market_data_saved", self._on_market_data_saved
                )
                self.unified_memory.register_event_callback(
                    "agent_decision_saved", self._on_agent_decision_saved
                )
                
            except Exception as e:
                logger.error(f"Failed to initialize unified memory: {e}")
                self.memory_enabled = False
                self.unified_memory = None
        
        if not self.memory_enabled:
            logger.warning("⚠️ Enhanced Data Bridge running without unified memory")
    
    def on_bar(self, bar: Bar):
        """Enhanced bar processing with unified memory storage"""
        try:
            # Call parent method for backward compatibility
            super().on_bar(bar)
            
            # Enhanced processing with unified memory
            if self.memory_enabled and self.unified_memory:
                # Convert bar to market data
                market_data = self._bar_to_market_data(bar)
                instrument_id = str(bar.instrument_id)
                
                # Save to unified memory (both cache and persistent)
                success = self.unified_memory.save_market_data(
                    instrument_id=instrument_id,
                    data_type="bar",
                    data=market_data,
                    memory_type=MemoryType.BOTH,
                    source=DataSource.NAUTILUS
                )
                
                if success:
                    # Publish cross-framework event
                    self.unified_memory.publish_event(
                        event_type="market_bar_received",
                        event_data={
                            "instrument_id": instrument_id,
                            "bar_data": market_data,
                            "timestamp": market_data["timestamp"]
                        },
                        source=DataSource.NAUTILUS,
                        target=DataSource.CREWAI
                    )
                    
                    logger.debug(f"✅ Enhanced bar processing for {instrument_id}")
                else:
                    logger.warning(f"⚠️ Failed to save bar data to unified memory: {instrument_id}")
            
        except Exception as e:
            logger.error(f"Error in enhanced bar processing: {e}")
    
    def on_tick(self, tick):
        """Enhanced tick processing with unified memory storage"""
        try:
            # Call parent method for backward compatibility
            super().on_tick(tick)
            
            # Enhanced processing with unified memory
            if self.memory_enabled and self.unified_memory:
                # Convert tick to market data
                tick_data = self._tick_to_market_data(tick)
                instrument_id = str(tick.instrument_id)
                
                # Save to unified memory (cache only for high-frequency data)
                success = self.unified_memory.save_market_data(
                    instrument_id=instrument_id,
                    data_type="tick",
                    data=tick_data,
                    memory_type=MemoryType.CACHE,  # Cache only for performance
                    source=DataSource.NAUTILUS
                )
                
                if success:
                    # Publish real-time event
                    self.unified_memory.publish_event(
                        event_type="market_tick_received",
                        event_data={
                            "instrument_id": instrument_id,
                            "tick_data": tick_data,
                            "timestamp": tick_data["timestamp"]
                        },
                        source=DataSource.NAUTILUS,
                        target=DataSource.CREWAI
                    )
                    
                    logger.debug(f"✅ Enhanced tick processing for {instrument_id}")
            
        except Exception as e:
            logger.error(f"Error in enhanced tick processing: {e}")
    
    def on_order_book(self, order_book: OrderBookDeltas):
        """Enhanced order book processing with unified memory storage"""
        try:
            # Call parent method for backward compatibility
            super().on_order_book(order_book)
            
            # Enhanced processing with unified memory
            if self.memory_enabled and self.unified_memory:
                # Convert order book to market data
                book_data = self._orderbook_to_market_data(order_book)
                instrument_id = str(order_book.instrument_id)
                
                # Save to unified memory (cache only for real-time data)
                success = self.unified_memory.save_market_data(
                    instrument_id=instrument_id,
                    data_type="orderbook",
                    data=book_data,
                    memory_type=MemoryType.CACHE,
                    source=DataSource.NAUTILUS
                )
                
                if success:
                    # Publish real-time event
                    self.unified_memory.publish_event(
                        event_type="orderbook_updated",
                        event_data={
                            "instrument_id": instrument_id,
                            "orderbook_data": book_data,
                            "timestamp": book_data["timestamp"]
                        },
                        source=DataSource.NAUTILUS,
                        target=DataSource.CREWAI
                    )
                    
                    logger.debug(f"✅ Enhanced orderbook processing for {instrument_id}")
            
        except Exception as e:
            logger.error(f"Error in enhanced orderbook processing: {e}")
    
    def save_agent_decision(self, agent_id: str, decision_type: str,
                          decision_data: Dict[str, Any], confidence: float = 0.0,
                          task_id: Optional[str] = None) -> bool:
        """Save agent decision to unified memory"""
        if not self.memory_enabled or not self.unified_memory:
            logger.warning("Unified memory not available for agent decision")
            return False
        
        try:
            success = self.unified_memory.save_agent_decision(
                agent_id=agent_id,
                decision_type=decision_type,
                decision_data=decision_data,
                confidence=confidence,
                task_id=task_id,
                memory_type=MemoryType.BOTH,
                source=DataSource.CREWAI
            )
            
            if success:
                # Publish cross-framework event
                self.unified_memory.publish_event(
                    event_type="agent_decision_made",
                    event_data={
                        "agent_id": agent_id,
                        "decision_type": decision_type,
                        "decision_data": decision_data,
                        "confidence": confidence,
                        "task_id": task_id
                    },
                    source=DataSource.CREWAI,
                    target=DataSource.NAUTILUS
                )
                
                logger.info(f"✅ Agent decision saved: {agent_id} - {decision_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving agent decision: {e}")
            return False
    
    def save_trading_signal(self, signal_id: str, signal_data: Dict[str, Any],
                          source: str = "ai") -> bool:
        """Save trading signal to unified memory"""
        if not self.memory_enabled or not self.unified_memory:
            logger.warning("Unified memory not available for trading signal")
            return False
        
        try:
            # Determine source
            data_source = DataSource.CREWAI if source == "ai" else DataSource.NAUTILUS
            
            success = self.unified_memory.save_trading_signal(
                signal_id=signal_id,
                signal_data=signal_data,
                source=data_source,
                memory_type=MemoryType.BOTH
            )
            
            if success:
                # Publish cross-framework event
                self.unified_memory.publish_event(
                    event_type="trading_signal_generated",
                    event_data={
                        "signal_id": signal_id,
                        "signal_data": signal_data,
                        "source": source
                    },
                    source=data_source,
                    target=None  # Broadcast to all
                )
                
                logger.info(f"✅ Trading signal saved: {signal_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving trading signal: {e}")
            return False
    
    def get_enhanced_market_data(self, instrument_id: str, data_type: Optional[str] = None,
                               memory_type: MemoryType = MemoryType.CACHE) -> Optional[Dict[str, Any]]:
        """Get market data from unified memory"""
        if not self.memory_enabled or not self.unified_memory:
            # Fallback to parent method
            if data_type == "bar":
                history = self.get_market_history(instrument_id, limit=1)
                return history[-1] if history else None
            elif data_type == "tick":
                history = self.get_tick_history(instrument_id, limit=1)
                return history[-1] if history else None
            elif data_type == "orderbook":
                return self.get_current_orderbook(instrument_id)
            return None
        
        try:
            return self.unified_memory.get_market_data(
                instrument_id=instrument_id,
                data_type=data_type,
                memory_type=memory_type
            )
        except Exception as e:
            logger.error(f"Error getting enhanced market data: {e}")
            return None
    
    def get_agent_decisions(self, agent_id: str, decision_type: Optional[str] = None,
                          memory_type: MemoryType = MemoryType.CACHE) -> Optional[Dict[str, Any]]:
        """Get agent decisions from unified memory"""
        if not self.memory_enabled or not self.unified_memory:
            return None
        
        try:
            return self.unified_memory.get_agent_decision(
                agent_id=agent_id,
                decision_type=decision_type,
                memory_type=memory_type
            )
        except Exception as e:
            logger.error(f"Error getting agent decisions: {e}")
            return None
    
    def get_trading_signals(self, signal_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get trading signals from unified memory"""
        if not self.memory_enabled or not self.unified_memory:
            return []
        
        try:
            if signal_id:
                signal = self.unified_memory.get_trading_signal(signal_id)
                return [signal] if signal else []
            else:
                # Get all active signals
                signal_ids = self.unified_memory.get_active_signals()
                signals = []
                for sid in signal_ids:
                    signal = self.unified_memory.get_trading_signal(sid)
                    if signal:
                        signals.append(signal)
                return signals
        except Exception as e:
            logger.error(f"Error getting trading signals: {e}")
            return []

    def get_cross_framework_events(self, target: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get cross-framework events"""
        if not self.memory_enabled or not self.unified_memory:
            return []

        try:
            target_source = None
            if target == "crewai":
                target_source = DataSource.CREWAI
            elif target == "nautilus":
                target_source = DataSource.NAUTILUS

            return self.unified_memory.get_events(target_source)
        except Exception as e:
            logger.error(f"Error getting cross-framework events: {e}")
            return []

    def set_system_state(self, component: str, state_data: Dict[str, Any]) -> bool:
        """Set system component state"""
        if not self.memory_enabled or not self.unified_memory:
            return False

        try:
            return self.unified_memory.set_system_state(component, state_data)
        except Exception as e:
            logger.error(f"Error setting system state: {e}")
            return False

    def get_system_state(self, component: str) -> Optional[Dict[str, Any]]:
        """Get system component state"""
        if not self.memory_enabled or not self.unified_memory:
            return None

        try:
            return self.unified_memory.get_system_state(component)
        except Exception as e:
            logger.error(f"Error getting system state: {e}")
            return None

    def get_memory_stats(self) -> Dict[str, Any]:
        """Get enhanced memory statistics"""
        try:
            # Get parent stats
            parent_stats = super().get_status()

            # Get unified memory stats
            if self.memory_enabled and self.unified_memory:
                memory_stats = self.unified_memory.get_memory_stats()

                return {
                    "legacy_bridge": parent_stats,
                    "unified_memory": memory_stats,
                    "enhanced_features": {
                        "unified_memory_enabled": self.memory_enabled,
                        "persistent_storage": True,
                        "redis_caching": memory_stats.get("cache", {}).get("redis_available", False),
                        "cross_framework_events": True,
                        "agent_decision_tracking": True,
                        "trading_signal_management": True
                    },
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "legacy_bridge": parent_stats,
                    "unified_memory": {"error": "Not available"},
                    "enhanced_features": {
                        "unified_memory_enabled": False,
                        "persistent_storage": False,
                        "redis_caching": False,
                        "cross_framework_events": False,
                        "agent_decision_tracking": False,
                        "trading_signal_management": False
                    },
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            return {"error": str(e)}

    def _on_market_data_saved(self, event_data: Dict[str, Any]):
        """Callback for market data saved events"""
        try:
            logger.debug(f"Market data saved event: {event_data}")

            # Trigger additional processing if needed
            instrument_id = event_data.get("instrument_id")
            data_type = event_data.get("data_type")

            # Example: Trigger technical analysis
            if instrument_id and data_type == "bar":
                self._trigger_technical_analysis(instrument_id)

        except Exception as e:
            logger.error(f"Error in market data saved callback: {e}")

    def _on_agent_decision_saved(self, event_data: Dict[str, Any]):
        """Callback for agent decision saved events"""
        try:
            logger.debug(f"Agent decision saved event: {event_data}")

            # Trigger additional processing if needed
            agent_id = event_data.get("agent_id")
            decision_type = event_data.get("decision_type")
            confidence = event_data.get("confidence", 0.0)

            # Example: High confidence decisions trigger immediate action
            if confidence > 0.8 and decision_type in ["buy_signal", "sell_signal"]:
                self._trigger_high_confidence_action(agent_id, decision_type, confidence)

        except Exception as e:
            logger.error(f"Error in agent decision saved callback: {e}")

    def _trigger_technical_analysis(self, instrument_id: str):
        """Trigger technical analysis for instrument"""
        try:
            # This could trigger additional AI analysis
            logger.debug(f"Triggering technical analysis for {instrument_id}")

            # Example: Get recent market data and analyze
            recent_data = self.get_enhanced_market_data(
                instrument_id, "bar", MemoryType.CACHE
            )

            if recent_data:
                # Publish analysis trigger event
                if self.unified_memory:
                    self.unified_memory.publish_event(
                        event_type="technical_analysis_trigger",
                        event_data={
                            "instrument_id": instrument_id,
                            "trigger_reason": "new_bar_data",
                            "data_timestamp": recent_data.get("timestamp")
                        },
                        source=DataSource.NAUTILUS,
                        target=DataSource.CREWAI
                    )

        except Exception as e:
            logger.error(f"Error triggering technical analysis: {e}")

    def _trigger_high_confidence_action(self, agent_id: str, decision_type: str, confidence: float):
        """Trigger action for high confidence decisions"""
        try:
            logger.info(f"High confidence decision detected: {agent_id} - {decision_type} ({confidence})")

            # Publish high priority event
            if self.unified_memory:
                self.unified_memory.publish_event(
                    event_type="high_confidence_decision",
                    event_data={
                        "agent_id": agent_id,
                        "decision_type": decision_type,
                        "confidence": confidence,
                        "priority": "high",
                        "requires_action": True
                    },
                    source=DataSource.CREWAI,
                    target=DataSource.NAUTILUS
                )

        except Exception as e:
            logger.error(f"Error triggering high confidence action: {e}")

    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.unified_memory:
                self.unified_memory.stop()
                logger.info("Enhanced Data Bridge cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def __del__(self):
        """Destructor"""
        self.cleanup()
