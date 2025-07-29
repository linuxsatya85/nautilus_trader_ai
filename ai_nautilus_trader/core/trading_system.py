"""
AI Trading System - Main System Orchestrator
============================================

This module provides the main AITradingSystem class that orchestrates
all components of the AI-enhanced trading backend.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

from ..adapters.real_crewai_adapter import RealCrewAIAdapter
from ..adapters.real_nautilus_adapter import RealNautilusAdapter
from ..config.settings import Settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


class AITradingSystem:
    """
    Main AI Trading System that orchestrates CrewAI and Nautilus Trader integration.
    
    This class provides the primary interface for the AI trading backend,
    managing all components and their interactions.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AI Trading System.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = Settings(config or {})
        self.is_running = False
        self.start_time: Optional[datetime] = None
        
        # Initialize adapters
        self.crewai_adapter: Optional[RealCrewAIAdapter] = None
        self.nautilus_adapter: Optional[RealNautilusAdapter] = None
        
        # System components
        self.active_strategies: Dict[str, Any] = {}
        self.active_agents: Dict[str, Any] = {}
        self.market_data_feeds: Dict[str, Any] = {}
        
        logger.info("🚀 AI Trading System initialized")
    
    async def initialize(self):
        """Initialize all system components."""
        try:
            logger.info("🔧 Initializing AI Trading System components...")
            
            # Initialize CrewAI adapter
            self.crewai_adapter = RealCrewAIAdapter()
            logger.info("✅ CrewAI adapter initialized")
            
            # Initialize Nautilus adapter
            self.nautilus_adapter = RealNautilusAdapter()
            logger.info("✅ Nautilus Trader adapter initialized")
            
            # Setup default AI agents
            await self._setup_default_agents()
            
            # Setup default trading strategies
            await self._setup_default_strategies()
            
            logger.info("✅ AI Trading System initialization complete")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI Trading System: {e}")
            raise
    
    async def start(self):
        """Start the AI Trading System."""
        if self.is_running:
            logger.warning("⚠️ AI Trading System is already running")
            return
        
        try:
            logger.info("🚀 Starting AI Trading System...")
            
            # Initialize if not already done
            if not self.crewai_adapter or not self.nautilus_adapter:
                await self.initialize()
            
            self.is_running = True
            self.start_time = datetime.now()
            
            # Start market data feeds
            await self._start_market_data()
            
            # Start AI agents
            await self._start_agents()
            
            # Start trading strategies
            await self._start_strategies()
            
            logger.info("✅ AI Trading System started successfully")
            logger.info(f"📊 System Status: {self.get_status()}")
            
        except Exception as e:
            logger.error(f"❌ Failed to start AI Trading System: {e}")
            self.is_running = False
            raise
    
    async def stop(self):
        """Stop the AI Trading System."""
        if not self.is_running:
            logger.warning("⚠️ AI Trading System is not running")
            return
        
        try:
            logger.info("🛑 Stopping AI Trading System...")
            
            # Stop trading strategies
            await self._stop_strategies()
            
            # Stop AI agents
            await self._stop_agents()
            
            # Stop market data feeds
            await self._stop_market_data()
            
            self.is_running = False
            
            logger.info("✅ AI Trading System stopped successfully")
            
        except Exception as e:
            logger.error(f"❌ Error stopping AI Trading System: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            "running": self.is_running,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "uptime": str(datetime.now() - self.start_time) if self.start_time else None,
            "active_strategies": len(self.active_strategies),
            "active_agents": len(self.active_agents),
            "market_data_feeds": len(self.market_data_feeds),
            "crewai_status": "connected" if self.crewai_adapter else "disconnected",
            "nautilus_status": "connected" if self.nautilus_adapter else "disconnected",
        }
    
    async def _setup_default_agents(self):
        """Setup default AI agents."""
        if not self.crewai_adapter:
            return
        
        try:
            # Create market analyst agent
            market_analyst = self.crewai_adapter.create_market_analyst()
            self.active_agents["market_analyst"] = market_analyst
            
            # Create risk manager agent
            risk_manager = self.crewai_adapter.create_risk_manager()
            self.active_agents["risk_manager"] = risk_manager
            
            logger.info(f"✅ Setup {len(self.active_agents)} default AI agents")
            
        except Exception as e:
            logger.error(f"❌ Failed to setup default agents: {e}")
            raise
    
    async def _setup_default_strategies(self):
        """Setup default trading strategies."""
        # This will be implemented based on Nautilus Trader strategy framework
        logger.info("📈 Default strategies setup (placeholder)")
    
    async def _start_market_data(self):
        """Start market data feeds."""
        logger.info("📊 Market data feeds started (placeholder)")
    
    async def _start_agents(self):
        """Start AI agents."""
        logger.info(f"🤖 Started {len(self.active_agents)} AI agents")
    
    async def _start_strategies(self):
        """Start trading strategies.""" 
        logger.info(f"📈 Started {len(self.active_strategies)} trading strategies")
    
    async def _stop_strategies(self):
        """Stop trading strategies."""
        logger.info("📈 Trading strategies stopped")
    
    async def _stop_agents(self):
        """Stop AI agents."""
        logger.info("🤖 AI agents stopped")
    
    async def _stop_market_data(self):
        """Stop market data feeds."""
        logger.info("📊 Market data feeds stopped")


# Convenience function for quick start
async def create_trading_system(config: Optional[Dict[str, Any]] = None) -> AITradingSystem:
    """
    Create and initialize an AI Trading System.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Initialized AITradingSystem instance
    """
    system = AITradingSystem(config)
    await system.initialize()
    return system
