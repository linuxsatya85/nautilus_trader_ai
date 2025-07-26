"""
Data Bridge - Connects existing Nautilus Trader data with CrewAI context

This bridge converts data between Nautilus Trader and CrewAI formats
without modifying either codebase.
"""

import sys
import os
import logging
from typing import Dict, Any, List, Optional

# Add both codebases to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'nautilus_trader'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'crewai', 'src'))

# Import existing classes - NO MODIFICATIONS NEEDED!
from nautilus_trader.model.data import Bar, Tick, OrderBookData
from nautilus_trader.model.identifiers import InstrumentId
from crewai.utilities.events import crewai_event_bus

logger = logging.getLogger(__name__)


class DataBridge:
    """
    Bridge between existing Nautilus Trader data and CrewAI context.
    
    This class:
    - Converts Nautilus data formats to CrewAI-friendly formats
    - Maintains data history for AI analysis
    - Provides real-time data streaming to AI agents
    """
    
    def __init__(self, crewai_adapter=None, nautilus_engine=None):
        self.crewai_adapter = crewai_adapter
        self.nautilus_engine = nautilus_engine
        
        # Data storage for AI context
        self.market_data_history: Dict[str, List[Dict[str, Any]]] = {}
        self.tick_data_history: Dict[str, List[Dict[str, Any]]] = {}
        self.orderbook_data: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.max_history_length = 1000
        self.data_subscribers: List[callable] = []
        
        logger.info("DataBridge initialized")
        
    def register_data_subscriber(self, callback: callable):
        """Register a callback for data updates."""
        self.data_subscribers.append(callback)
        logger.info(f"Registered data subscriber: {callback.__name__}")
        
    def on_bar(self, bar: Bar):
        """
        Process incoming bar data from existing Nautilus Trader.
        
        Args:
            bar: Nautilus Trader Bar object
        """
        try:
            # Convert Nautilus bar to AI-friendly format
            market_data = self._bar_to_market_data(bar)
            
            # Store in history
            instrument_str = str(bar.instrument_id)
            if instrument_str not in self.market_data_history:
                self.market_data_history[instrument_str] = []
                
            self.market_data_history[instrument_str].append(market_data)
            
            # Maintain history size
            if len(self.market_data_history[instrument_str]) > self.max_history_length:
                self.market_data_history[instrument_str].pop(0)
                
            # Notify subscribers
            self._notify_subscribers('bar', market_data)
            
            # Send to CrewAI event bus if available
            if hasattr(crewai_event_bus, 'emit'):
                crewai_event_bus.emit('market_data', {
                    'type': 'bar',
                    'data': market_data
                })
                
            logger.debug(f"Processed bar data for {instrument_str}")
            
        except Exception as e:
            logger.error(f"Error processing bar data: {str(e)}")
            
    def on_tick(self, tick: Tick):
        """
        Process incoming tick data from existing Nautilus Trader.
        
        Args:
            tick: Nautilus Trader Tick object
        """
        try:
            # Convert Nautilus tick to AI-friendly format
            tick_data = self._tick_to_market_data(tick)
            
            # Store in history
            instrument_str = str(tick.instrument_id)
            if instrument_str not in self.tick_data_history:
                self.tick_data_history[instrument_str] = []
                
            self.tick_data_history[instrument_str].append(tick_data)
            
            # Maintain history size
            if len(self.tick_data_history[instrument_str]) > self.max_history_length:
                self.tick_data_history[instrument_str].pop(0)
                
            # Notify subscribers
            self._notify_subscribers('tick', tick_data)
            
            # Send to CrewAI event bus if available
            if hasattr(crewai_event_bus, 'emit'):
                crewai_event_bus.emit('market_data', {
                    'type': 'tick',
                    'data': tick_data
                })
                
            logger.debug(f"Processed tick data for {instrument_str}")
            
        except Exception as e:
            logger.error(f"Error processing tick data: {str(e)}")
            
    def on_order_book(self, order_book: OrderBookData):
        """
        Process incoming order book data from existing Nautilus Trader.
        
        Args:
            order_book: Nautilus Trader OrderBookData object
        """
        try:
            # Convert order book to AI-friendly format
            book_data = self._orderbook_to_market_data(order_book)
            
            # Store current order book
            instrument_str = str(order_book.instrument_id)
            self.orderbook_data[instrument_str] = book_data
            
            # Notify subscribers
            self._notify_subscribers('orderbook', book_data)
            
            # Send to CrewAI event bus if available
            if hasattr(crewai_event_bus, 'emit'):
                crewai_event_bus.emit('market_data', {
                    'type': 'orderbook',
                    'data': book_data
                })
                
            logger.debug(f"Processed order book data for {instrument_str}")
            
        except Exception as e:
            logger.error(f"Error processing order book data: {str(e)}")
            
    def _bar_to_market_data(self, bar: Bar) -> Dict[str, Any]:
        """Convert Nautilus Bar to AI-friendly market data format."""
        return {
            'instrument_id': str(bar.instrument_id),
            'type': 'bar',
            'timestamp': bar.ts_event,
            'open': float(bar.open),
            'high': float(bar.high),
            'low': float(bar.low),
            'close': float(bar.close),
            'volume': float(bar.volume),
            'bar_type': str(bar.bar_type),
            'aggregation_source': str(bar.aggregation_source) if hasattr(bar, 'aggregation_source') else None
        }
        
    def _tick_to_market_data(self, tick: Tick) -> Dict[str, Any]:
        """Convert Nautilus Tick to AI-friendly market data format."""
        return {
            'instrument_id': str(tick.instrument_id),
            'type': 'tick',
            'timestamp': tick.ts_event,
            'price': float(tick.price),
            'size': float(tick.size),
            'aggressor_side': str(tick.aggressor_side) if hasattr(tick, 'aggressor_side') else None,
            'trade_id': str(tick.trade_id) if hasattr(tick, 'trade_id') else None
        }
        
    def _orderbook_to_market_data(self, order_book: OrderBookData) -> Dict[str, Any]:
        """Convert Nautilus OrderBookData to AI-friendly format."""
        try:
            # Extract bid/ask data
            bids = []
            asks = []
            
            if hasattr(order_book, 'bids') and order_book.bids:
                bids = [
                    {'price': float(level.price), 'size': float(level.size)}
                    for level in order_book.bids[:10]  # Top 10 levels
                ]
                
            if hasattr(order_book, 'asks') and order_book.asks:
                asks = [
                    {'price': float(level.price), 'size': float(level.size)}
                    for level in order_book.asks[:10]  # Top 10 levels
                ]
                
            return {
                'instrument_id': str(order_book.instrument_id),
                'type': 'orderbook',
                'timestamp': order_book.ts_event,
                'bids': bids,
                'asks': asks,
                'bid_price': float(bids[0]['price']) if bids else None,
                'ask_price': float(asks[0]['price']) if asks else None,
                'spread': float(asks[0]['price'] - bids[0]['price']) if bids and asks else None
            }
            
        except Exception as e:
            logger.error(f"Error converting order book: {str(e)}")
            return {
                'instrument_id': str(order_book.instrument_id),
                'type': 'orderbook',
                'timestamp': order_book.ts_event,
                'error': str(e)
            }
            
    def _notify_subscribers(self, data_type: str, data: Dict[str, Any]):
        """Notify all registered subscribers of new data."""
        for callback in self.data_subscribers:
            try:
                callback(data_type, data)
            except Exception as e:
                logger.error(f"Error in data subscriber callback: {str(e)}")
                
    def get_market_history(
        self, 
        instrument_id: str, 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get market data history for an instrument.
        
        Args:
            instrument_id: Instrument identifier
            limit: Maximum number of records to return
            
        Returns:
            List of market data records
        """
        history = self.market_data_history.get(instrument_id, [])
        if limit:
            return history[-limit:]
        return history
        
    def get_tick_history(
        self, 
        instrument_id: str, 
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get tick data history for an instrument.
        
        Args:
            instrument_id: Instrument identifier
            limit: Maximum number of records to return
            
        Returns:
            List of tick data records
        """
        history = self.tick_data_history.get(instrument_id, [])
        if limit:
            return history[-limit:]
        return history
        
    def get_current_orderbook(self, instrument_id: str) -> Optional[Dict[str, Any]]:
        """
        Get current order book for an instrument.
        
        Args:
            instrument_id: Instrument identifier
            
        Returns:
            Current order book data or None
        """
        return self.orderbook_data.get(instrument_id)
        
    def get_market_summary(self, instrument_id: str) -> Dict[str, Any]:
        """
        Get market summary for an instrument.
        
        Args:
            instrument_id: Instrument identifier
            
        Returns:
            Market summary with latest data
        """
        try:
            history = self.get_market_history(instrument_id, limit=1)
            tick_history = self.get_tick_history(instrument_id, limit=1)
            orderbook = self.get_current_orderbook(instrument_id)
            
            summary = {
                'instrument_id': instrument_id,
                'timestamp': None,
                'last_bar': history[-1] if history else None,
                'last_tick': tick_history[-1] if tick_history else None,
                'orderbook': orderbook,
                'data_available': {
                    'bars': len(self.market_data_history.get(instrument_id, [])),
                    'ticks': len(self.tick_data_history.get(instrument_id, [])),
                    'orderbook': orderbook is not None
                }
            }
            
            # Set timestamp from most recent data
            if history:
                summary['timestamp'] = history[-1]['timestamp']
            elif tick_history:
                summary['timestamp'] = tick_history[-1]['timestamp']
            elif orderbook:
                summary['timestamp'] = orderbook['timestamp']
                
            return summary
            
        except Exception as e:
            logger.error(f"Error creating market summary: {str(e)}")
            return {
                'instrument_id': instrument_id,
                'error': str(e)
            }
            
    def clear_history(self, instrument_id: Optional[str] = None):
        """
        Clear data history.
        
        Args:
            instrument_id: Specific instrument to clear, or None for all
        """
        if instrument_id:
            self.market_data_history.pop(instrument_id, None)
            self.tick_data_history.pop(instrument_id, None)
            self.orderbook_data.pop(instrument_id, None)
            logger.info(f"Cleared history for {instrument_id}")
        else:
            self.market_data_history.clear()
            self.tick_data_history.clear()
            self.orderbook_data.clear()
            logger.info("Cleared all data history")
            
    def get_status(self) -> Dict[str, Any]:
        """Get data bridge status."""
        return {
            'instruments_tracked': len(set(
                list(self.market_data_history.keys()) +
                list(self.tick_data_history.keys()) +
                list(self.orderbook_data.keys())
            )),
            'total_bars': sum(len(history) for history in self.market_data_history.values()),
            'total_ticks': sum(len(history) for history in self.tick_data_history.values()),
            'orderbooks_active': len(self.orderbook_data),
            'subscribers': len(self.data_subscribers),
            'max_history_length': self.max_history_length
        }