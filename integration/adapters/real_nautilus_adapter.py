"""
REAL Nautilus Trader Adapter - Uses actual Nautilus Trader classes

This adapter uses the REAL Nautilus Trader framework (not mocks) for trading operations.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timezone
from decimal import Decimal

# Import REAL Nautilus Trader classes
from nautilus_trader.core.nautilus_pyo3 import UUID4
from nautilus_trader.model.identifiers import InstrumentId, ClientId, TraderId, StrategyId, ClientOrderId
from nautilus_trader.model.data import QuoteTick, TradeTick, Bar
from nautilus_trader.model.enums import OrderSide, OrderType, TimeInForce, PriceType
from nautilus_trader.model.objects import Price, Quantity, Money
from nautilus_trader.model.orders import MarketOrder, LimitOrder
from nautilus_trader.model.events import OrderFilled, OrderSubmitted
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.core.datetime import dt_to_unix_nanos
from nautilus_trader.model.currencies import USD

logger = logging.getLogger(__name__)


class RealNautilusAdapter:
    """
    REAL Nautilus Trader Adapter that uses actual Nautilus Trader framework.
    
    This class integrates with real Nautilus Trader components for trading operations.
    """
    
    def __init__(self, trader_id: str = "AI-TRADER-001"):
        self.trader_id = TraderId(trader_id)
        self.client_id = ClientId("SIM")
        self.venue = "SIM"
        self.strategies: Dict[str, Strategy] = {}
        self.active_orders: Dict[str, Any] = {}
        self.market_data: Dict[str, Any] = {}
        self.order_counter = 0  # For generating unique order IDs
        
        logger.info(f"🚢 REAL Nautilus Adapter initialized with trader: {self.trader_id}")
        
    def _generate_order_id(self) -> ClientOrderId:
        """Generate a unique client order ID."""
        self.order_counter += 1
        return ClientOrderId(f"O-{self.order_counter:06d}")
        
    def create_real_instrument_id(self, symbol: str, venue: str = "SIM") -> InstrumentId:
        """Create a REAL Nautilus InstrumentId."""
        instrument_id = InstrumentId.from_str(f"{symbol}.{venue}")
        logger.info(f"📊 Created REAL instrument: {instrument_id}")
        return instrument_id
        
    def create_real_market_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert market data to REAL Nautilus format."""
        try:
            instrument_id = self.create_real_instrument_id(data.get('instrument_id', 'EURUSD'))
            
            # Create REAL Nautilus market data objects
            timestamp_ns = dt_to_unix_nanos(datetime.now(timezone.utc))
            
            # Create QuoteTick (bid/ask prices) with consistent precision
            bid_value = data.get('bid', data.get('close', 1.0))
            ask_value = data.get('ask', data.get('close', 1.0))
            
            # Ensure consistent precision (5 decimal places for forex)
            bid_price = Price.from_str(f"{bid_value:.5f}")
            ask_price = Price.from_str(f"{ask_value:.5f}")
            bid_size = Quantity.from_str(str(data.get('bid_size', 1000000)))
            ask_size = Quantity.from_str(str(data.get('ask_size', 1000000)))
            
            quote_tick = QuoteTick(
                instrument_id=instrument_id,
                bid_price=bid_price,
                ask_price=ask_price,
                bid_size=bid_size,
                ask_size=ask_size,
                ts_event=timestamp_ns,
                ts_init=timestamp_ns
            )
            
            # Store market data
            nautilus_data = {
                'instrument_id': instrument_id,
                'quote_tick': quote_tick,
                'timestamp': timestamp_ns,
                'bid': float(bid_price),
                'ask': float(ask_price),
                'mid': (float(bid_price) + float(ask_price)) / 2,
                'spread': float(ask_price) - float(bid_price),
                'volume': data.get('volume', 0),
                'raw_data': data
            }
            
            self.market_data[str(instrument_id)] = nautilus_data
            logger.info(f"📈 Created REAL market data for {instrument_id}: bid={bid_price}, ask={ask_price}")
            
            return nautilus_data
            
        except Exception as e:
            logger.error(f"Error creating REAL market data: {str(e)}")
            return {
                'error': str(e),
                'instrument_id': data.get('instrument_id', 'UNKNOWN'),
                'timestamp': datetime.now().timestamp()
            }
            
    def create_real_market_order(self, 
                                signal: str, 
                                instrument_id: InstrumentId,
                                quantity: float = 10000,
                                strategy_id: str = "AI_STRATEGY") -> Optional[MarketOrder]:
        """Create a REAL Nautilus MarketOrder."""
        try:
            # Determine order side
            if signal.upper() == "BUY":
                side = OrderSide.BUY
            elif signal.upper() == "SELL":
                side = OrderSide.SELL
            else:
                logger.warning(f"Invalid signal {signal}, no order created")
                return None
                
            # Create REAL Nautilus order
            order = MarketOrder(
                trader_id=self.trader_id,
                strategy_id=StrategyId(strategy_id.replace("_", "-")),
                instrument_id=instrument_id,
                client_order_id=self._generate_order_id(),
                order_side=side,
                quantity=Quantity.from_str(str(quantity)),
                time_in_force=TimeInForce.IOC,  # Immediate or Cancel
                reduce_only=False,
                quote_quantity=False,
                ts_init=dt_to_unix_nanos(datetime.now(timezone.utc))
            )
            
            order_key = str(order.client_order_id)
            self.active_orders[order_key] = {
                'order': order,
                'signal': signal,
                'instrument': str(instrument_id),
                'quantity': quantity,
                'side': str(side),
                'status': 'CREATED',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"📋 Created REAL market order: {order.client_order_id} - {side} {quantity} {instrument_id}")
            return order
            
        except Exception as e:
            logger.error(f"Error creating REAL market order: {str(e)}")
            return None
            
    def create_real_limit_order(self,
                               signal: str,
                               instrument_id: InstrumentId,
                               price: float,
                               quantity: float = 10000,
                               strategy_id: str = "AI_STRATEGY") -> Optional[LimitOrder]:
        """Create a REAL Nautilus LimitOrder."""
        try:
            # Determine order side
            if signal.upper() == "BUY":
                side = OrderSide.BUY
            elif signal.upper() == "SELL":
                side = OrderSide.SELL
            else:
                logger.warning(f"Invalid signal {signal}, no order created")
                return None
                
            # Create REAL Nautilus limit order
            order = LimitOrder(
                trader_id=self.trader_id,
                strategy_id=StrategyId(strategy_id.replace("_", "-")),
                instrument_id=instrument_id,
                client_order_id=self._generate_order_id(),
                order_side=side,
                quantity=Quantity.from_str(str(quantity)),
                price=Price.from_str(str(price)),
                time_in_force=TimeInForce.GTC,  # Good Till Cancel
                reduce_only=False,
                quote_quantity=False,
                ts_init=dt_to_unix_nanos(datetime.now(timezone.utc))
            )
            
            order_key = str(order.client_order_id)
            self.active_orders[order_key] = {
                'order': order,
                'signal': signal,
                'instrument': str(instrument_id),
                'quantity': quantity,
                'price': price,
                'side': str(side),
                'status': 'CREATED',
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"📋 Created REAL limit order: {order.client_order_id} - {side} {quantity} @ {price} {instrument_id}")
            return order
            
        except Exception as e:
            logger.error(f"Error creating REAL limit order: {str(e)}")
            return None
            
    async def execute_real_trading_signal(self, 
                                         signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a trading signal using REAL Nautilus Trader."""
        try:
            signal = signal_data.get('signal', 'HOLD')
            instrument_str = signal_data.get('instrument_id', 'EURUSD')
            confidence = signal_data.get('confidence', 0.5)
            
            # Skip HOLD signals
            if signal.upper() == 'HOLD':
                return {
                    'status': 'skipped',
                    'reason': 'HOLD signal - no action taken',
                    'signal': signal,
                    'instrument': instrument_str
                }
                
            # Create REAL instrument
            instrument_id = self.create_real_instrument_id(instrument_str)
            
            # Calculate position size based on confidence
            base_quantity = 10000
            quantity = base_quantity * confidence
            
            # Create REAL market order
            order = self.create_real_market_order(
                signal=signal,
                instrument_id=instrument_id,
                quantity=quantity,
                strategy_id="AI-CREWAI-STRATEGY"
            )
            
            if not order:
                return {
                    'status': 'failed',
                    'reason': 'Failed to create order',
                    'signal': signal,
                    'instrument': instrument_str
                }
                
            # Simulate order execution (in real system, this would go to broker)
            execution_result = self._simulate_order_execution(order, signal_data)
            
            return {
                'status': 'executed',
                'order_id': str(order.client_order_id),
                'signal': signal,
                'instrument': instrument_str,
                'quantity': quantity,
                'side': str(order.order_side),
                'execution': execution_result,
                'timestamp': datetime.now().isoformat(),
                'nautilus_order': True  # Flag indicating real Nautilus order
            }
            
        except Exception as e:
            logger.error(f"Error executing REAL trading signal: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'signal': signal_data.get('signal', 'UNKNOWN'),
                'instrument': signal_data.get('instrument_id', 'UNKNOWN')
            }
            
    def _simulate_order_execution(self, order: MarketOrder, signal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate order execution (in real system, this would be handled by execution engine)."""
        try:
            # Get market data for execution price
            instrument_str = str(order.instrument_id)
            market_data = self.market_data.get(instrument_str, {})
            
            # Determine execution price
            if order.order_side == OrderSide.BUY:
                execution_price = market_data.get('ask', signal_data.get('close', 1.0))
            else:
                execution_price = market_data.get('bid', signal_data.get('close', 1.0))
                
            # Create execution result
            execution_result = {
                'price': execution_price,
                'quantity': float(order.quantity),
                'side': str(order.order_side),
                'instrument': instrument_str,
                'execution_time': datetime.now().isoformat(),
                'commission': 0.0,  # Simplified
                'slippage': 0.0001,  # Simplified
                'status': 'FILLED'
            }
            
            # Update order status
            order_key = str(order.client_order_id)
            if order_key in self.active_orders:
                self.active_orders[order_key]['status'] = 'FILLED'
                self.active_orders[order_key]['execution'] = execution_result
                
            logger.info(f"💰 Simulated execution: {order.client_order_id} filled at {execution_price}")
            return execution_result
            
        except Exception as e:
            logger.error(f"Error simulating order execution: {str(e)}")
            return {
                'status': 'FAILED',
                'error': str(e),
                'price': 0.0,
                'quantity': 0.0
            }
            
    def get_real_order_status(self, order_id: str) -> Dict[str, Any]:
        """Get status of a REAL Nautilus order."""
        order_data = self.active_orders.get(order_id)
        if not order_data:
            return {'status': 'not_found', 'order_id': order_id}
            
        return {
            'order_id': order_id,
            'status': order_data.get('status', 'UNKNOWN'),
            'signal': order_data.get('signal'),
            'instrument': order_data.get('instrument'),
            'quantity': order_data.get('quantity'),
            'side': order_data.get('side'),
            'timestamp': order_data.get('timestamp'),
            'execution': order_data.get('execution'),
            'nautilus_order': True
        }
        
    def list_active_orders(self) -> List[Dict[str, Any]]:
        """List all active REAL orders."""
        return [
            {
                'order_id': order_id,
                'status': order_data.get('status'),
                'signal': order_data.get('signal'),
                'instrument': order_data.get('instrument'),
                'quantity': order_data.get('quantity'),
                'side': order_data.get('side'),
                'timestamp': order_data.get('timestamp')
            }
            for order_id, order_data in self.active_orders.items()
        ]
        
    def get_market_data_summary(self) -> Dict[str, Any]:
        """Get summary of current market data."""
        return {
            'instruments': list(self.market_data.keys()),
            'data_count': len(self.market_data),
            'last_update': datetime.now().isoformat(),
            'adapter_type': 'real_nautilus'
        }
        
    def get_trading_summary(self) -> Dict[str, Any]:
        """Get summary of trading activity."""
        total_orders = len(self.active_orders)
        filled_orders = sum(1 for order in self.active_orders.values() 
                           if order.get('status') == 'FILLED')
        
        return {
            'trader_id': str(self.trader_id),
            'total_orders': total_orders,
            'filled_orders': filled_orders,
            'active_orders': total_orders - filled_orders,
            'instruments_traded': len(set(order.get('instrument') 
                                        for order in self.active_orders.values())),
            'adapter_type': 'real_nautilus',
            'last_activity': datetime.now().isoformat()
        }