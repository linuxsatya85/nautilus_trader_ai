"""
Nautilus Adapter - Integrates existing Nautilus Trader with CrewAI

This adapter wraps existing Nautilus Trader functionality to work with CrewAI
without modifying the original Nautilus Trader source code.
"""

import sys
import os
import asyncio
import logging
from typing import Dict, Any, Optional, Type

# Add Nautilus Trader to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'nautilus_trader'))

# Import existing Nautilus Trader classes - NO MODIFICATIONS NEEDED!
from nautilus_trader.trading.strategy import Strategy
from nautilus_trader.model.data import Bar, Tick
from nautilus_trader.model.enums import OrderSide, TimeInForce
from nautilus_trader.model.objects import Quantity
from nautilus_trader.common.enums import LogColor

logger = logging.getLogger(__name__)


class NautilusAdapter:
    """
    Adapter to integrate existing Nautilus Trader with CrewAI.
    
    This class wraps Nautilus Trader functionality and provides methods to:
    - Enhance existing strategies with AI capabilities
    - Convert Nautilus data to CrewAI-friendly formats
    - Execute AI-driven trading decisions using Nautilus infrastructure
    """
    
    def __init__(self, crewai_adapter=None):
        self.crewai_adapter = crewai_adapter
        self.ai_signals: Dict[str, Dict[str, Any]] = {}
        self.strategy_configs: Dict[str, Dict[str, Any]] = {}
        
    def create_ai_enhanced_strategy(
        self, 
        base_strategy_class: Type[Strategy], 
        crew_name: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Type[Strategy]:
        """
        Create an AI-enhanced version of an existing Nautilus strategy.
        
        Args:
            base_strategy_class: Existing Nautilus strategy class
            crew_name: Name of CrewAI crew to use for analysis
            config: Optional configuration dictionary
            
        Returns:
            Enhanced strategy class with AI capabilities
        """
        
        crewai_adapter = self.crewai_adapter
        nautilus_adapter = self
        
        class AIEnhancedStrategy(base_strategy_class):
            """AI-enhanced strategy that wraps existing Nautilus strategy."""
            
            def __init__(self, strategy_config=None):
                super().__init__(strategy_config)
                self.crew_name = crew_name
                self.ai_adapter = crewai_adapter
                self.nautilus_adapter = nautilus_adapter
                self.ai_config = config or {}
                
                # AI-specific settings
                self.ai_confidence_threshold = self.ai_config.get('confidence_threshold', 0.7)
                self.ai_analysis_interval = self.ai_config.get('analysis_interval', 60)  # seconds
                self.last_ai_analysis = 0
                
                self.log.info(
                    f"AI-Enhanced Strategy initialized with crew: {crew_name}",
                    color=LogColor.BLUE
                )
                
            def on_start(self):
                """Enhanced strategy start with AI initialization."""
                super().on_start()
                self.log.info("AI analysis system activated", color=LogColor.GREEN)
                
            def on_bar(self, bar: Bar):
                """Enhanced bar processing with AI analysis."""
                try:
                    # Convert Nautilus bar to CrewAI format
                    market_data = self._bar_to_market_data(bar)
                    
                    # Check if we should run AI analysis
                    current_time = bar.ts_event / 1_000_000_000  # Convert to seconds
                    if (current_time - self.last_ai_analysis) >= self.ai_analysis_interval:
                        # Run AI analysis asynchronously
                        asyncio.create_task(self._run_ai_analysis(market_data))
                        self.last_ai_analysis = current_time
                    
                    # Check for existing AI signals
                    instrument_str = str(bar.instrument_id)
                    ai_signal = self.nautilus_adapter.ai_signals.get(instrument_str)
                    
                    if ai_signal and self._is_signal_valid(ai_signal, current_time):
                        self._process_ai_signal(ai_signal, bar)
                    
                    # Call original strategy logic
                    super().on_bar(bar)
                    
                except Exception as e:
                    self.log.error(f"Error in AI-enhanced bar processing: {str(e)}")
                    # Fallback to original strategy
                    super().on_bar(bar)
                    
            def on_tick(self, tick: Tick):
                """Enhanced tick processing with AI context."""
                try:
                    # Add AI context to tick processing if needed
                    super().on_tick(tick)
                except Exception as e:
                    self.log.error(f"Error in AI-enhanced tick processing: {str(e)}")
                    super().on_tick(tick)
                    
            async def _run_ai_analysis(self, market_data: Dict[str, Any]):
                """Run AI analysis using CrewAI."""
                try:
                    if not self.ai_adapter:
                        return
                        
                    # Execute CrewAI analysis
                    analysis_result = await self.ai_adapter.analyze_market_data(
                        self.crew_name, 
                        market_data
                    )
                    
                    # Store AI signal for later use
                    instrument_id = market_data['instrument_id']
                    self.nautilus_adapter.ai_signals[instrument_id] = analysis_result
                    
                    self.log.info(
                        f"AI Analysis completed for {instrument_id}: "
                        f"{analysis_result.get('signal', 'UNKNOWN')} "
                        f"(confidence: {analysis_result.get('confidence', 0):.2f})",
                        color=LogColor.CYAN
                    )
                    
                except Exception as e:
                    self.log.error(f"AI analysis error: {str(e)}")
                    
            def _bar_to_market_data(self, bar: Bar) -> Dict[str, Any]:
                """Convert Nautilus bar to CrewAI market data format."""
                return {
                    'instrument_id': str(bar.instrument_id),
                    'open': float(bar.open),
                    'high': float(bar.high),
                    'low': float(bar.low),
                    'close': float(bar.close),
                    'volume': float(bar.volume),
                    'timestamp': bar.ts_event,
                    'bar_type': str(bar.bar_type)
                }
                
            def _is_signal_valid(self, signal: Dict[str, Any], current_time: float) -> bool:
                """Check if AI signal is still valid."""
                signal_time = signal.get('timestamp', 0) / 1_000_000_000  # Convert to seconds
                age_seconds = current_time - signal_time
                max_age = self.ai_config.get('signal_max_age', 300)  # 5 minutes default
                
                return age_seconds <= max_age
                
            def _process_ai_signal(self, signal: Dict[str, Any], bar: Bar):
                """Process AI signal and execute trades using existing Nautilus methods."""
                try:
                    signal_type = signal.get('signal', 'HOLD')
                    confidence = signal.get('confidence', 0.0)
                    
                    if confidence < self.ai_confidence_threshold:
                        self.log.info(
                            f"AI signal confidence {confidence:.2f} below threshold "
                            f"{self.ai_confidence_threshold:.2f}",
                            color=LogColor.YELLOW
                        )
                        return
                        
                    # Calculate position size based on confidence
                    base_quantity = self.ai_config.get('base_quantity', 100)
                    adjusted_quantity = int(base_quantity * confidence)
                    
                    if signal_type == 'BUY':
                        self._execute_ai_buy(bar, adjusted_quantity, signal)
                    elif signal_type == 'SELL':
                        self._execute_ai_sell(bar, adjusted_quantity, signal)
                        
                except Exception as e:
                    self.log.error(f"Error processing AI signal: {str(e)}")
                    
            def _execute_ai_buy(self, bar: Bar, quantity: int, signal: Dict[str, Any]):
                """Execute AI-driven buy order using existing Nautilus methods."""
                try:
                    order = self.order_factory.market(
                        instrument_id=bar.instrument_id,
                        order_side=OrderSide.BUY,
                        quantity=Quantity.from_int(quantity),
                        time_in_force=TimeInForce.GTC
                    )
                    
                    self.submit_order(order)
                    
                    self.log.info(
                        f"AI BUY order submitted: {quantity} units at {bar.close} "
                        f"(confidence: {signal.get('confidence', 0):.2f})",
                        color=LogColor.GREEN
                    )
                    
                except Exception as e:
                    self.log.error(f"Error executing AI buy order: {str(e)}")
                    
            def _execute_ai_sell(self, bar: Bar, quantity: int, signal: Dict[str, Any]):
                """Execute AI-driven sell order using existing Nautilus methods."""
                try:
                    order = self.order_factory.market(
                        instrument_id=bar.instrument_id,
                        order_side=OrderSide.SELL,
                        quantity=Quantity.from_int(quantity),
                        time_in_force=TimeInForce.GTC
                    )
                    
                    self.submit_order(order)
                    
                    self.log.info(
                        f"AI SELL order submitted: {quantity} units at {bar.close} "
                        f"(confidence: {signal.get('confidence', 0):.2f})",
                        color=LogColor.RED
                    )
                    
                except Exception as e:
                    self.log.error(f"Error executing AI sell order: {str(e)}")
                    
            def on_stop(self):
                """Enhanced strategy stop with AI cleanup."""
                self.log.info("AI analysis system deactivated", color=LogColor.YELLOW)
                super().on_stop()
                
        return AIEnhancedStrategy
        
    def wrap_existing_strategy(
        self, 
        strategy_instance: Strategy, 
        crew_name: str
    ) -> Strategy:
        """
        Wrap an existing strategy instance with AI capabilities.
        
        Args:
            strategy_instance: Existing Nautilus strategy instance
            crew_name: Name of CrewAI crew to use
            
        Returns:
            AI-enhanced strategy instance
        """
        # Store original methods
        original_on_bar = strategy_instance.on_bar
        original_on_tick = strategy_instance.on_tick
        
        # Add AI capabilities
        strategy_instance.crew_name = crew_name
        strategy_instance.ai_adapter = self.crewai_adapter
        strategy_instance.ai_signals = {}
        
        def enhanced_on_bar(bar: Bar):
            """Enhanced on_bar with AI analysis."""
            try:
                # Convert bar to market data
                market_data = {
                    'instrument_id': str(bar.instrument_id),
                    'close': float(bar.close),
                    'volume': float(bar.volume),
                    'timestamp': bar.ts_event
                }
                
                # Run AI analysis if adapter is available
                if self.crewai_adapter:
                    asyncio.create_task(
                        self._update_ai_signals(strategy_instance, market_data)
                    )
                
                # Call original method
                original_on_bar(bar)
                
            except Exception as e:
                logger.error(f"Error in enhanced on_bar: {str(e)}")
                original_on_bar(bar)
                
        # Replace methods
        strategy_instance.on_bar = enhanced_on_bar
        
        return strategy_instance
        
    async def _update_ai_signals(self, strategy: Strategy, market_data: Dict[str, Any]):
        """Update AI signals for a strategy."""
        try:
            if not self.crewai_adapter:
                return
                
            result = await self.crewai_adapter.analyze_market_data(
                strategy.crew_name,
                market_data
            )
            
            instrument_id = market_data['instrument_id']
            strategy.ai_signals[instrument_id] = result
            
        except Exception as e:
            logger.error(f"Error updating AI signals: {str(e)}")
            
    def get_ai_signal(self, instrument_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest AI signal for an instrument."""
        return self.ai_signals.get(instrument_id)
        
    def clear_ai_signals(self, instrument_id: str = None):
        """Clear AI signals for an instrument or all instruments."""
        if instrument_id:
            self.ai_signals.pop(instrument_id, None)
        else:
            self.ai_signals.clear()
            
    def get_strategy_status(self) -> Dict[str, Any]:
        """Get status of AI-enhanced strategies."""
        return {
            "active_signals": len(self.ai_signals),
            "strategy_configs": len(self.strategy_configs),
            "crewai_connected": self.crewai_adapter is not None
        }