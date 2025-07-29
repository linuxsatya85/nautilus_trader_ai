"""
Trading Manager - Core Trading Operations Management
===================================================

This module provides the TradingManager class that handles all trading operations
and coordinates between AI analysis and trade execution.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..adapters.real_crewai_adapter import RealCrewAIAdapter
from ..adapters.real_nautilus_adapter import RealNautilusAdapter
from ..config.settings import Settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class TradingManager:
    """
    Core trading manager that coordinates AI analysis and trade execution.
    
    This class manages the flow from market data through AI analysis to trade execution.
    """
    
    def __init__(self, config: Optional[Settings] = None):
        """
        Initialize the Trading Manager.
        
        Args:
            config: Optional settings configuration
        """
        self.config = config or Settings()
        self.is_active = False
        
        # Adapters
        self.crewai_adapter: Optional[RealCrewAIAdapter] = None
        self.nautilus_adapter: Optional[RealNautilusAdapter] = None
        
        # Trading state
        self.active_strategies: Dict[str, Any] = {}
        self.active_positions: Dict[str, Any] = {}
        self.order_history: List[Dict[str, Any]] = []
        self.performance_metrics: Dict[str, float] = {}
        
        logger.info("📊 Trading Manager initialized")
    
    async def initialize(self):
        """Initialize the trading manager and its components."""
        try:
            logger.info("🔧 Initializing Trading Manager...")
            
            # Initialize adapters
            self.crewai_adapter = RealCrewAIAdapter()
            self.nautilus_adapter = RealNautilusAdapter(
                trader_id=self.config.get("nautilus.trader_id", "AI-TRADER")
            )
            
            # Initialize performance tracking
            self._reset_performance_metrics()
            
            logger.info("✅ Trading Manager initialized successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Trading Manager: {e}")
            raise
    
    async def start(self):
        """Start the trading manager."""
        if self.is_active:
            logger.warning("⚠️ Trading Manager is already active")
            return
        
        try:
            logger.info("🚀 Starting Trading Manager...")
            
            # Ensure initialization
            if not self.crewai_adapter or not self.nautilus_adapter:
                await self.initialize()
            
            self.is_active = True
            
            # Start monitoring and processing
            await self._start_monitoring()
            
            logger.info("✅ Trading Manager started successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to start Trading Manager: {e}")
            self.is_active = False
            raise
    
    async def stop(self):
        """Stop the trading manager."""
        if not self.is_active:
            logger.warning("⚠️ Trading Manager is not active")
            return
        
        try:
            logger.info("🛑 Stopping Trading Manager...")
            
            # Stop all strategies
            await self._stop_all_strategies()
            
            # Close all positions if configured
            if self.config.get("trading.close_on_stop", False):
                await self._close_all_positions()
            
            self.is_active = False
            
            logger.info("✅ Trading Manager stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Error stopping Trading Manager: {e}")
            raise
    
    async def process_market_data(self, instrument: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process market data through AI analysis and generate trading signals.
        
        Args:
            instrument: Trading instrument (e.g., "EURUSD")
            market_data: Market data dictionary
            
        Returns:
            Trading signal or None
        """
        if not self.is_active:
            logger.warning("Trading Manager is not active")
            return None
        
        try:
            logger.debug(f"📊 Processing market data for {instrument}")
            
            # AI Analysis
            if self.crewai_adapter:
                analysis_result = await self._analyze_with_ai(instrument, market_data)
                
                if analysis_result and analysis_result.get("confidence", 0) > 0.5:
                    # Generate trading signal
                    signal = await self._generate_trading_signal(instrument, analysis_result)
                    
                    # Execute if signal is strong enough
                    if signal and signal.get("strength", 0) > 0.7:
                        execution_result = await self._execute_signal(signal)
                        return execution_result
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error processing market data for {instrument}: {e}")
            return None
    
    async def _analyze_with_ai(self, instrument: str, market_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze market data using AI agents."""
        try:
            if not self.crewai_adapter:
                return None
            
            # Create analysis crew if not exists
            crew_name = f"analysis_crew_{instrument}"
            if crew_name not in self.active_strategies:
                crew = self.crewai_adapter.create_real_trading_crew(crew_name)
                self.active_strategies[crew_name] = crew
            
            # Perform analysis
            analysis = await self.crewai_adapter.analyze_market_with_real_ai(
                crew_name, market_data
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ AI analysis failed for {instrument}: {e}")
            return None
    
    async def _generate_trading_signal(self, instrument: str, analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate trading signal from AI analysis."""
        try:
            signal = {
                "instrument": instrument,
                "action": analysis.get("action", "HOLD"),
                "confidence": analysis.get("confidence", 0.0),
                "strength": analysis.get("confidence", 0.0),
                "quantity": self._calculate_position_size(instrument, analysis),
                "timestamp": datetime.now(),
                "reasoning": analysis.get("reasoning", ""),
            }
            
            logger.info(f"📈 Generated signal for {instrument}: {signal['action']} (confidence: {signal['confidence']:.2f})")
            
            return signal
            
        except Exception as e:
            logger.error(f"❌ Failed to generate trading signal for {instrument}: {e}")
            return None
    
    async def _execute_signal(self, signal: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute trading signal."""
        try:
            if not self.nautilus_adapter:
                return None
            
            instrument = signal["instrument"]
            action = signal["action"]
            quantity = signal["quantity"]
            
            if action in ["BUY", "SELL"]:
                # Execute the trade
                result = await self.nautilus_adapter.execute_real_trading_signal({
                    "instrument": instrument,
                    "side": action,
                    "quantity": quantity,
                    "signal_strength": signal["strength"]
                })
                
                # Record the trade
                self._record_trade(signal, result)
                
                logger.info(f"✅ Executed {action} order for {instrument}: {quantity} units")
                
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to execute signal: {e}")
            return None
    
    def _calculate_position_size(self, instrument: str, analysis: Dict[str, Any]) -> float:
        """Calculate position size based on risk management rules."""
        try:
            # Get base position size from config
            base_size = self.config.get("trading.default_quantity", 10000)
            
            # Adjust based on confidence
            confidence = analysis.get("confidence", 0.5)
            size_multiplier = min(confidence * 2, 1.0)  # Max 100% of base size
            
            # Apply risk management
            max_position = self.config.get("risk.position_limit", 0.1)  # 10% of portfolio
            
            calculated_size = base_size * size_multiplier
            
            # Ensure within risk limits
            # This would normally check against portfolio value
            # For now, just ensure it's reasonable
            max_allowed = base_size * 2  # Max 2x base size
            final_size = min(calculated_size, max_allowed)
            
            logger.debug(f"📊 Position size for {instrument}: {final_size} (confidence: {confidence:.2f})")
            
            return final_size
            
        except Exception as e:
            logger.error(f"❌ Error calculating position size: {e}")
            return self.config.get("trading.default_quantity", 10000)
    
    def _record_trade(self, signal: Dict[str, Any], result: Dict[str, Any]):
        """Record trade in history."""
        trade_record = {
            "timestamp": datetime.now(),
            "instrument": signal["instrument"],
            "action": signal["action"],
            "quantity": signal["quantity"],
            "confidence": signal["confidence"],
            "reasoning": signal["reasoning"],
            "execution_result": result,
        }
        
        self.order_history.append(trade_record)
        
        # Keep only last 1000 trades
        if len(self.order_history) > 1000:
            self.order_history = self.order_history[-1000:]
    
    def _reset_performance_metrics(self):
        """Reset performance metrics."""
        self.performance_metrics = {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "total_pnl": 0.0,
            "win_rate": 0.0,
            "avg_win": 0.0,
            "avg_loss": 0.0,
            "max_drawdown": 0.0,
        }
    
    async def _start_monitoring(self):
        """Start monitoring and processing tasks."""
        logger.info("📊 Starting trading monitoring...")
        # This would start background tasks for monitoring
        # For now, just log that monitoring is active
    
    async def _stop_all_strategies(self):
        """Stop all active strategies."""
        logger.info("🛑 Stopping all trading strategies...")
        self.active_strategies.clear()
    
    async def _close_all_positions(self):
        """Close all open positions."""
        logger.info("🛑 Closing all open positions...")
        self.active_positions.clear()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current trading manager status."""
        return {
            "active": self.is_active,
            "active_strategies": len(self.active_strategies),
            "active_positions": len(self.active_positions),
            "total_trades": len(self.order_history),
            "performance": self.performance_metrics.copy(),
            "adapters": {
                "crewai": self.crewai_adapter is not None,
                "nautilus": self.nautilus_adapter is not None,
            }
        }
