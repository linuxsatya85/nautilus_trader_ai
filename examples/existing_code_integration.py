#!/usr/bin/env python3
"""
Existing Code Integration Example

This example demonstrates how to integrate existing CrewAI and Nautilus Trader
codebases without modifying the original source code.

Features demonstrated:
1. Using existing CrewAI agents and crews
2. Using existing Nautilus Trader strategies
3. Creating AI-enhanced trading strategies
4. Real-time data flow between systems
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# Add project paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import integration adapters
from integration.adapters.crewai_adapter import CrewAIAdapter
from integration.adapters.nautilus_adapter import NautilusAdapter
from integration.bridges.data_bridge import DataBridge

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MockNautilusBar:
    """Mock Nautilus Bar for demonstration."""
    
    def __init__(self, instrument_id, open_price, high, low, close, volume, timestamp):
        self.instrument_id = instrument_id
        self.open = open_price
        self.high = high
        self.low = low
        self.close = close
        self.volume = volume
        self.ts_event = timestamp
        self.bar_type = "1-MINUTE-BID"


class MockNautilusStrategy:
    """Mock Nautilus Strategy for demonstration."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.positions = {}
        self.orders = []
        
    def on_start(self):
        logger.info("Strategy started")
        
    def on_bar(self, bar):
        logger.info(f"Original strategy processing bar: {bar.instrument_id} @ {bar.close}")
        
    def on_stop(self):
        logger.info("Strategy stopped")
        
    def submit_order(self, order):
        self.orders.append(order)
        logger.info(f"Order submitted: {order}")


class MockOrderFactory:
    """Mock order factory for demonstration."""
    
    def market(self, instrument_id, order_side, quantity, time_in_force=None):
        return {
            'type': 'MARKET',
            'instrument_id': instrument_id,
            'side': order_side,
            'quantity': quantity,
            'time_in_force': time_in_force
        }


class MockLogger:
    """Mock logger for demonstration."""
    
    def info(self, message, color=None):
        logger.info(f"Strategy: {message}")
        
    def error(self, message, color=None):
        logger.error(f"Strategy: {message}")


async def demonstrate_crewai_integration():
    """Demonstrate CrewAI integration using existing code."""
    logger.info("=== CrewAI Integration Demo ===")
    
    # Create CrewAI adapter - uses existing CrewAI classes
    crewai_adapter = CrewAIAdapter()
    
    # Create trading crew using existing CrewAI
    trading_crew = crewai_adapter.create_trading_crew("demo_crew")
    
    # Simulate market data
    market_data = {
        'instrument_id': 'EURUSD',
        'close': 1.0850,
        'volume': 1000000,
        'timestamp': int(datetime.now().timestamp() * 1000)
    }
    
    # Run AI analysis using existing CrewAI
    logger.info("Running AI analysis...")
    analysis_result = await crewai_adapter.analyze_market_data("demo_crew", market_data)
    
    logger.info(f"AI Analysis Result:")
    logger.info(f"  Signal: {analysis_result.get('signal', 'UNKNOWN')}")
    logger.info(f"  Confidence: {analysis_result.get('confidence', 0):.2f}")
    logger.info(f"  Reasoning: {analysis_result.get('reasoning', 'N/A')[:100]}...")
    
    return analysis_result


async def demonstrate_nautilus_integration(ai_signal):
    """Demonstrate Nautilus Trader integration using existing code."""
    logger.info("=== Nautilus Trader Integration Demo ===")
    
    # Create adapters
    crewai_adapter = CrewAIAdapter()
    nautilus_adapter = NautilusAdapter(crewai_adapter)
    
    # Create AI-enhanced strategy using existing Nautilus strategy
    AIEnhancedStrategy = nautilus_adapter.create_ai_enhanced_strategy(
        MockNautilusStrategy,
        "demo_crew",
        config={
            'confidence_threshold': 0.6,
            'base_quantity': 100
        }
    )
    
    # Create strategy instance
    strategy = AIEnhancedStrategy()
    
    # Add mock components
    strategy.order_factory = MockOrderFactory()
    strategy.log = MockLogger()
    
    # Simulate AI signal
    nautilus_adapter.ai_signals['EURUSD'] = ai_signal
    
    # Start strategy
    strategy.on_start()
    
    # Create mock bar data
    mock_bar = MockNautilusBar(
        instrument_id='EURUSD',
        open_price=1.0845,
        high=1.0855,
        low=1.0840,
        close=1.0850,
        volume=1000000,
        timestamp=int(datetime.now().timestamp() * 1_000_000_000)  # nanoseconds
    )
    
    # Process bar with AI enhancement
    logger.info("Processing bar with AI enhancement...")
    strategy.on_bar(mock_bar)
    
    # Stop strategy
    strategy.on_stop()
    
    logger.info(f"Orders generated: {len(strategy.orders)}")
    for i, order in enumerate(strategy.orders):
        logger.info(f"  Order {i+1}: {order}")


async def demonstrate_data_bridge():
    """Demonstrate data bridge functionality."""
    logger.info("=== Data Bridge Demo ===")
    
    # Create data bridge
    data_bridge = DataBridge()
    
    # Register data subscriber
    def data_callback(data_type, data):
        logger.info(f"Data Bridge received {data_type}: {data['instrument_id']}")
    
    data_bridge.register_data_subscriber(data_callback)
    
    # Create mock bar
    mock_bar = MockNautilusBar(
        instrument_id='GBPUSD',
        open_price=1.2500,
        high=1.2510,
        low=1.2495,
        close=1.2505,
        volume=500000,
        timestamp=int(datetime.now().timestamp() * 1_000_000_000)
    )
    
    # Process bar through data bridge
    data_bridge.on_bar(mock_bar)
    
    # Get market history
    history = data_bridge.get_market_history('GBPUSD')
    logger.info(f"Market history entries: {len(history)}")
    
    # Get market summary
    summary = data_bridge.get_market_summary('GBPUSD')
    logger.info(f"Market summary: {summary['data_available']}")
    
    return data_bridge


async def demonstrate_full_integration():
    """Demonstrate full integration of all components."""
    logger.info("=== Full Integration Demo ===")
    
    # Create all adapters
    crewai_adapter = CrewAIAdapter()
    nautilus_adapter = NautilusAdapter(crewai_adapter)
    data_bridge = DataBridge(crewai_adapter)
    
    # Create trading crew
    trading_crew = crewai_adapter.create_trading_crew("full_demo_crew")
    
    # Create AI-enhanced strategy
    AIStrategy = nautilus_adapter.create_ai_enhanced_strategy(
        MockNautilusStrategy,
        "full_demo_crew"
    )
    
    strategy = AIStrategy()
    strategy.order_factory = MockOrderFactory()
    strategy.log = MockLogger()
    
    # Start strategy
    strategy.on_start()
    
    # Simulate real-time data flow
    instruments = ['EURUSD', 'GBPUSD', 'USDJPY']
    
    for i in range(5):  # 5 iterations
        logger.info(f"--- Iteration {i+1} ---")
        
        for instrument in instruments:
            # Create mock market data
            base_price = {'EURUSD': 1.0850, 'GBPUSD': 1.2500, 'USDJPY': 110.50}[instrument]
            price_change = (i - 2) * 0.001  # Simulate price movement
            
            mock_bar = MockNautilusBar(
                instrument_id=instrument,
                open_price=base_price + price_change - 0.0005,
                high=base_price + price_change + 0.001,
                low=base_price + price_change - 0.001,
                close=base_price + price_change,
                volume=1000000,
                timestamp=int(datetime.now().timestamp() * 1_000_000_000)
            )
            
            # Process through data bridge
            data_bridge.on_bar(mock_bar)
            
            # Convert to market data for AI
            market_data = {
                'instrument_id': instrument,
                'close': mock_bar.close,
                'volume': mock_bar.volume,
                'timestamp': mock_bar.ts_event
            }
            
            # Run AI analysis
            ai_result = await crewai_adapter.analyze_market_data("full_demo_crew", market_data)
            
            # Store AI signal
            nautilus_adapter.ai_signals[instrument] = ai_result
            
            # Process through strategy
            strategy.on_bar(mock_bar)
            
        await asyncio.sleep(1)  # Simulate time delay
    
    # Stop strategy
    strategy.on_stop()
    
    # Show results
    logger.info(f"Total orders generated: {len(strategy.orders)}")
    logger.info(f"Data bridge status: {data_bridge.get_status()}")
    logger.info(f"Nautilus adapter status: {nautilus_adapter.get_strategy_status()}")


async def main():
    """Main demonstration function."""
    logger.info("Starting AI-Nautilus Integration Demo")
    logger.info("Using existing CrewAI and Nautilus Trader codebases")
    
    try:
        # Demo 1: CrewAI Integration
        ai_result = await demonstrate_crewai_integration()
        
        # Demo 2: Nautilus Integration
        await demonstrate_nautilus_integration(ai_result)
        
        # Demo 3: Data Bridge
        await demonstrate_data_bridge()
        
        # Demo 4: Full Integration
        await demonstrate_full_integration()
        
        logger.info("✅ All integration demos completed successfully!")
        logger.info("✅ Existing codebases integrated without modifications!")
        
    except Exception as e:
        logger.error(f"Demo error: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())